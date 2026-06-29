from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.upload import router as upload_router
from app.api.chat import router as chat_router
from app.rag.vectorstore import cleanup_vectorstore
from app.rag.hybrid_search import rebuild_bm25_index
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="Company AI Chatbot")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
cleanup_vectorstore()
rebuild_bm25_index()
app.include_router(upload_router)
app.include_router(chat_router)

@app.get("/")
def root():
    return {"message": "Company AI Chatbot Running"}