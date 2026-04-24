import asyncio
from anthropic import AsyncAnthropic
from src.core.config import settings
from src.db.session import async_session_maker
from src.db.models import ChatMessage, ChatSession
from src.services.vector_store import vector_store
from sqlalchemy import select

class MemoryService:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.vector_store = vector_store
        
    async def get_short_term_memory(self, session_id: str, limit: int = 10) -> list[dict]:
        """Load last N messages loaded from PostgreSQL per session."""
        history = []
        async with async_session_maker() as db:
            result = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at.desc())
                .limit(limit)
            )
            messages = result.scalars().all()
            messages.reverse() # chronological
            
            for msg in messages:
                history.append({"role": msg.role, "content": msg.content})
        
        return history

    async def get_semantic_memory(self, session_id: str, query: str, k: int = 3) -> str:
        """When building RAG context, embed the user query against past ChatMessage content in ChromaDB"""
        # Session isolated chroma collections:
        collection_id = f"session_{str(session_id).replace('-', '_')}"
        
        # Check if collection has data yet, if not, it will return [] gracefully handling missing collections
        chunks = await self.vector_store.similarity_search(session_id, query, k, custom_collection_id=collection_id)
        
        if not chunks:
            return ""
            
        formatted = "--- Past Relevant Conversation Context ---\n"
        for chunk in chunks:
            formatted += f"{chunk['content']}\n"
            
        return formatted

    async def get_session_summary(self, session_id: str) -> str:
        async with async_session_maker() as db:
            result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
            session = result.scalar_one_or_none()
            if session and session.summary:
                return f"--- Previous Conversation Summary ---\n{session.summary}\n"
            return ""

    async def get_memory_context(self, session_id: str, query: str) -> dict:
        """Returns merged context: {recent_messages, session_summary, semantically_similar_past_messages}"""
        # Concurrent memory fetching
        history, semantic_context, summary = await asyncio.gather(
            self.get_short_term_memory(session_id),
            self.get_semantic_memory(session_id, query),
            self.get_session_summary(session_id)
        )
        
        return {
            "recent_messages": history,
            "session_summary": summary,
            "semantic_past": semantic_context
        }

    async def update_session_summary_task(self, session_id: str):
        """Background task: every 20 messages, call Claude to produce a 3-sentence summary of the conversation so far"""
        try:
            async with async_session_maker() as db:
                result = await db.execute(
                    select(ChatMessage)
                    .where(ChatMessage.session_id == session_id)
                    .order_by(ChatMessage.created_at.asc())
                )
                messages = result.scalars().all()

                if len(messages) == 0:
                    return

                context = "\n".join([f"{m.role}: {m.content}" for m in messages])
                
                # Request 3-sentence summary
                prompt = f"Summarize the following conversation in exactly 3 sentences:\n\n{context}"
                
                response = await self.client.messages.create(
                    max_tokens=200,
                    messages=[{"role": "user", "content": prompt}],
                    model="claude-3-haiku-20240307" # Cheaper model for summarisation
                )
                
                summary = response.content[0].text
                
                # Update DB
                session_result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
                session = session_result.scalar_one()
                session.summary = summary
                await db.commit()
                
        except Exception as e:
            print(f"Failed to update summary: {e}")

    async def update_session_summary(self, session_id: str, message_count: int):
        """Triggers summarisation if message count % 20 == 0"""
        if message_count > 0 and message_count % 20 == 0:
            loop = asyncio.get_event_loop()
            loop.create_task(self.update_session_summary_task(session_id))
            
    async def push_to_semantic_memory(self, session_id: str, query: str, answer: str):
        """Helper to index a turn into session semantic cache"""
        collection_id = f"session_{str(session_id).replace('-', '_')}"
        # We need vector_store to accept custom collections
        chunk_content = f"User: {query}\nAssistant: {answer}"
        await self.vector_store.create_collection(collection_id, custom_collection_id=collection_id)
        
        # We just need a unique ID, we can hash the string or just use time. We'll let chromadb handle sequential pushes securely internally
        # by passing the total messages count
        async with async_session_maker() as db:
            count_res = await db.execute(select(ChatMessage).where(ChatMessage.session_id == session_id))
            count = len(count_res.scalars().all())
            
        await self.vector_store.add_chunks(
            doc_id=session_id, 
            chunks=[chunk_content], 
            metadatas=[{"role": "exchange", "turn": count}], 
            custom_collection_id=collection_id
        )

memory_service = MemoryService()
