from pydantic import BaseModel, UUID4
from typing import List, Optional

# Router payload schemas

class QuizGenerateRequest(BaseModel):
    document_id: UUID4
    num_questions: int = 10
    difficulty: str = "medium"
    topic_focus: Optional[str] = None

class QuizQuestionView(BaseModel):
    id: int
    question: str
    options: List[str]
    # Intentionally hiding 'correct', 'explanation', 'page_ref' from the frontend until submitted

class QuizOverviewResponse(BaseModel):
    quiz_id: UUID4
    title: str
    questions: List[QuizQuestionView]

class QuizSubmitAnswer(BaseModel):
    question_id: int
    selected: str

class QuizSubmitRequest(BaseModel):
    answers: List[QuizSubmitAnswer]

class QuizFeedbackView(BaseModel):
    id: int
    is_correct: bool
    correct_option: str
    selected_option: str
    explanation: str
    page_ref: Optional[int] = None

class QuizResultResponse(BaseModel):
    score: int
    total: int
    feedback: List[QuizFeedbackView]
    
class QuizHistoryResponse(BaseModel):
    id: UUID4
    title: str
    score: Optional[int]
    total_questions: int
