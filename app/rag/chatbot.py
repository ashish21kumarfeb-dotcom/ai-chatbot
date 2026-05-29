# from app.rag.hybrid_search import hybrid_search
# from app.rag.file_manager import get_uploaded_files
# from app.rag.query_router import detect_query_type
# from langchain_groq  import ChatGroq
# from dotenv import load_dotenv
# import os

# load_dotenv()

# llm = ChatGroq(
#     model="llama-3.1-8b-instant",
#     temperature=0
# )


# def handle_metadata_query(question: str):

#     files = get_uploaded_files()
#     q = question.lower()

#     if "how many" in q or "count" in q:
#         return {
#             "question": question,
#             "answer": f"There are {len(files)} documents.",
#             "sources": files
#         }

#     if "list" in q or "which" in q:
#         return {
#             "question": question,
#             "answer": "Uploaded documents:\n" + "\n".join(files),
#             "sources": files
#         }

#     return {
#         "question": question,
#         "answer": f"There are {len(files)} documents.",
#         "sources": files
#     }


# def build_context(docs):

#     context_parts = []
#     sources = set()

#     for doc in docs:

#         source = doc.metadata.get("source", "unknown")
#         source = source.split("\\")[-1]

#         sources.add(source)

#         context_parts.append(
#             f"""
# SOURCE:
# {source}

# CONTENT:
# {doc.page_content}
# """
#         )

#     return "\n\n".join(context_parts), list(sources)


# def handle_semantic_query(question: str):

#     docs = hybrid_search(question)

#     if not docs:
#         return {
#             "question": question,
#             "answer": "No relevant information found.",
#             "sources": []
#         }

#     context, sources = build_context(docs)

#     prompt = f"""
# Answer only from context.

# Context:
# {context}

# Question:
# {question}

# Answer:
# """

#     response = llm.invoke(prompt)

#     return {
#         "question": question,
#         "answer": response.content,
#         "sources": sources
#     }


# def ask_question(question: str, return_sources=True):

#     query_type = detect_query_type(question)

#     # 🚨 HARD ROUTE FIX
#     if query_type == "metadata":
#         result = handle_metadata_query(question)
#     else:
#         result = handle_semantic_query(question)

#     return result if return_sources else result["answer"]

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