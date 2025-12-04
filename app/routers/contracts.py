# app/routers/contracts.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Contract, Unit, User
from app.schemas.contract import ContractCreate, ContractResponse # Asumo que crearemos estos schemas luego
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/contracts",
    tags=["contracts"]
)

@router.post("/", response_model=ContractResponse)
def create_contract(contract_data: ContractCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. Verificar si la unidad existe y está vacante
    unit = db.query(Unit).filter(Unit.id == contract_data.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    if unit.status != "vacant":
        raise HTTPException(status_code=400, detail="Unit is already occupied")

    # 2. Crear el contrato
    new_contract = Contract(
        unit_id=contract_data.unit_id,
        tenant_id=contract_data.tenant_id,
        start_date=contract_data.start_date,
        end_date=contract_data.end_date,
        monthly_rent=contract_data.monthly_rent,
        status="active"
    )
    db.add(new_contract)
    
    # 3. Actualizar estado de la unidad
    unit.status = "occupied"
    unit.tenant_id = contract_data.tenant_id
    
    db.commit()
    db.refresh(new_contract)
    return new_contract