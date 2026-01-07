from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime  # <--- IMPORTANTE: Necesario para las fechas de pago
from app.models import PropertyType, UnitType, UnitStatus

# =======================
# UNIDADES
# =======================

class UnitBase(BaseModel):
    unit_number: str = Field(..., description="Número o nombre de la unidad (Ej: 101, A)")
    type: UnitType = UnitType.apartment
    floor: Optional[int] = None
    bedrooms: int = Field(1, ge=0)
    bathrooms: Decimal = Field(1.0, ge=0)
    area_m2: Optional[Decimal] = None
    base_price: Decimal = Field(..., gt=0, description="Precio referencial de alquiler")
    status: UnitStatus = UnitStatus.vacant 

class UnitCreate(UnitBase):
    pass

class UnitUpdate(BaseModel):
    unit_number: Optional[str] = None
    type: Optional[UnitType] = None
    floor: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[Decimal] = None
    area_m2: Optional[Decimal] = None
    base_price: Optional[Decimal] = None
    status: Optional[UnitStatus] = None

class UnitResponse(UnitBase):
    id: str  # TIPO STRING (Para UUID)
    property_id: str # TIPO STRING
    
    class Config:
        from_attributes = True

# =======================
# PROPIEDADES
# =======================

class PropertyBase(BaseModel):
    name: str = Field(..., min_length=3, description="Nombre del edificio o casa")
    type: PropertyType
    address: str
    city: str = "Riobamba"
    description: Optional[str] = None
    amenities: Optional[Dict[str, Any]] = Field(default_factory=dict, description="JSON de servicios")
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None

class PropertyCreate(PropertyBase):
    units: Optional[List[UnitCreate]] = []

class PropertyResponse(PropertyBase):
    id: str        # TIPO STRING (Para UUID)
    owner_id: str  # TIPO STRING
    units: List[UnitResponse] = []
    
    class Config:
        from_attributes = True

# =======================
# PAGOS (NUEVO MÓDULO)
# =======================

class PaymentBase(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Monto pagado")
    payment_method: str = Field(..., description="Ej: Transferencia, Efectivo, Depósito")
    notes: Optional[str] = None # Aquí el inquilino puede poner "Transferencia #12345"

class PaymentCreate(PaymentBase):
    contract_id: str # Vinculamos el pago a un contrato específico (UUID)

class PaymentResponse(PaymentBase):
    id: str
    contract_id: str
    payment_date: datetime
    
    class Config:
        from_attributes = True