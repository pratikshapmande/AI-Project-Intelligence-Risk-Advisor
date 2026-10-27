from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .ingestion import extract_document, chunk_text, SUPPORTED
from .store import add_document, list_documents, search as semantic_search, delete_document, get_collection

app = FastAPI(title="AI Project Intelligence & Risk Advisor", version="0.1.0",
              description="Milestone 1: document ingestion, chunking, embeddings and vector indexing.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    limit: int = Field(default=5, ge=1, le=10)

@app.get("/api/health")
def health():
    return {"status": "ok", "project": "AI Project Intelligence & Risk Advisor", "milestone": 1}

@app.get("/api/documents")
def documents():
    items = list_documents()
    return {"documents": items, "document_count": len(items),
            "chunk_count": sum(d["chunks"] for d in items)}

@app.post("/api/documents/upload")
async def upload_documents(files: list[UploadFile] = File(...)):
    results = []
    for file in files:
        name = Path(file.filename or "upload").name
        suffix = Path(name).suffix.lower()
        if suffix not in SUPPORTED:
            results.append({"filename": name, "status": "error",
                            "message": "Unsupported file type. Upload PDF, DOCX, CSV, or TXT."})
            continue
        try:
            content = await file.read()
            extracted = extract_document(name, content)
            chunks = chunk_text(extracted["text"])
            document_id = uuid4().hex
            count = add_document(document_id, extracted["source"], extracted["file_type"],
                                 extracted["metadata"], chunks)
            results.append({"filename": name, "status": "indexed", "document_id": document_id,
                            "characters_extracted": len(extracted["text"]), "chunks_indexed": count,
                            "file_type": extracted["file_type"], "metadata": extracted["metadata"]})
        except Exception as exc:
            results.append({"filename": name, "status": "error", "message": str(exc)})
    return {"results": results}

@app.post("/api/search")
def search(request: SearchRequest):
    try:
        return {"query": request.query, "results": semantic_search(request.query, request.limit)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {exc}")

@app.delete("/api/documents/{document_id}")
def remove_document(document_id: str):
    removed = delete_document(document_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"deleted": True, "document_id": document_id}
