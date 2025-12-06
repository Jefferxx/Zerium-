from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas import property as property_schema
from app.crud import property as property_crud
from app.dependencies import get_current_user 
from app.models import User, Unit # <--- Importante: Importar Unit

router = APIRouter(
    prefix="/properties",
    tags=["Properties"]
)

@router.post("/", response_model=property_schema.PropertyResponse, status_code=status.HTTP_201_CREATED)
def create_property(
    property: property_schema.PropertyCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crea una nueva propiedad (Edificio/Casa) y sus unidades.
    Automáticamente asigna al usuario logueado como dueño.
    """
    return property_crud.create_property_with_units(db=db, property=property, owner_id=current_user.id)

@router.get("/", response_model=List[property_schema.PropertyResponse])
def read_my_properties(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene solo las propiedades del usuario que inició sesión.
    """
    return property_crud.get_properties_by_owner(db=db, owner_id=current_user.id, skip=skip, limit=limit)

# --- NUEVO ENDPOINT: Editar Unidad ---
@router.put("/units/{unit_id}", response_model=property_schema.UnitResponse)
def update_unit(
    unit_id: str,
    unit_update: property_schema.UnitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Permite editar una unidad específica (Ej: cambiar precio, corregir baños).
    Solo el dueño de la propiedad puede hacerlo.
    """
    # 1. Buscar la unidad
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    # 2. Verificar permisos (Tenant Isolation para escritura)
    # Accedemos al padre (property) para ver quién es el dueño
    if unit.property.owner_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized to edit this unit")

    # 3. Actualizar campos
    # exclude_unset=True ignora los campos que no enviaste en el JSON
    update_data = unit_update.model_dump(exclude_unset=True) 
    
    for key, value in update_data.items():
        setattr(unit, key, value)

    db.commit()
    db.refresh(unit)
    return unit