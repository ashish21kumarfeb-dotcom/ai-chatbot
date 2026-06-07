from rank_bm25 import BM25Okapi
from langchain_core.documents import Document

from app.rag.vectorstore import vector_db, similarity_search

import re

bm25 = None
bm25_documents = []
tokenized_docs = []
VECTOR_K = 10
BM25_K = 10
FINAL_K = 5
SIMILARITY_THRESHOLD = 1.6
def tokenize(text: str):

    text = text.lower()

    text = re.sub(r"[^\w\s]", "", text)

    return text.split()


def rebuild_bm25_index():

    global bm25
    global bm25_documents
    global tokenized_docs

    data = vector_db.get()

    documents = data.get("documents", [])

    metadatas = data.get("metadatas", [])

    bm25_documents = []

    tokenized_docs = []

    for doc, metadata in zip(documents, metadatas):

        bm25_documents.append(Document(page_content=doc, metadata=metadata))

        tokenized_docs.append(tokenize(doc))

    if tokenized_docs:

        bm25 = BM25Okapi(tokenized_docs)

        print(f"BM25 rebuilt with {len(documents)} chunks")

    else:

        bm25 = None

        print("BM25 empty")


def bm25_search(query: str, k: int =BM25_K):

    if not bm25:
        return []

    scores = bm25.get_scores(tokenize(query))

    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]

    return [bm25_documents[i] for i in ranked]


def hybrid_search(query: str, k: int = FINAL_K):

    vector_docs = similarity_search(query,  k=VECTOR_K)

    bm25_docs = bm25_search(query, k=BM25_K)

    combined = []

    seen = set()

    for doc in bm25_docs + vector_docs:

        key = doc.metadata.get("source", "") + str(hash(doc.page_content))

        if key not in seen:

            seen.add(key)

            combined.append(doc)

    print("\n===== FINAL HYBRID DOCS =====")

    for doc in combined:

        print(doc.metadata.get("source"))

        print(doc.page_content[:200])

        print("-------------")

    return combined[:FINAL_K]


rebuild_bm25_index()
