from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DECIMAL, DateTime, Text, Enum, JSON
from sqlalchemy.orm import relationship, declarative_mixin
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum

# --- 1. ENUMS ---
class UserRole(str, enum.Enum):
    admin = "admin"
    landlord = "landlord"
    tenant = "tenant"

class PropertyStatus(str, enum.Enum):
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

# --- 2. MIXINS (Aquí estaba el error) ---

@declarative_mixin
class TimestampMixin:
    """Agrega marcas de tiempo automáticas."""
    # CORRECCIÓN: Agregados los paréntesis () a func.now()
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

@declarative_mixin
class SoftDeleteMixin:
    """Permite borrar lógico."""
    is_deleted = Column(Boolean, default=False)

# Función auxiliar ID
def generate_uuid():
    return str(uuid.uuid4())

# --- 3. MODELOS ---

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
    audit_logs = relationship("AuditLog", back_populates="user")

class Property(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "properties"

    id = Column(String, primary_key=True, default=generate_uuid)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    title = Column(String, nullable=False)
    description = Column(Text)
    address = Column(String)
    
    latitude = Column(DECIMAL(9, 6))
    longitude = Column(DECIMAL(9, 6))
    
    price = Column(DECIMAL(10, 2), nullable=False)
    status = Column(Enum(PropertyStatus), default=PropertyStatus.available)
    
    owner = relationship("User", back_populates="properties")
    contracts = relationship("Contract", back_populates="property")
    maintenance_tickets = relationship("MaintenanceTicket", back_populates="property")

class Contract(Base, TimestampMixin):
    __tablename__ = "contracts"

    id = Column(String, primary_key=True, default=generate_uuid)
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    tenant_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    payment_day = Column(Integer, default=5)
    amount = Column(DECIMAL(10, 2), nullable=False)
    
    contract_file_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    property = relationship("Property", back_populates="contracts")
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
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
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
    
    # CORRECCIÓN: Agregados los paréntesis () aquí también
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="audit_logs")