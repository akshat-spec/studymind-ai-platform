import json
import tiktoken
from typing import AsyncGenerator
from anthropic import AsyncAnthropic
from src.core.config import settings
from src.services.vector_store import vector_store
from src.services.memory_service import memory_service
from src.db.session import async_session_maker
from src.db.models import ChatMessage, ChatSession
from sqlalchemy import select

class RAGService:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.vector_store = vector_store
        self.encoder = tiktoken.get_encoding("cl100k_base") # Approximate token counting used generically

    def _count_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))

    async def retrieve_context(self, doc_id: str, query: str, k: int = 5) -> str:
        chunks = await self.vector_store.similarity_search(doc_id, query, k)
        
        formatted_chunks = []
        for chunk in chunks:
            formatted_chunks.append(f"{chunk['content']}\n")
            
        return "\n".join(formatted_chunks)

    async def build_rag_prompt(self, doc_id: str, session_id: str, query: str) -> tuple[list[dict], str]:
        # Fetch full memory context
        memory_ctx = await memory_service.get_memory_context(session_id, query)
        
        # Format RAG document context
        doc_context = await self.retrieve_context(doc_id, query, k=5)
        
        # Construct system message
        system_message = (
            "You are a helpful study assistant. "
            "Answer the user's question based ONLY on the provided document context and conversational history. "
            "Always cite your sources explicitly in your answer using the format: 'According to page [N] of your document...'. "
            "If the answer is not in the context, do not guess, simply state that you cannot find the answer in the document."
        )
        if memory_ctx["session_summary"]:
            system_message += f"\n\n{memory_ctx['session_summary']}"

        base_prompt_text = f"DOCUMENT CONTEXT:\n{doc_context}\n\n"
        
        # Calculate tokens to keep within 80k maximum limit
        budget = 80000
        current_tokens = self._count_tokens(system_message) + self._count_tokens(base_prompt_text) + self._count_tokens(query)
        
        # Add semantic context if budget allows
        semantic_text = memory_ctx["semantic_past"]
        if semantic_text and current_tokens + self._count_tokens(semantic_text) < budget:
            base_prompt_text += f"{semantic_text}\n\n"
            current_tokens += self._count_tokens(semantic_text)
            
        base_prompt_text += f"USER QUESTION: {query}"
        
        # Add short-term history, trimming oldest if over budget
        history = memory_ctx["recent_messages"]
        final_history = []
        for msg in reversed(history): # traverse from most recent
            msg_tokens = self._count_tokens(msg["content"])
            if current_tokens + msg_tokens < budget:
                final_history.insert(0, msg) # prepend to keep chronological
                current_tokens += msg_tokens
            else:
                break # exceeded budget for history
                
        # Append the new prompt
        final_history.append({"role": "user", "content": base_prompt_text})
        
        return final_history, system_message

    async def generate_answer(self, doc_id: str, session_id: str, query: str) -> AsyncGenerator[str, None]:
        # 1. Build prompt internally wrapped with budget mechanisms
        messages, system_message = await self.build_rag_prompt(doc_id, session_id, query)
        
        # 2. Call Claude API streamingly
        full_response = ""
        stream = await self.client.messages.create(
            max_tokens=1024,
            system=system_message,
            messages=messages,
            model="claude-3-5-sonnet-20240620",
            stream=True
        )
        
        async for event in stream:
            if event.type == "content_block_delta" and event.delta.type == "text_delta":
                chunk = event.delta.text
                full_response += chunk
                
                # yield SSE formatted chunk safely
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        # Signal completion
        yield "data: [DONE]\n\n"
        
        # 3. Store message & calculate updates
        async with async_session_maker() as db:
            # Query active msg counts
            count_res = await db.execute(select(ChatMessage).where(ChatMessage.session_id == session_id))
            messages_ct = len(count_res.scalars().all())
            
            user_msg = ChatMessage(session_id=session_id, role="user", content=query, token_count=self._count_tokens(query))
            assistant_msg = ChatMessage(session_id=session_id, role="assistant", content=full_response, token_count=self._count_tokens(full_response))
            db.add(user_msg)
            db.add(assistant_msg)
            
            # Autogenerate title if it's the very first message in the session
            if messages_ct == 0:
                session_res = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
                session = session_res.scalar_one()
                session.title = query[:50] + "..." if len(query) > 50 else query
            
            await db.commit()
            
            # 4. Trigger decoupled memory updates
            new_total = messages_ct + 2 # Add the 2 new messages
            await memory_service.update_session_summary(session_id, new_total)
            await memory_service.push_to_semantic_memory(session_id, query, full_response)

rag_service = RAGService()
