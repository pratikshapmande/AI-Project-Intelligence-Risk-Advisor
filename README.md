# AI Project Intelligence & Risk Advisor — Milestones 1, 2, 3 and 4

This ZIP is an incremental update of the supplied project. The existing React/Vite frontend, FastAPI backend, ChromaDB store, ingestion pipeline, semantic search endpoint and Milestone 2 agents are retained. Milestone 3 is integrated as a new navigation module; it is not a separate application.

## Implemented

### Milestones 1–2 retained
- PDF, DOCX, CSV and TXT ingestion, text extraction, chunking, Sentence Transformers embeddings and persistent ChromaDB indexing.
- Semantic search and document removal.
- Existing scope/deliverable, risk/dependency, and blocker/action extraction agents.

### Milestone 3
1. **Documentation Generation** — project-wide evidence aggregation, duplicate sentence consolidation, user-story candidates, a risk register and action items. Source references are retained. Missing acceptance criteria, owners, dates and impacts are explicitly `Not specified`; recommendations are labelled as suggestions, not source facts.
2. **Project Health Score** — overall 0–100 and five dimensions. Each dimension includes its evidence counts and scoring reason. The scoring formula is documented in the API response and dashboard. It is a transparent heuristic signal, not a certified audit or a prediction of delivery success.
3. **Conversational Project Assistant** — semantic retrieval from ChromaDB before answering, source names/chunk references, and recent conversational history. Configure `OPENAI_API_KEY` to enable grounded OpenAI answer synthesis. Without a key, it returns extractive retrieved passages and explicitly identifies this fallback; no fake generated answer is presented.
4. **RAG Validation** — corpus-derived checks for explicit fact retrieval, multi-document retrieval coverage and a potentially unavailable fact. Results include expected/actual evidence, source names and PASS/REVIEW. These are retrieval checks, not a substitute for human-labelled semantic accuracy testing. Conflicts require review; the validation limitation is shown in the report.

All outputs are generated from the combined currently indexed project corpus. The current data model is a single local project workspace; it does not yet provide separate tenant/project IDs or project selection. If multiple unrelated projects are indexed in the same workspace, their content will be treated as one project. Re-index only one project's documents for a project-specific assessment.

### Milestone 4
1. **Project Insights and Risk Summary Dashboard** — the Dashboard is the default landing page and sits first in the sidebar. The interface restores the original light content theme and blue sidebar. Navigation is grouped into Workspace, Project Intelligence and System. It consolidates the existing Milestone 3 health score, scope statements, extracted risks and action items. It includes a five-axis radar chart labelled Schedule, Risk, Scope, Blockers and Quality. Its values are mapped one-to-one from the existing five Milestone 3 API scores (the Quality label uses the existing deliverable-progress evidence score as a proxy; the backend does not calculate a separate quality score). The overall score displayed in the chart is read from the health API. Evidence/source names, document and finding counts, a generated-at timestamp, recent extracted insights and a downloadable PDF report. The chart and dimension bars read the same backend health-score payload. It reuses the existing M2/M3 extraction and scoring logic rather than creating a competing scoring model.
2. **Incremental document upload** — new PDF, DOCX, CSV or TXT meeting notes and progress updates are appended to the existing ChromaDB collection using unique document IDs. Existing indexed documents are not replaced. After a successful upload, the UI refreshes document counts, regenerates the consolidated dashboard from the complete updated corpus, and returns the user to Dashboard automatically. The knowledge base is a single local project corpus, not a multi-tenant workspace.
3. **End-to-end testing** — backend unit tests cover the Milestone 4 aggregation and route registration. Sample PDF, DOCX and TXT files are included for manual end-to-end checks of ingestion, agent outputs, documentation generation, health score, RAG chat and dashboard refresh. A live end-to-end run still depends on installing dependencies and downloading the embedding model on the target Windows machine.
4. **Technical documentation and demo** — this README, `docs/milestone4_implementation.md`, API reference and demo script describe setup, test commands, expected workflows and known limitations.

