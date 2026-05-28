import os
import shutil

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException
)

from app.rag.loader import load_document
from app.rag.splitter import split_documents

from app.rag.metadata_store import (
    add_file_metadata,
    delete_file_metadata
)

from app.rag.vectorstore import (
    add_documents,
    delete_by_source
)

router = APIRouter(
    prefix="/upload",
    tags=["Upload"]
)

UPLOAD_DIR = "app/uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/")
async def upload_file(
    file: UploadFile = File(...)
):

    file_path = os.path.join(
        UPLOAD_DIR,
        file.filename
    )

    # Prevent duplicate uploads
    if os.path.exists(file_path):

        raise HTTPException(
            status_code=400,
            detail="File already exists."
        )

    try:

        # Save file locally
        with open(file_path, "wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        # Load document
        documents = load_document(file_path)

        if not documents:

            os.remove(file_path)

            raise HTTPException(
                status_code=400,
                detail="No readable content found."
            )

        # Split into chunks
        chunks = split_documents(documents)

        # Store embeddings
        add_documents(chunks)

        # Extract metadata
        file_extension = os.path.splitext(
            file.filename
        )[1].lower()

        file_size = os.path.getsize(file_path)

        # Save metadata
        add_file_metadata(
            filename=file.filename,
            file_type=file_extension,
            size=file_size,
            chunks=len(chunks)
        )

        return {
            "message": "File uploaded and indexed successfully",
            "filename": file.filename,
            "file_type": file_extension,
            "chunks": len(chunks)
        }

    except Exception as e:

        # Rollback file if error occurs
        if os.path.exists(file_path):

            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.delete("/{filename}")
async def delete_file(filename: str):

    file_path = os.path.join(
        UPLOAD_DIR,
        filename
    )

    if not os.path.exists(file_path):

        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    try:

        # Delete physical file
        os.remove(file_path)

        # Delete embeddings
        delete_by_source(filename)

        # Delete metadata
        delete_file_metadata(filename)

        return {
            "message": f"{filename} deleted successfully"
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )