from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.session import get_db
from src.db.models import User
from src.auth.router import get_current_user
from src.services.usage_service import usage_service

router = APIRouter(prefix="/billing", tags=["billing"])

@router.get("/usage")
async def get_billing_usage(current_user: User = Depends(get_current_user)):
    summary = await usage_service.get_usage_summary(str(current_user.id), current_user.plan)
    return {"plan": current_user.plan, "usage": summary}

@router.get("/plans")
async def get_billing_plans():
    return {
        "free": {
            "name": "Free Plan",
            "price": "$0",
            "features": ["3 Documents", "50 AI Chat Messages / mo", "5 Quizzes / mo", "20 Flashcard Reviews / day"]
        },
        "pro": {
            "name": "Pro Plan",
            "price": "$9",
            "features": ["Unlimited Documents", "Unlimited AI Chat Messages", "Unlimited Quizzes", "Unlimited Flashcard Reviews"]
        }
    }

@router.post("/upgrade")
async def upgrade_to_pro(
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    # WARNING: Replace with real Stripe webhook flow in production environments!
    # Currently acting as a mockup portfolio endpoint
    
    # Query fresh instance directly from db
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.plan = "pro"
    await db.commit()
    
    return {"status": "success", "message": "Upgraded to PRO plan"}

@router.get("/portal")
async def get_portal_url(current_user: User = Depends(get_current_user)):
    # WARNING: Replace with Stripe Customer Portal URL creation
    return {"url": "https://billing.stripe.com/p/session/mock_url_for_portfolio"}
