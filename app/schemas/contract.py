from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models import ContractStatus # <--- IMPORTAR ENUM

class ContractBase(BaseModel):
    unit_id: str
    tenant_id: str
    start_date: datetime
    end_date: datetime
    amount: float
    payment_day: int = 5

class ContractCreate(ContractBase):
    pass

# --- CLASE PARA DATOS ANIDADOS ---
class UnitInfo(BaseModel):
    unit_number: str

class TenantInfo(BaseModel):
    email: str
    full_name: Optional[str] = None

class ContractResponse(ContractBase):
    id: str
    is_active: bool
    status: ContractStatus
    contract_file_url: Optional[str] = None
    
    # --- CAMPOS DE DEUDA ---
    total_contract_value: float = 0.0  # <--- ¡FALTABA ESTE! Agrégalo.
    balance: Optional[float] = None 
    
    unit: Optional[UnitInfo] = None      
    tenant: Optional[TenantInfo] = None  
    
    class Config:
        from_attributes = True