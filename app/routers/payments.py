from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
import uuid
from app.database import get_db
from app import models
from app.schemas import payment as payment_schema 
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)

# 1. REGISTRAR UN PAGO
@router.post("/", response_model=payment_schema.PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment: payment_schema.PaymentCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    contract = db.query(models.Contract).filter(models.Contract.id == payment.contract_id).first()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    # Validar Permisos
    if current_user.role == models.UserRole.tenant:
        if contract.tenant_id != current_user.id:
            raise HTTPException(status_code=403, detail="No puedes registrar pagos en un contrato ajeno")    
    elif current_user.role == models.UserRole.landlord:
        unit = db.query(models.Unit).filter(models.Unit.id == contract.unit_id).first()
        if not unit or unit.property.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="No tienes permiso sobre este contrato")
    else:
        raise HTTPException(status_code=403, detail="Rol no autorizado")

    # --- LÓGICA DEUDA GLOBAL ---
    # El balance ahora representa TODO lo que falta pagar del contrato entero
    current_debt = contract.balance 

    if current_debt <= 0:
        raise HTTPException(status_code=400, detail="¡Este contrato ya está pagado en su totalidad!")

    # Permitimos un pequeño margen de error por decimales (0.10 ctvs)
    if float(payment.amount) > (float(current_debt) + 0.10):
        raise HTTPException(
            status_code=400, 
            detail=f"El monto excede la deuda total del contrato. Deuda restante: ${current_debt}"
        )

    new_payment = models.Payment(
        id=str(uuid.uuid4()),
        contract_id=payment.contract_id,
        amount=payment.amount,
        payment_method=payment.payment_method,
        notes=payment.notes
    )
    
    # Restamos del Saldo Global
    contract.balance = float(current_debt) - float(payment.amount)

    # Si la deuda llega a 0, podriamos marcar el contrato como finalizado (opcional)
    if contract.balance <= 0.10:
        contract.balance = 0.0
        # contract.status = models.ContractStatus.terminated # Opcional

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
            .options(
                joinedload(models.Payment.contract).joinedload(models.Contract.unit).joinedload(models.Unit.property),
                joinedload(models.Payment.contract).joinedload(models.Contract.tenant)
            )\
            .filter(models.Property.owner_id == current_user.id)\
            .order_by(models.Payment.payment_date.desc()).all()
        
        results = []
        for p in payments:
            prop_name = p.contract.unit.property.name if (p.contract and p.contract.unit and p.contract.unit.property) else "N/A"
            unit_num = p.contract.unit.unit_number if (p.contract and p.contract.unit) else "N/A"
            t_name = "Desconocido"
            if p.contract and p.contract.tenant:
                t_name = p.contract.tenant.full_name or p.contract.tenant.email

            p_data = {
                "id": p.id,
                "amount": p.amount,
                "payment_method": p.payment_method,
                "notes": p.notes,
                "contract_id": p.contract_id,
                "payment_date": p.payment_date,
                "property_name": prop_name,
                "unit_number": unit_num,
                "tenant_name": t_name
            }
            results.append(p_data)
        return results
    
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

    if current_user.role == models.UserRole.tenant and contract.tenant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
        
    if current_user.role == models.UserRole.landlord:
        unit = db.query(models.Unit).filter(models.Unit.id == contract.unit_id).first()
        if unit.property.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Acceso denegado")

    return db.query(models.Payment)\
             .filter(models.Payment.contract_id == contract_id)\
             .order_by(models.Payment.payment_date.desc()).all()