"""
MODELOS DE BASE DE DATOS (ORM) - ZERIUM
---------------------------------------
Este archivo define la estructura de la base de datos usando SQLAlchemy.
Aquí transformamos clases de Python en tablas de SQL (PostgreSQL).

Conceptos clave aplicados:
1. Enums: Para restringir valores y evitar datos basura.
2. Mixins: Para reutilizar código (DRY - Don't Repeat Yourself).
3. Relaciones: Para conectar tablas (Foreign Keys).
4. Auditoría: Para rastrear cambios.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DECIMAL, DateTime, Text, Enum, JSON
from sqlalchemy.orm import relationship, declarative_mixin
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum

# ==============================================================================
# 1. ENUMS (REGLAS DE NEGOCIO)
# ==============================================================================
# Usamos 'enum.Enum' de Python para garantizar que solo se guarden valores válidos.
# Esto previene errores como escribir "pagado" en lugar de "paid".

class UserRole(str, enum.Enum):
    """Roles de usuario para el control de acceso (RBAC)."""
    admin = "admin"       # Superusuario
    landlord = "landlord" # Cliente principal (Dueño)
    tenant = "tenant"     # Cliente final (Inquilino)

class PropertyStatus(str, enum.Enum):
    """Estado físico/legal de la propiedad."""
    available = "available"     # Lista para alquilar
    occupied = "occupied"       # Tiene un contrato activo
    maintenance = "maintenance" # En reparación

class PaymentStatus(str, enum.Enum):
    """Ciclo de vida de un pago."""
    pending = "pending"     # Se generó la deuda pero no han pagado
    paid = "paid"           # Dinero recibido
    late = "late"           # Pasó la fecha límite
    cancelled = "cancelled" # Error operativo
    refunded = "refunded"   # Devolución de dinero

class TicketPriority(str, enum.Enum):
    """Nivel de urgencia para mantenimiento."""
    low = "low"             # Ej: Pintura desgastada
    medium = "medium"       # Ej: Grifo goteando
    high = "high"           # Ej: Sin agua caliente
    emergency = "emergency" # Ej: Inundación o incendio

# ==============================================================================
# 2. MIXINS (PATRONES DE DISEÑO)
# ==============================================================================
# Los Mixins son clases "plantilla". No crean tablas por sí mismos,
# pero otras tablas heredan sus columnas para no tener que repetirlas.

@declarative_mixin
@declarative_mixin
class TimestampMixin:
    """
    Agrega automáticamente marcas de tiempo a cualquier tabla.
    - created_at: Se llena solo al crear el registro (func.now()).
    - updated_at: Se actualiza automáticamente en el servidor en cada modificación (server_onupdate).
    """
    created_at = Column(DateTime(timezone=True), server_default=func.now)
    updated_at = Column(DateTime(timezone=True), server_default=func.now, server_onupdate=func.now)
    
@declarative_mixin
class SoftDeleteMixin:
    """
    Patrón 'Soft Delete' (Borrado Lógico).
    En sistemas Enterprise, NUNCA hacemos 'DELETE FROM'.
    En su lugar, marcamos is_deleted=True para ocultarlo, pero el dato persiste
    por seguridad y auditoría.
    """
    is_deleted = Column(Boolean, default=False)

# Función auxiliar para generar UUIDs (Identificadores únicos universales)
# Usamos UUID en lugar de ID numérico (1, 2, 3) por seguridad (no son adivinables).
def generate_uuid():
    return str(uuid.uuid4())

# ==============================================================================
# 3. MODELOS DE TABLAS (SCHEMA)
# ==============================================================================

class User(Base, TimestampMixin):
    """Tabla central de usuarios."""
    __tablename__ = "users"

    # Columnas
    id = Column(String, primary_key=True, default=generate_uuid)
    # unique=True: No permite dos usuarios con el mismo email
    # index=True: Hace que buscar por email sea muy rápido
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False) # ¡Nunca guardar contraseñas en texto plano!
    full_name = Column(String)
    phone_number = Column(String)
    role = Column(Enum(UserRole), default=UserRole.landlord)
    is_active = Column(Boolean, default=True) # Para bloquear usuarios sin borrarlos
    
    # Relaciones (SQLAlchemy Magic)
    # 'back_populates' crea una propiedad virtual en la otra tabla para navegar a la inversa.
    properties = relationship("Property", back_populates="owner")
    contracts_as_tenant = relationship("Contract", back_populates="tenant")
    audit_logs = relationship("AuditLog", back_populates="user")

class Property(Base, TimestampMixin, SoftDeleteMixin):
    """Inventario inmobiliario."""
    __tablename__ = "properties"

    id = Column(String, primary_key=True, default=generate_uuid)
    # ForeignKey: Crea la restricción en la base de datos.
    # Si borras al usuario, la base de datos protegerá estas propiedades (o fallará según configuración).
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    title = Column(String, nullable=False) # Ej: "Departamento Centro #302"
    description = Column(Text) # Campo de texto largo
    address = Column(String)
    
    # Georreferencia (DECIMAL es mejor que FLOAT para coordenadas precisas)
    latitude = Column(DECIMAL(9, 6))
    longitude = Column(DECIMAL(9, 6))
    
    price = Column(DECIMAL(10, 2), nullable=False) # DECIMAL para dinero (evita errores de redondeo)
    status = Column(Enum(PropertyStatus), default=PropertyStatus.available)
    
    # Relaciones
    owner = relationship("User", back_populates="properties")
    contracts = relationship("Contract", back_populates="property")
    maintenance_tickets = relationship("MaintenanceTicket", back_populates="property")

class Contract(Base, TimestampMixin):
    """
    El corazón del negocio. Vincula una Propiedad (Activo) con un Usuario (Inquilino).
    """
    __tablename__ = "contracts"

    id = Column(String, primary_key=True, default=generate_uuid)
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    tenant_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    payment_day = Column(Integer, default=5) # Día del mes límite para pagar
    amount = Column(DECIMAL(10, 2), nullable=False) # Precio pactado (puede diferir del precio actual de la propiedad)
    
    contract_file_url = Column(String, nullable=True) # URL al archivo en S3/Supabase Storage
    is_active = Column(Boolean, default=True)

    # Relaciones
    property = relationship("Property", back_populates="contracts")
    tenant = relationship("User", back_populates="contracts_as_tenant")
    payments = relationship("Payment", back_populates="contract")

class Payment(Base, TimestampMixin):
    """Registro de transacciones financieras."""
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=generate_uuid)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    
    amount = Column(DECIMAL(10, 2), nullable=False)
    due_date = Column(DateTime, nullable=False)   # Cuándo DEBIÓ pagar
    payment_date = Column(DateTime, nullable=True) # Cuándo PAGÓ realmente
    
    status = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    proof_file_url = Column(String, nullable=True) # Foto del comprobante de transferencia
    transaction_id = Column(String, nullable=True) # ID externo (Stripe/PayPal)

    # Relaciones
    contract = relationship("Contract", back_populates="payments")

class MaintenanceTicket(Base, TimestampMixin):
    """Sistema de tickets para reparaciones."""
    __tablename__ = "maintenance_tickets"

    id = Column(String, primary_key=True, default=generate_uuid)
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    requester_id = Column(String, ForeignKey("users.id"), nullable=False) # Quién reportó el daño
    
    title = Column(String, nullable=False)
    description = Column(Text)
    priority = Column(Enum(TicketPriority), default=TicketPriority.medium)
    
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

    # Relaciones
    property = relationship("Property", back_populates="maintenance_tickets")

class AuditLog(Base):
    """
    LA JOYA DE LA CORONA: AUDITORÍA
    Esta tabla es el 'CCTV' (Cámara de seguridad) de tu base de datos.
    Permite responder: "¿Quién borró el contrato el viernes pasado?"
    """
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True) # Puede ser Null si fue una tarea automática del sistema
    
    table_name = Column(String, nullable=False) # Ej: "contracts"
    record_id = Column(String, nullable=False)  # UUID del registro afectado
    action = Column(String, nullable=False)     # Valores: CREATE, UPDATE, DELETE
    
    # JSON Fields: PostgreSQL es muy potente guardando JSON.
    # Aquí guardamos una "foto" de cómo estaba el dato antes y después.
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now)

    # Relaciones
    user = relationship("User", back_populates="audit_logs")