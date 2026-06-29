import re
from collections import defaultdict
from typing import Any, Dict, List, Optional


def _ensure_entity_labels(answer: str, query_analysis: dict) -> str:
    if not answer:
        return answer

    target_entities = query_analysis.get("target_entities") or []

    if not isinstance(target_entities, list) or not target_entities:
        return answer

    # Only auto-prefix for single-entity queries.
    # Multi-entity answers should already be grouped by composer.
    if len(target_entities) != 1:
        return answer

    entity = str(target_entities[0]).strip()

    if not entity:
        return answer

    if entity.lower() in answer.lower():
        return answer

    return f"{entity}: {answer}"


def _parse_year_value(text: str) -> Optional[float]:
    value = (text or "").lower()

    # Avoid treating calendar years as work experience.
    if re.fullmatch(r"\s*(19|20)\d{2}\s*", value):
        return None

    match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years|year|yrs|yr)", value)
    if not match:
        match = re.search(
            r"(?:over|more than|around|approx(?:imately)?)?\s*(\d+(?:\.\d+)?)", value
        )

    if not match:
        return None

    number = float(match.group(1))
    if number < 0 or number > 60:
        return None

    return number


def _format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return str(round(value, 2)).rstrip("0").rstrip(".")


def compose_answer(
    question: str, query_analysis: Dict[str, Any], evidence: Dict[str, Any]
) -> Dict[str, Any]:
    """Build final answer from extracted evidence only.

    This keeps final response grounded. The final answer is not generated from
    raw context; it is generated from verified evidence facts.
    """

    facts: List[Dict[str, Any]] = evidence.get("facts", []) or []

    if not facts:
        return {
            "answer": "I could not find this information in uploaded documents.",
            "sources": [],
            "used_facts": [],
        }

    grouped = defaultdict(list)
    sources = []

    for fact in facts:
        entity = fact.get("entity") or "Result"
        grouped[entity].append(fact)
        source = fact.get("source")
        if source and source not in sources:
            sources.append(source)

    lines = []

    per_entity = (
        query_analysis.get("answer_granularity") == "per_entity" or len(grouped) > 1
    )

    for entity, entity_facts in grouped.items():
        if per_entity:
            lines.append(f"{entity}:")
            for fact in entity_facts:
                field = fact.get("field") or "Information"
                value = fact.get("value") or fact.get("fact")
                lines.append(f"- {field}: {value}")
        else:
            for fact in entity_facts:
                lines.append(fact.get("fact") or str(fact.get("value", "")))

    if query_analysis.get("needs_calculation"):
        numeric_values = []
        for fact in facts:
            combined = f"{fact.get('field', '')} {fact.get('value', '')} {fact.get('fact', '')}"
            year_value = _parse_year_value(combined)
            if year_value is not None:
                numeric_values.append(year_value)

        if len(numeric_values) >= 2:
            total = sum(numeric_values)
            lines.append(
                f"Combined total: approximately {_format_number(total)}+ years."
            )

    missing = evidence.get("missing", []) or []
    if missing:
        clean_missing = [str(item) for item in missing if str(item).strip()]
        if clean_missing:
            lines.append("Missing information: " + "; ".join(clean_missing))

    answer = "\n".join(line for line in lines if line.strip()).strip()

    return {
        "answer": answer or "I could not find this information in uploaded documents.",
        "sources": sources,
        "used_facts": facts,
    }
