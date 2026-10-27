# API Reference

Base URL: `http://127.0.0.1:8000`

## `GET /api/health`
Returns API status and milestone number.

## `GET /api/documents`
Returns the indexed document inventory and aggregate document/chunk counts.

## `POST /api/documents/upload`
Multipart form field: `files` (one or more files). Supported extensions: `.pdf`, `.docx`, `.csv`, `.txt`. Each file has its own success/error result.

## `POST /api/search`
JSON request:
```json
{"query": "project deadline", "limit": 5}
```
Returns retrieved chunks, source filename, chunk index, and vector distance.

## `DELETE /api/documents/{document_id}`
Deletes all indexed chunks belonging to the selected upload ID.
