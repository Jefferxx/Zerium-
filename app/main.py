from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import engine, Base, get_db
from app import models 
# Importamos los routers (las rutas de nuestra API)
from app.routers import users
from app.routers import auth  # <--- NUEVO: Importamos el router de Auth

# Crear las tablas en la base de datos automáticamente
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Zerium API",
    version="1.0.0",
    description="Backend profesional para la gestión inmobiliaria Zerium"
)

# --- REGISTRO DE ROUTERS ---
# Aquí le decimos a FastAPI: "Agrega estas rutas a tu lista"
app.include_router(users.router)
app.include_router(auth.router)  # <--- NUEVO: Registramos las rutas de Login

@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido al Backend de Zerium - Modo Profesional 🚀"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Consulta de prueba para verificar conexión
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "Conectada exitosamente a Supabase ✅"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}