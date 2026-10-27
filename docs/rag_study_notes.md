# Study Notes — Milestone 1

## 1. Retrieval-Augmented Generation (RAG)
RAG is a pattern that grounds an application in a selected collection of external documents. A common flow is ingest, split into chunks, embed, store vectors, retrieve relevant chunks for a query, and optionally pass those chunks to a language model to compose an answer.

### Key terms
- **Ingestion:** reading and extracting useful text from source files.
- **Chunking:** dividing long text into smaller segments that can be retrieved individually.
- **Embedding:** representing text as a numeric vector so semantically related text can be compared.
- **Vector store:** a database that stores vectors and associated text/metadata.
- **Retrieval:** selecting stored chunks most relevant to a query.
- **Grounding:** using retrieved source material as evidence rather than answering from unrelated assumptions.

In this Milestone 1 implementation, ingestion, chunking, embedding, vector storage, and retrieval are implemented. LLM answer synthesis is not implemented.

## 2. Multi-agent system design patterns
A multi-agent system typically separates work into specialized roles, such as scope extraction, risk identification, blocker detection, or documentation generation. Agents may exchange structured results and may be coordinated by a workflow/orchestrator. The uploaded project brief lists these as later project modules. They are design context only in this milestone; no agents are implemented here.

## 3. Project-management fundamentals
- **Scope:** what a project intends to deliver and what is excluded.
- **Deliverable:** a concrete output that can be reviewed.
- **Milestone:** a checkpoint with a defined set of outcomes.
- **Risk:** an uncertain event that may affect objectives.
- **Blocker:** an issue preventing progress.
- **Action item:** a task assigned to an owner, ideally with a due date.
- **Status reporting:** documenting progress, decisions, dependencies, and changes.

## 4. Why this foundation matters
Project artifacts are often distributed across documents and formats. A consistent ingestion and retrieval layer creates a searchable foundation for future intelligence features. The future risk agents and project-health features should be built only after this document knowledge base is reliable.
