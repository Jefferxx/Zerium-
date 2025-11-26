from sqlalchemy.orm import Session
from app.models import Property, Unit
from app.schemas import property as property_schema

def get_properties_by_owner(db: Session, owner_id: str, skip: int = 0, limit: int = 100):
    """Obtiene todos los edificios/casas de un dueño específico."""
    return db.query(Property)\
             .filter(Property.owner_id == owner_id, Property.is_deleted == False)\
             .offset(skip).limit(limit).all()

def create_property_with_units(db: Session, property: property_schema.PropertyCreate, owner_id: str):
    """
    Crea una Propiedad (Edificio) y opcionalmente sus Unidades (Deptos) 
    en una sola transacción atómica.
    """
    # 1. Crear la Propiedad Padre
    db_property = Property(
        owner_id=owner_id,
        name=property.name,
        type=property.type,
        address=property.address,
        city=property.city,
        description=property.description,
        amenities=property.amenities,
        latitude=property.latitude,
        longitude=property.longitude
    )
    db.add(db_property)
    db.flush() # Genera el ID de la propiedad sin confirmar la transacción aún

    # 2. Crear las Unidades Hijas (si existen)
    if property.units:
        for unit_data in property.units:
            db_unit = Unit(
                property_id=db_property.id, # Vinculamos con el papá
                unit_number=unit_data.unit_number,
                type=unit_data.type,
                floor=unit_data.floor,
                bedrooms=unit_data.bedrooms,
                bathrooms=unit_data.bathrooms,
                area_m2=unit_data.area_m2,
                base_price=unit_data.base_price,
                status=unit_data.status
            )
            db.add(db_unit)

    db.commit()
    db.refresh(db_property)
    return db_property