## Windows setup

Requirements: Windows 10/11, Python 3.11 or 3.12 recommended, Node.js 20 LTS+, and internet access for the first embedding-model download.

### 1. Backend
Open PowerShell in the project root:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Optional LLM configuration: open `backend\.env` and set `OPENAI_API_KEY=your_key_here`. The key is read only by the backend; do not place it in frontend files. The backend loads `backend\.env` automatically. Alternatively, set the key in the active PowerShell session before starting Uvicorn:

```powershell
$env:OPENAI_API_KEY="your_key_here"
$env:OPENAI_MODEL="gpt-4o-mini"
uvicorn app.main:app --reload
```

Without the key, documentation generation and health scoring still work, and chat uses retrieval-only fallback.

Backend: `http://127.0.0.1:8000` · API docs: `http://127.0.0.1:8000/docs`

### 2. Frontend
Open a second PowerShell window in the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL, normally `http://localhost:5173`.

### 3. Demonstrate Milestone 3
1. Upload project documents belonging to the same project (PDF, DOCX, TXT, CSV).
2. Use the **Dashboard** to review the consolidated project-level outputs.
3. Open the corresponding Project Intelligence navigation pages.
4. Generate documentation; expand User stories, Risk register and Action items. Download the generated PDF report.
5. Calculate the health score and review each dimension's reason and evidence. Download the report.
6. Ask questions such as “What are our biggest project risks?”, “Which deliverables remain?”, “Who is responsible for pending tasks?” and “Are we on track?”. Review source references in the response.
7. Run RAG validation and inspect each test's evidence, retrieved source references and PASS/REVIEW result.

Sample demonstration files are in `samples/`: `project_brief.txt`, `project_tasks.docx`, and `project_status.pdf`.

## API additions
- `GET /api/milestone3/documentation`
- `GET /api/milestone3/health-score`
- `POST /api/milestone3/chat` — JSON: `{"question":"...", "history":[]}`
- `GET /api/milestone3/validation`

Existing API routes remain: `/api/health`, `/api/documents`, `/api/documents/upload`, `/api/search`, `/api/agents/analyze`, and `DELETE /api/documents/{document_id}`.

## Data and limitations
- ChromaDB persists under `backend/data/chroma_db`.
- Uploaded original files are not retained by the existing Milestone 1 ingestion path; only extracted chunks and metadata are indexed.
- The heuristic documentation and health scoring do not infer project facts that are absent from source documents. They are intentionally conservative.
- Sentence-transformer embeddings may download on first start. API key absence or LLM service failure falls back to retrieval-only evidence.
- Validation is partly heuristic and surfaces human-review limitations. Do not claim full semantic accuracy from retrieval PASS alone.
- This is a local internship demonstration, not a production-secured multi-tenant system. Add authentication, authorization, file retention controls, rate limits, upload scanning and operational monitoring before public deployment.

## Testing
Backend syntax and automated checks are described in `backend/tests`. Run:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest -q
```

Build the frontend with:

```powershell
cd frontend
npm run build
```


## Frontend-to-FastAPI connection (important)

The React app now calls the API through the Vite same-origin proxy (`/api`). Vite forwards these requests to `http://127.0.0.1:8000`, avoiding browser CORS and `localhost` versus `127.0.0.1` hostname mismatches. Keep both local development servers running.

1. Start `start_backend_windows.bat` and wait until Uvicorn prints `Uvicorn running on http://127.0.0.1:8000`.
2. In a second terminal, start `start_frontend_windows.bat`.
3. Open **http://127.0.0.1:5173** (not the `file://` path and preferably not a different computer/device).
4. Verify the backend directly at **http://127.0.0.1:8000/api/health**. It should return JSON with `"status": "ok"`.
5. Verify the frontend proxy at **http://127.0.0.1:5173/api/health**. It should return the same JSON.

### If the dashboard still says API disconnected

