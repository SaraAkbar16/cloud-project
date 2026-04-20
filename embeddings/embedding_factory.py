# embeddings/embedding_factory.py
try:
    # Preferred import path for newer LangChain stacks.
    from langchain_huggingface import HuggingFaceEmbeddings
except Exception:
    # Fallback for environments where langchain_huggingface and langchain_core
    # versions are not fully compatible.
    from langchain_community.embeddings import HuggingFaceEmbeddings

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def get_embedding_model():
    """Return the single embedding model used by the application."""
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
