import json
import os
import re
from typing import Dict, List

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

# Keep this enum small and stable. Query planner will use these values later.
DOCUMENT_TYPES = {
    "resume",
    "company_policy",
    "handbook",
    "faq",
    "contract",
    "invoice",
    "knowledge_base",
    "meeting_notes",
    "report",
    "other",
}

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
)


def _sample_text(documents, max_chars: int = 6000) -> str:
    """
    Classifier does not need the full document.
    A bounded sample keeps classification faster and cheaper.
    """
    text = "\n\n".join(doc.page_content for doc in documents[:5])
    return text[:max_chars]


def _safe_json_loads(raw: str) -> Dict:
    """
    LLMs sometimes wrap JSON in markdown fences.
    This helper extracts the first JSON object safely.
    """
    if not raw:
        return {}

    cleaned = raw.strip()
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}


def _normalize_type(document_type: str) -> str:
    value = (document_type or "other").lower().strip()
    value = value.replace(" ", "_").replace("-", "_")
    return value if value in DOCUMENT_TYPES else "other"


def _rule_based_classification(text: str, filename: str = "") -> Dict:
    """
    Fast deterministic classifier.
    We use this before the LLM because many document types are obvious.
    """
    combined = f"{filename}\n{text}".lower()

    rules = [
        (
            "resume",
            [
                "resume",
                "curriculum vitae",
                "work experience",
                "professional experience",
                "technical skills",
                "education",
                "projects",
            ],
        ),
        (
            "invoice",
            [
                "invoice",
                "invoice number",
                "bill to",
                "amount due",
                "subtotal",
                "tax",
                "total amount",
            ],
        ),
        (
            "contract",
            [
                "agreement",
                "contract",
                "party",
                "parties",
                "termination",
                "governing law",
                "effective date",
            ],
        ),
        (
            "company_policy",
            [
                "policy",
                "leave policy",
                "remote work",
                "code of conduct",
                "probation",
                "compliance",
            ],
        ),
        (
            "handbook",
            [
                "employee handbook",
                "handbook",
                "benefits",
                "workplace",
                "hr",
                "employees must",
            ],
        ),
        (
            "faq",
            ["frequently asked questions", "faq", "question:", "answer:"],
        ),
        (
            "meeting_notes",
            [
                "meeting notes",
                "minutes of meeting",
                "attendees",
                "action items",
                "agenda",
            ],
        ),
        (
            "report",
            ["report", "executive summary", "findings", "recommendations", "analysis"],
        ),
        (
            "knowledge_base",
            ["knowledge base", "how to", "troubleshooting", "guide", "steps"],
        ),
    ]

    best_type = "other"
    best_score = 0
    best_matches: List[str] = []

    for document_type, keywords in rules:
        matches = [keyword for keyword in keywords if keyword in combined]
        if len(matches) > best_score:
            best_type = document_type
            best_score = len(matches)
            best_matches = matches

    if best_score >= 2:
        confidence = min(0.95, 0.55 + (best_score * 0.1))
    elif best_score == 1:
        confidence = 0.55
    else:
        confidence = 0.2

    return {
        "document_type": best_type,
        "confidence": confidence,
        "reason": f"Rule-based matches: {', '.join(best_matches) if best_matches else 'none'}",
        "method": "rules",
    }


def classify_document(documents, filename: str = "") -> Dict:
    """
    Returns a stable document classification object.

    Output example:
    {
        "document_type": "resume",
        "confidence": 0.86,
        "reason": "Contains work experience and technical skills",
        "method": "llm"
    }
    """
    text = _sample_text(documents)
    rule_result = _rule_based_classification(text, filename)

    # If rules are confident enough, do not spend an LLM call.
    if rule_result["confidence"] >= 0.75:
        return rule_result

    prompt = f"""
You are a document classification engine.

Classify the document into exactly one of these types:
- resume
- company_policy
- handbook
- faq
- contract
- invoice
- knowledge_base
- meeting_notes
- report
- other

Return JSON only with this schema:
{{
  "document_type": "one_of_the_allowed_types",
  "confidence": 0.0,
  "reason": "short reason"
}}

Rules:
- Do not invent information.
- Use "other" if the type is unclear.
- confidence must be between 0 and 1.

Filename:
{filename}

Document sample:
{text}
"""

    try:
        response = llm.invoke(prompt)
        parsed = _safe_json_loads(response.content)

        document_type = _normalize_type(parsed.get("document_type"))
        confidence = parsed.get("confidence", rule_result["confidence"])

        try:
            confidence = float(confidence)
        except TypeError, ValueError:
            confidence = rule_result["confidence"]

        confidence = max(0.0, min(1.0, confidence))

        return {
            "document_type": document_type,
            "confidence": confidence,
            "reason": parsed.get("reason") or rule_result["reason"],
            "method": "llm",
        }

    except Exception as exc:
        # Upload should not fail just because classification failed.
        return {
            **rule_result,
            "reason": f"{rule_result['reason']} | LLM fallback failed: {str(exc)}",
        }
