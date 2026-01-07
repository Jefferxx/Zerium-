from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import engine, Base, get_db
from app import models 

# Importación de routers
from app.routers import (
    users, 
    auth, 
    properties, 
    contracts, 
    payments, 
    tickets, 
    dashboard
)

# Crear tablas
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Zerium API",
    version="1.0.0",
    description="Backend profesional para la gestión inmobiliaria Zerium"
)

# --- CONFIGURACIÓN DE CORS (SOLUCIÓN DEFINITIVA) ---
# Usamos allow_origin_regex para permitir:
# 1. Cualquier subdominio de Vercel de tu proyecto (https://zerium-frontend-....vercel.app)
# 2. Localhost en cualquier puerto (para desarrollo)
# 3. La URL oficial de producción
origin_regex = r"https://zerium-frontend.*\.vercel\.app|http://localhost:\d+|http://127\.0\.0\.1:\d+"

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=origin_regex,  # <--- AQUÍ ESTÁ EL CAMBIO CLAVE
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------------------------------------------

# Inclusión de Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(properties.router)
app.include_router(contracts.router)
app.include_router(payments.router)
app.include_router(tickets.router)
app.include_router(dashboard.router)

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