- If the direct backend health URL fails, the backend did not start. Read the backend terminal and fix the first Python import/dependency error shown there.
- If the direct backend health URL works but the frontend proxy URL fails, ensure the frontend was restarted after the `vite.config.js` proxy change.
- If both health URLs work but the document list takes time on first launch, wait for the embedding model to initialize/download. The dashboard now reports API health separately from document-index initialization, so this first-run delay should not be mistaken for a failed API connection.
- Do not close the backend terminal while using the application.
- If port 8000 or 5173 is already occupied, stop the other process using that port before restarting these scripts.


### 4. Demonstrate Milestone 4
1. Start the backend and frontend as described above, then upload the supplied sample documents.
2. The **Dashboard** is the first page. Select **Load project insights** if the dashboard has not loaded automatically.
3. Review the overall health score, five labelled dimensions, scope summary, risks, blockers and action items. Open the source document references to verify findings.
4. Upload an additional meeting note or progress update through the existing upload area. The upload uses the incremental endpoint and appends the new document to ChromaDB; existing documents remain indexed.
5. Select **Refresh insights**. Confirm that document/chunk totals and extracted findings reflect the expanded corpus.
6. Download the consolidated Project Insights PDF report.

## Milestone 4 API additions
- `GET /api/milestone4/insights` — consolidated health, scope, risk and action summary.
- `POST /api/milestone4/documents/incremental-upload` — append new project documents to the existing knowledge base.

## Milestone 4 tests
Run from `backend` with the virtual environment activated:

```powershell
python -m pytest -q
```

The Milestone 4 tests verify dashboard aggregation/deduplication and route registration. For the full manual workflow, use the included sample PDF, DOCX and TXT files and follow `docs/milestone4_implementation.md`.

## PDF report downloads

The Documentation Generation, Project Health Score, RAG Validation, and Project Insights download actions now request a real PDF from `POST /api/reports/pdf`. The backend renders the supplied report payload with ReportLab and returns `application/pdf` with an attachment filename. Existing JSON endpoints for documentation, health scoring, validation, and insights remain unchanged for internal frontend use. Install the updated backend dependencies with `python -m pip install -r requirements.txt` so `reportlab` is available.


### Dashboard presentation update
- The dashboard restores the original light theme, blue sidebar and responsive navigation. Dashboard is the default landing page.
- Dashboard loads the Milestone 4 insights after indexed documents are detected; Refresh insights re-fetches the consolidated payload.
- The radar chart displays Schedule, Risk, Scope, Blockers and Quality using the existing API dimensions. Quality is explicitly identified as the deliverable-progress proxy; no separate quality calculation is introduced. The overall score is taken directly from the health API.
- The sidebar contains Dashboard, Documents, Document Upload, the six Project Intelligence destinations, Backend Health and System Status. Milestone-specific navigation tabs and Semantic Search navigation have been removed; underlying extraction, retrieval, ChromaDB and RAG code remains in place. The existing ingestion, ChromaDB, agent, RAG, assistant, incremental upload and PDF-report endpoints are retained.

## Final frontend organization update

The frontend now separates the Milestone 3 capabilities into their own dedicated destinations while reusing the same existing API endpoints and React state:

- **Dashboard** remains the default landing area and keeps the five-dimension radar chart and consolidated project insights. The detailed health calculation panel is not duplicated in the Dashboard.
- **Documentation Generation** contains the Generate Documentation action, user stories, risk register, action items, potential conflicting statements, source references and PDF download.
- **Project Health** contains the detailed Calculate Health Score action, all five backend dimensions, evidence explanations, scoring methodology and health PDF download.
- **Project Assistant** contains the conversational RAG interface only.
- **RAG Validation** remains available as a separate validation section so the existing validation API and workflow are retained.

These are frontend organization changes. The existing Milestone 1 ingestion/indexing, Milestone 2 agents, Milestone 3 APIs, Milestone 4 insights, ChromaDB store and PDF reporting implementation have not been intentionally replaced.
