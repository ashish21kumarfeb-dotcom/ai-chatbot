import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Set, Tuple

from app.rag.metadata_store import load_metadata

STOP_WORDS = {
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
    "how",
    "many",
    "tell",
    "me",
    "show",
    "give",
    "about",
    "total",
    "combined",
    "sum",
    "work",
    "working",
}

EXPERIENCE_QUERY_WORDS = {
    "experience",
    "experiences",
    "year",
    "years",
    "yr",
    "yrs",
    "professional",
    "work",
    "working",
    "total",
    "combined",
    "overall",
}

# Strict patterns: do NOT match plain dates like 2020 unless the text says "experience".
EXPERIENCE_PATTERNS = [
    re.compile(
        r"(?:over|more\s+than|around|approximately|approx\.?|about)?\s*"
        r"(?P<num>\d+(?:\.\d+)?)\s*\+?\s*"
        r"(?:years?|yrs?)\s+(?:of\s+)?"
        r"(?:professional\s+|work\s+|industry\s+|relevant\s+)?experience",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:professional\s+|work\s+|industry\s+|relevant\s+)?experience"
        r"[^\n\.;]{0,40}?"
        r"(?:over|more\s+than|around|approximately|approx\.?|about)?\s*"
        r"(?P<num>\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)",
        re.IGNORECASE,
    ),
]

RESUME_TYPES = {"resume", "cv"}


def _normalize(text: str) -> str:
    text = str(text or "").lower().strip()
    return re.sub(r"[^a-z0-9\s\.\+]+", " ", text)


def _tokens(text: str) -> Set[str]:
    return {
        token
        for token in _normalize(text).split()
        if len(token) > 1 and token not in STOP_WORDS
    }


def _target_name_tokens(question: str) -> Set[str]:
    """
    For: "What is total experience of Nitish and Brijesh?"
    return: {"nitish", "brijesh"}
    """
    return {token for token in _tokens(question) if token not in EXPERIENCE_QUERY_WORDS}


def _fact_to_text(fact: Any) -> str:
    if isinstance(fact, dict):
        return " ".join(
            str(fact.get(key, "")) for key in ["fact", "category", "value", "unit"]
        )
    return str(fact)


def _item_identity_text(item: Dict[str, Any]) -> str:
    universal = item.get("universal_metadata") or {}
    entities = universal.get("entities") or {}
    people = entities.get("people", []) or []

    return "\n".join(
        [
            item.get("filename", ""),
            item.get("document_type", ""),
            universal.get("title", ""),
            " ".join(str(person) for person in people),
        ]
    )


def _metadata_search_text(item: Dict[str, Any]) -> str:
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
        parts.append(_fact_to_text(fact))

    return "\n".join(parts)


def _match_score(question_tokens: Set[str], text: str) -> float:
    text_tokens = _tokens(text)
    if not question_tokens or not text_tokens:
        return 0.0

    overlap = len(question_tokens & text_tokens) / max(len(question_tokens), 1)
    fuzzy = SequenceMatcher(
        None, " ".join(sorted(question_tokens)), _normalize(text)
    ).ratio()
    return max(overlap, fuzzy)


def _matches_target_person(item: Dict[str, Any], target_tokens: Set[str]) -> bool:
    """
    Hard protection: if the user asked Nitish/Brijesh, do not include Acme.
    Match target names against people/title/filename only, not against summary/key_facts.
    """
    if not target_tokens:
        return True

    identity_tokens = _tokens(_item_identity_text(item))
    if target_tokens & identity_tokens:
        return True

    for target in target_tokens:
        for candidate in identity_tokens:
            if SequenceMatcher(None, target, candidate).ratio() >= 0.82:
                return True

    return False


def _extract_experience_years(text: str) -> Optional[float]:
    normalized_text = str(text or "")

    for pattern in EXPERIENCE_PATTERNS:
        match = pattern.search(normalized_text)
        if not match:
            continue

        years = float(match.group("num"))

        # Guardrail: experience cannot realistically be a calendar year like 2020.
        if years <= 0 or years > 60:
            continue

        return years

    return None


