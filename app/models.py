import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from app.database import Base

# --- CORRECCIÓN: Usamos minúsculas en las claves para coincidir con tu Schema ---
class UserRole(str, enum.Enum):
    admin = "admin"       # Antes era ADMIN
    user = "user"         # Antes era USER
    landlord = "landlord" # Esto arreglará el AttributeError
    tenant = "tenant"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Aquí referenciamos UserRole.user (minúscula)
    role = Column(Enum(UserRole), default=UserRole.user)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())