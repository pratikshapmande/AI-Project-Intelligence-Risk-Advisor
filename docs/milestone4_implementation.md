# Milestone 4 — Implementation and Verification

## Scope
Week 7–8 deliverables: project insights dashboard, incremental document upload, end-to-end verification guidance, and final technical/report/demo documentation.

## Dashboard
The React sidebar adds **Milestone 4**. Its API payload is assembled by `backend/app/milestone4.py` from the existing Milestone 3 `generate_docs()` and `health_score()` functions. It presents:
- overall health score and status;
- five health dimensions and their evidence-based reasons;
- extracted scope statements with source references;
- risk register entries with severity, likelihood, impact and sources;
- action items with owner, due date, status and sources;
- corpus counts, generation time and JSON export.

This avoids changing or duplicating Milestones 1–3 algorithms. It is a consolidated view of the current single-project ChromaDB corpus.

## Incremental upload
The new `POST /api/milestone4/documents/incremental-upload` route reuses the existing ingestion and chunking path. Each upload gets a fresh UUID document ID; ChromaDB `add()` appends its chunks. It does not clear or overwrite previously indexed documents. Supported formats remain PDF, DOCX, CSV and TXT. After a successful upload, the frontend refreshes the document inventory, regenerates project insights from the complete updated corpus, and automatically returns the user to Dashboard.

## Verification plan
1. Start FastAPI and verify `/api/health`.
2. Upload `samples/project_status.pdf`, `samples/project_tasks.docx`, and `samples/project_brief.txt`.
3. Run Milestone 2 agents and Milestone 3 documentation, health score, chat and RAG validation.
4. Load the Milestone 4 insights dashboard and verify the five dimensions, scope, risks, actions and source references.
5. Upload a new TXT meeting note through the upload area. Confirm the document count increases while earlier documents remain visible.
6. Refresh insights and verify the corpus counts are updated.
7. Download and open the JSON report.
8. Run `python -m pytest -q` in `backend` and `npm run build` in `frontend`.

## Automated tests in this ZIP
`backend/tests/test_milestone4.py` checks that the insights payload aggregates health/scope/risk/action data, deduplicates identical scope statements in the dashboard list, preserves counts, and registers both Milestone 4 routes.

## Important limitations
- The dashboard is evidence extraction, not an independently validated project-management judgement.
- The health score remains the Milestone 3 transparent heuristic; it is not a certified audit or delivery prediction.
- Incremental upload appends to one local project collection. It does not isolate multiple projects or deduplicate identical uploads across separate upload events.
- OCR for scanned/image-only PDFs, authentication and multi-user access are not added in this milestone.
- A complete live test requires the Windows environment to install the pinned/ranged dependencies and download the Sentence Transformers model. Automated tests in this package do not claim that a live ChromaDB/embedding end-to-end session was executed here.
