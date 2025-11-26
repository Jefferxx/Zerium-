from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas import property as property_schema
from app.crud import property as property_crud
from app.dependencies import get_current_user # Importamos la seguridad
from app.models import User

router = APIRouter(
    prefix="/properties",
    tags=["Properties"]
)

@router.post("/", response_model=property_schema.PropertyResponse, status_code=status.HTTP_201_CREATED)
def create_property(
    property: property_schema.PropertyCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # ¡Ruta Protegida!
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
    current_user: User = Depends(get_current_user) # ¡Ruta Protegida!
):
    """
    Obtiene solo las propiedades del usuario que inició sesión.
    """
    return property_crud.get_properties_by_owner(db=db, owner_id=current_user.id, skip=skip, limit=limit)