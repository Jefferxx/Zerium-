from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime

class PaymentBase(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Monto del pago")
    # CAMBIO IMPORTANTE: Lo hacemos opcional aquí para que no rompa la lectura si viene null
    payment_method: Optional[str] = Field(None, description="Efectivo, Transferencia, Depósito")
    notes: Optional[str] = None

# Lo que recibimos para crear un pago
class PaymentCreate(PaymentBase):
    contract_id: str
    # CAMBIO IMPORTANTE: Aquí REFORZAMOS que sea obligatorio al crear
    payment_method: str = Field(..., description="Método obligatorio al crear")

# Lo que devolvemos al frontend
class PaymentResponse(PaymentBase):
    id: str
    contract_id: str
    payment_date: datetime

    class Config:
        from_attributes = True