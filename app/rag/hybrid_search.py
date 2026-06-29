import os
import re
from typing import Iterable, List, Optional

from rank_bm25 import BM25Okapi
from langchain_core.documents import Document

from app.rag.vectorstore import vector_db, similarity_search

bm25 = None
bm25_documents: List[Document] = []
tokenized_docs: List[List[str]] = []

VECTOR_K = 12
BM25_K = 12
FINAL_K = 8

STOP_WORDS = {
    "what", "is", "are", "the", "a", "an", "of", "and", "or", "to", "in",
    "for", "with", "on", "by", "from", "tell", "give", "show", "me", "please",
    "total", "details", "detail", "about", "all", "any"
}


def tokenize(text: str):
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return [word for word in text.split() if word not in STOP_WORDS and len(word) > 1]


def _normalize_doc_type(value: str) -> str:
    return str(value or "").lower().strip().replace(" ", "_")


def _doc_type_allowed(doc: Document, document_types: Optional[Iterable[str]]) -> bool:
    allowed = [_normalize_doc_type(item) for item in (document_types or []) if item]
    if not allowed:
        return True

    doc_type = _normalize_doc_type(doc.metadata.get("document_type", ""))
    if not doc_type:
        # Allow old chunks without document_type. The verifier will still protect answer quality.
        return True

    return doc_type in allowed


def rebuild_bm25_index():
    global bm25, bm25_documents, tokenized_docs

    data = vector_db.get()
    documents = data.get("documents", [])
    metadatas = data.get("metadatas", [])

    bm25_documents = []
    tokenized_docs = []

    for doc, metadata in zip(documents, metadatas):
        metadata = metadata or {}
        bm25_documents.append(Document(page_content=doc, metadata=metadata))
        tokenized_docs.append(tokenize(doc))

    if tokenized_docs:
        bm25 = BM25Okapi(tokenized_docs)
        print(f"BM25 rebuilt with {len(documents)} chunks")
    else:
        bm25 = None
        print("BM25 empty")


def bm25_search(query: str, k: int = BM25_K, document_types: Optional[List[str]] = None):
    if not bm25:
        return []

    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

    results = []

    for i in ranked:
        if scores[i] <= 0:
            continue

        doc = bm25_documents[i]
        if not _doc_type_allowed(doc, document_types):
            continue

        results.append(doc)
        if len(results) >= k:
            break

    return results


def _dedupe(docs: List[Document]) -> List[Document]:
    combined = []
    seen = set()

    for doc in docs:
        source = os.path.basename(str(doc.metadata.get("source", "")))
        key = source + "::" + str(hash(doc.page_content))
        if key in seen:
            continue
        seen.add(key)
        combined.append(doc)

    return combined


def hybrid_search(query: str, k: int = FINAL_K, document_types: Optional[List[str]] = None):
    vector_docs = similarity_search(query, k=VECTOR_K)
    vector_docs = [doc for doc in vector_docs if _doc_type_allowed(doc, document_types)]

    bm25_docs = bm25_search(query, k=BM25_K, document_types=document_types)

    combined = _dedupe(bm25_docs + vector_docs)

    # If document-type filtering produced nothing, fallback to unfiltered search.
    # The evidence extractor and verifier still block wrong-field answers.
    if not combined and document_types:
        bm25_docs = bm25_search(query, k=BM25_K, document_types=None)
        vector_docs = similarity_search(query, k=VECTOR_K)
        combined = _dedupe(bm25_docs + vector_docs)

    print("\n===== FINAL HYBRID DOCS =====")
    for doc in combined[:k]:
        print("SOURCE:", doc.metadata.get("source"))
        print("DOC TYPE:", doc.metadata.get("document_type"))
        print(doc.page_content[:200])
        print("-------------")

    return combined[:k]


rebuild_bm25_index()
