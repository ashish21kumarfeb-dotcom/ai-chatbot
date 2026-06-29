import json
import re
from typing import Any, Dict

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)


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


def verify_answer(question: str, query_analysis: Dict[str, Any], evidence: Dict[str, Any], answer: str) -> Dict[str, Any]:
    """Final safety check before sending answer to UI."""

    if answer.strip() == "I could not find this information in uploaded documents.":
        return {
            "is_valid": True,
            "final_answer": answer,
            "reason": "Not-found answer is safe."
        }

    prompt = f"""
You are an Answer Verifier Agent.

Check whether the final answer exactly matches the user's requested information and is supported by extracted evidence.

Return JSON only:
{{
  "is_valid": true,
  "final_answer": "answer to send to user",
  "reason": "brief verification reason"
}}

Verification rules:
- The answer must address the requested information: {query_analysis.get('requested_information')}
- Expected fields: {query_analysis.get('expected_fields')}
- Target entities: {query_analysis.get('target_entities')}
- Do not allow unrelated information.
- If user asked contact details, an answer about experience/skills/language is invalid.
- If user asked experience, an answer about contact/skills/language is invalid unless requested.
- If answer is invalid and evidence does not contain correct facts, final_answer must be exactly:
  I could not find this information in uploaded documents.

User question:
{question}

Query analysis:
{json.dumps(query_analysis, ensure_ascii=False, indent=2)}

Extracted evidence:
{json.dumps(evidence, ensure_ascii=False, indent=2)}

Draft answer:
{answer}
"""

    try:
        response = llm.invoke(prompt)
        data = _extract_json(response.content)
    except Exception as exc:
        print("Answer verifier LLM failed:", exc)
        data = {}

    if not isinstance(data, dict):
        data = {}

    is_valid = bool(data.get("is_valid", False))
    final_answer = str(data.get("final_answer", "")).strip()

    if not is_valid:
        final_answer = final_answer or "I could not find this information in uploaded documents."

    return {
        "is_valid": is_valid,
        "final_answer": final_answer or answer,
        "reason": data.get("reason", "Verifier completed.")
    }
