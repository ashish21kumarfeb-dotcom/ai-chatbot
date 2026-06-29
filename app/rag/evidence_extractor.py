import json
import re
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)


CONTACT_FIELD_WORDS = {"email", "phone", "mobile", "linkedin", "website", "url", "contact"}


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


def _norm(value: Any) -> str:
    return str(value or "").lower().strip()


def _field_matches_expected(fact: Dict[str, Any], expected_fields: List[str]) -> bool:
    if not expected_fields:
        return True

    field_text = _norm(fact.get("field"))
    value_text = _norm(fact.get("value"))
    fact_text = _norm(fact.get("fact"))
    combined = f"{field_text} {value_text} {fact_text}"

    expected = [_norm(item) for item in expected_fields if item]

    # If answer contract requests contact data, require actual contact-like evidence.
    if any(item in CONTACT_FIELD_WORDS for item in expected):
        has_contact_signal = (
            re.search(r"[\w\.-]+@[\w\.-]+\.\w+", combined) is not None
            or re.search(r"(?:\+?\d[\d\s\-()]{7,}\d)", combined) is not None
            or "linkedin" in combined
            or "http" in combined
            or "www." in combined
            or "email" in combined
            or "phone" in combined
            or "mobile" in combined
        )
        return has_contact_signal

    return any(item in combined for item in expected)


def extract_evidence(question: str, query_analysis: Dict[str, Any], context: str) -> Dict[str, Any]:
    """Extract only evidence that directly answers the requested information.

    This is the key reliability layer. It prevents the system from answering
    with nearby-but-wrong facts, for example returning experience when the user
    asked for contact details.
    """

    if not context.strip():
        return {
            "answerable": False,
            "facts": [],
            "missing": ["No relevant document context was retrieved."],
            "reason": "No context available."
        }

    prompt = f"""
You are an Evidence Extraction Agent.

Your job is to extract facts from DOCUMENT CONTEXT that DIRECTLY answer the user's requested information.
Do NOT answer the user directly.
Do NOT include related-but-different information.

Return JSON only with this exact shape:
{{
  "answerable": true,
  "facts": [
    {{
      "entity": "who/what this fact is about",
      "field": "the exact information field, e.g. email, phone, experience_years, refund_policy, eligibility",
      "value": "the extracted value only",
      "fact": "short complete fact sentence",
      "source": "source filename if available",
      "quote": "short supporting quote from the context"
    }}
  ],
  "missing": ["specific requested information not found"],
  "reason": "why the evidence is or is not sufficient"
}}

Strict rules:
- Requested information: {query_analysis.get('requested_information')}
- Target entities: {query_analysis.get('target_entities')}
- Allowed/expected fields: {query_analysis.get('expected_fields')}
- Excluded fields: {query_analysis.get('excluded_fields')}
- If a fact does not match the requested information, exclude it.
- If user asked for contact details, extract only email, phone, mobile, LinkedIn, website, or URL. Exclude experience, skills, education, language.
- If user asked for experience, extract only experience/duration/year information. Exclude contact, skills, language unless directly requested.
- If user asked for a policy, extract only policy rules/eligibility/conditions/process/timeline.
- If the context has a person's resume but not the requested field, mark that field as missing.
- If no direct evidence is present, answerable must be false and facts must be empty.

User question:
{question}

Query analysis:
{json.dumps(query_analysis, ensure_ascii=False, indent=2)}

DOCUMENT CONTEXT:
{context}
"""

    data: Dict[str, Any] = {}

    try:
        response = llm.invoke(prompt)
        data = _extract_json(response.content)
    except Exception as exc:
        print("Evidence extraction LLM failed:", exc)
        data = {}

    if not isinstance(data, dict):
        data = {}

    facts = data.get("facts", [])
    if not isinstance(facts, list):
        facts = []

    expected_fields = query_analysis.get("expected_fields", []) or []
    filtered_facts = []

    for fact in facts:
        if not isinstance(fact, dict):
            continue
        if not _field_matches_expected(fact, expected_fields):
            continue
        filtered_facts.append({
            "entity": str(fact.get("entity", "")).strip(),
            "field": str(fact.get("field", "")).strip(),
            "value": str(fact.get("value", "")).strip(),
            "fact": str(fact.get("fact", "")).strip(),
            "source": str(fact.get("source", "")).strip(),
            "quote": str(fact.get("quote", "")).strip(),
        })

    missing = data.get("missing", [])
    if not isinstance(missing, list):
        missing = [str(missing)] if missing else []

    return {
        "answerable": bool(filtered_facts),
        "facts": filtered_facts,
        "missing": missing,
        "reason": data.get("reason", "Evidence extracted and filtered against answer contract.")
    }
