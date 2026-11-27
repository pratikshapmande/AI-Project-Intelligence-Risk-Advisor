import os
from pathlib import Path
from functools import lru_cache
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_DIR = DATA_DIR / "chroma_db"
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

@lru_cache(maxsize=1)
def get_collection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(DB_DIR))
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)
    return client.get_or_create_collection(
        name="project_knowledge",
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )

def add_document(document_id: str, source: str, file_type: str, metadata: dict, chunks: list[str]) -> int:
    collection = get_collection()
    ids = [f"{document_id}_{i}" for i in range(len(chunks))]
    metadatas = [{
        "document_id": document_id,
        "source": source,
        "file_type": file_type,
        "chunk_index": i,
        "document_metadata": str(metadata)
    } for i in range(len(chunks))]
    if chunks:
        collection.add(ids=ids, documents=chunks, metadatas=metadatas)
    return len(chunks)

def list_documents() -> list[dict]:
    collection = get_collection()
    result = collection.get(include=["metadatas"])
    docs = {}
    for meta in result.get("metadatas") or []:
        if not meta:
            continue
        did = meta.get("document_id")
        if did not in docs:
            docs[did] = {
                "id": did,
                "name": meta.get("source", "Unknown"),
                "file_type": meta.get("file_type", ""),
                "chunks": 0,
            }
        docs[did]["chunks"] += 1
    return sorted(docs.values(), key=lambda x: x["name"].lower())

def search(query: str, limit: int = 5) -> list[dict]:
    collection = get_collection()
    if collection.count() == 0:
        return []
    result = collection.query(query_texts=[query], n_results=min(limit, collection.count()),
                              include=["documents", "metadatas", "distances"])
    items = []
    ids = (result.get("ids") or [[]])[0]
    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    for i, chunk in enumerate(documents):
        meta = metadatas[i] or {}
        items.append({
            "id": ids[i],
            "source": meta.get("source", "Unknown"),
            "file_type": meta.get("file_type", ""),
            "chunk_index": meta.get("chunk_index", 0),
            "text": chunk,
            "distance": round(float(distances[i]), 4) if i < len(distances) and distances[i] is not None else None
        })
    return items

def delete_document(document_id: str) -> bool:
    collection = get_collection()
    result = collection.get(where={"document_id": document_id}, include=[])
    ids = result.get("ids") or []
    if ids:
        collection.delete(ids=ids)
    return bool(ids)
