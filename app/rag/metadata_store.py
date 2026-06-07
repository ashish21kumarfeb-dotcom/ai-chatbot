import os
import json
from datetime import datetime
import uuid

METADATA_FILE = "app/data/file_metadata.json"


def load_metadata():

    os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)

    if not os.path.exists(METADATA_FILE):

        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

        return []

    try:

        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except json.JSONDecodeError:

        return []


def save_metadata(data):

    os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)

    with open(METADATA_FILE, "w", encoding="utf-8") as f:

        json.dump(data, f, indent=4, ensure_ascii=False)


def add_file_metadata(document_id: uuid.UUID, filename: str, file_type: str, size: int, chunks: int):

    metadata = load_metadata()

    for item in metadata:

        if item["filename"].lower() == filename.lower():
            return

    metadata.append(
        {
            "document_id": document_id,
            "filename": filename,
            "file_type": file_type,
            "size": size,
            "chunks": chunks,
            "uploaded_at": datetime.now().isoformat(),
        }
    )

    save_metadata(metadata)


def delete_file_metadata(filename: str):

    metadata = load_metadata()

    metadata = [
        item for item in metadata if item["filename"].lower() != filename.lower()
    ]

    save_metadata(metadata)


def get_all_metadata():
    return load_metadata()


def get_document_count():
    return len(load_metadata())


def get_documents_by_type(file_type: str):

    return [
        item
        for item in load_metadata()
        if item["file_type"].lower() == file_type.lower()
    ]
