from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
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
    # Validar que la propiedad exista
    prop = db.query(Property).filter(Property.id == ticket.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    new_ticket = MaintenanceTicket(
        **ticket.model_dump(),
        requester_id=current_user.id,
        status="open"
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket

# Listar tickets (Dashboard del Landlord)
@router.get("/", response_model=List[TicketResponse])
def get_tickets(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # En v1.0, el admin ve todos. TODO: Filtrar por propiedad del landlord.
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
    
    # Actualizar campos permitidos
    if ticket_update.status:
        ticket.status = ticket_update.status
    if ticket_update.priority:
        ticket.priority = ticket_update.priority
        
    db.commit()
    db.refresh(ticket)
    return ticket