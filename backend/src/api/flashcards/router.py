from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import UUID4
from datetime import datetime, timezone

from src.db.session import get_db
from src.db.models import User, Flashcard
from src.auth.router import get_current_user
from src.api.flashcards.schemas import *
from src.services.flashcard_service import flashcard_service

router = APIRouter(prefix="/flashcards", tags=["flashcards"])

@router.post("/generate", response_model=list[FlashcardView])
async def generate_flashcards(
    data: FlashcardGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    cards = await flashcard_service.generate_flashcards(
        doc_id=str(data.document_id),
        user_id=str(current_user.id),
        num_cards=data.num_cards
    )
    return [FlashcardView(**c) for c in cards]

@router.get("/due", response_model=list[FlashcardDueView])
async def get_due_flashcards(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Flashcard)
        .where(Flashcard.user_id == current_user.id)
        .where(Flashcard.next_review <= now)
        .order_by(Flashcard.next_review.asc())
    )
    cards = result.scalars().all()
    
    return [
        FlashcardDueView(
            id=c.id, front=c.front, back=c.back,
            ease_factor=c.ease_factor, interval=c.interval
        ) for c in cards
    ]

from src.middleware.rate_limit import check_usage_limit

@router.post("/{card_id}/review", response_model=FlashcardReviewResponse, dependencies=[Depends(check_usage_limit("flashcard_review"))])
async def review_flashcard(
    card_id: UUID4,
    data: FlashcardReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not (0 <= data.rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 0 and 5")
        
    # Security bounds check
    check = await db.execute(select(Flashcard).where(Flashcard.id == card_id, Flashcard.user_id == current_user.id))
    if not check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Card not found")
        
    updated = await flashcard_service.update_flashcard_review(str(card_id), data.rating)
    if not updated:
        raise HTTPException(status_code=404, detail="Update failed")
        
    return FlashcardReviewResponse(
        id=updated.id,
        interval=updated.interval,
        next_review=updated.next_review
    )

@router.get("/stats", response_model=FlashcardStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    now = datetime.now(timezone.utc)
    
    # Due today
    due_res = await db.execute(
        select(func.count(Flashcard.id))
        .where(Flashcard.user_id == current_user.id)
        .where(Flashcard.next_review <= now)
    )
    due_today = due_res.scalar_one()
    
    # Mastered (interval > 21 days is generally considered mastered)
    mastered_res = await db.execute(
        select(func.count(Flashcard.id))
        .where(Flashcard.user_id == current_user.id)
        .where(Flashcard.interval > 21)
    )
    mastered = mastered_res.scalar_one()
    
    # Total
    total_res = await db.execute(
        select(func.count(Flashcard.id))
        .where(Flashcard.user_id == current_user.id)
    )
    total = total_res.scalar_one()
    
    return FlashcardStats(
        due_today=due_today,
        mastered=mastered,
        total=total
    )
