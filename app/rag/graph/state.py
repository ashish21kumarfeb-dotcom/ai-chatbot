from typing import TypedDict, List


class GraphState(TypedDict):

    question: str

    query_type: str

    context: str

    answer: str

    sources: List[str]

    session_id: str

    chat_history: str