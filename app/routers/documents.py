from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.database import get_db
from app import models
from app.schemas import document as doc_schema
from app.dependencies import get_current_user
from app.services.cloudinary_service import upload_file
from app.models import UserRole 

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

# 1. SUBIR DOCUMENTO
@router.post("/upload", response_model=doc_schema.DocumentResponse)
def upload_document(
    document_type: str = Form(...), 
    file: UploadFile = File(...),   
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Validar tipo de archivo
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Solo PDF, JPG o PNG")

    # Subir a Cloudinary
    upload_result = upload_file(file)
    if not upload_result:
        raise HTTPException(status_code=500, detail="Error al subir a la nube")

    # Guardar en BD
    new_doc = models.UserDocument(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        document_type=document_type,
        file_url=upload_result["url"],
        public_id=upload_result["public_id"],
        status=models.DocumentStatus.pending
    )
    
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    return new_doc

# 2. VER MIS DOCUMENTOS
@router.get("/my-documents", response_model=List[doc_schema.DocumentResponse])
def get_my_documents(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.UserDocument).filter(models.UserDocument.user_id == current_user.id).all()

# 3. VER DOCUMENTOS DE UN INQUILINO (Solo Landlord)
@router.get("/user/{user_id}", response_model=List[doc_schema.DocumentResponse])
def get_tenant_documents(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != models.UserRole.landlord:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    return db.query(models.UserDocument).filter(models.UserDocument.user_id == user_id).all()

# 4. APROBAR O RECHAZAR DOCUMENTO (Solo Landlord)
@router.patch("/{document_id}/status", response_model=doc_schema.DocumentResponse)
def update_document_status(
    document_id: str,
    status_update: doc_schema.DocumentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. Validar Permiso
    if current_user.role != models.UserRole.landlord:
        raise HTTPException(status_code=403, detail="Solo los dueños pueden verificar documentos")

    # 2. Buscar Documento
    doc = db.query(models.UserDocument).filter(models.UserDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # 3. Actualizar
    doc.status = status_update.status
    if status_update.rejection_reason:
        doc.rejection_reason = status_update.rejection_reason
    
    db.commit()
    db.refresh(doc)
    return doc