from fastapi import FastAPI, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, ForeignKey, String, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
from typing import List
import time
import uvicorn

# URL de conexión Railway
DATABASE_URL = "mysql+mysqlconnector://root:gOETksBanEaqSzdndWKVEQKKoHWaRmIU@hopper.proxy.rlwy.net:54973/railway"

# Configuración de SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---------------------
# Modelos de Base de Datos
# ---------------------

class Venta(Base):
    __tablename__ = "ventas"
    Id_Venta = Column(Integer, primary_key=True, index=True)
    Fecha_Venta = Column(DateTime)
    Total = Column(Float)
    Empleados_Id_Empleados = Column(Integer, ForeignKey("empleados.Id_Empleados"))

    empleado = relationship("empleados")

class empleados(Base):
    __tablename__ = "empleados"
    Id_Empleados = Column(Integer, primary_key=True, index=True)
    Nombres = Column(String(100))
    Telefono = Column(String(100))
    Correo = Column(String(100))

class Producto(Base):
    __tablename__ = "productos"
    Id_Producto = Column(Integer, primary_key=True, index=True)
    Nombre = Column(String(90))
    Precio_Venta = Column(Float)
    Precio_Compra = Column(Float)
    Cantidad = Column(Integer)
    Marca = Column(String(90))
    Descripcion = Column(String)
    Categoria = Column(String(50))
    Fecha_Entrada = Column(DateTime)
    Fecha_Vencimiento = Column(DateTime)
    Unidad_Medida = Column(String(20))
    Proveedor_ID = Column(Integer, ForeignKey("proveedores.Id_Proveedor"))
    Ubicacion_Estante = Column(String(50))
    Codigo_Barras = Column(String(50))
    ubicacion_pasillo = Column(String(50))

    proveedor = relationship("Proveedor", back_populates="productos")
    
class Proveedor(Base):
    __tablename__ = "proveedores"
    Id_Proveedor = Column(Integer, primary_key=True, index=True)
    Nombre = Column(String(100))
    Telefono = Column(String(20))
    Direccion = Column(String(200))
    Email = Column(String(100))

    productos = relationship("Producto", back_populates="proveedor")


class ProductoHasVenta(Base):
    __tablename__ = "productos_has_ventas"
    id = Column(Integer, primary_key=True, index=True)
    Ventas_Id_Factura = Column(Integer, ForeignKey("ventas.Id_Venta"))
    Productos_Id_Producto = Column(Integer, ForeignKey("productos.Id_Producto"))
    Cantidad = Column(Integer)
    Subtotal = Column(Float)

    venta = relationship("Venta")
    producto = relationship("Producto")
    

# ---------------------
# FastAPI App
# ---------------------

app = FastAPI()

# CORS para Flutter
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambiar a dominio real si es necesario
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------
# Dependencia para DB
# ---------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------
# Endpoints
# ---------------------

@app.get("/ventas")
def obtener_ventas(db: Session = Depends(get_db)):
    ventas = db.query(Venta).all()
    resultado = []

    for v in ventas:
        # Buscar productos vendidos relacionados con esta venta
        productos_vendidos = db.query(ProductoHasVenta).filter(
            ProductoHasVenta.Ventas_Id_Factura == v.Id_Venta
        ).all()

        productos = []
        for pv in productos_vendidos:
            productos.append({
                "Nombre_Producto": pv.producto.Nombre if pv.producto else None,
                "Cantidad": pv.Cantidad,
                "Precio": pv.producto.Precio_Venta if pv.producto else None
            })

        resultado.append({
            "Id_Venta": v.Id_Venta,
            "Fecha_Venta": v.Fecha_Venta.strftime("%Y-%m-%d %H:%M:%S"),
            "Total": v.Total,
            "empleados": {
                "Nombres": v.empleado.Nombres if v.empleado else None
            },
            "productos_vendidos": productos
        })

    return resultado


@app.get("/start-updating")
async def start_updating(background_tasks: BackgroundTasks):
    background_tasks.add_task(actualizar_ventas)
    return {"message": "Task started"}

# ---------------------
# Background Task
# ---------------------

def actualizar_ventas():
    while True:
        print("Actualizando ventas...")
        db = SessionLocal()
        ventas = db.query(Venta).all()
        # Aquí podrías enviar los datos a otro sistema si es necesario
        db.close()
        time.sleep(5)  # Esperar 5 segundos entre iteraciones

# ---------------------
# Rotación de productos
# ---------------------

@app.get("/rotacion/dia")
def productos_mas_vendidos_dia(db: Session = Depends(get_db), orden: str = "desc"):
    hoy = datetime.now().date()
    return obtener_rotacion(db, fecha_inicio=hoy, orden=orden)

@app.get("/rotacion/mes")
def productos_mas_vendidos_mes(db: Session = Depends(get_db), orden: str = "desc"):
    primer_dia_mes = datetime.now().replace(day=1).date()
    return obtener_rotacion(db, fecha_inicio=primer_dia_mes, orden=orden)

def obtener_rotacion(db: Session, fecha_inicio: datetime, orden: str = "desc", top_n: int = 5):
    query = (
        db.query(
            Producto.Id_Producto,
            Producto.Nombre,
            Producto.Marca,
            Producto.Precio_Venta,
            Producto.Precio_Compra,  # Obtenemos el costo de compra
            Producto.Codigo_Barras,
            func.sum(ProductoHasVenta.Cantidad).label("cantidad_total"),
            func.sum(ProductoHasVenta.Subtotal).label("ventas_total"),
            func.sum(Producto.Precio_Compra * ProductoHasVenta.Cantidad).label("costo_total")  # Calculamos el costo total
        )
        .join(Producto, Producto.Id_Producto == ProductoHasVenta.Productos_Id_Producto)
        .join(Venta, Venta.Id_Venta == ProductoHasVenta.Ventas_Id_Factura)
        .filter(Venta.Fecha_Venta >= fecha_inicio)
        .group_by(Producto.Id_Producto)
    )

    if orden == "asc":
        query = query.order_by(func.sum(ProductoHasVenta.Cantidad).asc())
    else:
        query = query.order_by(func.sum(ProductoHasVenta.Cantidad).desc())

    resultado = query.limit(top_n).all()

    # Calculamos la ganancia y retornamos los resultados
    return [
        {
            "id": r[0],
            "nombre": r[1],
            "marca": r[2],
            "precio": float(r[3]),
            "costo": float(r[4]),
            "codigo_barras": r[5],
            "cantidad": r[6],
            "total": float(r[7]),
            "costo_total": float(r[8]),
            "ganancia": float(r[7]) - float(r[8])  # Ganancia = ventas_total - costo_total
        }
        for r in resultado
    ]

# ---------------------
# Ejecutar servidor
# ---------------------

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

