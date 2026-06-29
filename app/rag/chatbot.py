from dotenv import load_dotenv

from app.rag.graph.graph_builder import app_graph

load_dotenv()


def ask_question(
    question: str, session_id: str = "default", return_sources: bool = True
):
    initial_state = {
        "question": question,
        "session_id": session_id,
        # Router / query flow
        "query_type": "",
        "query_analysis": {},
        # RAG / evidence flow
        "context": "",
        "sources": [],
        "evidence": {},
        # Answer flow
        "draft_answer": "",
        "answer": "",
        "verification": {},
        # Memory / chat history
        "chat_history": "",
        # Guardrails
        "guardrail_status": {},
        "blocked_by_guardrail": False,
    }

    result = app_graph.invoke(initial_state)

    final_result = {
        "question": question,
        "answer": result.get("answer", ""),
        "sources": result.get("sources", []),
        # Debug / development fields
        "query_analysis": result.get("query_analysis", {}),
        "evidence": result.get("evidence", {}),
        "verification": result.get("verification", {}),
        # Guardrail debug fields
        "guardrail_status": result.get("guardrail_status", {}),
        "blocked_by_guardrail": result.get("blocked_by_guardrail", False),
    }

    return final_result if return_sources else final_result["answer"]
             