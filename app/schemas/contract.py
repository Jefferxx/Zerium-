from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ContractBase(BaseModel):
    unit_id: str
    tenant_id: str
    start_date: datetime
    end_date: datetime
    amount: float      # Antes era monthly_rent
    payment_day: int = 5

class ContractCreate(ContractBase):
    pass

class ContractResponse(ContractBase):
    id: str
    is_active: bool    # Tu modelo usa boolean, no string "status"
    contract_file_url: Optional[str] = None
    
    class Config:
        from_attributes = True