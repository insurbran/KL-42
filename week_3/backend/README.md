# Week 3 - Skill Gap Detection App

## Project Description
A full-stack containerized application that combines the Week 2 AI skill gap detection pipeline with a chat-based frontend. Users can upload their resume as a PDF and receive a list of skill gaps based on real job market data. Built with FastAPI, Jinja2, Docker, and Docker Compose.

## Prerequisites

### Required Software
- Python 3.14+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) - Python package manager
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) - Container runtime
- [Ollama](https://github.com/ollama/ollama/releases/download/v0.21.0/OllamaSetup.exe) 0.21.* - Local LLM runner
- [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) (Windows only) - Required for Docker Desktop

### Install uv
**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install Docker Desktop
Download and install from https://www.docker.com/products/docker-desktop/

**Windows only** — install WSL2 first:
```powershell
wsl --install
```
Then restart your computer before installing Docker Desktop.

### Install Ollama 0.21.*
Download the exact version from:
https://github.com/ollama/ollama/releases/download/v0.21.0/OllamaSetup.exe

Then pull the required models:
```bash
ollama pull llama3.1
ollama pull phi3
ollama pull deepseek-r1:1.5b
```

Verify Ollama is running:
```bash
curl 127.0.0.1:11434
ollama -v
ollama ls
```

### Google AI API Key
1. Go to https://aistudio.google.com/
2. Click **Get API Key** → **Create API Key**
3. Copy the key

## Project Structure
week_3/
├── frontend/
│   ├── .dockerignore
│   ├── Dockerfile
│   ├── .python-version
│   ├── pyproject.toml
│   ├── uv.lock
│   └── src/
│       ├── app.py
│       └── templates/
│           └── chat_page.html
├── backend/
│   ├── .dockerignore
│   ├── Dockerfile
│   ├── .python-version
│   ├── pyproject.toml
│   ├── uv.lock
│   └── src/
│       ├── app.py
│       └── week_2/
│           ├── prompt_model.py
│           ├── find_skill_gaps.py
│           ├── tag_data.py
│           └── data/
│               ├── jobs_d1.db
│               └── resume_d3.txt
├── .gitignore
├── .env.example
├── docker-compose.yml
└── README.md

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/insurbran/KL-42.git
cd KL-42/week_3
```

### 2. Configure environment variables
Create a `.env` file in the `week_3/` folder:
GOOGLE_API_KEY=your_api_key_here

> ⚠️ Never commit your `.env` file. It is already in `.gitignore`.

### 3. Make sure Ollama is running
```bash
ollama serve
```

### 4. Build and run with Docker Compose
```bash
docker compose up --build
```

## Usage

### Access the app
Go to `http://localhost:8000` in your browser.

### Chat without PDF
Type any message and the bot will respond conversationally using llama3.1.

### Upload a PDF resume
Click the upload button and select a PDF resume. The app will automatically:
1. Extract text from the PDF
2. Send it to the backend
3. Compare it against job market tech stacks
4. Return a list of skill gaps

Expected output:
Skill gaps found: alibaba cloud, aws, azure, c++, mysql, node.js, ...

### Running services individually (without Docker)

**Frontend:**
```bash
cd frontend
uv run uvicorn --app-dir src app:app --reload --port 8000
```

**Backend:**
```bash
cd backend
uv run uvicorn --app-dir src app:app --reload --port 8001
```

## Architecture
Internet
↕ 8000
┌─────────────────────────────┐
│       Docker Network        │
│  ┌──────────┐  ┌─────────┐ │
│  │ Frontend │←→│ Backend │ │
│  │  :8000   │  │  :8001  │ │
│  └──────────┘  └─────────┘ │
│                    ↕ 11434  │
└─────────────────────────────┘
↕
OLLAMA
(host machine)

The frontend and backend run as separate Docker containers on a shared bridge network. The backend accesses Ollama on the host machine via `host.docker.internal:11434`.

## Security
The backend includes CORS middleware to only allow requests from the frontend. The skill gap analysis includes jailbreak detection — if a resume contains prompt injection attempts, the analysis is aborted.

## Technical Reflections

### Frontend Server
Why use FastAPI with Jinja2 instead of serving plain HTML?
- **Answer**: FastAPI with Jinja2 allows injecting server-side variables like `BACKEND_URL` into the HTML at request time. This means the backend URL can be configured via environment variables without hardcoding it in the HTML — making the frontend portable across different environments (local, Docker, cloud).

### Chat Page Implementation
Why convert PDF to text in the browser instead of sending the raw file to the backend?
- **Answer**: Converting in the browser using PDF.js avoids sending large binary files over the network. The extracted text is much smaller and can be sent as JSON directly. It also keeps the backend simple — it only receives plain text, not file uploads.

### Backend Server
Why use a POST endpoint instead of GET for the chat?
- **Answer**: GET requests are for retrieving data and have URL length limits. POST requests send data in the request body, which can handle large payloads like PDF text. Since we're sending user input and PDF content to the backend, POST is the correct method.

### Application Orchestration
Why use Docker Compose instead of running services manually?
- **Answer**: Docker Compose defines the entire application stack in one file — services, ports, networks, and environment variables. Running `docker compose up` starts everything in the correct order with the correct configuration. Without it, you'd have to manually start each service, set environment variables, and configure networking every time.