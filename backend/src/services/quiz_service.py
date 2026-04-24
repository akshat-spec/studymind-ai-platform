import json
import re
from anthropic import AsyncAnthropic
from src.core.config import settings
from src.db.session import async_session_maker
from src.db.models import Quiz
from src.services.vector_store import vector_store

class QuizService:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.vector_store = vector_store

    async def generate_quiz(self, doc_id: str, user_id: str, num_questions: int = 10, difficulty: str = "medium", topic_focus: str = None) -> str:
        # Build query conceptually representing topic or general spread
        query = f"Concepts about {topic_focus}" if topic_focus else "Summary of core concepts, facts, and essential details across the document."
        
        # Pull k=15 to ensure diverse spread
        chunks = await self.vector_store.similarity_search(doc_id, query, k=max(num_questions + 5, 20))
        if not chunks:
            raise ValueError("Document appears empty or not processed.")
            
        context_text = "\n".join([f"Page [{c['metadata'].get('page', 'Unknown')}]: {c['content']}" for c in chunks])
        
        diff_guide = {
            "easy": "factual recall, simple definitions",
            "medium": "comprehension, synthesis of ideas",
            "hard": "application, analysis, critical thinking"
        }.get(difficulty, "comprehension")

        system_prompt = (
            "You are an expert educational assessment creator. Your job is to strictly output JSON. "
            "Never output markdown wrapping. Start immediately with `{`."
        )
        
        prompt = f"""
        Given the following document chunks, generate a {num_questions}-question multiple choice quiz.
        The difficulty level should target: {diff_guide}.
        
        Strict JSON Schema to return:
        {{
           "questions": [
             {{
                "id": 1,
                "question": "string",
                "options": ["A", "B", "C", "D"],
                "correct": "A",
                "explanation": "string explaining why A is correct",
                "page_ref": 1
             }}
           ]
        }}
        
        Document Context:
        {context_text}
        """

        max_retries = 1
        data = None
        
        for _ in range(max_retries + 1):
            try:
                response = await self.client.messages.create(
                    max_tokens=4000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}],
                    model="claude-3-5-sonnet-20240620"
                )
                raw_json = response.content[0].text
                
                # Robust json clean step
                raw_json = re.sub(r'```json\n|\n```', '', raw_json).strip()
                idx1 = raw_json.find('{')
                idx2 = raw_json.rfind('}')
                if idx1 != -1 and idx2 != -1:
                    clean = raw_json[idx1:idx2+1]
                    data = json.loads(clean)
                    if "questions" in data and len(data["questions"]) > 0:
                        break
            except Exception as e:
                print(f"Quiz Json generation error: {e}, retrying...")
                continue
                
        if not data or "questions" not in data:
            raise ValueError("Failed to generate a valid quiz structural block.")
            
        title = f"{difficulty.title()} Assessment"
        if topic_focus:
            title += f" on {topic_focus}"

        async with async_session_maker() as db:
            quiz = Quiz(
                document_id=doc_id,
                user_id=user_id,
                title=title,
                questions=data["questions"]
            )
            db.add(quiz)
            await db.commit()
            await db.refresh(quiz)
            return str(quiz.id)

quiz_service = QuizService()
