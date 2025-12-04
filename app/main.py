from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import engine, Base, get_db
from app import models 
from app.routers import users
from app.routers import auth 
from app.routers import properties
from app.routers import contracts
from app.routers import payments
from app.routers import tickets

# Crear tablas
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Zerium API",
    version="1.0.0",
    description="Backend profesional para la gestión inmobiliaria Zerium"
)

# --- CONFIGURACIÓN DE CORS PARA PRODUCCIÓN ---
origins = [
    "http://localhost:5173",    # Tu entorno local
    "http://127.0.0.1:5173",    # Tu entorno local (IP)
    "*"                         # <--- EL COMODÍN MÁGICO PARA EL PRIMER DESPLIEGUE
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # Usa la lista con el asterisco
    allow_credentials=True,
    allow_methods=["*"],        # Permitir todo (GET, POST, etc.)
    allow_headers=["*"],        # Permitir tokens y auth headers
)
# ---------------------------------------------

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(properties.router)
app.include_router(contracts.router)
app.include_router(payments.router)
app.include_router(tickets.router)

@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido al Backend de Zerium - Modo Profesional 🚀"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "Conectada exitosamente a Supabase ✅"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}