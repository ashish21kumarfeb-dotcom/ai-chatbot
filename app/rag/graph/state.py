from typing import Any, Dict, List, TypedDict


class GraphState(TypedDict):
    question: str
    session_id: str

    query_type: Any
    query_analysis: Dict[str, Any]

    context: str
    sources: List[str]

    evidence: Dict[str, Any]
    draft_answer: str
    answer: str
    verification: Dict[str, Any]

    chat_history: str
    guardrail_status: dict
    blocked_by_guardrail: bool