from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi.middleware.cors import CORSMiddleware

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
    Total_Venta = Column(Float)

# Crear la aplicación FastAPI
app = FastAPI()

# Permitir peticiones desde Flutter (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Reemplaza con el dominio de tu app si lo deseas restringir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint para obtener todas las ventas
@app.get("/ventas")
def obtener_ventas():
    db = SessionLocal()
    ventas = db.query(Venta).all()
    resultado = [{"Id_Venta": v.Id_Venta, "Fecha_Venta": v.Fecha_Venta.isoformat(), "Total_Venta": v.Total_Venta} for v in ventas]
    db.close()
    return resultado
    
import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
