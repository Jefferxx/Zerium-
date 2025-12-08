from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models import MaintenanceTicket, Property, User, TicketStatus
from app.schemas import ticket as ticket_schema
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/tickets",
    tags=["Maintenance Tickets"]
)

# 1. CREAR TICKET
@router.post("/", response_model=ticket_schema.TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket: ticket_schema.TicketCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Validar que la propiedad exista
    prop = db.query(Property).filter(Property.id == ticket.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")

    # Crear Ticket (Nace como PENDING)
    new_ticket = MaintenanceTicket(
        title=ticket.title,
        description=ticket.description,
        priority=ticket.priority,
        property_id=ticket.property_id,
        unit_id=ticket.unit_id,
        requester_id=current_user.id,
        status=TicketStatus.pending, # Estado inicial
        is_resolved=False            # Compatibilidad
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket

# 2. LISTAR TICKETS (CON SEGURIDAD)
@router.get("/", response_model=List[ticket_schema.TicketResponse])
def get_tickets(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Filtra tickets para que cada usuario vea solo lo suyo.
    """
    if current_user.role == "tenant":
        # Inquilino ve lo que él pidió
        return db.query(MaintenanceTicket).filter(MaintenanceTicket.requester_id == current_user.id).all()
    
    # Landlord ve tickets de sus propiedades
    return db.query(MaintenanceTicket).join(Property).filter(Property.owner_id == current_user.id).all()

# 3. ACTUALIZAR ESTADO DEL TICKET (PATCH)
@router.patch("/{ticket_id}/status", response_model=ticket_schema.TicketResponse)
def update_ticket_status(
    ticket_id: str,
    status_update: ticket_schema.TicketStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Buscar el ticket
    ticket = db.query(MaintenanceTicket).filter(MaintenanceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    # Validar Permisos (Solo Landlord)
    if current_user.role != "landlord":
        raise HTTPException(status_code=403, detail="Solo el dueño puede cambiar el estado")
    
    # Verificar propiedad
    prop = db.query(Property).filter(Property.id == ticket.property_id, Property.owner_id == current_user.id).first()
    if not prop:
        raise HTTPException(status_code=403, detail="No tienes permiso sobre esta propiedad")

    # Actualizar Estado
    ticket.status = status_update.status

    # Lógica de sincronización (Legacy support)
    if status_update.status == TicketStatus.resolved:
        ticket.is_resolved = True
        ticket.resolved_at = datetime.now()
    elif status_update.status == TicketStatus.in_progress:
        ticket.is_resolved = False
        ticket.resolved_at = None
    else: # pending / cancelled
        ticket.is_resolved = False
        ticket.resolved_at = None
        
    db.commit()
    db.refresh(ticket)
    return ticket