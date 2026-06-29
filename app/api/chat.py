from typing import Optional
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel

from app.rag.chatbot import ask_question

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


@router.post("/chat")
async def chat(request: ChatRequest):
    if not request.session_id:
        request.session_id = str(uuid4())

    print(
        f"Received request: question={request.question}, "
        f"session_id={request.session_id}"
    )

    response = ask_question(
        question=request.question,
        session_id=request.session_id,
    )

    return {
        "session_id": request.session_id,
        "question": request.question,
        "answer": response["answer"],
        "sources": response["sources"],
        "query_analysis": response.get("query_analysis", {}),
        "evidence": response.get("evidence", {}),
        "verification": response.get("verification", {}),
    }
