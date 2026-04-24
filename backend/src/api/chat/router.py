from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import UUID4
import uuid

from src.db.session import get_db
from src.db.models import ChatSession, ChatMessage, User
from src.api.chat.schemas import ChatSessionCreate, ChatSessionResponse, SessionTitleUpdate, MessageCreate, MessageResponse
from src.services.rag_service import rag_service
from src.auth.router import get_current_user

router = APIRouter(prefix="/chat/sessions", tags=["chat"])

@router.post("", response_model=ChatSessionResponse)
async def create_chat_session(
    data: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = ChatSession(
        user_id=current_user.id,
        document_id=data.document_id,
        title="New Chat..." # Will be auto-updated on first message
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

@router.get("", response_model=list[ChatSessionResponse])
async def list_chat_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(ChatSession).where(ChatSession.user_id == current_user.id).order_by(ChatSession.updated_at.desc())
    )
    return result.scalars().all()

@router.get("/{session_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    session_id: UUID4,
    page: int = 1,
    size: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership
    session_check = await db.execute(select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id))
    if not session_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Session not found")
        
    offset = (page - 1) * size
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .offset(offset)
        .limit(size)
    )
    return result.scalars().all()

from src.middleware.rate_limit import check_usage_limit

@router.post("/{session_id}/messages", dependencies=[Depends(check_usage_limit("chat_message"))])
async def send_message(
    session_id: UUID4,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session_result = await db.execute(select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id))
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Generate streams directly out of the explicit rag_service
    return StreamingResponse(
        rag_service.generate_answer(str(session.document_id), str(session.id), data.content), 
        media_type="text/event-stream"
    )

@router.delete("/{session_id}")
async def delete_session(
    session_id: UUID4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    await db.delete(session)
    await db.commit()
    return {"message": "Session deleted"}

@router.patch("/{session_id}", response_model=ChatSessionResponse)
async def rename_session(
    session_id: UUID4,
    data: SessionTitleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session.title = data.title
    await db.commit()
    await db.refresh(session)
    return session
