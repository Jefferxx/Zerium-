from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.models import User
from app.schemas.user import UserCreate

# Configuración de encriptación (Hashing)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user_by_email(db: Session, email: str):
    """Busca si un usuario ya existe por su email."""
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    """Crea un nuevo usuario con contraseña encriptada."""
    # 1. Encriptar la contraseña (Hashing)
    hashed_password = pwd_context.hash(user.password)
    
    # 2. Crear la instancia del modelo User (Base de datos)
    db_user = User(
        email=user.email,
        password_hash=hashed_password, # Guardamos el hash, NO la password real
        full_name=user.full_name,
        phone_number=user.phone_number,
        role=user.role
    )
    
    # 3. Guardar en Supabase
    db.add(db_user)
    db.commit()
    db.refresh(db_user) # Recargar para obtener el ID generado y created_at
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Obtiene una lista de usuarios"""
    return db.query(User).offset(skip).limit(limit).all()