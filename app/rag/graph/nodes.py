import os

from langchain_groq import ChatGroq

from app.rag.intent_classifier import classify_intent
from app.rag.query_router import detect_query_type
from app.rag.hybrid_search import hybrid_search
from app.rag.metadata_store import load_metadata
from app.rag.graph.memory import build_chat_history, add_to_memory
from dotenv import load_dotenv
from textwrap import dedent

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)


def router_node(state):

    intent = classify_intent(
        state["question"]
    )

    state["query_type"] = intent

    print(
        "\n===== ROUTER ====="
    )

    print(
        "QUESTION:",
        state["question"]
    )

    print(
        "INTENT:",
        intent
    )

    return state


def greeting_node(state):

    prompt = f"""
You are a friendly AI assistant.

Conversation History:
{state.get("chat_history", "")}

User:
{state["question"]}

Rules:
- Reply naturally.
- Keep response under 25 words.
- Be conversational.
- If user says they are good, respond positively.
- If user asks how are you, answer briefly.
- Do not mention documents.
- Do not mention uploaded files.
"""

    response = llm.invoke(prompt)

    state["answer"] = response.content.strip()

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

    docs = hybrid_search(state["question"])

    context_parts = []

    sources = set()

    for doc in docs:

        source = os.path.basename(doc.metadata.get("source", "Unknown"))

        sources.add(source)

        print("\n===== DOC PASSED TO LLM =====")

        print("SOURCE:", source)

        print(doc.page_content[:300])

        context_parts.append(f"""
SOURCE:
{source}

CONTENT:
{doc.page_content}
""")

    state["context"] = "\n\n".join(context_parts)

    print("\n====== FINAL CONTEXT ======")

    print(state["context"])

    state["sources"] = list(sources)

    return state


def memory_node(state):

    history = build_chat_history(state["session_id"])

    state["chat_history"] = history

    return state

def llm_node(state):

    # No relevant context
    if not state["context"]:

        state["answer"] = "I could not find this information " "in uploaded documents."

        return state

    prompt = f"""
You are a company AI assistant.

Answer ONLY from the provided document context.

IMPORTANT RULES:

1. If the answer exists in the context,
   return the answer directly.

2. If the answer appears anywhere in the context,
   use it exactly as written.

3. Do NOT ignore contact information,
   email addresses, phone numbers,
   URLs, names or identifiers.

4. Do NOT say information is missing
   if it is present in the context.

5. If the answer is genuinely absent,
   respond exactly:

I could not find this information in uploaded documents.

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

    add_to_memory(state["session_id"], "user", state["question"])

    add_to_memory(state["session_id"], "assistant", answer)

    return state
