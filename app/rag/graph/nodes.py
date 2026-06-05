import os

from langchain_groq import ChatGroq

from app.rag.query_router import detect_query_type
from app.rag.hybrid_search import hybrid_search
from app.rag.metadata_store import load_metadata
from app.rag.graph.memory import (
    build_chat_history,
    add_to_memory
)
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)


def router_node(state):

    query_type = detect_query_type(
        state["question"]
    )

    state["query_type"] = query_type

    return state

def metadata_node(state):

    metadata = load_metadata()

    if not metadata:
        state["answer"] = "No documents uploaded."
        return state

    docs = []

    for item in metadata:
        docs.append(item["filename"])

    state["answer"] = "\n".join(docs)

    return state

def retrieval_node(state):

    docs = hybrid_search(
        state["question"]
    )

    context_parts = []

    sources = set()

    for doc in docs:

        source = os.path.basename(
            doc.metadata.get(
                "source",
                "Unknown"
            )
        )

        sources.add(source)

        context_parts.append(
            f"""
SOURCE:
{source}

CONTENT:
{doc.page_content}
"""
        )

    state["context"] = "\n\n".join(
        context_parts
    )

    state["sources"] = list(sources)

    return state

def memory_node(state):

    history = build_chat_history(
        state["session_id"]
    )

    state["chat_history"] = history

    return state

def llm_node(state):

    # No relevant context
    if not state["context"]:

        state["answer"] = (
            "I could not find this information "
            "in uploaded documents."
        )

        return state

    prompt = f"""
You are a company AI assistant.

Use ONLY the provided document context.

You also have access to previous
conversation history.

Rules:
- Answer ONLY from context
- Do NOT hallucinate
- Do NOT make assumptions
- Use chat history for follow-up questions
- Mention filenames only if relevant
- If answer not found, say:
"I could not find this information in uploaded documents."

CHAT HISTORY:
{state["chat_history"]}

DOCUMENT CONTEXT:
{state["context"]}

QUESTION:
{state["question"]}

ANSWER:
"""

    response = llm.invoke(prompt)

    answer = response.content.strip()

    state["answer"] = answer

    add_to_memory(
        state["session_id"],
        "user",
        state["question"]
    )

    add_to_memory(
        state["session_id"],
        "assistant",
        answer
    )

    return state