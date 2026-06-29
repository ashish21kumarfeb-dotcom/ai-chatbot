from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

from app.rag.graph.state import GraphState
from app.rag.graph.nodes import (
    input_guard_node,
    answer_composer_node,
    answer_verifier_node,
    evidence_extraction_node,
    greeting_node,
    memory_node,
    metadata_node,
    query_understanding_node,
    retrieval_node,
    router_node,
)

load_dotenv()

graph = StateGraph(GraphState)


def route_after_input_guard(state):
    """
    If input guard blocks the query, stop the graph immediately.
    Otherwise continue to normal router flow.
    """
    if state.get("blocked_by_guardrail"):
        return "blocked"

    return "continue"


def route_query(state):
    query_type = state.get("query_type")

    if query_type == "greeting":
        return "greeting"

    if query_type == "metadata":
        return "metadata"

    return "memory"


graph.add_node("input_guard", input_guard_node)
graph.add_node("router", router_node)
graph.add_node("greeting", greeting_node)
graph.add_node("metadata", metadata_node)
graph.add_node("memory", memory_node)
graph.add_node("query_understanding", query_understanding_node)
graph.add_node("retrieval", retrieval_node)
graph.add_node("evidence_extraction", evidence_extraction_node)
graph.add_node("answer_composer", answer_composer_node)
graph.add_node("answer_verifier", answer_verifier_node)

# Input guard must run first.
graph.set_entry_point("input_guard")

graph.add_conditional_edges(
    "input_guard",
    route_after_input_guard,
    {
        "blocked": END,
        "continue": "router",
    },
)

graph.add_conditional_edges(
    "router",
    route_query,
    {
        "greeting": "greeting",
        "metadata": "metadata",
        "memory": "memory",
    },
)

graph.add_edge("greeting", END)
graph.add_edge("metadata", END)

graph.add_edge("memory", "query_understanding")
graph.add_edge("query_understanding", "retrieval")
graph.add_edge("retrieval", "evidence_extraction")
graph.add_edge("evidence_extraction", "answer_composer")
graph.add_edge("answer_composer", "answer_verifier")
graph.add_edge("answer_verifier", END)

app_graph = graph.compile()
