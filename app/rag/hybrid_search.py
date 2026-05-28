from rank_bm25 import BM25Okapi
from langchain_core.documents import Document
from app.rag.vectorstore import vector_db, similarity_search
import re


def tokenize(text: str):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return text.split()


def bm25_search(query: str, k: int = 5):

    data = vector_db.get()
    documents = data.get("documents", [])
    metadatas = data.get("metadatas", [])

    if not documents:
        return []

    tokenized_docs = [tokenize(doc) for doc in documents]
    bm25 = BM25Okapi(tokenized_docs)

    scores = bm25.get_scores(tokenize(query))

    ranked = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:k]

    results = []

    for idx in ranked:
        results.append(Document(
            page_content=documents[idx],
            metadata=metadatas[idx]
        ))

    return results


def hybrid_search(query: str, k: int = 5):

    vector_docs = similarity_search(query)
    bm25_docs = bm25_search(query)

    combined = []
    seen_sources = set()

    for doc in vector_docs + bm25_docs:

        source = doc.metadata.get("source", "unknown")
        source = source.split("\\")[-1]

        if source not in seen_sources:
            seen_sources.add(source)
            combined.append(doc)

    return combined[:k]