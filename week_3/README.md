# Week 3 - Skill Gap Detection Chat App

## Project Overview
A full-stack containerized chat application that helps users identify skill gaps in the job market. Users can upload their resume as a PDF and receive a list of missing technical skills based on real job listing data from Week 1. The app is built with FastAPI, Jinja2, PDF.js, Docker, and integrates the AI pipeline from Week 2.

## Prerequisites

### Required Software
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) - Container runtime
- [Ollama](https://github.com/ollama/ollama/releases/download/v0.21.0/OllamaSetup.exe) 0.21.* - Local LLM runner
- [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) (Windows only) - Required for Docker Desktop
- [uv](https://docs.astral.sh/uv/getting-started/installation/) - Python package manager (for manual setup only)

### Install Docker Desktop
Download from https://www.docker.com/products/docker-desktop/

**Windows only** — install WSL2 first:
```powershell
wsl --install
```
Restart your computer, then install Docker Desktop.

### Install Ollama 0.21.*
Download the exact version:
https://github.com/ollama/ollama/releases/download/v0.21.0/OllamaSetup.exe

Pull the required models:
```bash
ollama pull llama3.1
ollama pull phi3
ollama pull deepseek-r1:1.5b
```

### Google AI API Key
1. Go to https://aistudio.google.com/
2. Click **Get API Key** → **Create API Key**
3. Copy the key

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/insurbran/KL-42.git
cd KL-42/week_3
```

### 2. Configure environment variables
Create a `.env` file in the `week_3/` folder based on `.env.example`:
GOOGLE_API_KEY=your_api_key_here

> ⚠️ Never commit your `.env` file. It is already in `.gitignore`.

### 3. Start Ollama
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
Type any message and send it. The bot will respond conversationally using llama3.1.

Example:
User: What skills should I learn for data engineering?
Bot: To get started in data engineering, you should focus on...

### Upload a PDF resume
Click the upload button (↑) and select a PDF resume. The app will automatically:
1. Extract text from the PDF using PDF.js in the browser
2. Send the extracted text to the backend
3. Compare it against job market tech stacks in the database
4. Return a list of skill gaps

Expected output:
Skill gaps found: alibaba cloud, aws, azure, c++, mysql, node.js, postgresql, spring boot...

## API / Function Reference

### Backend — `POST /chat`
Endpoint that processes user messages and PDF uploads.

**Request payload:**
```json
{
  "message": "user typed message",
  "pdf_text": "extracted text from PDF or empty string"
}
```

**Response:**
```json
{
  "reply": "Skill gaps found: aws, mysql, ..."
}
```

**Logic:**
- If `pdf_text` is not empty → run `find_skill_gaps()` and return gap list
- If `pdf_text` is empty → pass `message` to llama3.1 and return conversational response

### Frontend — Key JavaScript Functions

**`sendMessage()`**
Triggered by the Send button or Enter key. Reads the text input, appends it to the chat box as a user bubble, sends it to `POST /chat` with empty `pdf_text`, and appends the response as a bot bubble.

**PDF upload handler (`fileUpload` change event)**
Triggered when a PDF is selected. Uses PDF.js to extract text from each page, appends status messages to the chat box, then automatically sends the extracted text to `POST /chat` and displays the skill gap result.

**`appendMessage(role, text)`**
Helper function that creates a chat bubble and appends it to the chat box. Role is either `"user"` or `"bot"` which determines the bubble style and alignment.

### Service Communication
The frontend and backend run as separate Docker containers on a shared bridge network called `app-network`. The browser sends requests to `http://localhost:8001/chat` which is mapped to the backend container's port 8001. The backend accesses Ollama on the host machine via `host.docker.internal:11434`.

## Data / Assumptions

### Data Flow
1. User types a message or uploads a PDF in the browser
2. JavaScript sends a `POST` request to `http://localhost:8001/chat` with JSON payload
3. Backend receives the payload and decides to run skill gap analysis or call llama3.1
4. Backend returns a JSON response with a `reply` field
5. Frontend displays the reply as a bot bubble in the chat

### Input Format Expectations
- PDF files only (`.pdf`) — other file types are not supported
- PDF text is extracted page by page using PDF.js before being sent to the backend
- Messages are plain text strings

### Data Limitations
- The job database (`jobs_d1.db`) contains only 84 records from Week 1's scrape
- PDF text extraction may fail on scanned or image-based PDFs since PDF.js only reads text layers
- Job descriptions are truncated to 800 characters when sent to the AI model

### Simplifications
- The skill gap analysis always compares against the full job database — there is no filtering by job type or location
- Chat history is not sent to the backend — each message is processed independently with no memory

## Testing

### Backend Testing
Test the `/chat` endpoint directly using PowerShell:

```powershell
# Test conversational response (no PDF)
Invoke-WebRequest -Uri "http://localhost:8001/chat" -Method POST -ContentType "application/json" -Body '{"message": "hello", "pdf_text": ""}' -UseBasicParsing

# Test skill gap analysis (with PDF text)
Invoke-WebRequest -Uri "http://localhost:8001/chat" -Method POST -ContentType "application/json" -Body '{"message": "", "pdf_text": "Python, SQL, Docker"}' -UseBasicParsing
```

Expected response for skill gap test:
```json
{"reply": "Skill gaps found: aws, mysql, node.js, ..."}
```

### Frontend Testing
1. Go to `http://localhost:8000`
2. Type "hello" and click Send — verify a conversational response appears
3. Click the upload button and select `resume_d3_eval.pdf` — verify skill gaps appear automatically
4. Type "thank you" after uploading — verify the bot responds conversationally, not with skill gaps again

### Docker Network Testing
Verify both containers are running and connected:
```bash
docker compose ps
```
Expected output shows both `frontend` and `backend` with status `Up`.

## Limitations

- **No chat memory** — each message is processed independently. The bot has no context of previous messages in the conversation.
- **PDF quality** — scanned PDFs or image-based PDFs will not work since PDF.js only extracts text layers.
- **Slow responses** — llama3.1 is a large local model. Responses may take 10-30 seconds depending on hardware.
- **Small database** — skill gap analysis is based on only 84 job listings from a single scrape. Results may not reflect the broader job market.
- **No authentication** — anyone with access to the app can use it. There is no user login or session management.
- **Chat history not saved** — refreshing the page clears all chat history.
- **Single resume** — the app analyzes one resume at a time. There is no way to compare multiple resumes.
- **Rate limits** — Gemini models have a 20 RPD free tier limit. Heavy usage may exhaust the daily quota.

## Architecture Reflection

### Design Choices
The app uses a microservices architecture with the frontend and backend as separate Docker containers. This separation means the frontend only handles UI and user interaction while the backend handles all AI processing. If the AI model needs to be swapped or scaled, only the backend container needs to change — the frontend is unaffected. Docker Compose ties both services together with a shared bridge network, making deployment a single command.

### Trade-offs
Docker Compose was chosen over manual setup for ease of deployment — anyone can run the app without installing Python dependencies manually. The trade-off is that Docker adds overhead and requires more disk space. The chat interface was kept simple (no React or Vue) to reduce complexity — the trade-off is limited interactivity and no real-time streaming of model responses.

### Improvements
Given more time the following would be added:
- **Streaming responses** — show the model's response word by word instead of waiting for the full reply
- **Chat history persistence** — store conversations in a database so users can resume previous sessions
- **Better PDF handling** — use a server-side PDF parser to handle scanned documents
- **Cloud deployment** — deploy to AWS or GCP so the app is accessible without running Docker locally
- **Frontend framework** — rebuild the UI in React for better state management and component reuse
