import os
import re

from langchain_chroma import Chroma
from app.rag.embeddings import embeddings


vector_db = Chroma(
    persist_directory="app/vectorstore",
    embedding_function=embeddings,
)


def normalize_query(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)

    print("Normalized query:", text)

    return text


def add_documents(chunks):
    vector_db.add_documents(chunks)

    print(f"Added {len(chunks)} chunks.")


def similarity_search(query: str, k: int = 5):
    clean_query = normalize_query(query)

    results = vector_db.similarity_search_with_score(
        clean_query,
        k=k,
    )

    print("\n===== RAW RESULTS =====\n")

    docs = []

    for doc, score in results:
        print("SCORE:", score)
        print("SOURCE:", doc.metadata)
        print("CONTENT:", doc.page_content[:200])
        print("\n------------------\n")

        docs.append(doc)

    return docs


def get_document_ids_by_source(filename: str):
    data = vector_db.get()

    ids_to_delete = []

    for doc_id, metadata in zip(
        data.get("ids", []),
        data.get("metadatas", []),
    ):
        if not metadata:
            continue

        source = os.path.basename(
            metadata.get("source", "")
        )

        if source == filename:
            ids_to_delete.append(doc_id)

    return ids_to_delete


def delete_by_source(filename: str):
    ids_to_delete = get_document_ids_by_source(filename)

    if not ids_to_delete:
        print(f"No chunks found for {filename}")
        return

    vector_db.delete(ids=ids_to_delete)

    print(
        f"Deleted {len(ids_to_delete)} chunks for {filename}"
    )


def cleanup_vectorstore(uploads_dir="app/uploads"):
    current_files = set(os.listdir(uploads_dir))

    data = vector_db.get()

    stale_ids = []

    for doc_id, metadata in zip(
        data.get("ids", []),
        data.get("metadatas", []),
    ):
        if not metadata:
            continue

        source = os.path.basename(
            metadata.get("source", "")
        )

        if source not in current_files:
            stale_ids.append(doc_id)

    if not stale_ids:
        print("No stale documents found.")
        return

    vector_db.delete(ids=stale_ids)

    print(
        f"Removed {len(stale_ids)} stale chunks."
    )