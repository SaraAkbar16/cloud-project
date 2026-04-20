from langchain_community.vectorstores import FAISS
from pathlib import Path
import shutil
import logging

BASE_DIR = Path("Vector_Store")
FAISS_DIR = BASE_DIR / "faiss"

VECTOR_STORE_NAME = "FAISS"
logger = logging.getLogger(__name__)


def create_vector_store(texts, embeddings, metadatas):
    """Create and persist the single vector store used by the application."""
    if FAISS_DIR.exists():
        shutil.rmtree(FAISS_DIR)
    FAISS_DIR.mkdir(parents=True, exist_ok=True)

    store = FAISS.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
    )
    store.save_local(str(FAISS_DIR))
    return store


def load_vector_store(embeddings):
    """Load an existing persisted vector store."""
    if not FAISS_DIR.exists():
        return None

    if not (FAISS_DIR / "index.faiss").exists() or not (FAISS_DIR / "index.pkl").exists():
        return None

    try:
        return FAISS.load_local(
            str(FAISS_DIR),
            embeddings,
            allow_dangerous_deserialization=True,
        )
    except Exception as exc:
        # Persisted FAISS metadata uses pickle and can become incompatible
        # across dependency/version changes. Treat as "no usable store".
        logger.warning("Failed to load persisted FAISS index from %s: %s", FAISS_DIR, exc)
        return None
