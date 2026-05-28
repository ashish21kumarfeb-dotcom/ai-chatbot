from fastapi import APIRouter
from pydantic import BaseModel

from app.rag.chatbot import ask_question


router = APIRouter()


class ChatRequest(BaseModel):
    question: str


@router.post("/chat")
async def chat(request: ChatRequest):

    response = ask_question(
        request.question
    )

    return {
        "question": request.question,
        "answer": response["answer"],
        "sources": response["sources"]
    }