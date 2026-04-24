import redis.asyncio as redis
from datetime import datetime, timedelta, timezone
from src.core.config import settings
from src.core.limits import get_plan_limits
import calendar

# A global async redis connection pool
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

class UsageService:
    def _get_ttl_seconds(self, action: str) -> int:
        """
        Calculate TTL. Flashcards reset daily, others reset end of month.
        """
        now = datetime.now(timezone.utc)
        if action == "flashcard_review":
            tomorrow = now + timedelta(days=1)
            eod = datetime(tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=timezone.utc)
            return int((eod - now).total_seconds())
        else:
            _, last_day = calendar.monthrange(now.year, now.month)
            eom = datetime(now.year, now.month, last_day, 23, 59, 59, tzinfo=timezone.utc)
            return int((eom - now).total_seconds())
            
    def _get_key(self, user_id: str, action: str) -> str:
        now = datetime.now(timezone.utc)
        period = now.strftime("%Y-%m-%d") if action == "flashcard_review" else now.strftime("%Y-%m")
        return f"usage:{user_id}:{action}:{period}"

    async def check_and_increment(self, user_id: str, action: str, plan: str) -> dict:
        """
        Atomic increment over Redis.
        Returns {"allowed": bool, "limit": Optional[int], "used": Optional[int], "error": Optional[str]}
        """
        limits = get_plan_limits(plan)
        limit_val = getattr(limits, action, None)
        
        # None means unlimited tracking bypass
        if limit_val is None:
            return {"allowed": True, "limit": None, "used": None}
            
        key = self._get_key(user_id, action)
        ttl = self._get_ttl_seconds(action)
        
        # MULTI/EXEC block
        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.get(key)
            results = await pipe.execute()
            
            current_val = int(results[0]) if results[0] else 0
            
            if current_val >= limit_val:
                return {
                    "allowed": False, 
                    "limit": limit_val, 
                    "used": current_val,
                    "error": "limit_reached"
                }
                
            # It's allowed, increment atomically
            pipe.incr(key)
            pipe.expire(key, ttl)
            res = await pipe.execute()
            new_val = res[0]
            
            return {
                "allowed": True,
                "limit": limit_val,
                "used": new_val
            }

    async def get_usage_summary(self, user_id: str, plan: str) -> dict:
        """
        Return all current counters vs limits for UI banner display.
        """
        limits = get_plan_limits(plan)
        actions = ["document_uploaded", "chat_message", "quiz_generated", "flashcard_review"]
        
        summary = {}
        
        async with redis_client.pipeline(transaction=True) as pipe:
            for action in actions:
                key = self._get_key(user_id, action)
                pipe.get(key)
            results = await pipe.execute()
            
            for i, action in enumerate(actions):
                limit_val = getattr(limits, action, None)
                used_val = int(results[i]) if results[i] else 0
                
                summary[action] = {
                    "used": used_val,
                    "limit": limit_val,
                    "is_unlimited": limit_val is None
                }
                
        return summary
        
usage_service = UsageService()
