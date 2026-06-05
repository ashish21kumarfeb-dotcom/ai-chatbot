import os
import re

from langchain_chroma import Chroma
from app.rag.embeddings import embeddings

vector_db = Chroma(
    collection_name="company_documents",
    persist_directory="app/vectorstore",
    embedding_function=embeddings,
)


def normalize_query(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)

    print("Normalized query:", text)

    return text


def add_documents(chunks):

    for chunk in chunks:

        source = chunk.metadata.get("source", "")

        chunk.metadata["source"] = os.path.basename(source)
    source = os.path.basename(chunks[0].metadata["source"])

    delete_by_source(source)
    # print("\n===== BEFORE INSERT =====")

    # print("Chunks:", len(chunks))

    vector_db.add_documents(chunks)

    # print("\n===== AFTER INSERT =====")

    data = vector_db.get()

    # print("TOTAL DOCS:", len(data["documents"]))

    # print("TOTAL IDS:", len(data["ids"]))

    # print("LAST METADATA:")

    for meta in data["metadatas"][-3:]:

        print(meta)


def similarity_search(query: str, k: int = 5):

    results = vector_db.similarity_search_with_score(query, k=k)
    print("\n===== RAW RESULTS =====\n")
    docs = []

    for doc, score in results:
        print("SCORE:", score)
        print("SOURCE:", doc.metadata)
        print("CONTENT:", doc.page_content[:200])
        print("\n------------------\n")
        if score > 1.6:
            continue

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

        source = os.path.basename(metadata.get("source", ""))

        if source == filename:
            ids_to_delete.append(doc_id)

    return ids_to_delete


def delete_by_source(filename: str):
    ids_to_delete = get_document_ids_by_source(filename)

    if not ids_to_delete:
        print(f"No chunks found for {filename}")
        return

    vector_db.delete(ids=ids_to_delete)

    print(f"Deleted {len(ids_to_delete)} chunks for {filename}")


def cleanup_vectorstore(uploads_dir="app/uploads"):
    current_files = {
        f
        for f in os.listdir(uploads_dir)
        if os.path.isfile(os.path.join(uploads_dir, f))
    }
    data = vector_db.get()

    stale_ids = []

    for doc_id, metadata in zip(
        data.get("ids", []),
        data.get("metadatas", []),
    ):
        if not metadata:
            continue

        source = os.path.basename(metadata.get("source", ""))

        if source not in current_files:
            stale_ids.append(doc_id)

    if not stale_ids:
        print("No stale documents found.")
        return

    vector_db.delete(ids=stale_ids)

    print(f"Removed {len(stale_ids)} stale chunks.")
