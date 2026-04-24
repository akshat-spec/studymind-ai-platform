from pydantic import BaseModel, UUID4
from typing import List, Optional
from datetime import datetime

class FlashcardGenerateRequest(BaseModel):
    document_id: UUID4
    num_cards: int = 20

class FlashcardView(BaseModel):
    id: UUID4
    front: str
    back: str
    
class FlashcardDueView(BaseModel):
    id: UUID4
    front: str
    back: str
    ease_factor: float
    interval: int

class FlashcardReviewRequest(BaseModel):
    rating: int # 0 to 5

class FlashcardReviewResponse(BaseModel):
    id: UUID4
    interval: int
    next_review: datetime

class FlashcardStats(BaseModel):
    due_today: int
    mastered: int
    total: int
