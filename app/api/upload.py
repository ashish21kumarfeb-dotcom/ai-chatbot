import os
import shutil
import traceback
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.rag.loader import load_document
from app.rag.splitter import split_documents
from app.rag.hybrid_search import rebuild_bm25_index
from app.rag.metadata_store import (
    add_file_metadata,
    delete_file_metadata,
    load_metadata,
    get_all_metadata,
    get_document_by_filename,
)
from app.rag.vectorstore import add_documents, delete_by_source
from app.rag.document_classifier import classify_document
from app.rag.metadata_extractor import extract_universal_metadata

router = APIRouter(prefix="/upload", tags=["Upload"])

UPLOAD_DIR = "app/uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/files")
async def get_uploaded_files():

    metadata = load_metadata()

    return [item["filename"] for item in metadata]


@router.get("/metadata")
async def get_uploaded_metadata():
    """Return full document metadata for debugging and future UI use."""

    return get_all_metadata()


@router.get("/metadata/{filename}")
async def get_single_file_metadata(filename: str):
    item = get_document_by_filename(filename)

    if not item:
        raise HTTPException(status_code=404, detail="Metadata not found")

    return item


@router.post("/")
async def upload_file(file: UploadFile = File(...)):

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Prevent duplicate uploads
    if os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="File already exists.")

    try:

        # Save file locally
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Load document
        documents = load_document(file_path)

        if not documents:
            os.remove(file_path)

            raise HTTPException(status_code=400, detail="No readable content found.")

        # Generate document id
        document_id = str(uuid.uuid4())

        # Classify document before chunking.
        # This tells the system whether the document looks like a resume,
        # policy, handbook, contract, etc.
        classification = classify_document(
            documents=documents,
            filename=file.filename,
        )

        # Extract universal metadata before chunking.
        # This gives us title, summary, entities, keywords and key facts
        # for any document type.
        universal_metadata = extract_universal_metadata(
            documents=documents,
            classification=classification,
            filename=file.filename,
        )

        document_type = classification.get("document_type", "other")

        print("\n===== DOCUMENT CLASSIFICATION =====")
        print(classification)

        print("\n===== UNIVERSAL METADATA =====")
        print(universal_metadata)

        # Add document-level metadata to original documents.
        # These fields also flow into chunks after splitting.
        for doc in documents:
            doc.metadata["document_id"] = document_id
            doc.metadata["document_type"] = document_type
            doc.metadata["document_title"] = universal_metadata.get("title", "")

        # Split into chunks
        chunks = split_documents(documents)

        # Add metadata to chunks
        for index, chunk in enumerate(chunks):
            chunk.metadata["document_id"] = document_id
            chunk.metadata["document_type"] = document_type
            chunk.metadata["document_title"] = universal_metadata.get("title", "")
            chunk.metadata["chunk_id"] = index

        print("\n===== CHUNKS CREATED =====")
        print("TOTAL CHUNKS:", len(chunks))

        for chunk in chunks[:2]:
            print(chunk.page_content[:300])
            print(chunk.metadata)

        # Store embeddings
        add_documents(chunks)

        # Rebuild BM25
        rebuild_bm25_index()

        # Extract metadata
        file_extension = os.path.splitext(file.filename)[1].lower()

        file_size = os.path.getsize(file_path)

        # Save metadata
        add_file_metadata(
            document_id=document_id,
            filename=file.filename,
            file_type=file_extension,
            size=file_size,
            chunks=len(chunks),
            classification=classification,
            universal_metadata=universal_metadata,
        )

        return {
            "message": "File uploaded and indexed successfully",
            "document_id": document_id,
            "filename": file.filename,
            "file_type": file_extension,
            "chunks": len(chunks),
            "document_type": document_type,
            "classification": classification,
            "universal_metadata": universal_metadata,
        }

    except Exception as e:

        print("\n===== FULL ERROR =====")
        traceback.print_exc()

        # Rollback file if error occurs
        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{filename}")
async def delete_file(filename: str):

    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:

        # Delete physical file
        os.remove(file_path)

        # Delete embeddings
        delete_by_source(filename)

        # Delete metadata
        delete_file_metadata(filename)

        # Rebuild BM25 index
        rebuild_bm25_index()

        return {"message": f"{filename} deleted successfully"}

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))
