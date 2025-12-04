from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import Payment, PaymentStatus, Contract, User
from app.schemas.payment import PaymentResponse, PaymentUpdate, PaymentCreate
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/payments",
    tags=["payments"]
)

# 1. LISTAR PAGOS (Con filtro por contrato_id)
# Frontend llama a: /payments?contract_id=uuid
@router.get("/", response_model=List[PaymentResponse])
def get_payments(
    contract_id: Optional[str] = None, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    query = db.query(Payment)
    if contract_id:
        query = query.filter(Payment.contract_id == contract_id)
    return query.all()

# 2. CREAR DEUDA (Generar Cobro)
# Frontend llama a: POST /payments/
@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment_obligation(
    payment_data: PaymentCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validar que el contrato exista
    contract = db.query(Contract).filter(Contract.id == payment_data.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    new_payment = Payment(
        contract_id=payment_data.contract_id,
        amount=payment_data.amount,
        due_date=payment_data.due_date,
        status=PaymentStatus.pending
    )
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    return new_payment

# 3. REGISTRAR PAGO
# Frontend llama a: PUT /payments/{id}/pay
@router.put("/{payment_id}/pay", response_model=PaymentResponse)
def register_payment(
    payment_id: str, 
    payment_data: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Actualizar estado
    payment.status = PaymentStatus.paid
    payment.payment_date = datetime.now()
    payment.transaction_id = payment_data.transaction_id
        
    db.commit()
    db.refresh(payment)
    return payment