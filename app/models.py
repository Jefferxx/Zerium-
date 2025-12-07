"""
MODELOS DE BASE DE DATOS (ORM) - ZERIUM
---------------------------------------------------------
Estructura optimizada para MVP con módulo de Pagos.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DECIMAL, DateTime, Date, Text, Enum, JSON
from sqlalchemy.orm import relationship, declarative_mixin
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum
from datetime import datetime

# ==============================================================================
# 1. ENUMS
# ==============================================================================

class UserRole(str, enum.Enum):
    admin = "admin"
    landlord = "landlord"
    tenant = "tenant"

class PropertyType(str, enum.Enum):
    house = "house"
    building = "building"
    commercial = "commercial"
    land = "land"

class UnitType(str, enum.Enum):
    apartment = "apartment"
    house = "house"
    room = "room"
    office = "office"
    store = "store"

class UnitStatus(str, enum.Enum):
    available = "available"
    occupied = "occupied"
    maintenance = "maintenance"

class TicketPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    emergency = "emergency"

# ==============================================================================
# 2. MIXINS
# ==============================================================================

@declarative_mixin
class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

@declarative_mixin
class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False)

def generate_uuid():
    return str(uuid.uuid4())

# ==============================================================================
# 3. TABLAS
# ==============================================================================

class User(Base, TimestampMixin):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    phone_number = Column(String)
    role = Column(Enum(UserRole), default=UserRole.landlord)
    is_active = Column(Boolean, default=True)
    
    properties = relationship("Property", back_populates="owner")
    contracts_as_tenant = relationship("Contract", back_populates="tenant")
    # audit_logs = relationship("AuditLog", back_populates="user") # Opcional por ahora

class Property(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "properties"
    id = Column(String, primary_key=True, default=generate_uuid)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(Enum(PropertyType), nullable=False)
    address = Column(String)
    city = Column(String, default="Riobamba")
    description = Column(Text)
    amenities = Column(JSON, nullable=True) 
    latitude = Column(DECIMAL(9, 6))
    longitude = Column(DECIMAL(9, 6))
    
    owner = relationship("User", back_populates="properties")
    units = relationship("Unit", back_populates="property", cascade="all, delete-orphan")
    maintenance_tickets = relationship("MaintenanceTicket", back_populates="property")

class Unit(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "units"
    id = Column(String, primary_key=True, default=generate_uuid)
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    unit_number = Column(String, nullable=False)
    type = Column(Enum(UnitType), default=UnitType.apartment)
    floor = Column(Integer, nullable=True)
    bedrooms = Column(Integer, default=1)
    bathrooms = Column(DECIMAL(3, 1), default=1.0)
    area_m2 = Column(DECIMAL(10, 2))
    base_price = Column(DECIMAL(10, 2), nullable=False)
    status = Column(Enum(UnitStatus), default=UnitStatus.available)
    
    property = relationship("Property", back_populates="units")
    contracts = relationship("Contract", back_populates="unit")

class Contract(Base, TimestampMixin):
    __tablename__ = "contracts"
    id = Column(String, primary_key=True, default=generate_uuid)
    unit_id = Column(String, ForeignKey("units.id"), nullable=False)
    tenant_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    start_date = Column(Date, nullable=False) # Cambiado a Date para simplificar
    end_date = Column(Date, nullable=False)   # Cambiado a Date
    payment_day = Column(Integer, default=5)
    amount = Column(DECIMAL(10, 2), nullable=False)
    
    # --- CAMPO CRÍTICO PARA PAGOS ---
    balance = Column(DECIMAL(10, 2), default=0.00) # Deuda actual
    
    contract_file_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    unit = relationship("Unit", back_populates="contracts")
    tenant = relationship("User", back_populates="contracts_as_tenant")
    payments = relationship("Payment", back_populates="contract")

# --- MODELO DE PAGOS ACTUALIZADO ---
class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=generate_uuid)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    
    amount = Column(DECIMAL(10, 2), nullable=False)
    payment_date = Column(DateTime, default=datetime.now) # Fecha real del pago
    
    # Campos descriptivos simples
    payment_method = Column(String) # "Efectivo", "Transferencia"
    notes = Column(Text, nullable=True) # "Pago mes Enero"

    contract = relationship("Contract", back_populates="payments")

class MaintenanceTicket(Base, TimestampMixin):
    __tablename__ = "maintenance_tickets"
    id = Column(String, primary_key=True, default=generate_uuid)
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    unit_id = Column(String, ForeignKey("units.id"), nullable=True) 
    requester_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    priority = Column(Enum(TicketPriority), default=TicketPriority.medium)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

    property = relationship("Property", back_populates="maintenance_tickets")