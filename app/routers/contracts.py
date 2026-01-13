from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_ 
from typing import List
import math 
from datetime import datetime
from app.database import get_db
from app.models import Contract, Property, Unit, User, ContractStatus, UserDocument, DocumentStatus, UnitStatus
from app.schemas import contract as contract_schema
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/contracts",
    tags=["Contracts"]
)

# 1. LISTAR TODOS
@router.get("/", response_model=List[contract_schema.ContractResponse])
def get_contracts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == "landlord":
        return db.query(Contract).join(Unit).join(Property).filter(
            Property.owner_id == current_user.id
        ).all()
    elif current_user.role == "tenant":
        return db.query(Contract).filter(Contract.tenant_id == current_user.id).all()
    else:
        return []

# 2. CREAR CONTRATO
@router.post("/", response_model=contract_schema.ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    contract: contract_schema.ContractCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # A. Validar Permisos
    if current_user.role != "landlord":
        raise HTTPException(status_code=403, detail="Solo los dueños pueden crear contratos")
    
    # B. Validar Unidad
    unit = db.query(Unit).join(Property).filter(
        Unit.id == contract.unit_id, 
        Property.owner_id == current_user.id
    ).first()
    
    if not unit:
        raise HTTPException(status_code=404, detail="Unidad no encontrada o no te pertenece")

    # C. Validar Solapamiento
    overlapping_contract = db.query(Contract).filter(
        Contract.unit_id == contract.unit_id, 
        Contract.status.in_([ContractStatus.active, ContractStatus.pending, ContractStatus.signed_by_tenant]), 
        or_(
            and_(
                Contract.start_date <= contract.end_date,
                Contract.end_date >= contract.start_date
            )
        )
    ).first()

    if overlapping_contract:
        raise HTTPException(
            status_code=400, 
            detail=f"La unidad ya está reservada en esas fechas (Conflicto con contrato #{overlapping_contract.id})"
        )
        
    # D. CALCULAR TOTAL DEL CONTRATO
    start = contract.start_date
    end = contract.end_date

    delta_days = (end - start).days
    months = math.ceil(delta_days / 30) 
    
    if months < 1: 
        months = 1 

    calculated_total = float(contract.amount) * months

    # E. Crear el Contrato
    contract_data = contract.model_dump()
    
    new_contract = Contract(
        **contract_data, 
        total_contract_value=calculated_total, 
        balance=calculated_total,              
        status=ContractStatus.pending,
        is_active=False
    )
    
    db.add(new_contract)
    db.commit()
    db.refresh(new_contract)
    return new_contract

# 3. OBTENER UNO
@router.get("/{id}", response_model=contract_schema.ContractResponse)
def get_contract(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contract = db.query(Contract).filter(Contract.id == id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    if current_user.role == "landlord":
        is_owner = db.query(Property).join(Unit).filter(
            Unit.id == contract.unit_id,
            Property.owner_id == current_user.id
        ).first()
        if not is_owner:
            raise HTTPException(status_code=403, detail="No tienes permiso para ver este contrato")
            
    elif current_user.role == "tenant":
        if contract.tenant_id != current_user.id:
            raise HTTPException(status_code=403, detail="Este contrato no te pertenece")

    return contract

# 4. FIRMAR (INQUILINO)
@router.post("/{contract_id}/sign", response_model=contract_schema.ContractResponse)
def sign_contract(contract_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    if contract.tenant_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el inquilino de este contrato")

    if contract.status != ContractStatus.pending:
        raise HTTPException(status_code=400, detail="El contrato no está pendiente de firma")

    # Verificar Documentos
    verified_docs = db.query(UserDocument).filter(
        UserDocument.user_id == current_user.id,
        UserDocument.status == DocumentStatus.verified
    ).count()

    if verified_docs == 0:
        raise HTTPException(
            status_code=400, 
            detail="Debes tener tus documentos de identidad APROBADOS por el dueño antes de firmar."
        )

    contract.status = ContractStatus.signed_by_tenant
    contract.is_active = False 
    
    db.commit()
    db.refresh(contract)
    return contract

# 5. FINALIZAR / ACTIVAR (DUEÑO)
@router.post("/{contract_id}/finalize", response_model=contract_schema.ContractResponse)
def finalize_contract(contract_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    is_owner = db.query(Property).join(Unit).filter(
        Unit.id == contract.unit_id,
        Property.owner_id == current_user.id
    ).first()
    
    if not is_owner:
        raise HTTPException(status_code=403, detail="No tienes permiso para finalizar este contrato")

    if contract.status != ContractStatus.signed_by_tenant:
        raise HTTPException(status_code=400, detail="El contrato debe ser firmado primero por el inquilino")

    contract.status = ContractStatus.active
    contract.is_active = True
    
    unit = db.query(Unit).filter(Unit.id == contract.unit_id).first()
    if unit:
        unit.status = "occupied"

    db.commit()
    db.refresh(contract)
    return contract

# 6. TERMINAR CONTRATO / LIBERAR CASA (DUEÑO)
@router.post("/{contract_id}/terminate", response_model=contract_schema.ContractResponse)
def terminate_contract(contract_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Paso 3: El dueño da por terminado el contrato.
    - Cambia estado contrato a 'terminated'.
    - Libera la unidad (Unit -> 'available') para que pueda volver a alquilarse.
    - Desactiva el contrato (is_active -> False).
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    is_owner = db.query(Property).join(Unit).filter(
        Unit.id == contract.unit_id,
        Property.owner_id == current_user.id
    ).first()
    
    if not is_owner:
        raise HTTPException(status_code=403, detail="No tienes permiso para terminar este contrato")

    if contract.status != ContractStatus.active:
        raise HTTPException(status_code=400, detail="Solo se pueden terminar contratos activos")

    # Ejecutar Terminación
    contract.status = ContractStatus.terminated
    contract.is_active = False
    
    # Liberar la unidad
    unit = db.query(Unit).filter(Unit.id == contract.unit_id).first()
    if unit:
        # CORRECCIÓN CRÍTICA: Usamos "available" para que el frontend habilite el botón de alquilar
        unit.status = "available" 

    db.commit()
    db.refresh(contract)
    return contract