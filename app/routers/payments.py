from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.database import get_db
from app import models
# CORRECCIÓN: Importamos específicamente el esquema de pago
from app.schemas import payment as payment_schema 
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)

# 1. REGISTRAR UN PAGO (Inquilinos y Dueños)
@router.post("/", response_model=payment_schema.PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment: payment_schema.PaymentCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Buscar el contrato
    contract = db.query(models.Contract).filter(models.Contract.id == payment.contract_id).first()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    # --- VALIDACIÓN DE PERMISOS ---
    if current_user.role == models.UserRole.tenant:
        if contract.tenant_id != current_user.id:
            raise HTTPException(status_code=403, detail="No puedes registrar pagos en un contrato que no es tuyo")
            
    elif current_user.role == models.UserRole.landlord:
        # Verificar propiedad a través de la unidad
        unit = db.query(models.Unit).filter(models.Unit.id == contract.unit_id).first()
        if not unit or unit.property.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="No tienes permiso sobre este contrato")
    
    else:
        raise HTTPException(status_code=403, detail="Rol no autorizado para pagos")

    # --- TRANSACCIÓN FINANCIERA ---
    new_payment = models.Payment(
        id=str(uuid.uuid4()),
        contract_id=payment.contract_id,
        amount=payment.amount,
        payment_method=payment.payment_method,
        notes=payment.notes
    )
    
    # Actualizar el Balance
    current_balance = contract.balance if contract.balance is not None else contract.amount
    contract.balance = float(current_balance) - float(payment.amount)

    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    
    return new_payment

# 2. VER HISTORIAL DE PAGOS
@router.get("/my-history", response_model=List[payment_schema.PaymentResponse])
def get_my_payments_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Devuelve todos los pagos relacionados al usuario logueado.
    """
    if current_user.role == models.UserRole.tenant:
        payments = db.query(models.Payment).join(models.Contract).filter(
            models.Contract.tenant_id == current_user.id
        ).order_by(models.Payment.payment_date.desc()).all()
        return payments

    elif current_user.role == models.UserRole.landlord:
        payments = db.query(models.Payment)\
            .join(models.Contract)\
            .join(models.Unit)\
            .join(models.Property)\
            .filter(models.Property.owner_id == current_user.id)\
            .order_by(models.Payment.payment_date.desc()).all()
        return payments
    
    return []

# 3. VER PAGOS POR CONTRATO
@router.get("/contract/{contract_id}", response_model=List[payment_schema.PaymentResponse])
def get_payments_by_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    # Validación de seguridad
    if current_user.role == models.UserRole.tenant and contract.tenant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
        
    if current_user.role == models.UserRole.landlord:
        unit = db.query(models.Unit).filter(models.Unit.id == contract.unit_id).first()
        if unit.property.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Acceso denegado")

    return db.query(models.Payment)\
             .filter(models.Payment.contract_id == contract_id)\
             .order_by(models.Payment.payment_date.desc()).all()