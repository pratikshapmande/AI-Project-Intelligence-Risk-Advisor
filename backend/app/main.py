from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .ingestion import extract_document, chunk_text, SUPPORTED
from .store import add_document, list_documents, search as semantic_search, delete_document, get_collection
from .agents import analyze_indexed_documents
from .milestone3 import generate_docs, health_score, answer_question, validate_rag
from .milestone4 import build_insights_payload
from .reporting import build_pdf_report

app = FastAPI(title="AI Project Intelligence & Risk Advisor", version="0.4.0",
              description="Milestones 1-4: project knowledge base, agents, documentation, grounded assistant and insights dashboard.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

class PDFReportRequest(BaseModel):
    title: str = Field(default="Project Report", min_length=1, max_length=200)
    data: dict = Field(default_factory=dict)


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    limit: int = Field(default=5, ge=1, le=10)

@app.get("/api/health")
def health():
    return {"status": "ok", "project": "AI Project Intelligence & Risk Advisor", "milestone": 4}

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


@app.post("/api/agents/analyze")
def analyze_agents():
    """Run the three Milestone 2 extractors against currently indexed documents."""
    try:
        if get_collection().count() == 0:
            raise HTTPException(status_code=400, detail="Upload and index project documents before running the agents.")
        return analyze_indexed_documents()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent analysis failed: {exc}")


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    history: list[dict] = Field(default_factory=list)

@app.get("/api/milestone3/documentation")
def milestone3_documentation():
    if get_collection().count() == 0:
        raise HTTPException(status_code=400, detail="Upload project documents before generating documentation.")
    return generate_docs()

@app.get("/api/milestone3/health-score")
def milestone3_health_score():
    if get_collection().count() == 0:
        raise HTTPException(status_code=400, detail="Upload project documents before calculating project health.")
    return health_score()

@app.post("/api/milestone3/chat")
def milestone3_chat(request: ChatRequest):
    if get_collection().count() == 0:
        raise HTTPException(status_code=400, detail="Upload project documents before asking project questions.")
    return answer_question(request.question, request.history)

@app.get("/api/milestone3/validation")
def milestone3_validation():
    if get_collection().count() == 0:
        raise HTTPException(status_code=400, detail="Upload PDF, DOCX and TXT project documents to run RAG validation.")
    return validate_rag()


@app.get("/api/milestone4/insights")
def milestone4_insights():
    """Consolidated dashboard payload based on the current indexed project corpus."""
    if get_collection().count() == 0:
        raise HTTPException(status_code=400, detail="Upload project documents before loading the insights dashboard.")
    try:
        return build_insights_payload()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not build project insights: {exc}")


@app.post("/api/milestone4/documents/incremental-upload")
async def milestone4_incremental_upload(files: list[UploadFile] = File(...)):
    """Append new meeting notes/progress updates without replacing indexed documents."""
    result = await upload_documents(files)
    indexed_count = sum(1 for item in result.get("results", []) if item.get("status") == "indexed")
    failed_count = len(result.get("results", [])) - indexed_count
    # The ingestion pipeline assigns a fresh UUID to every upload and ChromaDB
    # add() appends its chunks to the existing project collection.
    current_documents = list_documents()
    result.update({
        "index_mode": "incremental_append",
        "indexed_count": indexed_count,
        "failed_count": failed_count,
        "knowledge_base": {
            "document_count": len(current_documents),
            "chunk_count": sum(item.get("chunks", 0) for item in current_documents),
        },
        "message": (
            "New documents were appended to the existing project knowledge base. "
            "Previously indexed documents and chunks were retained."
        ),
    })
    return result


@app.post("/api/reports/pdf")
def generate_pdf_report(request: PDFReportRequest):
    """Convert a frontend report payload into a genuine PDF attachment.

    Existing JSON report endpoints remain unchanged for internal application use.
    """
    try:
        pdf_bytes = build_pdf_report(request.title, request.data)
        safe_name = "".join(ch for ch in request.title if ch.isalnum() or ch in " -_").strip() or "project-report"
        filename = safe_name.replace(" ", "-")[:80] + ".pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF report generation failed: {exc}")
