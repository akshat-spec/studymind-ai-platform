<div align="center">
  <h1>🧠 StudyMind AI Platform</h1>
  <p><strong>The ultimate AI-powered workspace for modern students.</strong></p>
  <p>StudyMind transforms your static notes into an interactive learning environment using Retrieval-Augmented Generation (RAG), automated flashcards, and adaptive quizzes.</p>

  <!-- Badges -->
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React">
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="Postgres">
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</div>

---

## 🌟 Overview
**StudyMind AI** is a comprehensive SaaS platform designed to streamline the learning process. It allows students to upload their study materials (PDFs, notes) and interact with them through an intelligent AI tutor. The platform doesn't just answer questions—it builds a personalized learning path through spaced repetition and active recall.

### Developed By: **Akshat Saraswat**

---

## ✨ Key Features

- **📂 AI-Powered RAG Chat:** Upload documents and chat with them. The system uses vector embeddings to provide accurate, context-aware answers based solely on your materials.
- **🗂️ Automated Flashcards:** Instantly generate flashcards from your notes. Includes a built-in **SM-2 Spaced Repetition** algorithm to optimize long-term retention.
- **📝 Quiz Generation:** Test your knowledge with AI-generated quizzes based on specific chapters or entire documents.
- **💳 SaaS Subscription Logic:** Integrated plan-based limits (Free vs. Pro) for document uploads, chat messages, and flashcard generation.
- **📊 Usage Analytics:** Real-time usage tracking via a dynamic dashboard to monitor your monthly limits and performance.
- **⚡ High-Performance Architecture:** Built with FastAPI (Asynchronous Python) and React + Vite for a seamless, low-latency user experience.

---

## 🛠️ Technical Stack

| Component | Technology |
| :--- | :--- |
| **Backend** | FastAPI, SQLAlchemy (Async), Pydantic |
| **Frontend** | React, TypeScript, Tailwind CSS, Vite |
| **Database** | PostgreSQL (Persistent data), Redis (Rate limiting & Counters) |
| **Vector Store** | ChromaDB / PGVector (Contextual Search) |
| **AI/ML** | LangChain, OpenAI/Gemini API, SM-2 Spaced Repetition |
| **DevOps** | Docker, Docker Compose, GitHub Actions |

---

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- OpenAI or Gemini API Key

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/akshat-spec/studymind-ai-platform.git
   cd studymind-ai-platform
   ```

2. **Set up environment variables:**
   Create a `.env` file in the root directory (refer to `.env.example`).
   ```bash
   cp .env.example .env
   ```

3. **Launch the platform:**
   ```bash
   docker-compose -f docker-compose.dev.yml up --build
   ```

The application will be available at:
- **Frontend:** `http://localhost:5173`
- **Backend API:** `http://localhost:8000`
- **API Documentation:** `http://localhost:8000/docs`

---

## 📖 API Architecture

The backend is structured into modular routers:
- `/auth`: Secure JWT authentication and user management.
- `/chat`: RAG-based document interaction sessions.
- `/documents`: File upload processing and vectorization.
- `/flashcards`: Spaced repetition management.
- `/quiz`: AI quiz generation and scoring.
- `/usage`: Real-time subscription limit enforcement.

---

## 🛤️ Roadmap

- [ ] **Native PDF Annotation:** Highlight and take notes directly on uploaded documents.
- [ ] **Collaborative Study Rooms:** Study with friends in real-time with shared AI context.
- [ ] **Mobile Application:** Dedicated iOS/Android app using React Native.
- [ ] **Voice-to-Note:** Record lectures and automatically convert them into flashcards.

---

<div align="center">
  <p>Built with ❤️ by <strong>Akshat Saraswat</strong></p>
</div>
