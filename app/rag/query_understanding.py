import json
import re
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)


DOCUMENT_TYPE_HINTS = {
    "resume": ["resume", "cv", "candidate", "profile", "experience", "skills", "education", "contact", "email", "phone", "linkedin"],
    "company_policy": ["policy", "refund", "leave", "probation", "remote work", "benefit", "benefits", "handbook", "code of conduct", "support"],
    "contract": ["contract", "agreement", "termination", "clause", "party", "parties", "payment terms"],
    "invoice": ["invoice", "bill", "amount", "tax", "gst", "total due"],
    "report": ["report", "analysis", "findings", "summary", "recommendation"],
}


def _extract_json(text: str) -> Dict[str, Any]:
    if not text:
        return {}

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        return {}

    try:
        return json.loads(match.group(0))
    except Exception:
        return {}


def _fallback_document_types(question: str) -> List[str]:
    q = question.lower()
    selected: List[str] = []

    for doc_type, keywords in DOCUMENT_TYPE_HINTS.items():
        if any(keyword in q for keyword in keywords):
            selected.append(doc_type)

    if "resume" in selected:
        return ["resume", "cv"]

    if "company_policy" in selected:
        return ["company_policy", "policy", "handbook", "knowledge_base"]

    return selected


def _fallback_expected_fields(question: str) -> List[str]:
    q = question.lower()

    # These are broad information categories, not one-off bug fixes.
    # The verifier/evidence extractor uses them as an answer contract.
    if any(word in q for word in ["contact", "email", "phone", "mobile", "linkedin", "number"]):
        return ["email", "phone", "mobile", "linkedin", "website", "url", "contact"]

    if any(word in q for word in ["experience", "years", "work experience"]):
        return ["experience", "years", "duration"]

    if any(word in q for word in ["skill", "skills", "technology", "tech stack"]):
        return ["skills", "technology", "tools", "frameworks"]

    if any(word in q for word in ["refund", "policy", "leave", "probation", "benefit", "remote"]):
        return ["policy_rule", "eligibility", "conditions", "timeline", "process"]

    return []


def _fallback_entities(question: str) -> List[str]:
    # Lightweight fallback only. Main extraction should come from the LLM.
    ignored = {
        "What", "Who", "When", "Where", "Why", "How", "Tell", "Give", "List",
        "Contact", "Details", "Experience", "Policy", "Refund", "Total", "And",
        "Of", "For", "The", "A", "An", "In", "On", "To", "Is", "Are"
    }
    candidates = re.findall(r"\b[A-Z][a-zA-Z]+\b", question)
    return [c for c in candidates if c not in ignored]


def understand_query(question: str, chat_history: str = "") -> Dict[str, Any]:
    """Convert a natural language user question into an answer contract.

    The answer contract tells later nodes what information is requested,
    which entities are in scope, what document types are likely relevant,
    and what fields are allowed in the final answer.
    """

    fallback_doc_types = _fallback_document_types(question)
    fallback_fields = _fallback_expected_fields(question)
    fallback_entities = _fallback_entities(question)

    prompt = f"""
You are the Query Understanding Agent for a local document intelligence system.

Your job is NOT to answer the user.
Your job is to create a strict answer contract for downstream retrieval, extraction, and verification.

Return JSON only with this exact shape:
{{
  "task_type": "fact_lookup | policy_question | summary | comparison | calculation | generic_question",
  "requested_information": "short phrase describing exactly what the user asked for",
  "target_entities": ["specific people, companies, policies, documents, or things mentioned by the user"],
  "target_document_types": ["resume | cv | company_policy | policy | handbook | contract | invoice | report | knowledge_base | other"],
  "expected_fields": ["fields that are allowed in the answer"],
  "excluded_fields": ["fields that must NOT be used in the answer"],
  "needs_calculation": true,
  "answer_granularity": "per_entity | single_answer | list | summary",
  "reason": "brief reason for this plan"
}}

Rules:
- If the user asks for contact details, expected_fields should include only contact-style fields such as email, phone, mobile, linkedin, website, url.
- If the user asks for experience, expected_fields should include only experience/duration/year fields.
- If the user asks a policy question, expected_fields should include only policy-rule fields such as eligibility, conditions, process, timeline, exceptions.
- Do not include unrelated fields in expected_fields.
- If the user names people, keep those people in target_entities.
- If the query is about resumes/CVs/candidates, target_document_types should include resume/cv.
- If the query is about company rules/refund/leave/probation/benefits/handbook, target_document_types should include policy/handbook/company_policy.

Chat history:
{chat_history}

User question:
{question}
"""

    data: Dict[str, Any] = {}

    try:
        response = llm.invoke(prompt)
        data = _extract_json(response.content)
    except Exception as exc:
        print("Query understanding LLM failed:", exc)
        data = {}

    if not isinstance(data, dict):
        data = {}

    data.setdefault("task_type", "generic_question")
    data.setdefault("requested_information", question)
    data.setdefault("target_entities", fallback_entities)
    data.setdefault("target_document_types", fallback_doc_types)
    data.setdefault("expected_fields", fallback_fields)
    data.setdefault("excluded_fields", [])
    data.setdefault("needs_calculation", any(word in question.lower() for word in ["total", "sum", "combined", "add"] ))
    data.setdefault("answer_granularity", "single_answer")
    data.setdefault("reason", "Fallback query understanding used where needed.")

    if not data.get("target_document_types"):
        data["target_document_types"] = fallback_doc_types

    if not data.get("expected_fields"):
        data["expected_fields"] = fallback_fields

    if not data.get("target_entities"):
        data["target_entities"] = fallback_entities

    return data
