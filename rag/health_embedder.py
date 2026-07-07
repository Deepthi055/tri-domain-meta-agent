"""
health_embedder.py
Chunks the health knowledge base, embeds with sentence-transformers,
and builds a FAISS index for the health agent.
Run once to build the index:
    python rag/health_embedder.py
"""
import os
import pickle
import faiss
from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────
KB_PATH   = os.path.join(os.path.dirname(__file__), "knowledge_base", "health_kb.txt")
IDX_PATH  = os.path.join(os.path.dirname(__file__), "health_index.faiss")
META_PATH = os.path.join(os.path.dirname(__file__), "health_meta.pkl")
MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 200
OVERLAP    = 30


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = OVERLAP):
    """Split text into overlapping word chunks."""
    words  = text.split()
    chunks = []
    start  = 0
    while start < len(words):
        end   = min(start + size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += size - overlap
    return chunks


def build_health_index():
    print("[RAG-Health] Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    # Read health KB
    with open(KB_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_text(text)
    all_meta = []
    for i, chunk in enumerate(chunks):
        all_meta.append({
            "source": "health_kb.txt",
            "chunk_id": i,
            "text": chunk
        })
    print(f"[RAG-Health] health_kb.txt → {len(chunks)} chunks")

    print(f"\n[RAG-Health] Embedding {len(chunks)} chunks...")
    embeddings = model.encode(
        chunks,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    # Normalize for cosine similarity
    faiss.normalize_L2(embeddings)

    # Build FAISS flat index
    dim   = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    # Save index and metadata
    faiss.write_index(index, IDX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump(all_meta, f)

    print(f"\n[RAG-Health] Index built successfully!")
    print(f"      Chunks indexed : {len(chunks)}")
    print(f"      Index saved    : {IDX_PATH}")
    print(f"      Metadata saved : {META_PATH}")
    return index, all_meta


if __name__ == "__main__":
    build_health_index()