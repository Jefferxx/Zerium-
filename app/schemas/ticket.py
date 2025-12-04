from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

class TicketPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    emergency = "emergency"

class TicketStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"

class TicketBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TicketPriority = TicketPriority.medium
    property_id: str
    unit_id: Optional[str] = None # Opcional: el daño puede ser en el pasillo (edificio)
    photo_url: Optional[str] = None # Para cumplir RF-10 (Evidencia)

class TicketCreate(TicketBase):
    pass

class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    technician_notes: Optional[str] = None

class TicketResponse(TicketBase):
    id: str
    status: TicketStatus
    requester_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True