from pydantic import BaseModel
from typing import Optional

class PlanLimits(BaseModel):
    document_uploaded: Optional[int] = None # None means unlimited
    chat_message: Optional[int] = None
    quiz_generated: Optional[int] = None
    flashcard_review: Optional[int] = None
    
# FREE plan: 3 documents, 50 chat messages/month, 5 quizzes/month, 20 flashcard reviews/day
FREE_LIMITS = PlanLimits(
    document_uploaded=3,
    chat_message=50,
    quiz_generated=5,
    flashcard_review=20
)

# PRO plan: unlimited absolutely everything
PRO_LIMITS = PlanLimits(
    document_uploaded=None,
    chat_message=None,
    quiz_generated=None,
    flashcard_review=None
)

def get_plan_limits(plan: str) -> PlanLimits:
    if plan and plan.lower() == "pro":
        return PRO_LIMITS
    return FREE_LIMITS
