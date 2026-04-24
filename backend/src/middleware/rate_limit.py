from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone
from src.auth.router import get_current_user
from src.db.models import User
from src.services.usage_service import usage_service

def check_usage_limit(action: str):
    """
    FastAPI Dependency to check and lock active endpoints logically triggering HTTP 429 structured JSON.
    Example payload format: {"error": "limit_reached", "action": action, "limit": N, "resets_at": ISO8601, "upgrade_url": "/pricing"}
    """
    async def limitation_dependency(current_user: User = Depends(get_current_user)):
        checked = await usage_service.check_and_increment(
            user_id=str(current_user.id),
            action=action,
            plan=current_user.plan
        )
        
        if not checked["allowed"]:
            now = datetime.now(timezone.utc)
            if action == "flashcard_review":
                tomorrow = now + timedelta(days=1)
                resets_at = datetime(tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=timezone.utc).isoformat()
            else:
                import calendar
                _, last_day = calendar.monthrange(now.year, now.month)
                resets_at = datetime(now.year, now.month, last_day, 23, 59, 59, tzinfo=timezone.utc).isoformat()
            
            # Fastapi exception throws typical {"detail": string}
            # We want specific json bounds to match constraints, so we raise an HTTPException and catch it or just raise standard.
            # Using HTTPException with a dict detail allows frontend to parse `error.response.data.detail.error == "limit_reached"`
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "limit_reached",
                    "action": action,
                    "limit": checked["limit"],
                    "resets_at": resets_at,
                    "upgrade_url": "/pricing"
                }
            )
            
        return current_user
        
    return limitation_dependency
