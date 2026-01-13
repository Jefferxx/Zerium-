import enum
import uuid 
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Float, Text, JSON, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# =======================
# 1. ENUMS (Todos juntos al inicio)
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
    building = "building"

class UnitType(str, enum.Enum):
    room = "room"
    studio = "studio"
    apartment = "apartment"
    house = "house"
    store = "store"

class UnitStatus(str, enum.Enum):
    vacant = "vacant"
    occupied = "occupied"
    maintenance = "maintenance"
    available = "available"

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

# --- NUEVOS ENUMS PARA DOCUMENTOS ---
class DocumentType(str, enum.Enum):
    cedula = "cedula"
    antecedentes = "antecedentes" # Récord Policial
    buro_credito = "buro_credito" # Buró de crédito
    rol_pagos = "rol_pagos"       # Comprobante de ingresos
    otro = "otro"

class DocumentStatus(str, enum.Enum):
    pending = "pending"   # Subido, esperando revisión
    verified = "verified" # Aprobado por el dueño/admin
    rejected = "rejected" # Rechazado (foto borrosa, etc.)

# --- NUEVO ENUM PARA CONTRATOS ---
class ContractStatus(str, enum.Enum):
    pending = "pending"       # Creado, falta firma del inquilino
    active = "active"         # Firmado y vigente
    terminated = "terminated" # Finalizado
    rejected = "rejected"     # Inquilino rechazó

# =======================
# 2. TABLAS (MODELOS)
# =======================

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    
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
    
    # NUEVA RELACIÓN
    documents = relationship("UserDocument", back_populates="user")


class Property(Base):
    __tablename__ = "properties"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    type = Column(Enum(PropertyType), default=PropertyType.apartment)
    address = Column(String)
    city = Column(String, default="Riobamba")
    description = Column(Text, nullable=True)
    amenities = Column(JSON, default={})
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_deleted = Column(Boolean, default=False)

    owner_id = Column(String, ForeignKey("users.id"))
    owner = relationship("User", back_populates="properties")
    units = relationship("Unit", back_populates="property")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Unit(Base):
    __tablename__ = "units"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    unit_number = Column(String)
    type = Column(Enum(UnitType), default=UnitType.apartment) 
    floor = Column(Integer, nullable=True)
    bedrooms = Column(Integer, default=1)
    bathrooms = Column(Float, default=1.0)
    area_m2 = Column(Float, nullable=True)
    base_price = Column(Float, nullable=True)
    status = Column(Enum(UnitStatus), default=UnitStatus.vacant)
    
    property_id = Column(String, ForeignKey("properties.id"))
    property = relationship("Property", back_populates="units")
    
    contracts = relationship("Contract", back_populates="unit")
    tickets = relationship("MaintenanceTicket", back_populates="unit")

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    unit_id = Column(String, ForeignKey("units.id"))
    tenant_id = Column(String, ForeignKey("users.id"))
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    balance = Column(Float, default=0.0)
    payment_day = Column(Integer, default=5)
    
    # --- CAMBIOS DE ESTADO ---
    is_active = Column(Boolean, default=False) # Ahora nace inactivo
    status = Column(Enum(ContractStatus), default=ContractStatus.pending) # Nuevo campo status
    # -------------------------

    contract_file_url = Column(String, nullable=True)

    unit = relationship("Unit", back_populates="contracts")
    tenant = relationship("User", back_populates="contracts")
    payments = relationship("Payment", back_populates="contract")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String, ForeignKey("contracts.id"))
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    payment_method = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    contract = relationship("Contract", back_populates="payments")


class MaintenanceTicket(Base):
    __tablename__ = "maintenance_tickets"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text)
    priority = Column(Enum(TicketPriority), default=TicketPriority.medium)
    status = Column(Enum(TicketStatus), default=TicketStatus.pending)
    
    property_id = Column(String, ForeignKey("properties.id"))
    unit_id = Column(String, ForeignKey("units.id"), nullable=True)
    requester_id = Column(String, ForeignKey("users.id"))

    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

    requester = relationship("User", back_populates="tickets_requested")
    unit = relationship("Unit", back_populates="tickets")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# --- NUEVA TABLA: DOCUMENTOS DE USUARIO ---
class UserDocument(Base):
    __tablename__ = "user_documents"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    
    document_type = Column(Enum(DocumentType), default=DocumentType.otro)
    file_url = Column(String, nullable=False) # URL de Cloudinary
    public_id = Column(String, nullable=True) # ID para borrar en Cloudinary
    
    status = Column(Enum(DocumentStatus), default=DocumentStatus.pending)
    rejection_reason = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="documents")