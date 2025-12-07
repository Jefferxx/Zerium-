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

# --- CLASE PARA DATOS ANIDADOS ---
class UnitInfo(BaseModel):
    unit_number: str

class TenantInfo(BaseModel):
    email: str
    full_name: Optional[str] = None

class ContractResponse(ContractBase):
    id: str
    is_active: bool
    contract_file_url: Optional[str] = None
    
    # --- CAMPO NUEVO: BALANCE ---
    # Esto permitirá ver la deuda actual en Swagger y en el Frontend
    balance: Optional[float] = None 
    
    unit: Optional[UnitInfo] = None      
    tenant: Optional[TenantInfo] = None  
    
    class Config:
        from_attributes = True