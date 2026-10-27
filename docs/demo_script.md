# Suggested Milestone 1 Demo Script

1. Explain that the scope is limited to document ingestion and the RAG indexing foundation.
2. Open the React dashboard and point out the API connection status.
3. Upload one PDF, DOCX, CSV, or TXT sample file.
4. Show the result message and indexed chunk count.
5. Point out the document inventory and persistent ChromaDB storage.
6. Search for a phrase that exists in the uploaded document and show the retrieved passages.
7. Open `docs/architecture.md` and explain the flow: source files -> extraction -> chunking -> embedding -> ChromaDB -> retrieval.
8. State clearly that risk agents, forecasting, project-health scoring, and generated documentation are later modules and are not implemented in Milestone 1.
