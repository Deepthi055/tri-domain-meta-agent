"""
retriever.py
Loads the FAISS index and retrieves top-k relevant chunks
for a given query. Used by career_agent at runtime.
"""
import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

IDX_PATH  = os.path.join(os.path.dirname(__file__), "career_index.faiss")
META_PATH = os.path.join(os.path.dirname(__file__), "career_meta.pkl")
MODEL_NAME = "all-MiniLM-L6-v2"

# ── Singleton — load once, reuse across requests ──────────────
_model = None
_index = None
_meta  = None

def _load():
    global _model, _index, _meta
    if _model is None:
        print("[RAG] Loading retriever model...")
        _model = SentenceTransformer(MODEL_NAME)
    if _index is None:
        if not os.path.exists(IDX_PATH):
            raise FileNotFoundError(
                "FAISS index not found. Run: python rag/embedder.py"
            )
        _index = faiss.read_index(IDX_PATH)
        with open(META_PATH, "rb") as f:
            _meta = pickle.load(f)

def retrieve(query: str, top_k: int = 3) -> list[dict]:
    """
    Retrieve top_k most relevant chunks for a query.
    Returns list of dicts with text and source.
    """
    _load()

    # Embed and normalize query
    query_vec = _model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(query_vec)

    # Search
    scores, indices = _index.search(query_vec, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        chunk = _meta[idx].copy()
        chunk["relevance_score"] = round(float(score), 3)
        results.append(chunk)

    return results

def retrieve_as_context(query: str, top_k: int = 3) -> str:
    """
    Returns retrieved chunks formatted as a string
    ready to inject into an LLM prompt.
    """
    chunks = retrieve(query, top_k)
    if not chunks:
        return ""

    context = "\n\nRELEVANT KNOWLEDGE BASE CONTEXT:\n"
    context += "=" * 40 + "\n"
    for i, chunk in enumerate(chunks, 1):
        context += f"[Source {i}: {chunk['source']}]\n"
        context += chunk["text"] + "\n\n"
    context += "=" * 40
    return context