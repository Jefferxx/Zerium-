from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
import uuid
from datetime import datetime
from app.database import get_db
from app import models
# Importamos schemas y models con nombres claros
from app.schemas import ticket as ticket_schema
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/tickets",
    tags=["Maintenance Tickets"]
)

# 1. CREAR TICKET (Lógica Corregida)
@router.post("/", response_model=ticket_schema.TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket: ticket_schema.TicketCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    # 1. Buscar la Unidad
    unit = db.query(models.Unit).filter(models.Unit.id == ticket.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")

    # 2. Validar Seguridad (Inquilino vs Dueño)
    if current_user.role == models.UserRole.tenant:
        # Verificar que tenga contrato ACTIVO en esa unidad
        contract = db.query(models.Contract).filter(
            models.Contract.unit_id == unit.id,
            models.Contract.tenant_id == current_user.id,
            models.Contract.status.in_(['active', 'pending', 'signed_by_tenant'])
        ).first()
        
        if not contract:
            raise HTTPException(status_code=403, detail="No tienes un contrato válido en esta unidad.")
            
    elif current_user.role == models.UserRole.landlord:
        # Verificar que sea SU propiedad
        if unit.property.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="No puedes crear tickets en propiedades ajenas")

    # 3. Crear Ticket (Vinculación Automática)
    new_ticket = models.MaintenanceTicket(
        id=str(uuid.uuid4()),
        title=ticket.title,
        description=ticket.description,
        priority=ticket.priority,
        status=models.TicketStatus.pending,
        
        unit_id=unit.id,
        property_id=unit.property_id, # <--- El backend asigna la propiedad correcta
        requester_id=current_user.id,
        
        is_resolved=False 
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    
    # 4. Rellenar datos extra para la respuesta inmediata
    # (Opcional, pero ayuda al frontend a no mostrar "null")
    new_ticket.property_name = unit.property.name
    new_ticket.unit_number = unit.unit_number
    
    return new_ticket

# 2. LISTAR TICKETS (Enriquecido con datos)
@router.get("/", response_model=List[ticket_schema.TicketResponse])
def get_tickets(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    
    # Query base con relaciones cargadas para eficiencia
    query = db.query(models.MaintenanceTicket)\
        .join(models.Unit)\
        .join(models.Property)\
        .join(models.User, models.MaintenanceTicket.requester_id == models.User.id)\
        .options(
            joinedload(models.MaintenanceTicket.unit).joinedload(models.Unit.property),
            joinedload(models.MaintenanceTicket.requester)
        )

    if current_user.role == models.UserRole.tenant:
        tickets = query.filter(models.MaintenanceTicket.requester_id == current_user.id).all()
    
    elif current_user.role == models.UserRole.landlord:
        tickets = query.filter(models.Property.owner_id == current_user.id).all()
    
    else:
        return []

    # Mapeo manual para el Schema
    results = []
    for t in tickets:
        # Asignamos los valores calculados al objeto antes de devolverlo
        t.property_name = t.unit.property.name if t.unit and t.unit.property else "N/A"
        t.unit_number = t.unit.unit_number if t.unit else "N/A"
        t.requester_name = t.requester.full_name or t.requester.email
        results.append(t)

    return results

# 3. ACTUALIZAR ESTADO (Manteniendo tu lógica)
@router.patch("/{ticket_id}/status", response_model=ticket_schema.TicketResponse)
def update_ticket_status(
    ticket_id: str,
    status_update: ticket_schema.TicketStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    ticket = db.query(models.MaintenanceTicket).filter(models.MaintenanceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    if current_user.role != models.UserRole.landlord:
        raise HTTPException(status_code=403, detail="Solo el dueño puede cambiar el estado")
    
    # Verificación estricta de propiedad
    unit = db.query(models.Unit).filter(models.Unit.id == ticket.unit_id).first()
    if not unit or unit.property.owner_id != current_user.id:
         raise HTTPException(status_code=403, detail="No tienes permiso sobre esta propiedad")

    ticket.status = status_update.status

    # Lógica legacy
    if status_update.status == models.TicketStatus.resolved:
        ticket.is_resolved = True
        ticket.resolved_at = datetime.now()
    else:
        ticket.is_resolved = False
        ticket.resolved_at = None
        
    db.commit()
    db.refresh(ticket)
    return ticket