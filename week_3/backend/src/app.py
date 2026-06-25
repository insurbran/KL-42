from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.path.append(str(Path(__file__).parent / "week_2"))

from find_skill_gaps import find_skill_gaps
from prompt_model import prompt_model

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.getenv("DB_PATH", "src/week_2/data/jobs_d1.db")

@app.post("/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        message = body.get("message", "")
        pdf_text = body.get("pdf_text", "")

        if pdf_text:
            temp_path = "src/week_2/data/temp_resume.txt"
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(pdf_text)
            result = find_skill_gaps(temp_path, DB_PATH)
            reply = f"Skill gaps found: {', '.join(result.gaps)}"
        elif message:
            reply = prompt_model("llama3.1", message)
        else:
            reply = "Please type a message or upload a PDF resume."

        return JSONResponse({"reply": reply})

    except Exception as e:
        return JSONResponse({"reply": f"[Error] {e}"}, status_code=500)