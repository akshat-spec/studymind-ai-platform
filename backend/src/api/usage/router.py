from fastapi import APIRouter
from src.services.usage_service import redis_client

router = APIRouter(prefix="/usage", tags=["usage"])

@router.get("/stats")
async def get_usage_stats():
    # Admin mock endpoint gathering total redis interactions.
    # Note: Using KEYS in production over large datastore blocks thread, use SCAN natively.
    keys = await redis_client.keys("usage:*")
    
    msg_sent_count = 0
    for k in keys:
        if "chat_message" in k:
            val = await redis_client.get(k)
            msg_sent_count += int(val) if val else 0
            
    return {
        "total_active_monthly_records": len(keys),
        "total_messages_sent_tracked": msg_sent_count
    }
