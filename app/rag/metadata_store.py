import os
import json
from datetime import datetime

METADATA_FILE = "app/data/file_metadata.json"


def load_metadata():

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
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def add_file_metadata(filename: str, file_type: str, size: int, chunks: int):

    metadata = load_metadata()

    for item in metadata:
        if item["filename"] == filename:
            return

    metadata.append({
        "filename": filename,
        "file_type": file_type,
        "size": size,
        "chunks": chunks,
        "uploaded_at": datetime.now().isoformat()
    })

    save_metadata(metadata)


def delete_file_metadata(filename: str):

    metadata = load_metadata()

    metadata = [
        item for item in metadata
        if item["filename"] != filename
    ]

    save_metadata(metadata)