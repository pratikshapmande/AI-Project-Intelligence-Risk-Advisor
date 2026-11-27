# System Architecture — Milestones 1–3

## Purpose
The application retains the original React + Vite, FastAPI and ChromaDB foundation. Milestone 2 extraction agents and Milestone 3 project-level modules are integrated into the same application.

## High-level architecture
```text
PDF / DOCX / CSV / TXT
        |
        v
React + Vite dashboard (existing navigation + Milestone 3)
        |
        v
FastAPI ingestion endpoint -> extraction -> overlapping chunks
        |
        v
Sentence Transformers embeddings -> persistent ChromaDB
        |
        +--> Existing semantic search and Milestone 2 extraction agents
        |
        +--> Milestone 3 project corpus consolidation
                 |--> Documentation generation + conflict candidates
                 |--> Transparent evidence-based health scoring
                 |--> RAG retrieval -> optional backend OpenAI synthesis
                 |--> Retrieval/format/conflict validation checks
```

## Project-level processing
The backend reads all indexed chunks in the current workspace, groups them by source document, deduplicates identical sentence text while retaining source references, and uses the combined corpus for Milestone 3. Potential contradictory status statements are surfaced with both sources; the system does not silently select one. The workspace currently represents one project at a time and does not isolate multiple project IDs.

## Milestone 3 components
- **Documentation generation:** creates structured user-story candidates, risk entries and action items. Unknown owners, dates, impacts and acceptance criteria remain `Not specified`.
- **Health scoring:** computes five dimension scores from explicit evidence counts/signals. The overall score is the unweighted mean. Formula and reasons are returned with the report; it is a heuristic evidence indicator, not a certified project audit.
- **Conversational assistant:** queries the existing ChromaDB semantic index before answering. Optional OpenAI chat completion is called server-side using `OPENAI_API_KEY`; no key or service failure produces a retrieval-only fallback.
- **RAG validation:** exercises retrieval/source coverage and format presence, checks potential conflicts, and guards a likely unavailable fact. It reports review limitations rather than claiming full semantic evaluation.

## Design limitations
- Scanned PDFs without a text layer are not OCR-processed.
- Uploaded originals are not retained by the existing ingestion path; extracted chunks and metadata are stored.
- No authentication, multi-tenant isolation, public deployment security or production upload scanning.
- The first Sentence Transformers use may download a model.
