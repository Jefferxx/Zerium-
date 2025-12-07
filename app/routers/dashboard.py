from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
# IMPORTACIÓN CORREGIDA: Los modelos vienen de models.py
from app.models import User, Property, Unit, MaintenanceTicket, Contract, UnitStatus 
# IMPORTACIÓN CORREGIDA: La seguridad viene de dependencies.py
from app.dependencies import get_current_user 

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)

@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    # --- LOGICA PARA DUEÑO (LANDLORD) ---
    if current_user.role == "landlord":
        total_properties = db.query(Property).filter(Property.owner_id == current_user.id).count()
        
        total_units = db.query(Unit).join(Property).filter(Property.owner_id == current_user.id).count()
        
        occupied_units = db.query(Unit).join(Property).filter(
            Property.owner_id == current_user.id, 
            Unit.status == UnitStatus.occupied
        ).count()
        
        pending_tickets = db.query(MaintenanceTicket).join(Property).filter(
            Property.owner_id == current_user.id,
            MaintenanceTicket.is_resolved == False
        ).count()

        occupancy_rate = 0
        if total_units > 0:
            occupancy_rate = round((occupied_units / total_units) * 100, 1)

        return {
            "total_properties": total_properties,
            "total_units": total_units,
            "occupied_units": occupied_units,
            "pending_tickets": pending_tickets,
            "occupancy_rate": occupancy_rate
        }

    # --- LOGICA PARA INQUILINO (TENANT) ---
    elif current_user.role == "tenant":
        active_contracts = db.query(Contract).filter(
            Contract.tenant_id == current_user.id, 
            Contract.is_active == True
        ).count()
        
        my_tickets = db.query(MaintenanceTicket).filter(
            MaintenanceTicket.requester_id == current_user.id,
            MaintenanceTicket.is_resolved == False
        ).count()

        return {
            "active_contracts": active_contracts,
            "pending_tickets": my_tickets
        }
    
    return {}