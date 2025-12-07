from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas import user as user_schema
from app.crud import user as user_crud
# Importamos get_current_user para proteger rutas sensibles (como listar todos)
from app.dependencies import get_current_user 
from app.models import User

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# 1. REGISTRO PÚBLICO (Cualquiera puede crear su cuenta)
@router.post("/", response_model=user_schema.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    # 1. Validar si existe el email
    db_user = user_crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado.")
    
    # 2. Crear usuario
    return user_crud.create_user(db=db, user=user)

# 2. LISTAR USUARIOS (PROTEGIDO - Solo usuarios logueados)
@router.get("/", response_model=List[user_schema.UserResponse])
def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # <--- Protegido
):
    """
    Lista todos los usuarios registrados.
    Requiere estar autenticado.
    """
    users = user_crud.get_users(db, skip=skip, limit=limit)
    return users