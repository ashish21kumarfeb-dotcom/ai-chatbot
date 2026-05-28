# Splitter module for RAG
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150
)

def split_documents(documents):
    return text_splitter.split_documents(documents)


