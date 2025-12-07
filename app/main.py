from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import engine, Base, get_db
from app import models 

# Importación limpia de todos los routers
from app.routers import (
    users, 
    auth, 
    properties, 
    contracts, 
    payments, 
    tickets, 
    dashboard  # <--- NUEVO
)

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
    "*"                         # Permitir todo (Vercel, Render, etc.)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      
    allow_credentials=True,
    allow_methods=["*"],        
    allow_headers=["*"],        
)
# ---------------------------------------------

# Inclusión de Routers (El orden no altera el producto, pero auth primero es buena práctica)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(properties.router)
app.include_router(contracts.router)
app.include_router(payments.router)
app.include_router(tickets.router)
app.include_router(dashboard.router) # <--- REGISTRAMOS EL DASHBOARD

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