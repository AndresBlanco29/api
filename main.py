from fastapi import FastAPI, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, ForeignKey, String, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
from typing import List
from datetime import datetime, timedelta, time as dt_time
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

class Admin(Base):
    __tablename__ = "admin"
    id_admin = Column(Integer, primary_key=True, index=True)
    usuario = Column(String(100))
    contrasena = Column(String(100))
    Nombre = Column(String(100))
    telefono = Column(Integer)
    correo_electronico = Column(String(100))

class Venta(Base):
    __tablename__ = "ventas"
    Id_Venta = Column(Integer, primary_key=True, index=True)
    Fecha_Venta = Column(DateTime)
    Total = Column(Float)
    Empleados_Id_Empleados = Column(Integer, ForeignKey("empleados.Id_Empleados"))

    empleado = relationship("Empleado")

class Entrada(Base):
    __tablename__ = "entrada_dinero"
    Id_Entrada = Column(Integer,primary_key=True, index=True)
    Asunto = Column(String(100))
    Cantidad = Column(Float)
    Cajero = Column(String(100))
    Fecha = Column(DateTime)

class Salida(Base):
    __tablename__ = "salida_dinero"
    Id_Salida = Column(Integer,primary_key=True, index=True)
    Asunto = Column(String(100))
    Cantidad = Column(Float)
    Cajero = Column(String(100))
    Fecha = Column(DateTime)

class Empleado(Base):  # Renombrar la clase
    __tablename__ = "empleados"
    Id_Empleados = Column(Integer, primary_key=True, index=True)
    Nombres = Column(String(100))
    Telefono = Column(String(100))
    Correo = Column(String(100))
    Fecha_nacimiento = Column(DateTime, nullable=True)
    Fecha_ingreso = Column(DateTime, nullable=True)
    Cargo = Column(String(90), nullable=True)

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
    url_imagen = Column(String(255))

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

@app.get("/admin")
def validar_admin(db: Session = Depends(get_db)):
    admins = db.query(Admin).all()
    return [
        {
            "id_admin": a.id_admin,
            "usuario": a.usuario,
            "contrasena": a.contrasena,
            "Nombre": a.Nombre,
            "telefono": a.telefono,
            "correo_electronico": a.correo_electronico
        }
        for a in admins
    ]

    
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
    return ventas

@app.get("/finanzas")
def obtener_entrada_salida_dinero(db: Session = Depends(get_db)):
    entradas = db.query(Entrada).all()
    salidas = db.query(Salida).all()
    return {
        "entradas": entradas,
        "salidas": salidas
    }


    

@app.get("/productos")
def obtener_productos(db: Session = Depends(get_db)):
    productos = db.query(Producto).all()
    resultado = []

    for p in productos:
        resultado.append({
            "id": p.Id_Producto,
            "nombre": p.Nombre,
            "precio_venta": p.Precio_Venta,
            "precio_compra": p.Precio_Compra,
            "cantidad": p.Cantidad,
            "marca": p.Marca,
            "descripcion": p.Descripcion,
            "categoria": p.Categoria,
            "fecha_entrada": p.Fecha_Entrada.strftime("%Y-%m-%d") if p.Fecha_Entrada else None,
            "fecha_vencimiento": p.Fecha_Vencimiento.strftime("%Y-%m-%d") if p.Fecha_Vencimiento else None,
            "unidad_medida": p.Unidad_Medida,
            "proveedor": p.proveedor.Nombre if p.proveedor else None,
            "ubicacion_estante": p.Ubicacion_Estante,
            "ubicacion_pasillo": p.ubicacion_pasillo,
            "codigo_barras": p.Codigo_Barras,
            "url_imagen": p.url_imagen,
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
        "precio": float(r[3] or 0),
        "costo": float(r[4] or 0),
        "codigo_barras": r[5],
        "cantidad": r[6] or 0,
        "total": float(r[7] or 0),
        "costo_total": float(r[8] or 0),
        "ganancia": float(r[7] or 0) - float(r[8] or 0)
    }
    for r in resultado
]

