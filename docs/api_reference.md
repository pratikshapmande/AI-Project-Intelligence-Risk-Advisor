# API Reference — Milestones 1–3

Base URL: `http://127.0.0.1:8000`

## Existing APIs
- `GET /api/health` — service status and current milestone.
- `GET /api/documents` — indexed document inventory and aggregate document/chunk counts.
- `POST /api/documents/upload` — multipart field `files`; PDF, DOCX, CSV and TXT.
- `POST /api/search` — JSON `{"query":"project deadline","limit":5}`; returns source-labelled chunks.
- `DELETE /api/documents/{document_id}` — removes all indexed chunks for one uploaded file.
- `POST /api/agents/analyze` — Milestone 2 scope/deliverable, risk/dependency, blocker and action extraction.

## Milestone 3 APIs
- `GET /api/milestone3/documentation` — project-wide user-story candidates, risk register, action items and potential conflicting statements. Missing fields are marked `Not specified`.
- `GET /api/milestone3/health-score` — overall score, five dimension scores, reasons, recommendations and supporting evidence.
- `POST /api/milestone3/chat` — JSON `{"question":"Are we on track?","history":[{"role":"user","content":"..."}]}`. Retrieves ChromaDB passages before answering and returns source references. With `OPENAI_API_KEY`, uses backend-only OpenAI synthesis; without it, returns retrieval-only evidence.
- `GET /api/milestone3/validation` — checks explicit-fact retrieval, multi-document coverage, file-format coverage, potential conflicts and a likely-unavailable fact. Results are PASS/REVIEW with limitations.

All Milestone 3 endpoints operate over the complete indexed corpus in the current local workspace. This is one project workspace, not a multi-project/tenant database. Rule-based findings and validation require human review; PASS is not a guarantee of semantic correctness.


## Milestone 4
- `GET /api/milestone4/insights` — dashboard aggregate of project health, scope, risks and action items.
- `POST /api/milestone4/documents/incremental-upload` — append PDF, DOCX, CSV or TXT meeting notes/progress updates to the existing project knowledge base (multipart `files`); returns per-file results and current document/chunk totals without replacing existing indexed content.
