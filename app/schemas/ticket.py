from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

# Definimos los Enums aquí para validación de Pydantic
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

# Datos base
class TicketBase(BaseModel):
    title: str
    description: str
    priority: TicketPriority = TicketPriority.medium

# Datos para CREAR (POST)
class TicketCreate(TicketBase):
    property_id: str
    unit_id: Optional[str] = None

# Datos para ACTUALIZAR ESTADO (PATCH)
class TicketStatusUpdate(BaseModel):
    status: TicketStatus

# Datos para RESPONDER (GET)
class TicketResponse(TicketBase):
    id: str
    property_id: str
    requester_id: str
    status: TicketStatus
    created_at: datetime
    # resolved_at: Optional[datetime] = None 

    class Config:
        from_attributes = True