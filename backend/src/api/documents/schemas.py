from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class DocumentUploadResponse(BaseModel):
    id: UUID
    filename: str
    status: str
    message: str

class DocumentListItem(BaseModel):
    id: UUID
    title: str
    filename: str
    file_size: int
    page_count: int
    status: str # processing/ready/failed
    created_at: datetime
    
    class Config:
        from_attributes = True

class DocumentDetail(DocumentListItem):
    chroma_collection_id: Optional[str]
    
    class Config:
        from_attributes = True
