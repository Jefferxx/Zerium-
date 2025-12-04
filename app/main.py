from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware # <--- 1. IMPORTAR ESTO
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import engine, Base, get_db
from app import models 
from app.routers import users
from app.routers import auth 
from app.routers import properties
from app.routers import contracts
from app.routers import payments

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Zerium API",
    version="1.0.0",
    description="Backend profesional para la gestión inmobiliaria Zerium"
)

# --- 2. CONFIGURACIÓN DE CORS (CRÍTICO) ---
# Esto permite que el Frontend (puerto 5173) hable con el Backend
origins = [
    "http://localhost:5173",    # Frontend Vite Local
    "http://127.0.0.1:5173",    # Alternativa IP
    "http://localhost:3000",    # Por si usas otro puerto a veces
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # Qué dominios pueden entrar
    allow_credentials=True,     # Permitir cookies/tokens
    allow_methods=["*"],        # Permitir todos los métodos (GET, POST, PUT, DELETE)
    allow_headers=["*"],        # Permitir todos los headers
)
# ------------------------------------------

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(properties.router)
app.include_router(contracts.router)
app.include_router(payments.router)

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