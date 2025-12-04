from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List  # <--- IMPORTANTE: Necesario para devolver listas
from app.database import get_db
from app.schemas import user as user_schema
from app.crud import user as user_crud
from app.models import User # Para tipado si hace falta, o auth

# (Opcional) Si quieres proteger la lista de usuarios solo para Admins/Landlords
from app.dependencies import get_current_user 

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post("/", response_model=user_schema.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    # 1. Validar si existe el email
    db_user = user_crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado.")
    
    # 2. Crear usuario
    return user_crud.create_user(db=db, user=user)

# --- NUEVO ENDPOINT: GET /users/ ---
@router.get("/", response_model=List[user_schema.UserResponse])
def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    # current_user = Depends(get_current_user) # Descomenta para proteger ruta
):
    """
    Lista todos los usuarios registrados.
    Usado por el Frontend para buscar UUIDs por email.
    """
    users = user_crud.get_users(db, skip=skip, limit=limit)
    return users