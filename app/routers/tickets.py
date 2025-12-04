from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models import MaintenanceTicket, Property, User
from app.schemas.ticket import TicketCreate, TicketResponse, TicketUpdate
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/tickets",
    tags=["tickets"]
)

# RF-10: Reportar incidente
@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket: TicketCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # 1. Validar que la propiedad exista
    prop = db.query(Property).filter(Property.id == ticket.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    # 2. Crear Ticket (Mapeo explícito para evitar errores de campos extra)
    new_ticket = MaintenanceTicket(
        title=ticket.title,
        description=ticket.description,
        priority=ticket.priority,
        property_id=ticket.property_id,
        unit_id=ticket.unit_id,
        requester_id=current_user.id,
        is_resolved=False # Usamos el booleano que sí existe en tu DB
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket

# Listar tickets (Dashboard del Landlord)
@router.get("/", response_model=List[TicketResponse])
def get_tickets(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # TODO: En el futuro filtrar por propiedad del landlord
    return db.query(MaintenanceTicket).all()

# RF-11: Actualizar estado (Gestionar ticket)
@router.put("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: str,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(MaintenanceTicket).filter(MaintenanceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Actualizar Prioridad
    if ticket_update.priority:
        ticket.priority = ticket_update.priority
    
    # Actualizar Estado (Resolver/Reabrir)
    if ticket_update.is_resolved is not None:
        ticket.is_resolved = ticket_update.is_resolved
        # Opcional: Guardar fecha de resolución
        if ticket_update.is_resolved:
            ticket.resolved_at = datetime.now()
        else:
            ticket.resolved_at = None
        
    db.commit()
    db.refresh(ticket)
    return ticket