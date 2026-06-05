from langgraph.graph import StateGraph
from langgraph.graph import END

from app.rag.graph.state import GraphState

from app.rag.graph.nodes import (
    greeting_node,
    router_node,
    retrieval_node,
    memory_node,
    llm_node,
    metadata_node,
)
from dotenv import load_dotenv
from app.rag.intent_classifier import classify_intent

load_dotenv()
graph = StateGraph(GraphState)


def route_query(state):

    if state["query_type"] == "greeting":
        return "greeting"

    if state["query_type"] == "metadata":
        return "metadata"

    return "memory"


graph.add_node("metadata", metadata_node)
graph.add_node("router", router_node)
graph.add_node("greeting",greeting_node)
graph.add_node("memory", memory_node)

graph.add_node("retrieval", retrieval_node)

graph.add_node("llm", llm_node)

graph.set_entry_point("router")

graph.add_conditional_edges(
    "router",
    route_query,
    {
        "greeting": "greeting",
        "metadata": "metadata",
        "memory": "memory"
    }
)
graph.add_edge(
    "greeting",
    END
)
graph.add_edge("metadata", END)

graph.add_edge("memory", "retrieval")

graph.add_edge("retrieval", "llm")

graph.add_edge("llm", END)

app_graph = graph.compile()
