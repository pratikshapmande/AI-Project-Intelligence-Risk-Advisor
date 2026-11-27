# Project Report — Milestone 4
## AI Project Intelligence & Risk Advisor

### 1. Objective
Milestone 4 completes the planned project insights and delivery dashboard, adds incremental document updates, and prepares verification and demonstration documentation while retaining the existing Milestone 1–3 implementation.

### 2. Implemented work
**Project Insights and Risk Summary Dashboard:** A new Milestone 4 navigation item presents the existing health score and its five dimensions alongside extracted scope statements, risk register entries and action items. The dashboard shows source document references, corpus counts, a generation timestamp and a downloadable JSON snapshot.

**Incremental document upload:** A new FastAPI endpoint accepts supported PDF, DOCX, CSV and TXT files. It reuses the existing extraction, chunking and embedding pipeline and adds chunks to the current ChromaDB collection with a new document ID. It does not clear or replace previously indexed documents. The existing upload interface uses this incremental route.

**Testing:** Automated tests cover dashboard aggregation, duplicate scope summary suppression and route registration. A manual test sequence is included for multi-format upload, Milestone 2 agents, Milestone 3 outputs, RAG chat and Milestone 4 dashboard refresh.

**Documentation and demonstration:** Implementation notes, API references, a test plan and a concise demo sequence are included in the `docs` directory.

### 3. Technology
- Frontend: React and Vite
- Backend: FastAPI
- Knowledge storage: ChromaDB
- Embeddings: Sentence Transformers
- Supported documents: PDF, DOCX, CSV and TXT

### 4. Verification status
Python source compilation completed successfully in the packaging environment. Pytest collection could not complete in this environment because the ChromaDB dependency is not installed here. The frontend production build could not be run because frontend packages were not installed and the package installation attempt timed out. Run the documented test and build commands on the target Windows machine after dependency installation.

### 5. Known limitations
The project uses one local project index rather than multiple isolated project workspaces. The health score remains a transparent heuristic signal and not a certified audit or guaranteed delivery forecast. Findings must be checked against source documents. Scanned PDFs without embedded text require OCR, which is not included. The dashboard is refreshed on demand after incremental upload.
