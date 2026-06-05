from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# from langchain_community.embeddings import FakeEmbeddings

# embeddings = FakeEmbeddings(size=384)