def obtener_rotacion_todos(db: Session, fecha_inicio: datetime, orden: str = "desc"):
    query = (
        db.query(
            Producto.Id_Producto,
            Producto.Nombre,
            Producto.Marca,
            Producto.Precio_Venta,
            Producto.Precio_Compra,
            Producto.Codigo_Barras,
            func.coalesce(func.sum(ProductoHasVenta.Cantidad), 0).label("cantidad_total"),
            func.coalesce(func.sum(ProductoHasVenta.Subtotal), 0).label("ventas_total"),
            func.coalesce(func.sum(Producto.Precio_Compra * ProductoHasVenta.Cantidad), 0).label("costo_total")
        )
        .outerjoin(ProductoHasVenta, Producto.Id_Producto == ProductoHasVenta.Productos_Id_Producto)
        .outerjoin(Venta, Venta.Id_Venta == ProductoHasVenta.Ventas_Id_Factura)
        .filter(
            (Venta.Fecha_Venta >= fecha_inicio) | (Venta.Fecha_Venta == None)
        )
        .group_by(Producto.Id_Producto)
    )
    
    if orden == "asc":
        query = query.order_by(func.coalesce(func.sum(ProductoHasVenta.Cantidad), 0).asc())
    else:
        query = query.order_by(func.coalesce(func.sum(ProductoHasVenta.Cantidad), 0).desc())
        
    resultado = query.limit(7).all()
    
    return [
        {
            "id": r[0],
            "nombre": r[1],
            "marca": r[2],
            "precio": float(r[3] or 0),
            "costo": float(r[4] or 0),
            "codigo_barras": r[5],
            "cantidad": r[6] or 0,
            "total": float(r[7] or 0),
            "costo_total": float(r[8] or 0),
            "ganancia": float(r[7] or 0) - float(r[8] or 0)
        }
        for r in resultado
    ]

@app.get("/rotacion/dia")
def productos_mas_vendidos_dia(db: Session = Depends(get_db), orden: str = "desc"):
    # Ajustar para incluir todo el día (inicio del día)
    hoy = datetime.combine(datetime.now().date(), dt_time.min)
    return obtener_rotacion(db, fecha_inicio=hoy, orden=orden)

@app.get("/rotacion/mes")
def productos_mas_vendidos_mes(db: Session = Depends(get_db), orden: str = "desc"):
    # Ajustar para incluir el primer día completo del mes
    primer_dia_mes = datetime.combine(datetime.now().replace(day=1).date(), dt_time.min)
    return obtener_rotacion(db, fecha_inicio=primer_dia_mes, orden=orden)

@app.get("/rotacion/masVendidos/dia")
def productos_mas_vendidos_dia_mas(db: Session = Depends(get_db), orden: str = "desc"):
    hoy = datetime.now().date()
    return obtener_rotacion(db, fecha_inicio=hoy, orden=orden)

@app.get("/rotacion/masVendidos/mes")
def productos_mas_vendidos_mes_mas(db: Session = Depends(get_db), orden: str = "desc"):
    primer_dia_mes = datetime.now().replace(day=1).date()
    return obtener_rotacion(db, fecha_inicio=primer_dia_mes, orden=orden)
    
@app.get("/rotacion/todos/{periodo}")
def productos_todos_rotacion(periodo: str, db: Session = Depends(get_db), orden: str = "desc"):
    if periodo == "dia":
        fecha_inicio = datetime.now().date()
    elif periodo == "mes":
        fecha_inicio = datetime.now().replace(day=1).date()
    else:
        return {"error": "Periodo no válido"}
    return obtener_rotacion_todos(db, fecha_inicio=fecha_inicio, orden=orden)

