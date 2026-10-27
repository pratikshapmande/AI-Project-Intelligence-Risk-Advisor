# Milestone 1 Architecture

```text
User
 |
 v
Streamlit UI
 |
 v
Document Upload
 |-- PDF  -> pypdf text extraction
 |-- DOCX -> python-docx paragraph/table extraction
 |-- CSV  -> pandas parsing
 `-- TXT  -> UTF-8 / fallback decoding
 |
 v
Normalized extracted text
 |
 v
Chunking (configurable chunk size + overlap)
 |
 v
Local embedding model
sentence-transformers/all-MiniLM-L6-v2
 |
 v
Normalized embedding vectors
 + chunk/source metadata
 |
 v
Local vector index
NumPy vectors + JSON metadata
 |
 v
Semantic query embedding
 |
 v
Cosine-similarity retrieval
 |
 v
Ranked source chunks displayed in UI
```

## Data model

Each indexed chunk is represented by:

- `text`: extracted chunk content
- `source`: original uploaded filename
- `chunk_id`: zero-based chunk number within the uploaded file
- `file_type`: file extension without the dot

The vector matrix uses one row per chunk, with rows aligned to records in `chunks.json`.

## Scope boundary

This architecture stops at retrieval of relevant document chunks. It does not generate answers or run risk/project-management agents.
