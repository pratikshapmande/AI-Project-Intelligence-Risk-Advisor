# AI Project Intelligence & Risk Advisor — Milestone 1

A runnable Milestone 1 implementation based on the uploaded Infosys Springboard project document.

## Scope implemented
- PDF, DOCX, CSV and TXT document ingestion
- Text extraction and metadata
- Chunking
- Embedding generation using Sentence Transformers
- Persistent ChromaDB vector indexing
- Semantic retrieval from indexed document chunks
- React + Vite user interface
- Architecture, RAG workflow, document data model, study notes, and basic tests

## Explicit scope boundary
This project does **not** implement the later multi-agent pipeline, risk forecasting, blocker/action-item agent, documentation generation agent, project-health scoring, or a full conversational project assistant. The search screen is a retrieval demonstration over indexed document chunks only.

## Requirements
- Windows 10/11
- Python 3.10 or 3.11 recommended
- Node.js 20 LTS or newer (includes npm)
- Internet connection on first backend start to download the embedding model

## 1. Start the backend (Windows PowerShell)
Open a terminal in this project folder:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```

If PowerShell blocks activation, run this in the same terminal:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```
This changes execution policy only for the current PowerShell process.

The API runs at `http://127.0.0.1:8000`; interactive API docs at `http://127.0.0.1:8000/docs`.

## 2. Start the frontend
Open a **second** terminal in the project root:
```powershell
cd frontend
npm install
npm run dev
```
Open the local URL printed by Vite, normally `http://localhost:5173`.

## 3. Use the app
1. Upload one or more PDF, DOCX, CSV, or TXT files.
2. Wait for ingestion and indexing to finish.
3. Review indexed documents and chunk counts.
4. Enter a question or phrase in Knowledge Base Search to retrieve the most relevant indexed chunks.
5. The ChromaDB database is stored in `backend/data/chroma_db` and persists across restarts.

## API endpoints
- `GET /api/health` — service status
- `GET /api/documents` — indexed document inventory
- `POST /api/documents/upload` — upload and index one or more files
- `POST /api/search` — semantic retrieval of matching chunks
- `DELETE /api/documents/{document_id}` — remove a document and its chunks

## Notes
- The first embedding-model download can take time. Keep the backend terminal open.
- This is a learning milestone, not a production-secured deployment. Do not expose it to the public internet without adding authentication, authorization, upload quotas, malware scanning, and operational hardening.
- ChromaDB's local database and uploaded source files are local to this project folder.
