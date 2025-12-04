from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

# Replicamos el Enum para que Pydantic lo valide
class PaymentStatusEnum(str, Enum):
    pending = "pending"
    paid = "paid"
    late = "late"
    cancelled = "cancelled"
    refunded = "refunded"

class PaymentBase(BaseModel):
    contract_id: str
    amount: float
    due_date: datetime

class PaymentCreate(PaymentBase):
    """Usado para generar deuda manualmente si es necesario"""
    pass

class PaymentUpdate(BaseModel):
    """Usado cuando el inquilino paga"""
    transaction_id: Optional[str] = None
    proof_file_url: Optional[str] = None

class PaymentResponse(PaymentBase):
    id: str
    status: PaymentStatusEnum
    payment_date: Optional[datetime] = None
    transaction_id: Optional[str] = None
    
    class Config:
        from_attributes = True