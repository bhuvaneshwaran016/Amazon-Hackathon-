import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env before importing modules that read environment variables.
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from task_store import init_db, list_tasks
from agent import chat

init_db()
app = FastAPI(title="TaskPilot AI", version="1.0.0")
INDEX = Path(__file__).parent / "static" / "index.html"

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

@app.get("/", response_class=HTMLResponse)
def home():
    return INDEX.read_text(encoding="utf-8")

@app.get("/api/tasks")
def tasks():
    return list_tasks("all")

@app.post("/api/chat")
def chat_endpoint(body: ChatRequest):
    try:
        return {"reply": chat(body.message), "tasks": list_tasks("all")["tasks"]}
    except Exception as exc:
        print(f"Chat error: {type(exc).__name__}: {exc}")
        raise HTTPException(
    status_code=500,
    detail="The AI backend failed. Check Ollama, provider settings, and the server terminal."
)