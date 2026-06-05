from dotenv import load_dotenv

from app.rag.graph.graph_builder import app_graph

load_dotenv()


def ask_question(
    question: str,
    session_id: str = "default",
    return_sources: bool = True
):

    result = app_graph.invoke({

        "question": question,

        "session_id": session_id,

        "query_type": "",

        "context": "",

        "answer": "",

        "sources": [],

        "chat_history": ""

    })

    final_result = {

        "question": question,

        "answer": result["answer"],

        "sources": result.get(
            "sources",
            []
        )
    }

    return (
        final_result
        if return_sources
        else final_result["answer"]
    )