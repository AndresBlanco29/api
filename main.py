from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

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

# CORS para Flutter
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Reemplaza "*" por el dominio real si es necesario
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Manejo de conexiones WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# WebSocket endpoint
@app.websocket("/ws/ventas")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Para mantener la conexión activa
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Endpoint para obtener ventas
@app.get("/ventas")
def obtener_ventas():
    db = SessionLocal()
    ventas = db.query(Venta).all()
    resultado = [{"Id_Venta": v.Id_Venta, "Fecha_Venta": v.Fecha_Venta.isoformat(), "Total_Venta": v.Total_Venta} for v in ventas]
    db.close()
    return resultado

# Endpoint para crear una venta (ejemplo de uso real)
from datetime import datetime
from fastapi import Body

@app.post("/ventas")
async def crear_venta(total: float = Body(...)):
    db = SessionLocal()
    nueva_venta = Venta(Total_Venta=total, Fecha_Venta=datetime.now())
    db.add(nueva_venta)
    db.commit()
    db.refresh(nueva_venta)
    db.close()

    # Enviar la nueva venta a todos los clientes conectados
    await manager.broadcast("nueva_venta")
    return {"mensaje": "Venta creada", "venta": {
        "Id_Venta": nueva_venta.Id_Venta,
        "Fecha_Venta": nueva_venta.Fecha_Venta.isoformat(),
        "Total_Venta": nueva_venta.Total_Venta
    }}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