def _is_experience_query(question: str) -> bool:
    q = _normalize(question)
    return "experience" in q or "years" in q or "yrs" in q


def _format_sources(items: List[Dict[str, Any]]) -> List[str]:
    sources = []
    for item in items:
        filename = item.get("filename")
        if filename and filename not in sources:
            sources.append(filename)
    return sources


def _allowed_document_types_for_plan(question: str, plan: Dict[str, Any]) -> Set[str]:
    plan_types = set(plan.get("document_types") or [])

    # For experience questions, be strict. Company policies/handbooks must not be used.
    if _is_experience_query(question):
        return plan_types & RESUME_TYPES if plan_types else RESUME_TYPES

    return plan_types


def answer_from_metadata(question: str, plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tries to answer from structured metadata only.

    If it cannot answer confidently, returns found=False so graph can fallback to RAG.
    """
    metadata = load_metadata()
    if not metadata:
        return {"found": False, "answer": "", "sources": []}

    question_tokens = _tokens(question)
    target_tokens = (
        _target_name_tokens(question) if _is_experience_query(question) else set()
    )
    allowed_doc_types = _allowed_document_types_for_plan(question, plan)

    target_filenames = {
        target.get("filename")
        for target in plan.get("target_documents", [])
        if target.get("filename")
    }

    scored_items: List[Tuple[float, Dict[str, Any]]] = []

    for item in metadata:
        item_doc_type = item.get("document_type") or (
            item.get("classification") or {}
        ).get("document_type")

        # Hard filter: if planner selected resume, company_policy must not enter metadata answer.
        if allowed_doc_types and item_doc_type not in allowed_doc_types:
            continue

        # Hard filter for person-specific experience questions.
        if _is_experience_query(question) and not _matches_target_person(
            item, target_tokens
        ):
            continue

        text = _metadata_search_text(item)
        score = _match_score(question_tokens, text)

        if item.get("filename") in target_filenames:
            score += 0.35

        scored_items.append((score, item))

    scored_items.sort(key=lambda pair: pair[0], reverse=True)
    relevant_items = [item for score, item in scored_items if score >= 0.15][:5]

    if not relevant_items:
        return {"found": False, "answer": "", "sources": []}

    if _is_experience_query(question):
        lines = []
        used_items = []
        total_years = 0.0
        years_found = 0

        for item in relevant_items:
            universal = item.get("universal_metadata") or {}
            key_facts = universal.get("key_facts") or []
            people = (universal.get("entities") or {}).get("people", []) or []
            display_name = (
                people[0] if people else universal.get("title") or item.get("filename")
            )

            best_years = None

            # Prefer explicit key facts.
            for fact in key_facts:
                fact_text = _fact_to_text(fact)
                fact_norm = _normalize(fact_text)
                if "experience" not in fact_norm:
                    continue

                years = _extract_experience_years(fact_text)
                if years is not None:
                    best_years = years
                    break

            # Fallback: search full metadata, but strict regex prevents matching plain dates.
            if best_years is None:
                metadata_text = _metadata_search_text(item)
                best_years = _extract_experience_years(metadata_text)

            if best_years is not None:
                total_years += best_years
                years_found += 1
                used_items.append(item)
                lines.append(f"{display_name}: {best_years:g}+ years of experience.")

        if lines:
            if plan.get("needs_calculation") and years_found >= 2:
                lines.append(f"Combined total: approximately {total_years:g}+ years.")

            return {
                "found": True,
                "answer": "\n".join(lines),
                "sources": _format_sources(used_items),
            }

    # Generic metadata answer: return key facts if they match.
    matched_facts = []
    source_items = []

    for item in relevant_items:
        universal = item.get("universal_metadata") or {}
        key_facts = universal.get("key_facts") or []

        for fact in key_facts:
            fact_text = _fact_to_text(fact).strip()
            if not fact_text:
                continue
            if _match_score(question_tokens, fact_text) >= 0.25:
                matched_facts.append(f"- {fact_text}")
                source_items.append(item)

    if matched_facts:
        return {
            "found": True,
            "answer": "\n".join(matched_facts[:8]),
            "sources": _format_sources(source_items),
        }

    return {"found": False, "answer": "", "sources": []}
