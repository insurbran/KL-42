import os
import httpx
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="src/templates")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="chat_page.html",
        context={"backend_url": ""}
    )


@app.post("/chat")
async def chat_proxy(request: Request):
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(f"{BACKEND_URL}/chat", json=body)
            print(f"[Proxy] Backend response status: {response.status_code}")
            print(f"[Proxy] Backend response: {response.text[:200]}")
            return JSONResponse(response.json())
    except Exception as e:
        print(f"[Frontend Proxy Error] {type(e).__name__}: {e}")
        return JSONResponse({"reply": f"[Error] {e}"}, status_code=500)