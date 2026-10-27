import json
from pathlib import Path
from collections import Counter
import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 120):
    """Split extracted text into overlapping character chunks, preferring word boundaries."""
    text = " ".join(text.split())
    if not text:
        return []
    if chunk_size < 1 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Use chunk_size > overlap >= 0.")
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start + int(chunk_size * 0.65), end)
            if boundary > start:
                end = boundary
        part = text[start:end].strip()
        if part:
            chunks.append(part)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


class RAGKnowledgeBase:
    """Small persistent vector index using local Sentence Transformers and cosine similarity."""

    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.meta_path = self.directory / "chunks.json"
        self.vector_path = self.directory / "vectors.npy"
        self._model = None
        self.records = []
        self.vectors = np.empty((0, 0), dtype=np.float32)
        self._load()

    def _get_model(self):
        if self._model is None:
            self._model = SentenceTransformer(MODEL_NAME)
        return self._model

    def _load(self):
        if self.meta_path.exists() and self.vector_path.exists():
            try:
                self.records = json.loads(self.meta_path.read_text(encoding="utf-8"))
                self.vectors = np.load(self.vector_path).astype(np.float32)
                if len(self.records) != len(self.vectors):
                    self.records = []
                    self.vectors = np.empty((0, 0), dtype=np.float32)
            except Exception:
                self.records = []
                self.vectors = np.empty((0, 0), dtype=np.float32)

    def _save(self):
        self.meta_path.write_text(json.dumps(self.records, ensure_ascii=False, indent=2), encoding="utf-8")
        np.save(self.vector_path, self.vectors)

    def add_chunks(self, chunks):
        if not chunks:
            return
        model = self._get_model()
        texts = [item["text"] for item in chunks]
        new_vectors = model.encode(
            texts, convert_to_numpy=True, normalize_embeddings=True,
            show_progress_bar=False
        ).astype(np.float32)

        if self.vectors.size and self.vectors.ndim == 2 and self.vectors.shape[1] == new_vectors.shape[1]:
            self.vectors = np.vstack([self.vectors, new_vectors])
        else:
            self.vectors = new_vectors
            if len(self.records):
                # Existing index used a different embedding dimension; replace it safely.
                self.records = []
        self.records.extend(chunks)
        self._save()

    def search(self, query, top_k=5):
        if not self.records or self.vectors.size == 0:
            return []
        qvec = self._get_model().encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        ).astype(np.float32)[0]
        if qvec.shape[0] != self.vectors.shape[1]:
            raise ValueError("Embedding dimension does not match the saved index. Clear and rebuild the index.")
        scores = self.vectors @ qvec
        indices = np.argsort(scores)[::-1][:max(1, min(top_k, len(scores)))]
        results = []
        for idx in indices:
            item = dict(self.records[int(idx)])
            item["score"] = float(scores[int(idx)])
            results.append(item)
        return results

    def count(self):
        return len(self.records)

    def stats(self):
        sources = Counter(item.get("source", "Unknown") for item in self.records)
        return {
            "chunks": len(self.records),
            "documents": len(sources),
            "sources": [{"Source file": name, "Chunks": count} for name, count in sorted(sources.items())]
        }

    def clear(self):
        self.records = []
        self.vectors = np.empty((0, 0), dtype=np.float32)
        for path in (self.meta_path, self.vector_path):
            if path.exists():
                path.unlink()