@app.get("/sales")
def sales_data(start: str, end: str, aggregation: str = "Diario", db: Session = Depends(get_db)):
    try:
        # 1. Parsear fechas ISO UTC directamente.
        #    datetime.fromisoformat maneja 'Z' o '+00:00'. Usamos replace para compatibilidad.
        start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))

        # --- Logging para Depuración ---
        print("-" * 20)
        print(f"Endpoint /sales - Recibido:")
        print(f"  Raw start: {start}")
        print(f"  Raw end: {end}")
        print(f"  Aggregation: {aggregation}")
        print(f"Parseado:")
        print(f"  start_date: {start_date} (TZ: {start_date.tzinfo})")
        print(f"  end_date: {end_date} (TZ: {end_date.tzinfo})")
        print("-" * 20)
        # --- Fin Logging ---

    except ValueError as e:
        print(f"ERROR [sales_data]: Error parseando fechas - Start='{start}', End='{end}'. Error: {e}")
        raise HTTPException(status_code=400, detail=f"Formato de fecha inválido: {e}")
    except Exception as e: # Captura otros errores inesperados durante el parseo
         print(f"ERROR [sales_data]: Error inesperado parseando fechas - {e}")
         raise HTTPException(status_code=500, detail="Error interno procesando fechas.")

    # 2. Realizar consulta a la Base de Datos
    if aggregation.lower() == "diario":
        try:
            # Agrupar por día calendario (basado en la fecha UTC)
            results = db.query(
                func.date(Venta.Fecha_Venta).label("date"), # func.date extrae la parte de fecha
                func.sum(Venta.Total).label("ventas")
            ).filter(
                Venta.Fecha_Venta >= start_date, # Comparación con fechas UTC
                Venta.Fecha_Venta <= end_date
            ).group_by(
                func.date(Venta.Fecha_Venta) # Agrupa por el día
            ).order_by(
                func.date(Venta.Fecha_Venta) # Ordena por fecha
            ).all()

            print(f"INFO [sales_data]: Resultados BD (Diario): {results}")

            # 3. Formatear la respuesta para agregación diaria
            return [
                {
                    # Combina la fecha (date) con la hora mínima (00:00:00) y formatea como ISO UTC
                    "date": datetime.combine(r.date, dt_time.min).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "ventas": float(r.ventas or 0) # Asegura que sea float, maneja None
                }
                for r in results
            ]
        except Exception as e:
            print(f"ERROR [sales_data]: Error en consulta DB (Diario) - {e}")
            # Considerar loggear el traceback completo para depuración
            # import traceback
            # print(traceback.format_exc())
            raise HTTPException(status_code=500, detail="Error consultando datos agregados.")

    else: # Si no es 'Diario', devolver datos individuales (o implementar otras agregaciones)
         try:
            # Obtener ventas individuales dentro del rango UTC
            ventas = db.query(Venta).filter(
                Venta.Fecha_Venta >= start_date,
                Venta.Fecha_Venta <= end_date
            ).order_by(
                Venta.Fecha_Venta # Ordenar por fecha/hora
            ).all()

            print(f"INFO [sales_data]: Resultados BD (No-Diario): {len(ventas)} registros")

            # 3. Formatear la respuesta para datos individuales
            return [
                {
                    # Formatear timestamp completo como ISO UTC
                    "date": v.Fecha_Venta.strftime("%Y-%m-%dT%H:%M:%SZ") if v.Fecha_Venta else None,
                    "ventas": float(v.Total or 0) # Asegura que sea float, maneja None
                }
                for v in ventas
            ]
         except Exception as e:
            print(f"ERROR [sales_data]: Error en consulta DB (No-Diario) - {e}")
            # import traceback
            # print(traceback.format_exc())
            raise HTTPException(status_code=500, detail="Error consultando datos detallados.")

@app.get("/ventas-fechas")
def obtener_fechas_ventas(db: Session = Depends(get_db)):
    fechas = db.query(Venta.Fecha_Venta).order_by(Venta.Fecha_Venta.asc()).limit(10).all()
    return [{"fecha": f[0]} for f in fechas]



@app.get("/empleados")
def obtener_empleados(db: Session = Depends(get_db)):
    empleados = db.query(Empleado).all()
    return [
        {
            "Id_Empleados": e.Id_Empleados,
            "Nombres": e.Nombres,
            "Telefono": e.Telefono,
            "Correo": e.Correo,
            "Fecha_nacimiento": e.Fecha_nacimiento.strftime("%Y-%m-%d %H:%M:%S") if e.Fecha_nacimiento else None,
            "Fecha_ingreso": e.Fecha_ingreso.strftime("%Y-%m-%d %H:%M:%S") if e.Fecha_ingreso else None,
            "Cargo": e.Cargo
        }
        for e in empleados
    ]
    
# ---------------------
# Ejecutar servidor
# ---------------------

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
