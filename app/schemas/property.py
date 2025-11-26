from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from decimal import Decimal
from app.models import PropertyType, UnitType, UnitStatus

# --- UNIDADES (Departamentos/Locales) ---

class UnitBase(BaseModel):
    unit_number: str = Field(..., description="Número o nombre de la unidad (Ej: 101, A)")
    type: UnitType = UnitType.apartment
    floor: Optional[int] = None
    bedrooms: int = Field(1, ge=0)
    bathrooms: Decimal = Field(1.0, ge=0)
    area_m2: Optional[Decimal] = None
    base_price: Decimal = Field(..., gt=0, description="Precio referencial de alquiler")
    status: UnitStatus = UnitStatus.available

class UnitCreate(UnitBase):
    pass

class UnitResponse(UnitBase):
    id: str
    property_id: str
    
    class Config:
        from_attributes = True

# --- PROPIEDADES (Edificios/Casas) ---

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
    # Opcional: Permitir crear unidades al mismo tiempo que la propiedad
    units: Optional[List[UnitCreate]] = []

class PropertyResponse(PropertyBase):
    id: str
    owner_id: str
    # Incluimos las unidades en la respuesta para ver todo el edificio
    units: List[UnitResponse] = []
    
    class Config:
        from_attributes = True