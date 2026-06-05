from typing import TypedDict, List,Dict,Any


class GraphState(TypedDict):

    question: str

    query_type: Dict[str, Any]

    context: str

    answer: str

    sources: List[str]

    session_id: str

    chat_history: str