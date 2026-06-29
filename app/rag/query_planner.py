import json
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from app.rag.metadata_store import load_metadata

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)


RESUME_TERMS = {
    "resume",
    "cv",
    "candidate",
    "profile",
    "experience",
    "experiences",
    "skill",
    "skills",
    "education",
    "project",
    "projects",
    "developer",
    "engineer",
    "email",
    "phone",
    "contact",
}

POLICY_TERMS = {
    "policy",
    "policies",
    "handbook",
    "leave",
    "leaves",
    "holiday",
    "holidays",
    "probation",
    "benefit",
    "benefits",
    "attendance",
    "remote",
    "work",
    "salary",
    "reimbursement",
    "conduct",
    "rule",
    "rules",
}

CONTRACT_TERMS = {
    "contract",
    "agreement",
    "clause",
    "party",
    "parties",
    "termination",
    "payment",
    "renewal",
    "liability",
    "effective",
    "expiry",
}

CALCULATION_TERMS = {
    "total",
    "combined",
    "sum",
    "average",
    "difference",
    "more",
    "less",
    "highest",
    "lowest",
    "compare",
    "comparison",
    "count",
}

METADATA_FIRST_TERMS = {
    "experience",
    "experiences",
    "skill",
    "skills",
    "email",
    "phone",
    "contact",
    "name",
    "candidate",
    "person",
    "profile",
    "education",
    "company name",
    "title",
    "summary",
    "date",
    "effective date",
}


def _normalize(text: str) -> str:
    text = text.lower().strip()
    return re.sub(r"[^a-z0-9\s]+", " ", text)


def _tokens(text: str) -> set[str]:
    stop_words = {
        "what",
        "is",
        "are",
        "the",
        "a",
        "an",
        "of",
        "and",
        "or",
        "to",
        "in",
        "for",
        "with",
        "on",
        "by",
        "from",
        "total",
        "combined",
        "how",
        "many",
        "tell",
        "me",
        "show",
        "give",
        "about",
    }
    return {
        token
        for token in _normalize(text).split()
        if len(token) > 1 and token not in stop_words
    }


def _score_text_match(question_tokens: set[str], candidate: str) -> float:
    candidate_tokens = _tokens(candidate)
    if not question_tokens or not candidate_tokens:
        return 0.0

    overlap = len(question_tokens & candidate_tokens) / len(candidate_tokens)
    fuzzy = SequenceMatcher(
        None, " ".join(sorted(question_tokens)), _normalize(candidate)
    ).ratio()
    return max(overlap, fuzzy)


def _metadata_text(item: Dict[str, Any]) -> str:
    universal = item.get("universal_metadata") or {}
    entities = universal.get("entities") or {}
    key_facts = universal.get("key_facts") or []

    parts: List[str] = [
        item.get("filename", ""),
        item.get("document_type", ""),
        universal.get("title", ""),
        universal.get("summary", ""),
        " ".join(universal.get("keywords", []) or []),
        " ".join(universal.get("topics", []) or []),
    ]

    for value in entities.values():
        if isinstance(value, list):
            parts.append(" ".join(str(v) for v in value))

    for fact in key_facts:
        if isinstance(fact, dict):
            parts.append(str(fact.get("fact", "")))
            parts.append(str(fact.get("category", "")))
        else:
            parts.append(str(fact))

    return "\n".join(parts)


def _detect_document_types(question: str) -> List[str]:
    q_tokens = _tokens(question)
    document_types: List[str] = []

    if q_tokens & RESUME_TERMS:
        document_types.append("resume")

    if q_tokens & POLICY_TERMS:
        document_types.extend(["company_policy", "policy", "handbook"])

    if q_tokens & CONTRACT_TERMS:
        document_types.append("contract")

    return list(dict.fromkeys(document_types))


def _detect_target_documents(
    question: str, metadata: List[Dict[str, Any]]
) -> List[Dict[str, str]]:
    question_tokens = _tokens(question)
    matches: List[Dict[str, str]] = []

    for item in metadata:
        filename = item.get("filename", "")
        candidates = [filename]

        universal = item.get("universal_metadata") or {}
        if universal.get("title"):
            candidates.append(universal["title"])

        entities = universal.get("entities") or {}
        for person in entities.get("people", []) or []:
            candidates.append(str(person))

        best_name = filename
        best_score = 0.0
        for candidate in candidates:
            score = _score_text_match(question_tokens, candidate)
            if score > best_score:
                best_score = score
                best_name = candidate

        if best_score >= 0.45:
            matches.append(
                {
                    "filename": filename,
                    "matched_as": best_name,
                    "score": round(best_score, 3),
                }
            )

    return sorted(matches, key=lambda item: item["score"], reverse=True)


