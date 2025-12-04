from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import Payment, PaymentStatus, User
from app.schemas.payment import PaymentResponse, PaymentUpdate
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/payments",
    tags=["payments"]
)

@router.get("/", response_model=list[PaymentResponse])
def get_payments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Payment).all()

@router.put("/{payment_id}/pay", response_model=PaymentResponse)
def register_payment(
    payment_id: str, 
    payment_data: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Buscar el pago por UUID
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.status == PaymentStatus.paid:
        raise HTTPException(status_code=400, detail="Payment is already processed")

    # Registrar pago
    payment.status = PaymentStatus.paid
    payment.payment_date = datetime.now()
    payment.transaction_id = payment_data.transaction_id
    payment.proof_file_url = payment_data.proof_file_url
        
    db.commit()
    db.refresh(payment)
    return payment