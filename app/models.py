"""
MODELOS DE BASE DE DATOS (ORM) - ZERIUM v2.0 (Jerárquico)
---------------------------------------------------------
Este archivo define la estructura de la base de datos.
Arquitectura: Propietario -> Propiedad (Edificio/Casa) -> Unidades (Departamentos)
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DECIMAL, DateTime, Text, Enum, JSON
from sqlalchemy.orm import relationship, declarative_mixin
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum

# ==============================================================================
# 1. ENUMS (Reglas de Negocio Estrictas)
# ==============================================================================

class UserRole(str, enum.Enum):
    admin = "admin"
    landlord = "landlord"
    tenant = "tenant"

class PropertyType(str, enum.Enum):
    """Diferencia entre el tipo de construcción global."""
    house = "house"           # Casa unifamiliar
    building = "building"     # Edificio multifamiliar
    commercial = "commercial" # Centro comercial/Oficinas
    land = "land"             # Terreno vacío

class UnitType(str, enum.Enum):
    """Diferencia el tipo de espacio alquilable."""
    apartment = "apartment"
    house = "house"           # Si la propiedad es casa, la unidad también es casa
    room = "room"             # Habitación
    office = "office"
    store = "store"           # Local

class UnitStatus(str, enum.Enum):
    """Estado de ocupación de una unidad específica."""
    available = "available"
    occupied = "occupied"
    maintenance = "maintenance"

class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    late = "late"
    cancelled = "cancelled"
    refunded = "refunded"

class TicketPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    emergency = "emergency"

# ==============================================================================
# 2. MIXINS (Patrones de Diseño Reutilizables)
# ==============================================================================

@declarative_mixin
class TimestampMixin:
    """Agrega created_at y updated_at automáticamente."""
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

@declarative_mixin
class SoftDeleteMixin:
    """Permite ocultar registros en lugar de borrarlos."""
    is_deleted = Column(Boolean, default=False)

def generate_uuid():
    return str(uuid.uuid4())

# ==============================================================================
# 3. MODELOS DE TABLAS (SCHEMA)
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
    
    # Relaciones
    properties = relationship("Property", back_populates="owner")
    contracts_as_tenant = relationship("Contract", back_populates="tenant")
    audit_logs = relationship("AuditLog", back_populates="user")

class Property(Base, TimestampMixin, SoftDeleteMixin):
    """
    PROPIEDAD PADRE (El Activo Físico).
    Representa el Edificio completo, la Casa principal o el Terreno.
    NO se alquila directamente (se alquilan sus Unidades).
    """
    __tablename__ = "properties"

    id = Column(String, primary_key=True, default=generate_uuid)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    name = Column(String, nullable=False) # Ej: "Edificio Torres del Sol"
    type = Column(Enum(PropertyType), nullable=False)
    address = Column(String)
    city = Column(String, default="Riobamba")
    description = Column(Text)
    
    # Servicios Generales (JSON para flexibilidad: {pool: true, security: true})
    amenities = Column(JSON, nullable=True) 
    
    # Georreferencia (Para mapas)
    latitude = Column(DECIMAL(9, 6))
    longitude = Column(DECIMAL(9, 6))
    
    # Relaciones
    owner = relationship("User", back_populates="properties")
    # cascade="all, delete-orphan" significa que si borras el edificio, se borran sus deptos.
    units = relationship("Unit", back_populates="property", cascade="all, delete-orphan")
    maintenance_tickets = relationship("MaintenanceTicket", back_populates="property")

class Unit(Base, TimestampMixin, SoftDeleteMixin):
    """
    UNIDAD ALQUILABLE (El Producto).
    Es el Departamento 101, la Casa A, el Local 3.
    Aquí es donde vive el precio y el estado de ocupación.
    """
    __tablename__ = "units"

    id = Column(String, primary_key=True, default=generate_uuid)
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    
    unit_number = Column(String, nullable=False) # Ej: "101", "PB", "Casa Unica"
    type = Column(Enum(UnitType), default=UnitType.apartment)
    floor = Column(Integer, nullable=True) # Piso 1, 2, etc.
    
    # Características específicas
    bedrooms = Column(Integer, default=1)
    bathrooms = Column(DECIMAL(3, 1), default=1.0) # Soporta 1.5 baños
    area_m2 = Column(DECIMAL(10, 2))
    
    # Precio Base (Referencial para el mercado)
    base_price = Column(DECIMAL(10, 2), nullable=False)
    status = Column(Enum(UnitStatus), default=UnitStatus.available)
    
    # Relaciones
    property = relationship("Property", back_populates="units")
    contracts = relationship("Contract", back_populates="unit")

class Contract(Base, TimestampMixin):
    """
    Vincula una UNIDAD específica con un INQUILINO.
    """
    __tablename__ = "contracts"

    id = Column(String, primary_key=True, default=generate_uuid)
    # CAMBIO CRÍTICO: Ahora el contrato es con la UNIDAD, no con la PROPIEDAD
    unit_id = Column(String, ForeignKey("units.id"), nullable=False)
    tenant_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    payment_day = Column(Integer, default=5)
    amount = Column(DECIMAL(10, 2), nullable=False) # Precio real pactado
    
    contract_file_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relaciones
    unit = relationship("Unit", back_populates="contracts")
    tenant = relationship("User", back_populates="contracts_as_tenant")
    payments = relationship("Payment", back_populates="contract")

class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=generate_uuid)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    
    amount = Column(DECIMAL(10, 2), nullable=False)
    due_date = Column(DateTime, nullable=False)
    payment_date = Column(DateTime, nullable=True)
    
    status = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    proof_file_url = Column(String, nullable=True)
    transaction_id = Column(String, nullable=True)

    contract = relationship("Contract", back_populates="payments")

class MaintenanceTicket(Base, TimestampMixin):
    __tablename__ = "maintenance_tickets"

    id = Column(String, primary_key=True, default=generate_uuid)
    # Puede ser un problema del Edificio (property) o del Depto (unit)
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    unit_id = Column(String, ForeignKey("units.id"), nullable=True) 
    requester_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    title = Column(String, nullable=False)
    description = Column(Text)
    priority = Column(Enum(TicketPriority), default=TicketPriority.medium)
    
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

    property = relationship("Property", back_populates="maintenance_tickets")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    table_name = Column(String, nullable=False)
    record_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="audit_logs")