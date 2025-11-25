from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import engine, Base, get_db
from app import models 
# --- NUEVO: Importar el router de usuarios ---
from app.routers import users 

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Zerium API",
    version="1.0.0",
    description="Backend profesional para la gestión inmobiliaria Zerium"
)

# --- NUEVO: Registrar el router en la app ---
app.include_router(users.router)

@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido al Backend de Zerium - Modo Profesional "}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "Conectada exitosamente a Supabase ✅"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}