def _rule_based_plan(question: str, metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
    q = _normalize(question)
    q_tokens = _tokens(question)

    document_types = _detect_document_types(question)
    target_documents = _detect_target_documents(question, metadata)

    needs_calculation = bool(q_tokens & CALCULATION_TERMS)
    metadata_first = any(term in q for term in METADATA_FIRST_TERMS)

    route = "rag"
    reason = "Default semantic RAG route."

    if metadata_first:
        route = "metadata_lookup_first"
        reason = "The query asks for structured facts like experience, skills, contact, names, dates, or profile information."

    if document_types and not metadata_first:
        route = "rag_with_filters"
        reason = "The query is about a known document type, so retrieval should be filtered/prioritized by document type."

    if needs_calculation and metadata_first:
        route = "metadata_lookup_first"
        reason = "The query needs factual extraction plus simple calculation. Metadata should be checked before RAG."

    rewritten_query = question
    if target_documents:
        matched_names = ", ".join(item["matched_as"] for item in target_documents[:5])
        rewritten_query = (
            f"{question}\nRelevant possible documents/entities: {matched_names}"
        )

    confidence = 0.75 if route != "rag" else 0.55

    return {
        "route": route,
        "reason": reason,
        "confidence": confidence,
        "needs_calculation": needs_calculation,
        "document_types": document_types,
        "target_documents": target_documents,
        "rewritten_query": rewritten_query,
        "fallback_route": "rag",
        "answer_style": "grounded_with_sources",
    }


def build_query_plan(question: str) -> Dict[str, Any]:
    """
    Query Planner Agent.

    It decides how the system should answer the question:
    - metadata_lookup_first: use structured document metadata first, then RAG fallback
    - rag_with_filters: use vector/BM25 retrieval but prioritize document types
    - rag: normal semantic RAG

    This starts rule-first for reliability and speed. If confidence is weak,
    it asks the LLM to refine the plan.
    """
    metadata = load_metadata()
    plan = _rule_based_plan(question, metadata)

    # Keep deterministic plan if confident enough.
    if plan["confidence"] >= 0.70:
        plan["planner_method"] = "rules"
        return plan

    metadata_snapshot = []
    for item in metadata[:20]:
        universal = item.get("universal_metadata") or {}
        metadata_snapshot.append(
            {
                "filename": item.get("filename"),
                "document_type": item.get("document_type", "other"),
                "title": universal.get("title", ""),
                "topics": (
                    universal.get("topics", [])[:8]
                    if isinstance(universal.get("topics", []), list)
                    else []
                ),
                "keywords": (
                    universal.get("keywords", [])[:8]
                    if isinstance(universal.get("keywords", []), list)
                    else []
                ),
            }
        )

    prompt = f"""
You are a query planner agent for a local document intelligence system.

Choose the best route for answering the user question.

Available routes:
- metadata_lookup_first: use when the question asks for structured facts like experience, skills, names, emails, dates, profile facts, titles, summaries, or simple calculations from extracted facts.
- rag_with_filters: use when the question asks about policies, handbook rules, contracts, reports, or broad document content and a document type filter can help.
- rag: use for general semantic questions, summaries, explanations, comparisons, and unknown cases.

Return JSON only with this schema:
{{
  "route": "metadata_lookup_first | rag_with_filters | rag",
  "reason": "short reason",
  "confidence": 0.0,
  "needs_calculation": false,
  "document_types": [],
  "rewritten_query": "improved query",
  "fallback_route": "rag",
  "answer_style": "grounded_with_sources"
}}

Question:
{question}

Known uploaded documents:
{json.dumps(metadata_snapshot, indent=2, ensure_ascii=False)}
"""

    try:
        response = llm.invoke(prompt)
        parsed = json.loads(response.content)
        plan.update({k: parsed.get(k, v) for k, v in plan.items()})
        plan["planner_method"] = "llm"
        return plan
    except Exception:
        plan["planner_method"] = "rules_fallback"
        return plan
