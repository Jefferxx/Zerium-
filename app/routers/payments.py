from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.database import get_db
from app import models, schemas
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)

# 1. REGISTRAR UN PAGO (Inquilinos y Dueños)
@router.post("/", response_model=schemas.PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment: schemas.PaymentCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Buscar el contrato
    # Nota: Como los IDs son strings (UUIDs), no hace falta conversión especial
    contract = db.query(models.Contract).filter(models.Contract.id == payment.contract_id).first()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    # --- VALIDACIÓN DE PERMISOS ---
    if current_user.role == models.UserRole.tenant:
        # El inquilino solo puede pagar SU contrato
        if contract.tenant_id != current_user.id:
            raise HTTPException(status_code=403, detail="No puedes registrar pagos en un contrato que no es tuyo")
            
    elif current_user.role == models.UserRole.landlord:
        # El dueño debe ser propietario de la unidad asociada
        # Join: Contract -> Unit -> Property
        unit = db.query(models.Unit).filter(models.Unit.id == contract.unit_id).first()
        if not unit or unit.property.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="No tienes permiso sobre este contrato")
    
    else:
        # Otros roles (admin, etc.) o roles no reconocidos
        raise HTTPException(status_code=403, detail="Rol no autorizado para pagos")

    # --- TRANSACCIÓN FINANCIERA ---
    # 1. Crear el objeto Pago con UUID explícito
    new_payment = models.Payment(
        id=str(uuid.uuid4()), # Generamos ID manual para asegurar que no falle
        contract_id=payment.contract_id,
        amount=payment.amount,
        payment_method=payment.payment_method,
        notes=payment.notes
    )
    
    # 2. Actualizar el Balance del Contrato (Restar deuda)
    # Si balance es None, asumimos que la deuda es el monto total original
    current_balance = contract.balance if contract.balance is not None else contract.amount
    
    # Restamos el pago al balance
    contract.balance = float(current_balance) - float(payment.amount)

    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    
    return new_payment

# 2. VER HISTORIAL DE PAGOS (Filtrado por Usuario)
@router.get("/my-history", response_model=List[schemas.PaymentResponse])
def get_my_payments_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Devuelve todos los pagos relacionados al usuario logueado.
    - Si es Inquilino: Pagos que él ha hecho.
    - Si es Dueño: Pagos que ha recibido en sus propiedades.
    """
    if current_user.role == models.UserRole.tenant:
        # Pagos de contratos donde el usuario es el inquilino
        payments = db.query(models.Payment).join(models.Contract).filter(
            models.Contract.tenant_id == current_user.id
        ).order_by(models.Payment.payment_date.desc()).all()
        return payments

    elif current_user.role == models.UserRole.landlord:
        # Pagos de contratos -> unidades -> propiedades del dueño
        payments = db.query(models.Payment)\
            .join(models.Contract)\
            .join(models.Unit)\
            .join(models.Property)\
            .filter(models.Property.owner_id == current_user.id)\
            .order_by(models.Payment.payment_date.desc()).all()
        return payments
    
    return []

# 3. VER PAGOS POR CONTRATO ESPECÍFICO (Detalle)
@router.get("/contract/{contract_id}", response_model=List[schemas.PaymentResponse])
def get_payments_by_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    # Validación rápida de seguridad
    if current_user.role == models.UserRole.tenant and contract.tenant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
        
    if current_user.role == models.UserRole.landlord:
        # Verificamos ownership indirecto
        unit = db.query(models.Unit).filter(models.Unit.id == contract.unit_id).first()
        if unit.property.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Acceso denegado")

    return db.query(models.Payment)\
             .filter(models.Payment.contract_id == contract_id)\
             .order_by(models.Payment.payment_date.desc()).all()