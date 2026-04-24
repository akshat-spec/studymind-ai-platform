import os
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Security
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import UUID4

from src.db.session import get_db
from src.db.models import Document, User
from src.api.documents.schemas import DocumentUploadResponse, DocumentListItem, DocumentDetail
from src.services.pdf_processor import process_pdf
from src.services.vector_store import vector_store

# Note: We simulate `get_current_user` dependency from auth integration.
# In a real setup, import it from src.auth.router.
from src.auth.router import get_current_user

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 50 * 1024 * 1024 # 50MB

from src.middleware.rate_limit import check_usage_limit

@router.post("/upload", response_model=DocumentUploadResponse, dependencies=[Depends(check_usage_limit("document_uploaded"))])
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Read and check size limits
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")

    # Save to db with 'processing' state
    new_doc = Document(
        user_id=current_user.id,
        title=file.filename,
        filename=file.filename,
        file_size=len(content),
        page_count=0, # Computed later
        status="processing"
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)

    # Scoped user directory
    user_dir = os.path.join(UPLOAD_DIR, str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)
    
    file_path = os.path.join(user_dir, f"{new_doc.id}.pdf")
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        await out_file.write(content)

    # Background processing
    background_tasks.add_task(process_pdf, str(new_doc.id), file_path)

    return DocumentUploadResponse(
        id=new_doc.id,
        filename=file.filename,
        status=new_doc.status,
        message="Document uploaded and processing started."
    )

@router.get("/", response_model=list[DocumentListItem])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Document).where(Document.user_id == current_user.id).order_by(Document.created_at.desc())
    )
    return result.scalars().all()

@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document(
    doc_id: UUID4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Document).where(Document.user_id == current_user.id, Document.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return doc

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: UUID4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Document).where(Document.user_id == current_user.id, Document.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Remove from Chroma
    await vector_store.delete_collection(str(doc_id))
    
    # Remove local file
    file_path = os.path.join(UPLOAD_DIR, str(current_user.id), f"{doc_id}.pdf")
    if os.path.exists(file_path):
        os.remove(file_path)
        
    # Remove from DB
    await db.delete(doc)
    await db.commit()
    
    return {"message": "Document and associated artifacts removed."}
