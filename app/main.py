from fastapi import FastAPI, Depends
from app import models 
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import engine, Base, get_db
# 1. Crear las tablas en la base de datos automáticamente
# Al importar 'models', esta línea lee todas las clases definidas y las crea en Supabase
models.Base.metadata.create_all(bind=engine)

# 2. Inicializar la aplicación FastAPI
app = FastAPI(
    title="Zerium API",
    version="1.0.0",
    description="Backend profesional para la gestión inmobiliaria Zerium"
)

# 3. Ruta de inicio (Home)
@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido al Backend de Zerium - Modo Profesional 🚀"}

# 4. Ruta de salud (Health Check)
@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Consulta de prueba para verificar conexión
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "Conectada exitosamente a Supabase ✅"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}