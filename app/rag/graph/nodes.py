import os


import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq

from app.rag.intent_classifier import classify_intent
from app.rag.hybrid_search import hybrid_search
from app.rag.metadata_store import load_metadata
from app.rag.graph.memory import build_chat_history, add_to_memory
from app.rag.query_understanding import understand_query
from app.rag.evidence_extractor import extract_evidence
from app.rag.answer_composer import compose_answer
from app.rag.answer_verifier import verify_answer
from app.rag.guardrails.input_guard import validate_user_question

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)


def router_node(state):
    intent = classify_intent(state["question"])
    state["query_type"] = intent

    print("\n===== ROUTER =====")
    print("QUESTION:", state["question"])
    print("INTENT:", intent)

    return state


def greeting_node(state):
    prompt = f"""
You are a friendly AI assistant.

Conversation History:
{state.get('chat_history', '')}

User:
{state['question']}

Rules:
- Reply naturally.
- Keep response under 25 words.
- Be conversational.
- Do not mention documents unless user asked about documents.
"""
    response = llm.invoke(prompt)
    state["answer"] = response.content.strip()
    return state


def _load_all_file_metadata() -> list[dict]:
    possible_paths = [
        Path("app/data/file_metadata.json"),
        Path("data/file_metadata.json"),
        Path("app/rag/data/file_metadata.json"),
    ]

    metadata_path = None

    for path in possible_paths:
        if path.exists():
            metadata_path = path
            break

    if metadata_path is None:
        return []

    try:
        raw = json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    if isinstance(raw, list):
        return raw

    if isinstance(raw, dict):
        if isinstance(raw.get("files"), list):
            return raw["files"]

        # Handles dict format like:
        # {"filename.pdf": {...}, "other.pdf": {...}}
        values = list(raw.values())
        if values and all(isinstance(item, dict) for item in values):
            return values

    return []


def _is_uploaded_documents_summary_question(question: str) -> bool:
    q = (question or "").lower()

    summary_words = ["summarize", "summary", "overview", "brief"]
    document_words = ["uploaded documents", "uploaded files", "documents", "files"]

    return any(word in q for word in summary_words) and any(
        word in q for word in document_words
    )


def _build_uploaded_documents_summary() -> tuple[str, list[str]]:
    all_metadata = _load_all_file_metadata()

    if not all_metadata:
        return "I could not find uploaded document metadata.", []

    lines = ["Here is a summary of the uploaded documents:"]

    sources = []

    for item in all_metadata:
        filename = item.get("filename", "Unknown file")
        document_type = item.get("document_type", "unknown")

        universal_metadata = item.get("universal_metadata", {}) or {}

        title = universal_metadata.get("title") or filename
        summary = universal_metadata.get("summary") or ""
        topics = universal_metadata.get("topics") or []
        keywords = universal_metadata.get("keywords") or []
        key_facts = universal_metadata.get("key_facts") or []

        sources.append(filename)

        lines.append("")
        lines.append(f"- {title}")
        lines.append(f"  Source file: {filename}")
        lines.append(f"  Document type: {document_type}")

        if summary:
            lines.append(f"  Summary: {summary}")

        if topics:
            topic_text = ", ".join(str(topic) for topic in topics[:8])
            lines.append(f"  Main topics: {topic_text}")

        if keywords:
            keyword_text = ", ".join(str(keyword) for keyword in keywords[:10])
            lines.append(f"  Keywords: {keyword_text}")

        if key_facts:
            fact_texts = []

            for fact in key_facts[:3]:
                if isinstance(fact, dict):
                    fact_value = fact.get("fact") or fact.get("value") or ""
                else:
                    fact_value = str(fact)

                if fact_value:
                    fact_texts.append(fact_value)

            if fact_texts:
                lines.append("  Key facts:")
                for fact_text in fact_texts:
                    lines.append(f"    - {fact_text}")

    return "\n".join(lines), sources


def metadata_node(state):
    metadata = load_metadata()

    if not metadata:
        state["answer"] = "No documents uploaded."
        state["sources"] = []
        return state

    question = state.get("question", "")

    if _is_uploaded_documents_summary_question(question):
        answer, sources = _build_uploaded_documents_summary(metadata)

        state["answer"] = answer
        state["sources"] = sources
        return state

    filenames = [item.get("filename", "Unknown") for item in metadata]

    state["answer"] = "\n".join(filenames)
    state["sources"] = filenames
    return state


def memory_node(state):
    state["chat_history"] = build_chat_history(state["session_id"])
    return state


def query_understanding_node(state):
    analysis = understand_query(
        question=state["question"],
        chat_history=state.get("chat_history", ""),
    )

    state["query_analysis"] = analysis

    print("\n===== QUERY UNDERSTANDING =====")
    print(analysis)

    return state


def retrieval_node(state):
    query_analysis = state.get("query_analysis", {}) or {}
    document_types = query_analysis.get("target_document_types", []) or []

    docs = hybrid_search(
        state["question"],
        document_types=document_types,
    )

    context_parts = []
    sources = []

    for doc in docs:
        source = os.path.basename(doc.metadata.get("source", "Unknown"))
        doc_type = doc.metadata.get("document_type", "unknown")

        if source not in sources:
            sources.append(source)

        print("\n===== DOC PASSED TO EVIDENCE EXTRACTOR =====")
        print("SOURCE:", source)
        print("DOC TYPE:", doc_type)
        print(doc.page_content[:300])

        context_parts.append(f"""
SOURCE: {source}
DOCUMENT_TYPE: {doc_type}
CONTENT:
{doc.page_content}
""")

    state["context"] = "\n\n".join(context_parts)
    state["sources"] = sources

    return state


def evidence_extraction_node(state):
    evidence = extract_evidence(
        question=state["question"],
        query_analysis=state.get("query_analysis", {}),
        context=state.get("context", ""),
    )

    state["evidence"] = evidence

    print("\n===== EXTRACTED EVIDENCE =====")
    print(evidence)

    return state


def answer_composer_node(state):
    result = compose_answer(
        question=state["question"],
        query_analysis=state.get("query_analysis", {}),
        evidence=state.get("evidence", {}),
    )

    state["draft_answer"] = result["answer"]
    state["answer"] = result["answer"]

    # Use only actual evidence sources, not every retrieved source.
    if result.get("sources"):
        state["sources"] = result["sources"]

    print("\n===== DRAFT ANSWER =====")
    print(state["draft_answer"])

    return state


def answer_verifier_node(state):
    verification = verify_answer(
        question=state["question"],
        query_analysis=state.get("query_analysis", {}),
        evidence=state.get("evidence", {}),
        answer=state.get("draft_answer", ""),
    )

    state["verification"] = verification
    state["answer"] = verification.get("final_answer") or state.get("draft_answer", "")

    add_to_memory(state["session_id"], "user", state["question"])
    add_to_memory(state["session_id"], "assistant", state["answer"])

    print("\n===== ANSWER VERIFICATION =====")
    print(verification)

    return state


def input_guard_node(state: dict) -> dict:
    print("\n===== INPUT GUARD =====")
    print("QUESTION:", state.get("question"))

    result = validate_user_question(state.get("question", ""))

    print("GUARD RESULT:", result.to_dict())

    if not result.allowed:
        return {
            **state,
            "question": state.get("question", ""),
            "answer": result.user_message,
            "sources": [],
            "context": "",
            "guardrail_status": result.to_dict(),
            "blocked_by_guardrail": True,
        }

    return {
        **state,
        "question": result.safe_question,
        "guardrail_status": result.to_dict(),
        "blocked_by_guardrail": False,
    }
