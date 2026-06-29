import os
import json
from datetime import datetime
import uuid
from typing import Any, Dict, Optional

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


def add_file_metadata(
    document_id: uuid.UUID,
    filename: str,
    file_type: str,
    size: int,
    chunks: int,
    classification: Optional[Dict[str, Any]] = None,
    universal_metadata: Optional[Dict[str, Any]] = None,
):

    metadata = load_metadata()

    classification = classification or {"document_type": "other", "confidence": 0.0}
    universal_metadata = universal_metadata or {}

    existing_item = None

    for item in metadata:

        if item["filename"].lower() == filename.lower():
            existing_item = item
            break

    now = datetime.now().isoformat()

    new_item = {
        "document_id": str(document_id),
        "filename": filename,
        "file_type": file_type,
        "size": size,
        "chunks": chunks,
        "document_type": classification.get("document_type", "other"),
        "classification": classification,
        "universal_metadata": universal_metadata,
        "uploaded_at": existing_item.get("uploaded_at", now) if existing_item else now,
        "metadata_updated_at": now,
    }

    if existing_item:
        existing_item.clear()
        existing_item.update(new_item)
    else:
        metadata.append(new_item)

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


def get_documents_by_type(document_type: str):

    return [
        item
        for item in load_metadata()
        if item.get("document_type", "").lower() == document_type.lower()
    ]


def get_document_by_filename(filename: str):
    for item in load_metadata():
        if item["filename"].lower() == filename.lower():
            return item
    return None
