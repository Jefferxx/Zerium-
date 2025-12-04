from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Contract, Unit, User, UnitStatus
from app.schemas.contract import ContractCreate, ContractResponse
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/contracts",
    tags=["contracts"]
)

# 1. CREAR CONTRATO
@router.post("/", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    contract_data: ContractCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Crea un nuevo contrato de alquiler.
    - Valida que la unidad exista y esté disponible.
    - Cambia el estado de la unidad a 'occupied'.
    """
    # 1. Validar que la unidad existe
    unit = db.query(Unit).filter(Unit.id == contract_data.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    # 2. Validar disponibilidad
    if unit.status != UnitStatus.available:
        # unit.status es un Enum, usamos .value para mostrar el texto real
        raise HTTPException(status_code=400, detail=f"Unit is currently {unit.status.value}")

    # 3. Crear Contrato
    new_contract = Contract(
        unit_id=contract_data.unit_id,
        tenant_id=contract_data.tenant_id,
        start_date=contract_data.start_date,
        end_date=contract_data.end_date,
        amount=contract_data.amount,
        payment_day=contract_data.payment_day,
        is_active=True
    )
    db.add(new_contract)
    
    # 4. Actualizar estado de la unidad
    unit.status = UnitStatus.occupied
    
    db.commit()
    db.refresh(new_contract)
    return new_contract

# 2. LISTAR CONTRATOS
@router.get("/", response_model=List[ContractResponse])
def get_contracts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Obtiene todos los contratos.
    Incluye datos anidados de Unidad e Inquilino gracias al Schema.
    """
    # Si quisieras filtrar por el usuario logueado (ej. solo ver mis contratos):
    # return db.query(Contract).filter(Contract.tenant_id == current_user.id).all()
    
    return db.query(Contract).all()