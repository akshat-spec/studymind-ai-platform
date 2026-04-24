from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import UUID4

from src.db.session import get_db
from src.db.models import User, Quiz
from src.auth.router import get_current_user
from src.api.quiz.schemas import *
from src.services.quiz_service import quiz_service

router = APIRouter(prefix="/quiz", tags=["quiz"])

from src.middleware.rate_limit import check_usage_limit

@router.post("/generate", response_model=dict, dependencies=[Depends(check_usage_limit("quiz_generated"))])
async def generate_quiz(
    data: QuizGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        quiz_id = await quiz_service.generate_quiz(
            doc_id=str(data.document_id),
            user_id=str(current_user.id),
            num_questions=data.num_questions,
            difficulty=data.difficulty,
            topic_focus=data.topic_focus
        )
        return {"quiz_id": quiz_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Generation completely failed after retries.")

@router.get("/{quiz_id}", response_model=QuizOverviewResponse)
async def get_quiz(
    quiz_id: UUID4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id, Quiz.user_id == current_user.id))
    quiz = result.scalar_one_or_none()
    
    if not quiz: raise HTTPException(status_code=404, detail="Quiz not found")
        
    safe_questions = []
    for q in quiz.questions:
        safe_questions.append(QuizQuestionView(
            id=q["id"],
            question=q["question"],
            options=q["options"]
        ))
        
    return QuizOverviewResponse(
        quiz_id=quiz.id,
        title=quiz.title,
        questions=safe_questions
    )

@router.post("/{quiz_id}/submit", response_model=QuizResultResponse)
async def submit_quiz(
    quiz_id: UUID4,
    data: QuizSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id, Quiz.user_id == current_user.id))
    quiz = result.scalar_one_or_none()
    
    if not quiz: raise HTTPException(status_code=404, detail="Quiz not found")
        
    score = 0
    feedback = []
    answers_map = {a.question_id: a.selected for a in data.answers}
    
    for q in quiz.questions:
        qid = q["id"]
        correct = q["correct"]
        selected = answers_map.get(qid, "")
        
        is_correct = (selected == correct)
        if is_correct: score += 1
            
        feedback.append(QuizFeedbackView(
            id=qid,
            is_correct=is_correct,
            correct_option=correct,
            selected_option=selected,
            explanation=q["explanation"],
            page_ref=q.get("page_ref")
        ))
        
    # Standardize score percent
    total = len(quiz.questions)
    percentage = int((score / total) * 100)
    quiz.score = percentage
    await db.commit()
    
    return QuizResultResponse(score=score, total=total, feedback=feedback)

@router.get("/user/history", response_model=list[QuizHistoryResponse])
async def get_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Quiz).where(Quiz.user_id == current_user.id).order_by(Quiz.created_at.desc())
    )
    quizzes = result.scalars().all()
    
    out = []
    for q in quizzes:
        out.append(QuizHistoryResponse(
            id=q.id,
            title=q.title,
            score=q.score,
            total_questions=len(q.questions)
        ))
    return out
