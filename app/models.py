import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from app.database import Base

# --- AQUÍ ESTÁ EL CAMBIO ---
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    LANDLORD = "landlord"  # <--- El que faltaba
    TENANT = "tenant"      # <--- Probablemente lo necesites pronto

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # El rol por defecto. Si prefieres que sea 'tenant' o 'landlord', cámbialo aquí.
    role = Column(Enum(UserRole), default=UserRole.USER)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())