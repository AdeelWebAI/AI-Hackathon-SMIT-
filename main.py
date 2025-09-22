import os
from typing import List, Optional, Any, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# your existing imports (same as in your working agent)
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

from tools import (
    add_student,
    get_student,
    update_student,
    delete_student,
    list_students,
    get_total_students,
    get_students_by_department,
    get_recent_onboarded_students,
    get_active_students_last_7_days,
)

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing in .env")

app = FastAPI(title="MongoDB Agent API (FastAPI)")

# Agent will be created once at startup
agent = None

# ---- request/response models ----
class MessageItem(BaseModel):
    role: str    # e.g. "user", "assistant", "system"
    content: str

class ChatRequest(BaseModel):
    # either provide `query` (a single user message) or `history` (list of role/content)
    query: Optional[str] = None
    history: Optional[List[MessageItem]] = None

class ChatResponse(BaseModel):
    assistant: str
    raw: Any

# ---- startup: create model + agent ----
@app.on_event("startup")
async def startup_event():
    global agent
    model = ChatOpenAI(
        model="gemini-2.0-flash",
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    tools = [
        add_student,
        get_student,
        update_student,
        delete_student,
        list_students,
        get_total_students,
        get_students_by_department,
        get_recent_onboarded_students,
        get_active_students_last_7_days,
    ]

    # create agent (same call you use in the terminal)
    agent = create_react_agent(model, tools)


@app.get("/health")
async def health():
    return {"status": "ok", "agent_ready": agent is not None}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent is not initialized yet")

    # build messages in the same format your agent expects: list of (role, content)
    messages = []
    if req.history:
        for m in req.history:
            messages.append((m.role, m.content))

    if req.query:
        messages.append(("user", req.query))

    if not messages:
        raise HTTPException(status_code=400, detail="Provide `query` or `history` in the request body")

    try:
        result = await agent.ainvoke({"messages": messages})
    except Exception as e:
        # return a helpful error
        raise HTTPException(status_code=500, detail=f"Agent invocation failed: {e}")

    # robustly extract assistant text from result
    assistant_text = ""
    try:
        if isinstance(result, dict):
            msgs = result.get("messages") or result.get("output") or None
            if msgs and len(msgs) > 0:
                last = msgs[-1]
                if isinstance(last, dict):
                    assistant_text = last.get("content") or last.get("text") or str(last)
                else:
                    assistant_text = getattr(last, "content", None) or getattr(last, "text", None) or str(last)
            else:
                assistant_text = str(result)
        else:
            assistant_text = str(result)
        assistant_text = assistant_text.strip()
    except Exception:
        assistant_text = str(result)

    return {"assistant": assistant_text, "raw": result}
