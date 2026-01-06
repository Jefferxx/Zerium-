from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_ # <--- IMPORTANTE: Necesarios para la validación de fechas
from typing import List
from app.database import get_db
from app.models import Contract, Property, Unit, User
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

# 2. CREAR CONTRATO (CON VALIDACIÓN RF-06)
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

    # C. VALIDACIÓN RF-06: Verificar solapamiento de fechas
    # Regla: (NuevoInicio <= FinExistente) Y (NuevoFin >= InicioExistente)
    overlapping_contract = db.query(Contract).filter(
        Contract.unit_id == contract.unit_id, # Misma unidad
        Contract.is_active == True,           # Solo contratos activos
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
            detail=f"La unidad ya está ocupada en esas fechas (Conflicto con contrato #{overlapping_contract.id})"
        )
        
    # D. Crear el Contrato
    # Convertimos el modelo Pydantic a diccionario
    contract_data = contract.model_dump()
    
    # Creamos la instancia DB, inicializando el balance con el monto total
    new_contract = Contract(**contract_data, balance=contract.amount)
    
    # E. Actualizar estado de la unidad
    unit.status = "occupied"
    
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

    # VALIDAR PERMISOS (Seguridad)
    if current_user.role == "landlord":
        # Verificar que la propiedad sea suya mediante Joins
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