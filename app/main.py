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

# Crear tablas en la base de datos
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Zerium API",
    version="1.0.0",
    description="Backend profesional para la gestión inmobiliaria Zerium"
)

# --- CONFIGURACIÓN DE CORS (MODO LISTA EXPLÍCITA - SOLUCIÓN SEGURA) ---
# Definimos exactamente quién puede conectarse para evitar bloqueos
origins = [
    "http://localhost:5173",       # Desarrollo local (Vite)
    "http://127.0.0.1:5173",       # Desarrollo local (IP)
    "https://zerium-frontend.vercel.app",  # <--- Tu dominio principal de Vercel
    "https://zerium-frontend-9ocul695u-jeffersonjordan2004-9065s-projects.vercel.app" # <--- Tu URL específica de despliegue
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # Usamos la lista exacta en lugar de regex
    allow_credentials=True,     # Permite cookies y tokens
    allow_methods=["*"],        # Permite todos los métodos (GET, POST, PUT, DELETE...)
    allow_headers=["*"],        # Permite todos los headers
)
# -----------------------------------------------------------------------

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
        # Prueba simple de conexión a la base de datos
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "Conectada exitosamente a Supabase ✅"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}