# AI Company Chatbot

An AI-powered company knowledge assistant built using FastAPI, LangGraph, LangChain, ChromaDB, BM25 Hybrid Search, and Groq LLMs.

The chatbot allows users to:

- Upload company documents
- Ask questions about uploaded documents
- Retrieve contextual answers using RAG
- Maintain conversation memory
- Perform hybrid retrieval using:
  - Vector Search (ChromaDB)
  - BM25 Keyword Search
- Use LangGraph workflow orchestration

---

## Features

### Document Upload

Supports:

- PDF
- DOCX
- TXT
- CSV
- XLSX
- PPTX
- JSON
- HTML
- Markdown

### Hybrid Retrieval

Combines:

- Semantic Search (Embeddings)
- BM25 Keyword Search

Improves retrieval accuracy for both:

- Meaning-based queries
- Exact keyword queries

### Conversation Memory

Maintains chat history per session.

Example:

User:
```
Who is the CEO?
```

User:
```
What is his email?
```

The chatbot understands follow-up questions.

### LangGraph Workflow

```text
User Question
      │
      ▼
Router Node
      │
      ▼
Memory Node
      │
      ▼
Retrieval Node
      │
      ▼
LLM Node
      │
      ▼
Answer
```

---

## Tech Stack

### Backend

- FastAPI
- LangChain
- LangGraph

### Retrieval

- ChromaDB
- Sentence Transformers
- BM25

### LLM

- Groq
- Llama 3.1 8B Instant

---

## Installation

### Clone Repository

```bash
git clone https://github.com/yourusername/ai-company-chatbot.git

cd ai-company-chatbot
```

### Create Virtual Environment

Using uv:

```bash
uv venv
```

Activate:

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/Mac:

```bash
source .venv/bin/activate
```

### Install Dependencies

```bash
uv pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file.

```env
GROQ_API_KEY=your_key_here
```

---

## Run Project

```bash
uvicorn app.main:app --reload
```

Swagger:

```text
http://localhost:8000/docs
```

---

## API Endpoints

### Upload File

```http
POST /upload
```

### Delete File

```http
DELETE /upload/{filename}
```

### Chat

```http
POST /chat
```

Request:

```json
{
  "session_id": "user123",
  "question": "What is the leave policy?"
}
```

Response:

```json
{
  "session_id": "user123",
  "question": "What is the leave policy?",
  "answer": "...",
  "sources": [
    "employee_handbook.pdf"
  ]
}
```

---

## Project Structure

```text
app
│
├── api
│   ├── upload.py
│   └── chat.py
│
├── rag
│   ├── graph
│   │   ├── graph_builder.py
│   │   ├── nodes.py
│   │   ├── memory.py
│   │   └── state.py
│   │
│   ├── vectorstore.py
│   ├── hybrid_search.py
│   ├── embeddings.py
│   ├── loader.py
│   └── splitter.py
│
├── uploads
├── vectorstore
│
└── main.py
```

---

## Roadmap

- [ ] Persistent memory
- [ ] User authentication
- [ ] Streaming responses
- [ ] Citations with chunk references
- [ ] Multi-user support
- [ ] Docker deployment
- [ ] Kubernetes deployment
- [ ] Agentic RAG
- [ ] MCP integration
- [ ] Evaluation framework

---

## License

MIT License
