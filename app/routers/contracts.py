from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_ 
from typing import List
from app.database import get_db
from app.models import Contract, Property, Unit, User, ContractStatus # <--- IMPORTAR STATUS
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
        # Landlord ve todos los contratos de sus propiedades
        return db.query(Contract).join(Unit).join(Property).filter(
            Property.owner_id == current_user.id
        ).all()
    elif current_user.role == "tenant":
        # Inquilino ve solo sus contratos
        return db.query(Contract).filter(Contract.tenant_id == current_user.id).all()
    else:
        return []

# 2. CREAR CONTRATO (CON VALIDACIÓN RF-06 Y ESTADO PENDING)
@router.post("/", response_model=contract_schema.ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    contract: contract_schema.ContractCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # A. Validar Permisos (Solo Landlord)
    if current_user.role != "landlord":
        raise HTTPException(status_code=403, detail="Solo los dueños pueden crear contratos")
    
    # B. Validar que la Unidad exista y pertenezca al Landlord
    unit = db.query(Unit).join(Property).filter(
        Unit.id == contract.unit_id, 
        Property.owner_id == current_user.id
    ).first()
    
    if not unit:
        raise HTTPException(status_code=404, detail="Unidad no encontrada o no te pertenece")

    # C. VALIDACIÓN RF-06 ACTUALIZADA
    # Verificamos solapamiento con contratos que estén ACTIVOS o PENDIENTES
    overlapping_contract = db.query(Contract).filter(
        Contract.unit_id == contract.unit_id, 
        Contract.status.in_([ContractStatus.active, ContractStatus.pending]), # <--- CAMBIO CRÍTICO
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
        
    # D. Crear el Contrato
    contract_data = contract.model_dump()
    
    # Creamos la instancia DB, inicializando status PENDING y desactivado
    new_contract = Contract(
        **contract_data, 
        balance=contract.amount,
        status=ContractStatus.pending,
        is_active=False
    )
    
    # NOTA: No marcamos la unidad como 'occupied' todavía. Eso sucede al firmar.
    
    db.add(new_contract)
    db.commit()
    db.refresh(new_contract)
    return new_contract

# 3. OBTENER UN SOLO CONTRATO
@router.get("/{id}", response_model=contract_schema.ContractResponse)
def get_contract(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Buscar el contrato por ID
    contract = db.query(Contract).filter(Contract.id == id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    # VALIDAR PERMISOS
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

# 4. FIRMAR CONTRATO (NUEVO ENDPOINT)
@router.post("/{contract_id}/sign", response_model=contract_schema.ContractResponse)
def sign_contract(contract_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    El inquilino acepta el contrato. Pasa de 'pending' a 'active'.
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    # Solo el inquilino asignado puede firmar
    if contract.tenant_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el inquilino de este contrato")

    if contract.status != ContractStatus.pending:
        raise HTTPException(status_code=400, detail="El contrato no está pendiente de firma")

    # ACTIVACIÓN
    contract.status = ContractStatus.active
    contract.is_active = True
    
    # Actualizar estado de la unidad a ocupado
    unit = db.query(Unit).filter(Unit.id == contract.unit_id).first()
    if unit:
        unit.status = "occupied"

    db.commit()
    db.refresh(contract)
    return contract