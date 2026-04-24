<div align="center">
  <h1>🧠 StudyMind AI Platform</h1>
  <p><strong>The ultimate AI-powered workspace for modern students.</strong></p>
  <p>StudyMind transforms static notes into an interactive learning environment using Retrieval-Augmented Generation (RAG), automated flashcards, and adaptive quizzes.</p>

  <!-- Badges -->
  <img src="https://img.shields.io/badge/Python-3.11-blue.svg?style=for-the-badge&logo=python" alt="Python 3.11">
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react" alt="React 18">
  <img src="https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker" alt="Docker">
  <img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="License MIT">
  <img src="https://img.shields.io/badge/Coverage-75%25-brightgreen.svg?style=for-the-badge" alt="Coverage">
  <img src="https://img.shields.io/badge/Live_Demo-Available-blueviolet?style=for-the-badge" alt="Live Demo">
</div>

---

## 🌟 Overview
**StudyMind AI** is an enterprise-grade SaaS designed to automate the most tedious parts of studying. It allows students to "talk" to their textbooks, generate high-quality study materials instantly, and retain knowledge longer using cognitive-science-backed algorithms.

### 👤 Developed By: **Akshat Saraswat**

---

## 🚀 Quick Start (Production)

Spin up the entire production-grade stack in under 2 minutes.

```bash
# 1. Clone & Enter
git clone https://github.com/akshat-spec/studymind-ai-platform.git && cd studymind-ai-platform

# 2. Environment Setup
cp .env.example .env

# 3. Launch Services
docker-compose up --build -d

# 4. Initialize & Seed Demo Data
./scripts/init_db.sh && python scripts/seed_demo.py
```

### 🔑 Demo Credentials
Recruiters can instantly test the app without manual setup:
- **URL:** `http://localhost`
- **Email:** `demo@studymind.ai`
- **Password:** `demo1234`

---

## 🏗️ Architecture & Technical Depth

### 🧠 The RAG Pipeline
Built with **ChromaDB** and `sentence-transformers` (`all-MiniLM-L6-v2`), the system implements a robust Retrieval-Augmented Generation flow:
1. **Semantic Chunking:** Documents are split using recursive character text splitters with overlap to preserve context.
2. **Vector Retrieval:** Queries are embedded and compared against the vector store using cosine similarity.
3. **3-Tier Memory:**
   - *Sliding Window:* Recent conversation history for immediate context.
   - *Summarization:* Long-term conversation gist.
   - *Semantic Retrieval:* Relevant past facts retrieved from vector memory.

### 📈 Cognitive Optimization
- **SM-2 Algorithm:** Flashcards aren't just random; they use a mathematical implementation of the SuperMemo-2 algorithm to schedule reviews exactly when your brain is about to forget the information.
- **SSE Streaming:** Real-time AI responses are delivered via **Server-Sent Events (SSE)** for a "typing" effect, reducing perceived latency.

### 💼 SaaS Infrastructure
- **Usage Metering:** Atomic counters in **Redis** track document uploads, chat tokens, and card generations in real-time.
- **Rate Limiting:** Custom FastAPI middleware prevents API abuse via Leaky Bucket algorithms.

---

## 🛠️ Tech Stack

| Category | Tool | Why? |
| :--- | :--- | :--- |
| **Backend** | FastAPI | Asynchronous performance and automatic OpenAPI documentation. |
| **Frontend** | React + Vite | Blazing fast HMR and optimized production bundles. |
| **Database** | PostgreSQL | Robust relational storage for users, sessions, and analytics. |
| **Vector DB** | ChromaDB | Lightweight, high-performance vector search for RAG. |
| **Cache** | Redis | sub-millisecond usage metering and session management. |
| **Deployment** | Docker & Compose | Consistent, reproducible environments from local to EC2. |

---

## 📖 API Reference (Core Endpoints)

| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/register` | User onboarding with JWT issuance. |
| `POST` | `/api/documents/upload`| PDF processing and vectorization. |
| `POST` | `/api/chat/sessions` | Create a new AI-powered RAG session. |
| `GET` | `/api/flashcards/due` | Fetch cards scheduled for review via SM-2. |
| `GET` | `/api/usage/status` | Real-time subscription tier monitoring. |

---

## 📸 Screenshots

<div align="center">
  <img src="https://via.placeholder.com/800x450?text=AI+RAG+Chat+Interface" alt="Chat Interface" width="400">
  <img src="https://via.placeholder.com/800x450?text=Automated+Quiz+Generation" alt="Quiz Generation" width="400">
  <br>
  <img src="https://via.placeholder.com/800x450?text=SM-2+Flashcard+System" alt="Flashcards" width="400">
  <img src="https://via.placeholder.com/800x450?text=Usage+Metering+Dashboard" alt="Dashboard" width="400">
</div>

---

## 🔮 Future Work
- **Multimodal RAG:** Support for images and tables within PDF documents.
- **Collaborative Study Groups:** Real-time shared vector context for group projects.
- **Mobile Integration:** React Native companion app for on-the-go flashcard review.

---
<div align="center">
  <p>Built with ❤️ by <strong>Akshat Saraswat</strong></p>
</div>
