import React, { useEffect, useRef, useState } from 'react'
import { Activity, ArrowUpRight, BookOpen, CheckCircle2, ChevronRight, CircleHelp, Database, FileText, Files, Gauge, Layers3, LoaderCircle, Search, ShieldCheck, UploadCloud, X, AlertCircle, RefreshCw, Trash2, Sparkles } from 'lucide-react'

const API = 'http://127.0.0.1:8000/api'
const fmt = n => new Intl.NumberFormat().format(n || 0)

export default function App() {
  const [health, setHealth] = useState(false)
  const [docs, setDocs] = useState([])
  const [stats, setStats] = useState({document_count:0,chunk_count:0})
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState(null)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [active, setActive] = useState('Overview')
  const inputRef = useRef(null)
  const uploadRef = useRef(null)

  async function refresh() {
    try {
      const [h, d] = await Promise.all([fetch(`${API}/health`), fetch(`${API}/documents`)])
      setHealth(h.ok)
      if (d.ok) { const data = await d.json(); setDocs(data.documents || []); setStats(data) }
    } catch { setHealth(false) }
  }
  useEffect(() => { refresh(); const t = setInterval(refresh, 8000); return () => clearInterval(t) }, [])

  async function upload(files) {
    if (!files?.length) return
    setBusy(true); setNotice(null); setResults([])
    const form = new FormData()
    Array.from(files).forEach(f => form.append('files', f))
    try {
      const res = await fetch(`${API}/documents/upload`, {method:'POST', body:form})
      const data = await res.json()
      const ok = (data.results || []).filter(r => r.status === 'indexed').length
      const failed = (data.results || []).filter(r => r.status !== 'indexed').length
      setNotice({type: failed ? 'warn' : 'success', text:`${ok} file(s) indexed${failed ? ` · ${failed} failed` : ''}`, details:data.results})
      await refresh()
    } catch { setNotice({type:'error', text:'Cannot reach the API. Start the FastAPI backend on port 8000 and try again.'}) }
    finally { setBusy(false); if (uploadRef.current) uploadRef.current.value = '' }
  }

  async function runSearch(e) {
    e?.preventDefault()
    if (query.trim().length < 2) return
    setSearching(true); setResults([])
    try {
      const res = await fetch(`${API}/search`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({query:query.trim(), limit:5})})
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Search failed')
      setResults(data.results || [])
    } catch (err) { setNotice({type:'error', text:err.message || 'Search failed. Check the backend.'}) }
    finally { setSearching(false) }
  }

  async function removeDoc(doc) {
    if (!confirm(`Remove "${doc.name}" and its indexed chunks?`)) return
    try {
      const res = await fetch(`${API}/documents/${doc.id}`, {method:'DELETE'})
      if (!res.ok) throw new Error((await res.json()).detail || 'Could not remove document')
      setNotice({type:'success', text:`Removed ${doc.name} from the vector index.`}); await refresh()
    } catch (err) { setNotice({type:'error', text:err.message}) }
  }

  const nav = [
    {label:'Overview', icon:Gauge},
    {label:'Knowledge Base', icon:Database},
    {label:'Architecture', icon:Layers3},
    {label:'Milestone Scope', icon:BookOpen},
  ]
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><Activity size={22}/></div><div><div className="brand-title">Project<span>IQ</span></div><div className="brand-sub">INTELLIGENCE PLATFORM</div></div></div>
      <div className="workspace-label">WORKSPACE</div>
      <div className="workspace"><div className="workspace-avatar">AI</div><div className="workspace-copy"><strong>Project Advisor</strong><span>Milestone 1 workspace</span></div><ChevronRight size={15}/></div>
      <div className="nav-label">PLATFORM</div>
      <nav>{nav.map(item => <button key={item.label} className={`nav-item ${active===item.label?'active':''}`} onClick={()=>{setActive(item.label); if(item.label==='Knowledge Base') document.getElementById('knowledge')?.scrollIntoView({behavior:'smooth'}); else if(item.label==='Overview') window.scrollTo({top:0,behavior:'smooth'}); else document.getElementById(item.label==='Architecture'?'architecture':'scope')?.scrollIntoView({behavior:'smooth'})}}><item.icon size={18}/><span>{item.label}</span>{item.label==='Knowledge Base'&&<span className="nav-count">{stats.document_count}</span>}</button>)}</nav>
      <div className="sidebar-bottom"><div className="scope-mini"><ShieldCheck size={18}/><div><strong>Milestone 1 only</strong><span>Ingestion · RAG · Indexing</span></div></div><div className="user-row"><div className="user-avatar">PI</div><div className="user-meta"><strong>Internship Project</strong><span>Local development</span></div><CircleHelp size={17}/></div></div>
    </aside>
    <main className="main">
      <header className="topbar"><div className="crumb">Workspace <ChevronRight size={14}/> <strong>{active}</strong></div><div className="top-actions"><span className={`api-status ${health?'online':'offline'}`}><span className="status-dot"/>{health?'API connected':'API disconnected'}</span><button className="icon-button" title="Refresh data" onClick={refresh}><RefreshCw size={17}/></button><div className="top-avatar">PI</div></div></header>
      <div className="content">
        <div className="page-heading"><div><div className="eyebrow"><span className="eyebrow-dot"/> INTERNSHIP PROJECT / MILESTONE 01</div><h1>Project intelligence overview</h1><p className="subtitle">Turn scattered project documents into a searchable knowledge base.</p></div><button className="primary-button" onClick={()=>uploadRef.current?.click()} disabled={busy}><UploadCloud size={17}/>{busy?'Indexing documents…':'Upload documents'}</button><input ref={uploadRef} type="file" hidden multiple accept=".pdf,.docx,.csv,.txt" onChange={e=>upload(e.target.files)}/></div>

        {!health && <div className="banner error-banner"><AlertCircle size={18}/><div><strong>Backend not connected</strong><span>Start FastAPI in the backend folder. The UI will connect automatically when the API is available.</span></div></div>}
        {notice && <div className={`banner ${notice.type==='success'?'success-banner':notice.type==='warn'?'warn-banner':'error-banner'}`}><CheckCircle2 size={18}/><div><strong>{notice.text}</strong>{notice.details?.map((r,i)=><span key={i}>{r.filename}: {r.status==='indexed'?`${r.chunks_indexed} chunks indexed` : r.message}</span>)}</div><button className="dismiss" onClick={()=>setNotice(null)}><X size={16}/></button></div>}

        <div className="stat-grid">
          <Stat icon={Files} label="Documents indexed" value={fmt(stats.document_count)} note="Supported source files" color="blue"/>
          <Stat icon={Database} label="Vector chunks" value={fmt(stats.chunk_count)} note="Stored in ChromaDB" color="purple"/>
          <Stat icon={Activity} label="API status" value={health?'Operational':'Offline'} note={health?'FastAPI responding':'Waiting for backend'} color={health?'green':'orange'} small/>
          <Stat icon={ShieldCheck} label="Current milestone" value="01 / 04" note="Ingestion & RAG foundation" color="teal" small/>
        </div>

        <section className="panel upload-panel">
          <div className="section-heading"><div><h2>Build your project knowledge base</h2><p>Upload project artifacts to extract text, create embeddings, and index them for semantic retrieval.</p></div><span className="step-pill">STEP 01–04</span></div>
          <div className="dropzone" onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();upload(e.dataTransfer.files)}} onClick={()=>uploadRef.current?.click()}>
            <div className="upload-icon"><UploadCloud size={26}/></div><div className="drop-title">Drop your documents here, or <button type="button" className="text-link" onClick={e=>{e.stopPropagation();uploadRef.current?.click()}}>browse files</button></div><div className="drop-desc">Upload project proposals, specifications, notes, or task lists</div><div className="file-types"><span><FileText size={13}/> PDF</span><span><FileText size={13}/> DOCX</span><span><FileText size={13}/> CSV</span><span><FileText size={13}/> TXT</span></div>{busy&&<div className="processing"><LoaderCircle className="spin" size={15}/> Extracting, chunking, embedding and indexing…</div>}
          </div>
          <div className="pipeline">
            <PipelineStep n="01" title="Ingest" desc="Extract document text" active/>
            <div className="pipeline-line"/>
            <PipelineStep n="02" title="Chunk" desc="Split into text segments"/>
            <div className="pipeline-line"/>
            <PipelineStep n="03" title="Embed" desc="Generate vector embeddings"/>
            <div className="pipeline-line"/>
            <PipelineStep n="04" title="Index" desc="Persist in ChromaDB"/>
          </div>
        </section>

        <section className="panel" id="knowledge">
          <div className="section-heading"><div><h2>Knowledge base</h2><p>Manage indexed source files and test retrieval from their content.</p></div><button className="secondary-button" onClick={refresh}><RefreshCw size={15}/> Refresh</button></div>
          <form className="search-form" onSubmit={runSearch}><div className="search-input-wrap"><Search size={18}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search your documents, e.g. project deadlines or requirements…"/></div><button className="primary-button" type="submit" disabled={searching||query.trim().length<2}>{searching?<LoaderCircle className="spin" size={16}/>:<Search size={16}/>} Search</button></form>
          {results.length>0&&<div className="results-block"><div className="results-heading"><strong>Retrieval results</strong><span>{results.length} relevant chunk(s) · similarity distance shown by the API</span></div>{results.map((r,i)=><div className="result-card" key={r.id}><div className="result-top"><span className="result-number">0{i+1}</span><strong>{r.source}</strong><span className="chunk-tag">Chunk {r.chunk_index+1}</span></div><p>{r.text}</p></div>)}</div>}
          {results.length===0&&<div className="empty-search"><div className="empty-icon"><Search size={20}/></div><strong>Search indexed knowledge</strong><span>Ask about a project detail to retrieve matching passages from uploaded documents. This is retrieval, not AI-generated risk analysis.</span></div>}
          <div className="table-wrap"><table><thead><tr><th>SOURCE DOCUMENT</th><th>TYPE</th><th>INDEXED CHUNKS</th><th>STATUS</th><th></th></tr></thead><tbody>{docs.map(d=><tr key={d.id}><td><div className="doc-cell"><div className="doc-icon"><FileText size={17}/></div><div><strong>{d.name}</strong><span>Indexed in local knowledge base</span></div></div></td><td><span className="type-tag">{d.file_type.toUpperCase()}</span></td><td>{d.chunks}</td><td><span className="indexed-status"><span/>Indexed</span></td><td><button className="row-action" title="Remove document from index" onClick={()=>removeDoc(d)}><Trash2 size={15}/></button></td></tr>)}</tbody></table>{docs.length===0&&<div className="table-empty"><Files size={22}/><strong>No documents indexed yet</strong><span>Upload a PDF, DOCX, CSV, or TXT file to get started.</span></div>}</div>
        </section>

        <section className="bottom-grid" id="architecture">
          <div className="panel architecture-panel"><div className="section-heading"><div><h2>Milestone 1 architecture</h2><p>Implemented data flow</p></div><span className="small-icon"><Layers3 size={18}/></span></div><div className="architecture-flow"><ArchNode icon={Files} title="Source files" desc="PDF · DOCX · CSV · TXT"/><div className="flow-arrow"><ArrowUpRight size={16}/></div><ArchNode icon={FileText} title="Ingestion API" desc="Extract + normalize"/><div className="flow-arrow"><ArrowUpRight size={16}/></div><ArchNode icon={Sparkles} title="RAG preparation" desc="Chunk + embed"/><div className="flow-arrow"><ArrowUpRight size={16}/></div><ArchNode icon={Database} title="ChromaDB" desc="Persistent vectors"/></div><div className="architecture-foot"><CheckCircle2 size={15}/> Solid-line stages are implemented in this milestone.</div></div>
          <div className="panel scope-panel" id="scope"><div className="section-heading"><div><h2>Milestone scope</h2><p>Progress against the source brief</p></div></div><div className="scope-list"><ScopeRow done title="RAG & project-management study notes" tag="DOCUMENTED"/><ScopeRow done title="Architecture and data model" tag="DOCUMENTED"/><ScopeRow done title="Multi-format document ingestion" tag="IMPLEMENTED"/><ScopeRow done title="Chunking, embeddings & vector index" tag="IMPLEMENTED"/><ScopeRow title="Risk agents & delivery forecasting" tag="LATER MILESTONE"/><ScopeRow title="Health scoring & generated documents" tag="LATER MILESTONE"/></div></div>
        </section>
        <footer><div className="footer-brand"><div className="brand-mark tiny"><Activity size={15}/></div><strong>ProjectIQ</strong><span>Milestone 1 prototype</span></div><span>Local development · React + FastAPI + ChromaDB</span></footer>
      </div>
    </main>
  </div>
}

function Stat({icon:Icon,label,value,note,color,small}) { return <div className="stat-card"><div className={`stat-icon ${color}`}><Icon size={19}/></div><div className="stat-label">{label}</div><div className={`stat-value ${small?'smaller':''}`}>{value}</div><div className="stat-note">{note}</div></div> }
function PipelineStep({n,title,desc,active}) { return <div className={`pipeline-step ${active?'current':''}`}><div className="step-number">{n}</div><div><strong>{title}</strong><span>{desc}</span></div></div> }
function ArchNode({icon:Icon,title,desc}) { return <div className="arch-node"><div className="arch-icon"><Icon size={17}/></div><strong>{title}</strong><span>{desc}</span></div> }
function ScopeRow({done,title,tag}) { return <div className="scope-row"><span className={`scope-check ${done?'done':''}`}>{done?<CheckCircle2 size={16}/>:<div className="empty-circle"/>}</span><div className="scope-text"><strong>{title}</strong><span className={`scope-tag ${done?'tag-done':'tag-later'}`}>{tag}</span></div></div> }
