from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi.middleware.cors import CORSMiddleware

# URL de conexión Railway
DATABASE_URL = "mysql+mysqlconnector://root:jAvqAVgchtkGmQIWjgMkOqaptECwSVKk@metro.proxy.rlwy.net:49192/railway"

# Configuración de SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo de la tabla ventas
class Venta(Base):
    __tablename__ = "ventas"
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime)
    total = Column(Float)

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
    resultado = [{"id": v.id, "fecha": v.fecha.isoformat(), "total": v.total} for v in ventas]
    db.close()
    return resultado
