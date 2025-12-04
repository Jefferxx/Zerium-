# app/routers/payments.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Payment
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/payments",
    tags=["payments"]
)

@router.get("/")
def get_payments(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Retorna pagos asociados a las propiedades del usuario (si es Landlord)
    # TODO: Refinar filtro por rol
    return db.query(Payment).all()

@router.post("/{payment_id}/pay")
def register_payment(payment_id: int, amount: float, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    payment.amount_paid += amount
    if payment.amount_paid >= payment.total_amount:
        payment.status = "paid"
    else:
        payment.status = "partial"
        
    db.commit()
    return {"message": "Payment registered", "new_status": payment.status}