# Loader module for RAG
import os

from langchain_community.document_loaders import PyPDFLoader,Docx2txtLoader,TextLoader


def load_document(file_path: str):
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)

    elif file_path.endswith(".docx"):
        loader = Docx2txtLoader(file_path)

    elif file_path.endswith(".txt"):
        loader = TextLoader(file_path)

    else:
        raise Exception("Unsupported file type")

    docs = loader.load()

    filename = os.path.basename(file_path)

    for doc in docs:
        doc.metadata["source"] = filename
        
    return docs