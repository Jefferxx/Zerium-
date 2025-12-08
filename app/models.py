import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# =======================
# 1. ENUMS (Listas de opciones)
# =======================

class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"
    landlord = "landlord"
    tenant = "tenant"

# Estos son los que te faltaban y causaban el error:
class PropertyType(str, enum.Enum):
    apartment = "apartment"
    house = "house"
    commercial = "commercial"

class UnitType(str, enum.Enum):
    room = "room"
    studio = "studio"
    apartment = "apartment"

class UnitStatus(str, enum.Enum):
    vacant = "vacant"
    occupied = "occupied"
    maintenance = "maintenance"


# =======================
# 2. MODELOS (Tablas de DB)
# =======================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.user)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relación: Un Landlord tiene muchas propiedades
    properties = relationship("Property", back_populates="landlord")


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True) # Ej: "Edificio Central"
    address = Column(String)
    description = Column(Text, nullable=True)
    property_type = Column(Enum(PropertyType), default=PropertyType.apartment)
    
    # Relación con el Dueño (Landlord)
    landlord_id = Column(Integer, ForeignKey("users.id"))
    landlord = relationship("User", back_populates="properties")
    
    # Relación: Una propiedad tiene muchas unidades
    units = relationship("Unit", back_populates="property")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True)
    unit_number = Column(String) # Ej: "A-101"
    floor = Column(Integer, nullable=True)
    rent_amount = Column(Float, nullable=True)
    
    unit_type = Column(Enum(UnitType), default=UnitType.apartment)
    status = Column(Enum(UnitStatus), default=UnitStatus.vacant)
    
    # Relación con la Propiedad Padre
    property_id = Column(Integer, ForeignKey("properties.id"))
    property = relationship("Property", back_populates="units")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())