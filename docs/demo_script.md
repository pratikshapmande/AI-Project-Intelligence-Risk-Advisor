# Unified Project Intelligence Platform — Demo Script

1. Start FastAPI and Vite; show the API-connected indicator.
2. Upload `samples/project_brief.txt`, `samples/project_tasks.docx` and `samples/project_status.pdf`.
3. Show document inventory and ChromaDB chunk indexing; demonstrate a semantic search.
4. From the Dashboard, review the consolidated scope, risk, blocker and action summaries. The Milestone 2 extraction logic remains available in the integrated workspace.
5. Open **Project Intelligence → Documentation Generation**. Generate the user-story candidates, risk register and action items; inspect the `Not specified` fields, source references and the conflicting completed/incomplete login-prototype statements. Download the generated PDF report.
6. Calculate the Project Health Score. Explain the five dimensions, evidence reasons and documented heuristic formula. Download the report.
7. Ask the assistant: “What are our biggest project risks?”, “Who is responsible for pending tasks?”, “Which deliverables remain?” and “Are we on track?”. Point out source documents and chunk numbers. Without an OpenAI key, show the explicit retrieval-only fallback.
8. Run RAG Validation. Inspect explicit-fact, multi-document, format, unavailable-fact and conflict checks. Explain that PASS is retrieval/source coverage, not a proof of semantic correctness.
9. Explain the architecture: shared ingestion and ChromaDB corpus -> Milestone 2 agents and Milestone 3 modules.


## Milestone 4 demonstration
- Open **Dashboard** (the default landing page) and load the project insights if they have not loaded automatically.
- Explain the overall score and five evidence-count dimensions.
- Review scope summary, risk entries and action items with source document references.
- Upload a new meeting note as an incremental update, confirm the document count increases, and refresh the dashboard.
- Download the generated PDF report. State clearly that scoring is heuristic and missing fields remain Not specified.
