from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Contract, Property, Unit, User
from app.schemas import contract as contract_schema
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/contracts",
    tags=["Contracts"]
)

# 1. LISTAR TODOS (Ya lo tenías)
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

# 2. CREAR CONTRATO (Ya lo tenías)
@router.post("/", response_model=contract_schema.ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(contract: contract_schema.ContractCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "landlord":
        raise HTTPException(status_code=403, detail="Solo los dueños pueden crear contratos")
    
    unit = db.query(Unit).join(Property).filter(Unit.id == contract.unit_id, Property.owner_id == current_user.id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unidad no encontrada o no te pertenece")
        
    new_contract = Contract(**contract.model_dump())
    db.add(new_contract)
    db.commit()
    db.refresh(new_contract)
    return new_contract

# 3. OBTENER UN SOLO CONTRATO (¡ESTA ES LA PIEZA QUE FALTA!)
@router.get("/{id}", response_model=contract_schema.ContractResponse)
def get_contract(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Buscar el contrato por ID
    contract = db.query(Contract).filter(Contract.id == id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    # VALIDAR PERMISOS (Seguridad)
    if current_user.role == "landlord":
        # Verificar que la propiedad sea suya
        is_owner = db.query(Property).join(Unit).filter(
            Unit.id == contract.unit_id,
            Property.owner_id == current_user.id
        ).first()
        if not is_owner:
            raise HTTPException(status_code=403, detail="No tienes permiso para ver este contrato")
            
    elif current_user.role == "tenant":
        # Verificar que sea SU contrato
        if contract.tenant_id != current_user.id:
            raise HTTPException(status_code=403, detail="Este contrato no te pertenece")

    return contract