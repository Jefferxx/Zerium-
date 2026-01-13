from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class TicketPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    emergency = "emergency"

class TicketStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    resolved = "resolved"
    cancelled = "cancelled"

class TicketBase(BaseModel):
    title: str
    description: str
    priority: TicketPriority = TicketPriority.medium

# --- CAMBIO IMPORTANTE ---
class TicketCreate(TicketBase):
    unit_id: str  # Obligatorio: El usuario DEBE decir dónde es el problema
    property_id: Optional[str] = None # Opcional: El backend lo calcula

class TicketStatusUpdate(BaseModel):
    status: TicketStatus

class TicketResponse(TicketBase):
    id: str
    property_id: str
    unit_id: Optional[str]
    requester_id: str
    status: TicketStatus
    created_at: datetime
    
    # Campos extra informativos (Opcionales por si vienen vacíos)
    property_name: Optional[str] = None
    unit_number: Optional[str] = None
    requester_name: Optional[str] = None

    class Config:
        from_attributes = True