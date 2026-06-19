# Week 2 - AI Skill Gap Detection Pipeline

## Project Description
An AI-powered pipeline that analyzes job listings and resumes to identify skill gaps. It uses LLMs (Gemini and local Ollama models) to extract tech stacks from job descriptions and compare them against a candidate's resume to surface missing skills in the job market.

## Prerequisites

### Required Software
- Python 3.14+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) - Python package manager
- [Ollama](https://ollama.com/download) 0.21.* - Local LLM runner

### Install uv
**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install Ollama
Download from https://ollama.com/download and install it.

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

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/insurbran/KL-42.git
cd KL-42/week_2
```

### 2. Install dependencies
```bash
uv sync
```

### 3. Configure environment variables
Create a `.env` file in the `week_2/` folder:

> ⚠️ Never commit your `.env` file. It is already in `.gitignore`.

### 4. Prepare data
Place your database and resume files in the `data/` folder:

## Usage

### Test the model connection
```bash
# Test Ollama
uv run prompt_model.py llama3.1 "tell me a joke"

# Test Gemini
uv run prompt_model.py gemini-2.5-flash "tell me a joke"
```

### Tag job descriptions with tech stacks
```bash
uv run tag_data.py
```
Reads untagged jobs from `data/jobs_d1.db` and populates the `tech_stack` column using Gemini.

Expected output: 
Analyzed Job 91397216: Python, SQL, Java, R, Tableau...

Analyzed Job 91347112: Java, Spring Boot, Python, Docker...

...

Total tokens used: 2044, took 19305.595ms

Running again produces:
No data to tag

Total tokens used: 0, took 16.676ms


### Find skill gaps
```bash
uv run find_skill_gaps.py
```
Compares the resume against all job tech stacks in the database and returns missing skills.

Expected output:
gaps=['alibaba cloud', 'aws', 'azure', ...] time=21315 tokens=800 demand={'mysql': 4, 'aws': 2, ...}
📊 Skill Demand:

mysql: 4 job(s)

aws: 2 job(s)

...

## Rate Limits
See `rate_limits.txt` for Gemini model rate limits.

> ⚠️ Gemini free tier allows only 20 requests per day. Use Ollama models for testing to avoid hitting limits.

To switch between models, change the model name in `tag_data.py` and `find_skill_gaps.py`:
```python
# Ollama (local, unlimited)
response = prompt_model("llama3.1", prompt)

# Gemini (cloud, limited)
response = prompt_model("gemini-2.5-flash", prompt)
```

## Security
`find_skill_gaps.py` includes jailbreak detection on resume input. If a resume contains prompt injection attempts like `ignore previous instructions`, the program will abort and return empty results.

Example of detected jailbreak:
[Security] Jailbreak attempt detected in resume. Aborting.

gaps=[] time=0 tokens=0 demand={}

## Technical Reflections

### LLM Setup and Rate Limits
Why use both Gemini and Ollama instead of just one?
- **Answer**: Gemini offers higher quality responses but has strict rate limits (5 RPM, 20 RPD on free tier). Ollama runs locally with no rate limits, making it ideal for development and testing. Using both gives flexibility — Ollama for iteration, Gemini for final quality output. The batch size and retry delay in `tag_data.py` are calculated based on Gemini's 5 RPM limit — 5 seconds between retries ensures we never exceed the rate limit.

### Input and Output Serialization
Why use Pydantic for the output of `find_skill_gaps`?
- **Answer**: Pydantic enforces a strict data contract on the output. Without it, the function could return inconsistent structures — sometimes missing `demand`, sometimes returning gaps as a string instead of a list. Pydantic guarantees the shape of the output every time, making it safe to consume downstream in Week 3's frontend.

### LLM Resource Management
How do you prevent wasting tokens?
- **Answer**: Job descriptions are truncated to 800 characters before being sent to the model. The prompt is kept minimal and specific — no examples beyond the format hint. The `WHERE tech_stack IS NULL OR tech_stack = ''` query ensures already-tagged jobs are never sent to the model again. Together these reduce token usage significantly.

### LLM Performance Benchmarking
How is performance measured?
- **Answer**: Both `tag_data.py` and `find_skill_gaps.py` track total tokens used and total time elapsed in milliseconds. Token count is estimated at 4 tokens per word when the model doesn't return usage metadata. This allows comparing model performance across runs and between Gemini and Ollama.

### LLM Feature Engineering
Why tag tech stacks separately instead of sending raw descriptions to `find_skill_gaps`?
- **Answer**: Raw job descriptions contain noise — company culture, benefits, soft skills, salary ranges. By pre-extracting tech stacks into a structured column during tagging, the skill gap analysis works on clean, focused data. This improves accuracy, reduces token usage in `find_skill_gaps`, and separates concerns cleanly — tagging is a one-time ETL step, gap analysis is a real-time query.
