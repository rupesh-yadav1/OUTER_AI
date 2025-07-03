# 🤖 AI Multi-Model Chat Router

> A smart AI assistant that automatically routes your questions to the best language model (ChatGPT, Gemini, or Groq) for optimal responses.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com)

---

## 🎯 Overview

This application intelligently routes user queries to the most suitable AI model based on the question type and context. Whether you need coding help, image generation, or quick calculations, the system automatically selects the best model for your needs.

---

### ✨ Key Features

- 🧠 **Smart Model Routing** – Selects ChatGPT, Gemini, or Groq based on content
- ⚡ **Real-time Streaming** – Live token streaming from all models
- 🖼️ **Image Generation** – Supports Gemini's image capabilities
- 🔐 **JWT Authentication** – Secure login/signup with token auth
- 💬 **Chat History** – User-specific persistent message storage
- 🐳 **Docker Ready** – Fully containerized app with multi-stage Docker build
- 📱 **Single-Page UI** – `chat.html` powered frontend with Markdown/KaTeX/code support

---

## 🏗️ Architecture

```
Frontend (chat.html)
      │
      ▼
FastAPI Backend ──→ [Router] → ChatGPT / Gemini / Groq
      │
      ▼
   MongoDB (Users + Chat History)
```

---

## 🚀 Quick Start

### 🔧 Prerequisites

- Docker & Docker Compose
- API Keys (OpenAI, Gemini, Groq)
- MongoDB URI (Atlas or local)

---

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ai-multi-model-router.git
cd ai-multi-model-router
```

---

### 2. Configure Environment

Create a `.env` file in your project root:

```env
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
GROQ_API_KEY=...
MONGODB_URI=mongodb+srv://...
SECRET_KEY=super-secret-key
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

---

### 3. Build and Run with Docker

```bash
docker build -t ai-router .
docker run -p 8000:8000 --env-file .env ai-router
```

Then open:  
➡️ `http://localhost:8000/chat.html`

---

## 🛠️ Local Development

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

pip install -r requirements.txt

uvicorn backend.main:app --reload
```

---

## 📂 Project Structure

```
ai-router/
├── backend/
│   ├── main.py           # App entry
│   ├── auth.py           # JWT auth
│   ├── router.py         # Model routing
│   ├── db.py             # MongoDB connector
│   └── models/
│       ├── chatgpt.py
│       ├── gemini.py
│       └── groq.py
├── chat.html             # Frontend UI
├── Dockerfile
├── requirements.txt
├── .env                  # API keys (ignored)
└── README.md             # This file
```

---

## 📡 API Endpoints

### 🔐 Auth

| Method | Endpoint        | Description       |
|--------|------------------|-------------------|
| POST   | `/auth/signup`   | Register user     |
| POST   | `/auth/token`    | Login + JWT token |
| GET    | `/auth/me`       | Current user info |

### 💬 Chat

| Method | Endpoint        | Description             |
|--------|------------------|-------------------------|
| POST   | `/chat-stream`   | Chat with LLM (stream)  |
| GET    | `/history`       | Retrieve chat history   |
| GET    | `/health`        | Health check            |

---

## 🧠 Model Routing Logic

- **💻 ChatGPT**: Complex prompts, reasoning, coding
- **🎨 Gemini**: Creative prompts, image generation
- **⚡ Groq**: Fast, low-latency responses for basic/maths

Routing is done via rules and can fall back on GPT-assisted routing logic.

---

## 🔒 Security

- ✅ JWT-based login with token expiration
- ✅ Passwords hashed with bcrypt
- ✅ Secrets isolated in `.env` (not committed)

---

## 🐳 Docker Compose (Optional)

```yaml
version: '3.8'
services:
  ai-router:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - mongodb

  mongodb:
    image: mongo
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

---

## ✅ Deployment

For production:

```bash
docker build -t ai-router:prod .
docker run -d --env-file .env -p 8000:8000 --name ai-app ai-router:prod
```

---

## 🧪 Testing

```bash
pytest
pytest --cov=backend
```

---

## 🤝 Contributing

1. Fork the repo
2. Create your branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to GitHub: `git push origin feature/my-feature`
5. Open a Pull Request 🎉

---

## 📄 License

MIT License – see [`LICENSE`](LICENSE) for full details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com)
- [OpenAI](https://platform.openai.com)
- [Gemini](https://ai.google.dev/)
- [Groq](https://groq.com)
- [MongoDB](https://mongodb.com)

---

## 📬 Contact

- 📧 your-email@example.com
- 🌐 GitHub: [yourusername](https://github.com/yourusername)

---

<div align="center"><strong>Built with ❤️ by [Your Name]</strong></div>
