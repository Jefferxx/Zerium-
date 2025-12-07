from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Payment, Contract, Property, Unit, User
from app.schemas import payment as payment_schema
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)

# 1. REGISTRAR UN PAGO (Solo Landlord)
@router.post("/", response_model=payment_schema.PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment: payment_schema.PaymentCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validar permisos: Solo el dueño puede registrar pagos
    if current_user.role != "landlord":
        raise HTTPException(status_code=403, detail="Solo los dueños pueden registrar pagos")

    # Buscar el contrato
    contract = db.query(Contract).filter(Contract.id == payment.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    # Validar que el contrato pertenezca a una propiedad de este dueño
    # Contract -> Unit -> Property -> Owner
    is_owner = db.query(Property).join(Unit).filter(
        Unit.id == contract.unit_id,
        Property.owner_id == current_user.id
    ).first()

    if not is_owner:
        raise HTTPException(status_code=403, detail="No tienes permiso sobre este contrato")

    # --- TRANSACCIÓN FINANCIERA ---
    # 1. Crear el objeto Pago
    new_payment = Payment(
        contract_id=payment.contract_id,
        amount=payment.amount,
        payment_method=payment.payment_method,
        notes=payment.notes
    )
    
    # 2. Actualizar el Balance del Contrato (Restar deuda)
    # Nota: Si quisieras llevar un historial de saldo a favor, la lógica sería más compleja.
    # Por ahora, asumimos que 'balance' disminuye con los pagos.
    contract.balance = contract.balance - payment.amount

    db.add(new_payment)
    # No hace falta db.add(contract) porque SQLAlchemy rastrea el cambio automáticamente
    
    db.commit()
    db.refresh(new_payment)
    
    return new_payment

# 2. VER HISTORIAL DE PAGOS DE UN CONTRATO
@router.get("/contract/{contract_id}", response_model=List[payment_schema.PaymentResponse])
def get_payments_by_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Buscar el contrato
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    # SEGURIDAD:
    # - Si es Dueño: Debe ser dueño de la propiedad.
    # - Si es Inquilino: Debe ser SU contrato.
    
    if current_user.role == "tenant":
        if contract.tenant_id != current_user.id:
            raise HTTPException(status_code=403, detail="No puedes ver pagos de otro contrato")
            
    elif current_user.role == "landlord":
        # Verificar propiedad
        is_owner = db.query(Property).join(Unit).filter(
            Unit.id == contract.unit_id,
            Property.owner_id == current_user.id
        ).first()
        if not is_owner:
            raise HTTPException(status_code=403, detail="No tienes acceso a este contrato")

    # Retornar pagos ordenados por fecha (más reciente primero)
    return db.query(Payment).filter(Payment.contract_id == contract_id).order_by(Payment.payment_date.desc()).all()