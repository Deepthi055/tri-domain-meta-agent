"""
embedder.py
Chunks the knowledge base text, embeds with sentence-transformers,
and builds a FAISS index. Run once to build the index.
"""
import os
import json
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────
KB_DIR   = os.path.join(os.path.dirname(__file__), "knowledge_base")
IDX_PATH = os.path.join(os.path.dirname(__file__), "career_index.faiss")
META_PATH = os.path.join(os.path.dirname(__file__), "career_meta.pkl")
MODEL_NAME = "all-MiniLM-L6-v2"   # fast, small, good quality
CHUNK_SIZE = 200                    # words per chunk
OVERLAP    = 30                     # words overlap between chunks

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

def build_index():
    """
    Read all .txt files in knowledge_base/,
    chunk them, embed, and save FAISS index.
    """
    print("[RAG] Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    all_chunks = []
    all_meta   = []

    for fname in os.listdir(KB_DIR):
        if not fname.endswith(".txt"):
            continue
        fpath = os.path.join(KB_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_meta.append({
                "source": fname,
                "chunk_id": i,
                "text": chunk
            })
        print(f"[RAG] {fname} → {len(chunks)} chunks")

    print(f"\n[RAG] Embedding {len(all_chunks)} chunks...")
    embeddings = model.encode(
        all_chunks,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    # Normalize for cosine similarity
    faiss.normalize_L2(embeddings)

    # Build FAISS flat index
    dim   = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)   # Inner product = cosine after normalization
    index.add(embeddings)

    # Save index and metadata
    faiss.write_index(index, IDX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump(all_meta, f)

    print(f"\n[RAG] Index built successfully!")
    print(f"      Chunks indexed : {len(all_chunks)}")
    print(f"      Index saved    : {IDX_PATH}")
    print(f"      Metadata saved : {META_PATH}")
    return index, all_meta

if __name__ == "__main__":
    build_index()