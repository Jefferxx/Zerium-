from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ContractBase(BaseModel):
    unit_id: str
    tenant_id: str
    start_date: datetime
    end_date: datetime
    amount: float
    payment_day: int = 5

class ContractCreate(ContractBase):
    pass

# --- CLASE PARA DATOS ANIDADOS (NUEVO) ---
class UnitInfo(BaseModel):
    unit_number: str

class TenantInfo(BaseModel):
    email: str
    full_name: Optional[str] = None

class ContractResponse(ContractBase):
    id: str
    is_active: bool
    contract_file_url: Optional[str] = None
    
    # --- CAMPOS NUEVOS ---
    unit: Optional[UnitInfo] = None      # Traerá info de la unidad
    tenant: Optional[TenantInfo] = None  # Traerá info del usuario
    
    class Config:
        from_attributes = True