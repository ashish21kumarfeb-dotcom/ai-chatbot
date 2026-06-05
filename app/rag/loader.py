import os

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    CSVLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
    JSONLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader
)

from app.rag.file_manager import SUPPORTED_EXTENSIONS


LOADERS = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": lambda path: TextLoader(
        path,
        encoding="utf-8"
    ),
    ".csv": CSVLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".pptx": UnstructuredPowerPointLoader,
    ".json": lambda path: JSONLoader(
        file_path=path,
        jq_schema=".",
        text_content=False
    ),
    ".html": UnstructuredHTMLLoader,
    ".md": UnstructuredMarkdownLoader
}


def load_document(file_path: str):

    extension = os.path.splitext(
        file_path
    )[1].lower()

    if extension not in SUPPORTED_EXTENSIONS:

        raise Exception(
            f"Unsupported file type: {extension}"
        )

    loader_class = LOADERS.get(extension)

    if not loader_class:

        raise Exception(
            f"No loader configured for {extension}"
        )

    loader = loader_class(file_path)

    docs = loader.load()

    filename = os.path.basename(file_path)

    for doc in docs:

        doc.metadata["source"] = filename

    return docs