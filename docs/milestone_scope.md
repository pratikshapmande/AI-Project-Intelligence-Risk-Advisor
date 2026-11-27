# Milestone Scope and Acceptance Checklist

## Milestone 1 — Knowledge foundation
- [x] PDF, DOCX, CSV and TXT extraction
- [x] Chunking, embeddings and persistent ChromaDB indexing
- [x] React dashboard, upload, inventory, retrieval and document deletion
- [x] Extraction/chunking tests

## Milestone 2 — Project intelligence agents
- [x] Scope and deliverable extraction
- [x] Risk/dependency and delivery challenge detection
- [x] Blocker and action-item identification
- [x] Source document/chunk evidence on findings

## Milestone 3 — Documentation, health and conversational intelligence
- [x] Project-wide documentation generation: user-story candidates, risk register and action items
- [x] Unknown owners, deadlines, acceptance criteria and impacts marked `Not specified`
- [x] Duplicate sentence consolidation with source traceability
- [x] Potential conflicting status statements surfaced with both source references
- [x] Five-dimension health score, overall 0–100, reasons and recommendations
- [x] ChromaDB RAG conversational assistant with source evidence and recent-turn context
- [x] Optional backend-only OpenAI synthesis and retrieval-only fallback
- [x] Retrieval validation checks for explicit facts, cross-document coverage, unavailable facts, formats and conflict review
- [x] PDF, DOCX and TXT demonstration documents supplied in `samples/`

## Milestone 4 — Insights dashboard, incremental updates and finalization
- [x] New Milestone 4 navigation item and consolidated Project Insights dashboard
- [x] Health score, scope summary, extracted risks and action items shown together
- [x] Source references and corpus counts included in the dashboard
- [x] JSON export of the consolidated insights snapshot
- [x] Incremental upload endpoint appends new PDF, DOCX, CSV and TXT files to the existing ChromaDB collection
- [x] Milestone 4 aggregation and API route registration tests added
- [x] Technical implementation notes, project report and demonstration steps documented

## Validation caveats
The deterministic documentation and scoring use transparent heuristics. RAG validation checks retrieval coverage and source presence, not a fully human-labelled semantic accuracy benchmark. Review all results against source documents. The current local index is a single project workspace; do not mix unrelated projects in one index.
