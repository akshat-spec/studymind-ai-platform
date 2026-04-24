import json
from datetime import datetime, timedelta, timezone
from anthropic import AsyncAnthropic
from src.core.config import settings
from src.db.session import async_session_maker
from src.db.models import Flashcard
from sqlalchemy import select
from src.services.vector_store import vector_store

class FlashcardService:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.vector_store = vector_store

    def _calculate_sm2(self, ease_factor: float, interval: int, repetitions: int, rating: int):
        """
        SuperMemo-2 algorithm implementation.
        Rating: 0 (Blackout) - 5 (Perfect answer)
        If rating < 3: the card is rescheduled for immediate review (interval=0)
        """
        if rating >= 3:
            if repetitions == 0:
                interval = 1
            elif repetitions == 1:
                interval = 6
            else:
                interval = round(interval * ease_factor)
            repetitions += 1
        else:
            repetitions = 0
            interval = 0

        ease_factor = ease_factor + (0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02))
        
        if ease_factor < 1.3:
            ease_factor = 1.3
            
        return round(ease_factor, 2), interval, repetitions

    async def generate_flashcards(self, doc_id: str, user_id: str, num_cards: int = 20) -> list[dict]:
        """
        Extract concepts dynamically from scattered chunks via Claude API.
        Chunks are pulled sequentially to avoid overloading context limits, batching 5 at a time.
        """
        generated = []
        batch_size = 5
        
        # Pull chunks from Chroma
        # To avoid duplicating topics, we just simulate broad sampling over the doc by taking a large k
        chunks = await self.vector_store.similarity_search(doc_id, "Summary of key concepts and definitions", k=num_cards)
        if not chunks:
            return [] # No document content
            
        system_prompt = (
            "You are an expert study guide creator. Extract the most important concepts, facts, or definitions "
            "from the provided text and format them as high-quality flashcards. "
            "Always respond with a raw JSON block starting with `{\"flashcards\": [`. Do not wrap it in markdown. Do not include any other text."
        )

        for i in range(0, len(chunks), batch_size):
            if len(generated) >= num_cards:
                break
                
            batch_chunks = chunks[i:i + len(chunks) if len(chunks) < batch_size else i + batch_size]
            context_text = "\n".join([c["content"] for c in batch_chunks])
            
            prompt = f"Extract exactly {min(batch_size, num_cards - len(generated))} flashcards from this text:\n{context_text}\n\nFormat: {{\"flashcards\": [{{\"front\": \"Question/Concept\", \"back\": \"Answer/Definition\"}}]}}"

            try:
                response = await self.client.messages.create(
                    max_tokens=1000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}],
                    model="claude-3-haiku-20240307"
                )
                
                # Raw JSON extraction
                raw_json = response.content[0].text
                idx1 = raw_json.find('{')
                idx2 = raw_json.rfind('}')
                if idx1 != -1 and idx2 != -1:
                    json_text = raw_json[idx1:idx2+1]
                    data = json.loads(json_text)
                    generated.extend(data.get("flashcards", []))
            except Exception as e:
                print(f"Error generating flashcards batch: {e}")
                continue
                
        # Save to DB
        async with async_session_maker() as db:
            models = []
            for item in generated:
                card = Flashcard(
                    document_id=doc_id,
                    user_id=user_id,
                    front=item.get("front", "Unknown concept"),
                    back=item.get("back", "Unknown definition")
                )
                models.append(card)
                db.add(card)
            await db.commit()
            
            return [{"front": m.front, "back": m.back, "id": m.id} for m in models]

    async def update_flashcard_review(self, card_id: str, rating: int):
        async with async_session_maker() as db:
            result = await db.execute(select(Flashcard).where(Flashcard.id == card_id))
            card = result.scalar_one_or_none()
            
            if not card: return None
            
            new_ef, new_interval, new_reps = self._calculate_sm2(card.ease_factor, card.interval, card.repetitions, rating)
            
            card.ease_factor = new_ef
            card.interval = new_interval
            card.repetitions = new_reps
            
            # Map intervals to exact days, except if 0 then map to identical time right now
            if new_interval == 0:
                card.next_review = datetime.now(timezone.utc)
            else:
                card.next_review = datetime.now(timezone.utc) + timedelta(days=new_interval)
                
            await db.commit()
            await db.refresh(card)
            return card

flashcard_service = FlashcardService()
