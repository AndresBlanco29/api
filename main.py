from fastapi import FastAPI, BackgroundTasks
from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
from typing import List
from sqlalchemy import func, desc
import time

# URL de conexión Railway
DATABASE_URL = "mysql+mysqlconnector://root:gOETksBanEaqSzdndWKVEQKKoHWaRmIU@hopper.proxy.rlwy.net:54973/railway"

# Configuración de SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo de la tabla ventas
class Venta(Base):
    __tablename__ = "ventas"
    Id_Venta = Column(Integer, primary_key=True, index=True)
    Fecha_Venta = Column(DateTime)
    Total = Column(Float)


class Producto(Base):
    __tablename__ = "productos"
    Id_Producto = Column(Integer, primary_key=True, index=True)
    Nombre = Column(String(255))

class ProductosHasVentas(Base):
    __tablename__ = "productos_has_ventas"
    Productos_Id_Producto = Column(Integer, primary_key=True)
    Ventas_Id_Factura = Column(Integer, primary_key=True)
    Cantidad = Column(Integer)


# Crear la aplicación FastAPI
app = FastAPI()

# CORS para Flutter
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Reemplaza "*" por el dominio real si es necesario
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint para obtener ventas
@app.get("/ventas")
def obtener_ventas():
    db = SessionLocal()
    ventas = db.query(Venta).all()
    resultado = [{"Id_Venta": v.Id_Venta, "Fecha_Venta": v.Fecha_Venta.isoformat(), "Total": v.Total} for v in ventas]
    db.close()
    return resultado

# Función de fondo para actualizar ventas
def actualizar_ventas():
    while True:
        # Realiza el trabajo de actualización de ventas
        print("Actualizando ventas...")

        # Aquí puedes consultar la base de datos para obtener nuevas ventas y actualizarlas
        # Este código está solo para ilustración
        db = SessionLocal()
        ventas = db.query(Venta).all()
        # Aquí procesas las ventas o las envías a algún sistema

        time.sleep(1)  # Espera 5 segundos antes de hacer la siguiente actualización

# Endpoint para iniciar el background task
@app.get("/start-updating")
async def start_updating(background_tasks: BackgroundTasks):
    background_tasks.add_task(actualizar_ventas)
    return {"message": "Task started"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

@app.get("/productos-mas-vendidos")
def productos_mas_vendidos():
    db = SessionLocal()
    resultados = (
        db.query(
            Venta.Fecha_Venta,
            Producto.Nombre,
            func.sum(ProductosHasVentas.Cantidad).label("cantidad_vendida")
        )
        .join(ProductosHasVentas, ProductosHasVentas.Ventas_Id_Factura == Venta.Id_Venta)
        .join(Producto, Producto.Id_Producto == ProductosHasVentas.Productos_Id_Producto)
        .group_by(Producto.Nombre)
        .order_by(desc("cantidad_vendida"))
        .limit(10)
        .all()
    )
    db.close()
    return [
        {
            "nombre": r[1],
            "cantidad_vendida": r[2]
        } for r in resultados
    ]


