from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Contract, Unit, User, UnitStatus, UserRole
from app.schemas.contract import ContractCreate, ContractResponse
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/contracts",
    tags=["contracts"]
)

@router.post("/", response_model=ContractResponse)
def create_contract(
    contract_data: ContractCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # 1. Validar que la unidad existe
    unit = db.query(Unit).filter(Unit.id == contract_data.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    # 2. Validar disponibilidad (Usando tu Enum UnitStatus)
    if unit.status != UnitStatus.available:
        raise HTTPException(status_code=400, detail=f"Unit is currently {unit.status.value}")

    # 3. Crear Contrato
    new_contract = Contract(
        unit_id=contract_data.unit_id,
        tenant_id=contract_data.tenant_id,
        start_date=contract_data.start_date,
        end_date=contract_data.end_date,
        amount=contract_data.amount,  # Coincide con tu modelo
        payment_day=contract_data.payment_day,
        is_active=True
    )
    db.add(new_contract)
    
    # 4. Actualizar estado de la unidad a 'occupied'
    unit.status = UnitStatus.occupied
    
    db.commit()
    db.refresh(new_contract)
    return new_contract

@router.get("/", response_model=list[ContractResponse])
def get_contracts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # TODO: Filtrar solo contratos del usuario si no es admin
    return db.query(Contract).all()