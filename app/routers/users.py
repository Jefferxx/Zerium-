from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import user as user_schema
from app.crud import user as user_crud

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post("/", response_model=user_schema.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo usuario en el sistema.
    - Verifica que el email no exista.
    - Encripta la contraseña.
    - Devuelve el usuario creado (sin la contraseña).
    """
    # 1. Validar si existe el email
    db_user = user_crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado.")
    
    # 2. Crear usuario
    return user_crud.create_user(db=db, user=user)