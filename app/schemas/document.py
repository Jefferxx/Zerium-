from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models import DocumentType, DocumentStatus

class DocumentBase(BaseModel):
    document_type: DocumentType

class DocumentResponse(DocumentBase):
    id: str
    user_id: str
    file_url: str
    status: DocumentStatus
    rejection_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
        
class DocumentStatusUpdate(BaseModel):
    status: DocumentStatus
    rejection_reason: Optional[str] = None