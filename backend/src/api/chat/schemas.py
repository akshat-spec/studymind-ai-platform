from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class ChatSessionCreate(BaseModel):
    document_id: UUID

class ChatSessionResponse(BaseModel):
    id: UUID
    document_id: UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SessionTitleUpdate(BaseModel):
    title: str

class MessageCreate(BaseModel):
    content: str
    
class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class StreamChunk(BaseModel):
    chunk: str
