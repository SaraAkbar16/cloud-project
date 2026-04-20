from pathlib import Path
import logging

import pdfplumber
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

# Your modules
from app.gui import render_gui
from embeddings.embedding_factory import EMBEDDING_MODEL_NAME, get_embedding_model
from Vector_Store.vector_factory import (
    FAISS_DIR,
    VECTOR_STORE_NAME,
    create_vector_store,
    load_vector_store,
)

# LangChain text splitter
from langchain.text_splitter import CharacterTextSplitter

DOCS_DIR = Path("data") / "docs"
SUPPORTED_EXTENSIONS = {".txt", ".pdf"}

# Silence verbose font-metadata warnings from pdfminer used by pdfplumber.
logging.getLogger("pdfminer").setLevel(logging.ERROR)

app = FastAPI(title="Semantic Search Engine")

# Global state
VECTOR_STORE = None
DATASET_INFO = None

# Chunking settings
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
splitter = CharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)


def _extract_text(file_path: Path) -> str:
    if file_path.suffix.lower() == ".txt":
        return file_path.read_text(encoding="utf-8", errors="ignore")

    if file_path.suffix.lower() == ".pdf":
        with pdfplumber.open(file_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)

    return ""


def _read_docs_and_build_chunks():
    if not DOCS_DIR.exists() or not DOCS_DIR.is_dir():
        raise FileNotFoundError(f"Documents directory not found: {DOCS_DIR}")

    source_files = [
        p
        for p in DOCS_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not source_files:
        raise ValueError(f"No supported files found in {DOCS_DIR}. Add .txt or .pdf files.")

    all_texts, all_metadatas = [], []
    total_chars, total_size = 0, 0

    for file_path in sorted(source_files):
        content = _extract_text(file_path)
        total_size += file_path.stat().st_size

        if not content.strip():
            continue

        chunks = splitter.split_text(content)
        for chunk in chunks:
            all_texts.append(chunk)
            all_metadatas.append({"source": file_path.name})
            total_chars += len(chunk)

    if not all_texts:
        raise ValueError("No readable text content found in data/docs.")

    dataset_info = {
        "doc_count": len(source_files),
        "char_count": total_chars,
        "size_mb": round(total_size / (1024 * 1024), 2),
    }
    return all_texts, all_metadatas, dataset_info


def _build_and_persist_embeddings():
    texts, metadatas, dataset_info = _read_docs_and_build_chunks()
    embeddings = get_embedding_model()
    store = create_vector_store(texts, embeddings, metadatas)
    return store, dataset_info


def _read_docs_summary():
    """Read lightweight dataset stats without chunking or embedding work."""
    if not DOCS_DIR.exists() or not DOCS_DIR.is_dir():
        return None

    source_files = [
        p
        for p in DOCS_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not source_files:
        return None

    total_size = sum(p.stat().st_size for p in source_files)
    return {
        "doc_count": len(source_files),
        "char_count": "-",
        "size_mb": round(total_size / (1024 * 1024), 2),
    }


@app.on_event("startup")
async def startup_load_index():
    """Load saved embeddings on startup without rebuilding automatically."""
    global VECTOR_STORE, DATASET_INFO

    # Do not initialize/download embedding models unless a persisted index exists.
    index_exists = (FAISS_DIR / "index.faiss").exists() and (FAISS_DIR / "index.pkl").exists()
    if not index_exists:
        VECTOR_STORE = None
        DATASET_INFO = None
        return

    embeddings = get_embedding_model()
    VECTOR_STORE = load_vector_store(embeddings)

    if VECTOR_STORE is not None:
        DATASET_INFO = _read_docs_summary()
        return

    VECTOR_STORE = None
    DATASET_INFO = None


@app.get("/", response_class=HTMLResponse)
async def home():
    """Render initial GUI."""
    return render_gui(
        embeddings_ready=VECTOR_STORE is not None,
        dataset_info=DATASET_INFO,
        embedding_model_name=EMBEDDING_MODEL_NAME,
        vector_store_name=VECTOR_STORE_NAME,
        docs_path=str(DOCS_DIR).replace("\\", "/"),
    )


@app.post("/upload", response_class=HTMLResponse)
async def upload():
    """Load existing embeddings if available; otherwise build and persist them."""
    global VECTOR_STORE, DATASET_INFO

    try:
        embeddings = get_embedding_model()
        existing_store = load_vector_store(embeddings)

        if existing_store is not None:
            VECTOR_STORE = existing_store
            DATASET_INFO = _read_docs_summary()

            return render_gui(
                embeddings_ready=True,
                dataset_info=DATASET_INFO,
                message="Existing embeddings loaded from disk. No rebuild was needed.",
                embedding_model_name=EMBEDDING_MODEL_NAME,
                vector_store_name=VECTOR_STORE_NAME,
                docs_path=str(DOCS_DIR).replace("\\", "/"),
            )

        VECTOR_STORE, DATASET_INFO = _build_and_persist_embeddings()

        return render_gui(
            embeddings_ready=True,
            dataset_info=DATASET_INFO,
            message="Embeddings generated and saved successfully from data/docs.",
            embedding_model_name=EMBEDDING_MODEL_NAME,
            vector_store_name=VECTOR_STORE_NAME,
            docs_path=str(DOCS_DIR).replace("\\", "/"),
        )

    except Exception as e:
        return render_gui(
            error=f"An error occurred: {str(e)}",
            embeddings_ready=VECTOR_STORE is not None,
            dataset_info=DATASET_INFO,
            embedding_model_name=EMBEDDING_MODEL_NAME,
            vector_store_name=VECTOR_STORE_NAME,
            docs_path=str(DOCS_DIR).replace("\\", "/"),
        )


@app.post("/search", response_class=HTMLResponse)
async def search(query: str = Form(...), top_k: int = Form(...)):
    """Semantic retrieval."""
    global VECTOR_STORE, DATASET_INFO

    if not VECTOR_STORE:
        return render_gui(
            error="No index found. Generate embeddings from data/docs first.",
            embeddings_ready=False,
            dataset_info=DATASET_INFO,
            embedding_model_name=EMBEDDING_MODEL_NAME,
            vector_store_name=VECTOR_STORE_NAME,
            docs_path=str(DOCS_DIR).replace("\\", "/"),
        )

    docs = VECTOR_STORE.similarity_search(query, k=top_k)

    results = []
    for i, doc in enumerate(docs):
        results.append(
            {
                "rank": i + 1,
                "source": doc.metadata.get("source", "Unknown"),
                "content": doc.page_content[:600],  # snippet
            }
        )

    return render_gui(
        query=query,
        results=results,
        embeddings_ready=True,
        dataset_info=DATASET_INFO,
        embedding_model_name=EMBEDDING_MODEL_NAME,
        vector_store_name=VECTOR_STORE_NAME,
        docs_path=str(DOCS_DIR).replace("\\", "/"),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)