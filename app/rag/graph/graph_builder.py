from langgraph.graph import StateGraph
from langgraph.graph import END

from app.rag.graph.state import GraphState

from app.rag.graph.nodes import (
    router_node,
    retrieval_node,
    memory_node,
    llm_node
)
from dotenv import load_dotenv

load_dotenv()
graph = StateGraph(GraphState)

graph.add_node(
    "router",
    router_node
)

graph.add_node(
    "memory",
    memory_node
)

graph.add_node(
    "retrieval",
    retrieval_node
)

graph.add_node(
    "llm",
    llm_node
)

graph.set_entry_point("router")

graph.add_edge(
    "router",
    "memory"
)

graph.add_edge(
    "memory",
    "retrieval"
)

graph.add_edge(
    "retrieval",
    "llm"
)

graph.add_edge(
    "llm",
    END
)

app_graph = graph.compile()