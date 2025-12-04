from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

class TicketPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    emergency = "emergency"

# Eliminamos TicketStatus porque tu DB no lo tiene, usa is_resolved
# class TicketStatus(str, Enum): ... 

class TicketBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TicketPriority = TicketPriority.medium
    property_id: str
    unit_id: Optional[str] = None
    photo_url: Optional[str] = None

class TicketCreate(TicketBase):
    pass

class TicketUpdate(BaseModel):
    is_resolved: bool # Usamos booleano directo
    priority: Optional[TicketPriority] = None

class TicketResponse(TicketBase):
    id: str
    # status: TicketStatus <--- CAMBIAMOS ESTO
    is_resolved: bool     # <--- POR ESTO (Coincide con DB)
    requester_id: str
    created_at: datetime
    # updated_at viene del mixin, pero a veces Pydantic se queja si es null
    
    class Config:
        from_attributes = True