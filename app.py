import streamlit as st
from pathlib import Path
import pandas as pd

from src.ingestion import extract_text
from src.rag import RAGKnowledgeBase, chunk_text

st.set_page_config(page_title="AI Project Intelligence & Risk Advisor", page_icon="🧠", layout="wide")

st.markdown("""
<style>
.main {background-color: #f7f9fc;}
.block-container {padding-top: 1.5rem; max-width: 1200px;}
.hero {padding: 1.4rem 1.6rem; border-radius: 16px; background: linear-gradient(120deg,#102a43,#176b87); color: white; margin-bottom: 1.2rem;}
.hero h1 {font-size: 2rem; margin: 0 0 .35rem 0;}
.hero p {margin: 0; color: #e2f3fa;}
.small-note {color: #526579; font-size: .9rem;}
</style>
<div class="hero">
<h1>🧠 AI Project Intelligence & Risk Advisor</h1>
<p>Milestone 1 prototype · Document ingestion · Chunking · Local embeddings · Vector indexing · Semantic retrieval</p>
</div>
""", unsafe_allow_html=True)

INDEX_DIR = Path("data/knowledge_base")
kb = RAGKnowledgeBase(INDEX_DIR)

with st.sidebar:
    st.header("Milestone 1")
    st.caption("This build intentionally stops at the RAG knowledge-base foundation.")
    st.markdown("""
    **Included**
    - PDF, DOCX, CSV and TXT uploads
    - Text extraction
    - Text chunking
    - Local embedding model
    - Persistent vector index
    - Semantic retrieval

    **Not included yet**
    - Risk forecasting agents
    - Project health scoring
    - Auto-generated risk registers
    - Multi-agent execution
    - Conversational assistant
    """)
    st.divider()
    st.caption("First run downloads the embedding model from Hugging Face. After it is cached, embeddings run locally.")

tab_upload, tab_search, tab_index = st.tabs(["📄 Ingest documents", "🔎 Semantic search", "🗂️ Knowledge base"])

with tab_upload:
    st.subheader("Add project documents")
    st.write("Upload project proposals, meeting notes, progress updates, task lists or other project artifacts.")
    uploads = st.file_uploader(
        "Choose files",
        type=["pdf", "docx", "csv", "txt"],
        accept_multiple_files=True,
        help="Supported formats: PDF, DOCX, CSV and plain text."
    )
    col1, col2 = st.columns([1, 2])
    with col1:
        chunk_size = st.slider("Chunk size (characters)", 300, 1800, 900, 100)
    with col2:
        overlap = st.slider("Chunk overlap (characters)", 0, 300, 120, 20)

    if st.button("Process and index documents", type="primary", disabled=not uploads):
        if overlap >= chunk_size:
            st.error("Chunk overlap must be smaller than chunk size.")
        else:
            progress = st.progress(0, text="Preparing documents...")
            processed = 0
            errors = []
            all_chunks = []
            for i, uploaded in enumerate(uploads):
                try:
                    raw = uploaded.getvalue()
                    extracted = extract_text(uploaded.name, raw)
                    if not extracted.strip():
                        errors.append(f"{uploaded.name}: no readable text was found.")
                        continue
                    pieces = chunk_text(extracted, chunk_size=chunk_size, overlap=overlap)
                    for j, piece in enumerate(pieces):
                        all_chunks.append({
                            "text": piece,
                            "source": uploaded.name,
                            "chunk_id": j,
                            "file_type": Path(uploaded.name).suffix.lower().lstrip(".")
                        })
                    processed += 1
                except Exception as exc:
                    errors.append(f"{uploaded.name}: {exc}")
                progress.progress((i + 1) / len(uploads), text=f"Processed {i + 1} of {len(uploads)} file(s)")

            if all_chunks:
                try:
                    with st.spinner("Creating local embeddings and updating the vector index..."):
                        kb.add_chunks(all_chunks)
                    st.success(f"Indexed {len(all_chunks)} text chunk(s) from {processed} document(s).")
                except Exception as exc:
                    st.error(f"Could not create embeddings/index: {exc}")
                    st.info("Check the installation instructions in README.md. The first model download requires internet access.")
            if errors:
                with st.expander("Files needing attention"):
                    for err in errors:
                        st.warning(err)
            progress.empty()

with tab_search:
    st.subheader("Search the uploaded knowledge base")
    st.write("Enter a question or phrase. The system retrieves the most semantically relevant chunks from indexed documents.")
    query = st.text_input("Search query", placeholder="e.g., What are the main project deliverables?")
    top_k = st.slider("Number of results", 1, 10, 5)
    if st.button("Search knowledge base", type="primary"):
        if not query.strip():
            st.warning("Enter a search query first.")
        elif kb.count() == 0:
            st.warning("No indexed chunks yet. Upload and process documents first.")
        else:
            try:
                with st.spinner("Searching the local vector index..."):
                    results = kb.search(query, top_k=top_k)
                if not results:
                    st.info("No results were found.")
                for rank, item in enumerate(results, 1):
                    score = item.get("score", 0.0)
                    with st.container(border=True):
                        top = st.columns([5, 1])
                        top[0].markdown(f"**{rank}. {item['source']}**")
                        top[1].metric("Similarity", f"{score:.3f}")
                        st.caption(f"Chunk {item['chunk_id'] + 1} · {item['file_type'].upper()}")
                        st.write(item["text"])
            except Exception as exc:
                st.error(f"Search failed: {exc}")

with tab_index:
    st.subheader("Indexed knowledge base")
    stats = kb.stats()
    c1, c2, c3 = st.columns(3)
    c1.metric("Indexed chunks", stats["chunks"])
    c2.metric("Source documents", stats["documents"])
    c3.metric("Embedding model", "all-MiniLM-L6-v2")
    if stats["documents"]:
        st.markdown("#### Source files")
        st.dataframe(pd.DataFrame(stats["sources"]), use_container_width=True, hide_index=True)
    else:
        st.info("The knowledge base is empty. Ingest a document to get started.")
    st.caption(f"Index storage location: `{INDEX_DIR}`")
    if st.button("Clear knowledge base", type="secondary"):
        kb.clear()
        st.success("Knowledge base cleared. Refresh the page to update the counters.")
        st.rerun()

st.divider()
st.markdown('<p class="small-note">Milestone 1 scope only: system design, supported document ingestion, chunking, local embeddings and vector indexing. Retrieval is included as a practical way to validate the RAG foundation.</p>', unsafe_allow_html=True)
