import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Float, Text, JSON, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid # Opcional, por si necesitas generar UUIDs por defecto en el futuro

# =======================
# 1. ENUMS (CORREGIDOS)
# =======================

class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"
    landlord = "landlord"
    tenant = "tenant"

class PropertyType(str, enum.Enum):
    apartment = "apartment"
    house = "house"
    commercial = "commercial"
    building = "building" # <--- AGREGADO (Faltaba)

class UnitType(str, enum.Enum):
    room = "room"
    studio = "studio"
    apartment = "apartment"
    house = "house"       # <--- AGREGADO (Faltaba)

class UnitStatus(str, enum.Enum):
    vacant = "vacant"
    occupied = "occupied"
    maintenance = "maintenance"
    available = "available" # <--- AGREGADO (Faltaba)

class TicketPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    emergency = "emergency"

class TicketStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    resolved = "resolved"
    cancelled = "cancelled"

# =======================
# 2. TABLAS (MODELOS)
# =======================

class User(Base):
    __tablename__ = "users"

    # CORRECCIÓN: Cambiado a String para soportar UUIDs
    id = Column(String, primary_key=True, index=True)
    
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False) 
    full_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.user)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    properties = relationship("Property", back_populates="owner")
    contracts = relationship("Contract", back_populates="tenant")
    tickets_requested = relationship("MaintenanceTicket", back_populates="requester")


class Property(Base):
    __tablename__ = "properties"

    # CORRECCIÓN: Cambiado a String para soportar UUIDs
    id = Column(String, primary_key=True, index=True)
    
    name = Column(String, index=True)
    type = Column(Enum(PropertyType), default=PropertyType.apartment)
    address = Column(String)
    city = Column(String, default="Riobamba")
    description = Column(Text, nullable=True)
    
    amenities = Column(JSON, default={})
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_deleted = Column(Boolean, default=False)

    # Relación con Dueño (FK también debe ser String)
    owner_id = Column(String, ForeignKey("users.id"))
    owner = relationship("User", back_populates="properties")
    
    units = relationship("Unit", back_populates="property")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Unit(Base):
    __tablename__ = "units"

    # CORRECCIÓN: Cambiado a String para soportar UUIDs
    id = Column(String, primary_key=True, index=True)
    
    unit_number = Column(String)
    type = Column(Enum(UnitType), default=UnitType.apartment) 
    floor = Column(Integer, nullable=True)
    bedrooms = Column(Integer, default=1)
    bathrooms = Column(Float, default=1.0)
    area_m2 = Column(Float, nullable=True)
    base_price = Column(Float, nullable=True)
    
    status = Column(Enum(UnitStatus), default=UnitStatus.vacant)
    
    # FK debe ser String
    property_id = Column(String, ForeignKey("properties.id"))
    property = relationship("Property", back_populates="units")
    
    contracts = relationship("Contract", back_populates="unit")
    tickets = relationship("MaintenanceTicket", back_populates="unit")

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Contract(Base):
    __tablename__ = "contracts"

    # CORRECCIÓN: Cambiado a String para soportar UUIDs
    id = Column(String, primary_key=True, index=True)
    
    # FKs deben ser String
    unit_id = Column(String, ForeignKey("units.id"))
    tenant_id = Column(String, ForeignKey("users.id"))
    
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    balance = Column(Float, default=0.0)
    payment_day = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
    contract_file_url = Column(String, nullable=True)

    unit = relationship("Unit", back_populates="contracts")
    tenant = relationship("User", back_populates="contracts")
    payments = relationship("Payment", back_populates="contract")


class Payment(Base):
    __tablename__ = "payments"

    # CORRECCIÓN: Cambiado a String para soportar UUIDs
    id = Column(String, primary_key=True, index=True)
    
    # FK debe ser String
    contract_id = Column(String, ForeignKey("contracts.id"))
    
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    payment_method = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    contract = relationship("Contract", back_populates="payments")


class MaintenanceTicket(Base):
    __tablename__ = "maintenance_tickets"

    # CORRECCIÓN: Cambiado a String para soportar UUIDs
    id = Column(String, primary_key=True, index=True)
    
    title = Column(String, nullable=False)
    description = Column(Text)
    priority = Column(Enum(TicketPriority), default=TicketPriority.medium)
    status = Column(Enum(TicketStatus), default=TicketStatus.pending)
    
    # FKs deben ser String
    property_id = Column(String, ForeignKey("properties.id"))
    unit_id = Column(String, ForeignKey("units.id"), nullable=True)
    requester_id = Column(String, ForeignKey("users.id"))

    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

    requester = relationship("User", back_populates="tickets_requested")
    unit = relationship("Unit", back_populates="tickets")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())