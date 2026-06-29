import json
import re
from typing import Dict, List

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)


EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
URL_RE = re.compile(r'https?://[^\s)>"]+|www\.[^\s)>"]+')
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")


def _sample_text(documents, max_chars: int = 8000) -> str:
    text = "\n\n".join(doc.page_content for doc in documents[:6])
    return text[:max_chars]


def _safe_json_loads(raw: str) -> Dict:
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


def _dedupe(values: List[str]) -> List[str]:
    seen = set()
    output = []

    for value in values or []:
        if not value:
            continue
        cleaned = str(value).strip()
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(cleaned)

    return output


def _regex_entities(text: str) -> Dict:
    return {
        "emails": _dedupe(EMAIL_RE.findall(text)),
        "phone_numbers": _dedupe(PHONE_RE.findall(text)),
        "urls": _dedupe(URL_RE.findall(text)),
    }


def _normalize_metadata(
    parsed: Dict, regex_entities: Dict, classification: Dict
) -> Dict:
    entities = (
        parsed.get("entities") if isinstance(parsed.get("entities"), dict) else {}
    )

    normalized = {
        "title": parsed.get("title") or "",
        "summary": parsed.get("summary") or "",
        "language": parsed.get("language") or "unknown",
        "keywords": _dedupe(parsed.get("keywords", []))[:12],
        "topics": _dedupe(parsed.get("topics", []))[:12],
        "entities": {
            "people": _dedupe(entities.get("people", []))[:20],
            "organizations": _dedupe(entities.get("organizations", []))[:20],
            "locations": _dedupe(entities.get("locations", []))[:20],
            "dates": _dedupe(entities.get("dates", []))[:20],
            "emails": _dedupe(
                (entities.get("emails", []) or []) + regex_entities["emails"]
            ),
            "phone_numbers": _dedupe(
                (entities.get("phone_numbers", []) or [])
                + regex_entities["phone_numbers"]
            ),
            "urls": _dedupe((entities.get("urls", []) or []) + regex_entities["urls"]),
        },
        "key_facts": [],
        "document_type": classification.get("document_type", "other"),
    }

    facts = parsed.get("key_facts", [])
    if isinstance(facts, list):
        for fact in facts[:20]:
            if isinstance(fact, str):
                normalized["key_facts"].append(
                    {
                        "fact": fact,
                        "category": "general",
                        "value": "",
                        "unit": "",
                    }
                )
            elif isinstance(fact, dict):
                normalized["key_facts"].append(
                    {
                        "fact": fact.get("fact") or "",
                        "category": fact.get("category") or "general",
                        "value": fact.get("value") or "",
                        "unit": fact.get("unit") or "",
                    }
                )

    return normalized


def extract_universal_metadata(
    documents, classification: Dict, filename: str = ""
) -> Dict:
    """
    Universal metadata is document-type independent.
    It gives the future query planner a structured overview of any document.

    This is not a replacement for vector RAG.
    It is a reliability layer for predictable facts, entities, summaries and routing.
    """
    text = _sample_text(documents)
    regex_entities = _regex_entities(text)

    prompt = f"""
You are a universal document metadata extraction engine.

Extract metadata from the document sample.
Return JSON only with this exact schema:
{{
  "title": "short title of the document",
  "summary": "2-4 sentence summary",
  "language": "language name",
  "keywords": ["keyword1", "keyword2"],
  "topics": ["topic1", "topic2"],
  "entities": {{
    "people": [],
    "organizations": [],
    "locations": [],
    "dates": [],
    "emails": [],
    "phone_numbers": [],
    "urls": []
  }},
  "key_facts": [
    {{
      "fact": "short factual statement found in the document",
      "category": "experience|policy_rule|date|money|contact|responsibility|general",
      "value": "exact value if any",
      "unit": "years|days|INR|USD|percent|none"
    }}
  ]
}}

Rules:
- Use only facts present in the document sample.
- Do not invent missing values.
- Prefer exact wording for important numbers, dates, rules and names.
- Extract facts useful for answering future questions.
- If no value/unit exists, use an empty string.
- Keep arrays concise.

Filename:
{filename}

Known document classification:
{json.dumps(classification, ensure_ascii=False)}

Document sample:
{text}
"""

    try:
        response = llm.invoke(prompt)
        parsed = _safe_json_loads(response.content)
        return _normalize_metadata(parsed, regex_entities, classification)
    except Exception as exc:
        # Safe fallback: no LLM extraction, but still keep regex-extracted entities.
        return {
            "title": filename,
            "summary": "",
            "language": "unknown",
            "keywords": [],
            "topics": [],
            "entities": {
                "people": [],
                "organizations": [],
                "locations": [],
                "dates": [],
                "emails": regex_entities["emails"],
                "phone_numbers": regex_entities["phone_numbers"],
                "urls": regex_entities["urls"],
            },
            "key_facts": [],
            "document_type": classification.get("document_type", "other"),
            "extraction_error": str(exc),
        }


# Backward-compatible function name for existing imports.
def extract_metadata(documents, classification, filename: str = ""):
    return extract_universal_metadata(documents, classification, filename)
