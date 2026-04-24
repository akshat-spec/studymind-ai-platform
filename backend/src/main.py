from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.auth.router import router as auth_router
from src.api.documents.router import router as documents_router
from src.api.chat.router import router as chat_router
from src.api.quiz.router import router as quiz_router
from src.api.flashcards.router import router as flashcards_router
from src.api.billing.router import router as billing_router
from src.api.usage.router import router as usage_router
from src.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True, # Need this for cookies to work
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(quiz_router)
app.include_router(flashcards_router)
app.include_router(billing_router)
app.include_router(usage_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
