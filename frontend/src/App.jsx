import React, { useEffect, useRef, useState } from 'react'
import { Activity, ArrowUpRight, BookOpen, CheckCircle2, ChevronRight, CircleHelp, Database, FileText, Files, Gauge, Layers3, LoaderCircle, Search, ShieldCheck, UploadCloud, X, AlertCircle, RefreshCw, Trash2, Sparkles } from 'lucide-react'

// Use the Vite same-origin proxy so localhost/127.0.0.1 and LAN hostnames work consistently.
const API = '/api'
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
  const [agentData, setAgentData] = useState(null)
  const [agentBusy, setAgentBusy] = useState(false)
  const [m3Docs, setM3Docs] = useState(null)
  const [m3Health, setM3Health] = useState(null)
  const [m3Validation, setM3Validation] = useState(null)
  const [chatQuestion, setChatQuestion] = useState('')
  const [chatHistory, setChatHistory] = useState([])
  const [m3Busy, setM3Busy] = useState(false)
  const [m4Insights, setM4Insights] = useState(null)
  const [m4Busy, setM4Busy] = useState(false)
  const [active, setActive] = useState('Dashboard')
  const inputRef = useRef(null)
  const uploadRef = useRef(null)

  async function refresh({reloadInsights = false, preserveNotice = false} = {}) {
    // Check the lightweight API health endpoint separately. Listing documents may
    // initialize ChromaDB and download the embedding model on first run.
    try {
      const h = await fetch(`${API}/health`, {signal: AbortSignal.timeout(5000)})
      setHealth(h.ok)
    } catch { setHealth(false); return null }
    try {
      const d = await fetch(`${API}/documents`, {signal: AbortSignal.timeout(90000)})
      if (d.ok) {
        const data = await d.json()
        setDocs(data.documents || [])
        setStats(data)
        if (reloadInsights && (data.document_count || 0) > 0) {
          await loadM4Insights({preserveNotice})
        } else if (reloadInsights) {
          setM4Insights(null)
        }
        return data
      }
      setNotice({type:'error', text:`API is running, but document service returned HTTP ${d.status}. Check the backend terminal.`})
    } catch (err) {
      setNotice({type:'warn', text:`API is running, but the document index is still starting or unavailable. ${err.name === 'TimeoutError' ? 'First-time embedding model setup can take several minutes.' : 'Check the backend terminal for the error.'}`})
    }
    return null
  }
  useEffect(() => {
    refresh({reloadInsights:true})
    const t = setInterval(() => refresh(), 30000)
    return () => clearInterval(t)
  }, [])

  async function upload(files) {
    if (!files?.length) return
    setBusy(true); setNotice(null); setResults([])
    const form = new FormData()
    Array.from(files).forEach(f => form.append('files', f))
    try {
      const res = await fetch(`${API}/milestone4/documents/incremental-upload`, {method:'POST', body:form})
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Incremental upload failed')
      const indexed = (data.results || []).filter(r => r.status === 'indexed')
      const failed = (data.results || []).filter(r => r.status !== 'indexed')
      if (indexed.length > 0) {
        // New files are appended to the existing ChromaDB collection. Refresh the
        // inventory and rebuild project-wide insights from the complete corpus.
        setActive('Dashboard')
        await refresh({reloadInsights:true, preserveNotice:true})
        document.getElementById('dashboard')?.scrollIntoView({behavior:'smooth', block:'start'})
        setNotice({
          type: failed.length ? 'warn' : 'success',
          text:`${indexed.length} new document(s) added to the existing knowledge base. Dashboard insights refreshed using all indexed documents${failed.length ? ` · ${failed.length} file(s) could not be added` : ''}.`,
          details:data.results
        })
      } else {
        await refresh()
        setNotice({type:'warn', text:'No documents were added. Check the upload results below.', details:data.results})
      }
    } catch (err) {
      setNotice({type:'error', text:err.message || 'Cannot reach the API. Start the FastAPI backend on port 8000 and try again.'})
    }
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

  async function runAgents() {
    setAgentBusy(true); setNotice(null)
    try {
      const res = await fetch(`${API}/agents/analyze`, {method:'POST'})
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Agent analysis failed')
      setAgentData(data)
    } catch (err) { setNotice({type:'error', text:err.message || 'Agent analysis failed. Check the backend.'}) }
    finally { setAgentBusy(false) }
  }

  async function loadM3(endpoint, setter) {
    setM3Busy(true); setNotice(null)
    try { const res=await fetch(`${API}/milestone3/${endpoint}`); const data=await res.json(); if(!res.ok) throw new Error(data.detail||'Milestone 3 request failed'); setter(data) }
    catch(err) { setNotice({type:'error',text:err.message}) } finally { setM3Busy(false) }
  }
  async function loadM4Insights({preserveNotice = false} = {}) {
    setM4Busy(true); if (!preserveNotice) setNotice(null)
    try {
      const res = await fetch(`${API}/milestone4/insights`)
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Could not load Milestone 4 insights')
      setM4Insights(data)
    } catch (err) { setNotice({type:'error', text:err.message}) }
    finally { setM4Busy(false) }
  }
  async function askProject(e) {
    e?.preventDefault(); if(!chatQuestion.trim()) return
    const question=chatQuestion.trim(); const prior=chatHistory
    setChatHistory(h=>[...h,{role:'user',content:question}]); setChatQuestion(''); setM3Busy(true)
    try { const res=await fetch(`${API}/milestone3/chat`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question,history:prior})}); const data=await res.json(); if(!res.ok) throw new Error(data.detail||'Assistant request failed'); setChatHistory(h=>[...h,{role:'assistant',content:data.answer,sources:data.sources,mode:data.mode}]) }
    catch(err) { setChatHistory(h=>[...h,{role:'assistant',content:`Error: ${err.message}`}]) } finally { setM3Busy(false) }
  }
  async function downloadPDF(data, filename, title) {
    try {
      const res = await fetch(`${API}/reports/pdf`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({title, data})
      })
      if (!res.ok) {
        let message = 'Could not generate PDF report'
        try { const detail = await res.json(); message = detail.detail || message } catch {}
        throw new Error(message)
      }
      const contentType = res.headers.get('content-type') || ''
      if (!contentType.toLowerCase().includes('application/pdf'))
        throw new Error('The report service did not return a PDF file.')
      const blob = await res.blob()
      if (blob.size < 8 || (await blob.slice(0, 5).text()) !== '%PDF-')
        throw new Error('The generated file is not a valid PDF document.')
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename.endsWith('.pdf') ? filename : `${filename}.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.setTimeout(() => URL.revokeObjectURL(url), 1000)
      setNotice({type:'success', text:`PDF report downloaded: ${a.download}`})
    } catch (err) {
      setNotice({type:'error', text:err.message || 'PDF download failed. Check that the backend is running.'})
    }
  }

  async function removeDoc(doc) {
    if (!confirm(`Remove "${doc.name}" and its indexed chunks?`)) return
    try {
      const res = await fetch(`${API}/documents/${doc.id}`, {method:'DELETE'})
      if (!res.ok) throw new Error((await res.json()).detail || 'Could not remove document')
      setNotice({type:'success', text:`Removed ${doc.name} from the vector index.`}); await refresh()
    } catch (err) { setNotice({type:'error', text:err.message}) }
  }

  const navGroups = [
    {title:'WORKSPACE', items:[
      {label:'Dashboard', icon:Gauge, target:'dashboard'},
      {label:'Documents', icon:Files, target:'knowledge'},
      {label:'Document Upload', icon:UploadCloud, target:'document-upload'},
    ]},
    {title:'PROJECT INTELLIGENCE', items:[
      {label:'Scope & Deliverables', icon:BookOpen, target:'scope-deliverables'},
      {label:'Risk Intelligence', icon:AlertCircle, target:'risk-intelligence'},
      {label:'Blockers & Actions', icon:CheckCircle2, target:'blockers-actions'},
      {label:'Documentation Generation', icon:FileText, target:'documentation-generation'},
      {label:'Project Health', icon:Activity, target:'project-health'},
      {label:'Project Assistant', icon:Sparkles, target:'project-assistant'},
    ]},
    {title:'SYSTEM', items:[
      {label:'Backend Health', icon:Activity, target:'backend-health'},
      {label:'System Status', icon:ShieldCheck, target:'system-status'},
    ]}
  ]
  const goTo = (label,target) => {
    setActive(label)
    if (target === 'document-upload') document.getElementById('document-upload')?.scrollIntoView({behavior:'smooth'})
    else if (target === 'backend-health' || target === 'system-status') document.getElementById('backend-health')?.scrollIntoView({behavior:'smooth'})
    else if (target === 'scope-deliverables') document.getElementById('scope-deliverables')?.scrollIntoView({behavior:'smooth'})
    else if (target === 'risk-intelligence') document.getElementById('risk-intelligence')?.scrollIntoView({behavior:'smooth'})
    else if (target === 'blockers-actions') document.getElementById('blockers-actions')?.scrollIntoView({behavior:'smooth'})
    else if (target === 'documentation-generation') document.getElementById('documentation-generation')?.scrollIntoView({behavior:'smooth'})
    else if (target === 'project-health') document.getElementById('project-health')?.scrollIntoView({behavior:'smooth'})
    else if (target === 'project-assistant') document.getElementById('project-assistant')?.scrollIntoView({behavior:'smooth'})
    else if (target === 'dashboard') document.getElementById('dashboard')?.scrollIntoView({behavior:'smooth'})
    else document.getElementById(target)?.scrollIntoView({behavior:'smooth'})
  }
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><Activity size={22}/></div><div><div className="brand-title">Project<span>IQ</span></div><div className="brand-sub">INTELLIGENCE PLATFORM</div></div></div>
      <div className="workspace-label">WORKSPACE</div>
      <div className="workspace"><div className="workspace-avatar">AI</div><div className="workspace-copy"><strong>Project Advisor</strong><span>Unified project workspace</span></div><ChevronRight size={15}/></div>
      <nav className="sidebar-navigation">{navGroups.map(group=><div className="nav-group" key={group.title}><div className="nav-label">{group.title}</div>{group.items.map(item=><button key={item.label} className={`nav-item ${active===item.label?'active':''}`} onClick={()=>goTo(item.label,item.target)}><item.icon size={17}/><span>{item.label}</span>{item.label==='Documents'&&<span className="nav-count">{stats.document_count}</span>}</button>)}</div>)}</nav>
      <div className="sidebar-bottom"><div className="scope-mini"><ShieldCheck size={18}/><div><strong>Project intelligence</strong><span>Documents · Insights · Actions</span></div></div><div className="user-row"><div className="user-avatar">PI</div><div className="user-meta"><strong>Internship Project</strong><span>Local development</span></div><CircleHelp size={17}/></div></div>
    </aside>
    <main className="main">
      <header className="topbar" id="backend-health"><div className="crumb">Workspace <ChevronRight size={14}/> <strong>{active}</strong></div><div className="top-actions" id="system-status"><span className={`api-status ${health?'online':'offline'}`}><span className="status-dot"/>{health?'API connected':'API disconnected'}</span><button className="icon-button" title="Refresh data" onClick={refresh}><RefreshCw size={17}/></button><div className="top-avatar">PI</div></div></header>
      <div className="content" id="overview">
        <div className="page-heading"><div><div className="eyebrow"><span className="eyebrow-dot"/> AI PROJECT INTELLIGENCE / WORKSPACE</div><h1>Project Dashboard</h1><p className="subtitle">A unified, evidence-backed view of project health, scope, risks, blockers and delivery actions.</p></div><button className="primary-button" onClick={()=>goTo('Document Upload','document-upload')}><UploadCloud size={17}/>Go to document upload</button></div>

        {!health && <div className="banner error-banner"><AlertCircle size={18}/><div><strong>Backend not connected</strong><span>Start FastAPI in the backend folder. The UI will connect automatically when the API is available.</span></div></div>}
        {notice && <div className={`banner ${notice.type==='success'?'success-banner':notice.type==='warn'?'warn-banner':'error-banner'}`}><CheckCircle2 size={18}/><div><strong>{notice.text}</strong>{notice.details?.map((r,i)=><span key={i}>{r.filename}: {r.status==='indexed'?`${r.chunks_indexed} chunks indexed` : r.message}</span>)}</div><button className="dismiss" onClick={()=>setNotice(null)}><X size={16}/></button></div>}

        <section className="panel milestone4-panel" id="dashboard">
          <div className="section-heading"><div><div className="eyebrow"><span className="eyebrow-dot"/> CENTRALIZED PROJECT INTELLIGENCE</div><h2>Project health & delivery insights</h2><p>Consolidated outputs from document ingestion, project intelligence agents and project-level analysis.</p></div><button className="primary-button" onClick={loadM4Insights} disabled={m4Busy||!stats.document_count}>{m4Busy?<LoaderCircle className="spin" size={16}/>:<RefreshCw size={16}/>} {m4Busy?'Refreshing…':'Refresh insights'}</button></div>
          {!m4Insights && <div className="agent-empty"><Activity size={19}/><strong>Your project dashboard is ready</strong><span>Start by adding project documents to build the knowledge base and generate project insights.</span><button className="secondary-button" onClick={()=>goTo('Document Upload','document-upload')}>Upload project documents</button></div>}
          {m4Insights && <>
            <div className="m4-metrics">
              <button className="m4-metric metric-button" onClick={()=>goTo('Project Health','project-health')}><span>PROJECT HEALTH</span><strong>{m4Insights.project_health.overall_score ?? '—'}<small>/100</small></strong><em>{m4Insights.project_health.status || 'Not available'}</em></button>
              <button className="m4-metric metric-button" onClick={()=>goTo('Scope & Deliverables','scope-deliverables')}><span>SCOPE ITEMS</span><strong>{m4Insights.counts.scope_items}</strong><em>Extracted statements</em></button>
              <button className="m4-metric metric-button" onClick={()=>goTo('Risk Intelligence','risk-intelligence')}><span>IDENTIFIED RISKS</span><strong>{m4Insights.counts.risks}</strong><em>{m4Insights.risks.filter(x=>(x.severity||'').toLowerCase()==='high').length} high priority</em></button>
              <button className="m4-metric metric-button" onClick={()=>goTo('Blockers & Actions','blockers-actions')}><span>BLOCKERS</span><strong>{m4Insights.counts.blockers ?? m4Insights.project_health.evidence_summary?.blockers ?? '—'}</strong><em>Open blocker items</em></button>
              <button className="m4-metric metric-button" onClick={()=>goTo('Blockers & Actions','blockers-actions')}><span>ACTION ITEMS</span><strong>{m4Insights.counts.action_items}</strong><em>{m4Insights.action_items.filter(x=>(x.status||'').toLowerCase()==='open').length} marked open</em></button>
            </div>
            <div className="m4-grid">

              <div className="m4-card" id="scope-deliverables"><div className="m3-card-head"><BookOpen size={18}/><strong>Scope summary</strong></div>{m4Insights.scope_summary.length ? m4Insights.scope_summary.map((x,i)=><div className="m4-line" key={i}><p>{x.summary}</p><small>{x.sources?.map(src=>`${src.source} · chunk ${src.chunk_index}`).join(' | ') || 'Source reference unavailable'}</small></div>) : <p className="no-findings">No scope statements detected in indexed documents.</p>}</div>
              <div className="m4-card" id="risk-intelligence"><div className="m3-card-head"><AlertCircle size={18}/><strong>Extracted risk summary</strong></div>{m4Insights.risks.length ? m4Insights.risks.map((x,i)=><div className="m4-line" key={i}><div className="m4-line-title"><strong>{x.severity || 'Severity not specified'}</strong><span>{x.risk_description}</span></div><small>Likelihood: {x.likelihood} · Impact: {x.impact} · Status: {x.status || 'Not specified'} · {x.sources?.map(src=>src.source).join(', ')}</small></div>) : <p className="no-findings">No matching risk statements detected. This does not guarantee the project is risk-free.</p>}</div>
              <div className="m4-card" id="blockers-actions"><div className="m3-card-head"><CheckCircle2 size={18}/><strong>Blockers & action items</strong></div><div className="m4-subsection"><strong>Open blockers ({m4Insights.counts.blockers ?? 0})</strong>{(m4Insights.blockers || []).length ? m4Insights.blockers.map((x,i)=><div className="m4-line" key={`b-${i}`}><p>{x.task}</p><small>Owner: {x.responsible_person} · Due: {x.due_date} · Status: {x.status}</small><small>{x.sources?.map(src=>src.source).join(', ')}</small></div>) : <p className="no-findings">No items explicitly marked as open blockers.</p>}</div><div className="m4-subsection"><strong>Action items ({m4Insights.counts.action_items})</strong>{m4Insights.action_items.length ? m4Insights.action_items.map((x,i)=><div className="m4-line" key={`a-${i}`}><p>{x.task}</p><small>Owner: {x.responsible_person} · Due: {x.due_date} · Status: {x.status}</small><small>{x.sources?.map(src=>src.source).join(', ')}</small></div>) : <p className="no-findings">No action items detected in indexed documents.</p>}</div></div>
                            <div className="m4-card"><div className="m3-card-head"><Activity size={18}/><strong>Recent project insights</strong></div>{[...m4Insights.risks.slice(0,3).map(x=>({kind:'Risk',text:x.risk_description,source:x.sources?.[0]?.source})),...m4Insights.blockers.slice(0,2).map(x=>({kind:'Blocker',text:x.task,source:x.sources?.[0]?.source})),...m4Insights.action_items.slice(0,2).map(x=>({kind:'Action',text:x.task,source:x.sources?.[0]?.source}))].slice(0,5).map((x,i)=><div className="m4-line" key={i}><div className="m4-line-title"><strong>{x.kind}</strong><span>{x.text}</span></div><small>Source: {x.source || 'Reference unavailable'}</small></div>)}{!m4Insights.risks.length&&!m4Insights.action_items.length&&<p className="no-findings">No recent risk or action findings were extracted from indexed documents.</p>}</div>
            </div>
            <div className="m4-export"><span>Updated {new Date(m4Insights.generated_at).toLocaleString()} · {m4Insights.counts.documents_scanned} documents · {m4Insights.counts.chunks_scanned} chunks</span><button className="secondary-button" onClick={()=>downloadPDF(m4Insights,'project-insights-report.pdf','Project Insights Report')}>Download insights report</button></div>
            <p className="m3-note">{m4Insights.source_notice} Health score is a transparent heuristic signal, not a certified audit or delivery guarantee.</p>
          </>}
        </section>

        <section className="panel upload-panel" id="document-upload">
          <div className="section-heading"><div><div className="eyebrow"><span className="eyebrow-dot"/> WORKSPACE</div><h2>Build your project knowledge base</h2><p>Upload project artifacts to extract text, create embeddings, and index them for semantic retrieval.</p></div><span className="step-pill">STEP 01–04</span></div>
          <div className="stat-grid upload-stats">
            <Stat icon={Files} label="Documents indexed" value={fmt(stats.document_count)} note="Supported source files" color="blue"/>
            <Stat icon={Database} label="Vector chunks" value={fmt(stats.chunk_count)} note="Stored in ChromaDB" color="purple"/>
            <Stat icon={Activity} label="API status" value={health?'Operational':'Offline'} note={health?'FastAPI responding':'Waiting for backend'} color={health?'green':'orange'} small/>
            <Stat icon={ShieldCheck} label="Current milestone" value="04 / 04" note="Project intelligence suite" color="teal" small/>
          </div>
          <input ref={uploadRef} type="file" hidden multiple accept=".pdf,.docx,.csv,.txt" onChange={e=>upload(e.target.files)}/>
          <div className="dropzone" onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();upload(e.dataTransfer.files)}} onClick={()=>uploadRef.current?.click()}>
            <div className="upload-icon"><UploadCloud size={26}/></div><div className="drop-title">Drop your documents here, or <button type="button" className="text-link" onClick={e=>{e.stopPropagation();uploadRef.current?.click()}}>browse files</button></div><div className="drop-desc">Upload project proposals, specifications, notes, or task lists</div><div className="file-types"><span><FileText size={13}/> PDF</span><span><FileText size={13}/> DOCX</span><span><FileText size={13}/> CSV</span><span><FileText size={13}/> TXT</span></div>{busy&&<div className="processing"><LoaderCircle className="spin" size={15}/> Extracting, chunking, embedding and indexing…</div>}
          </div>
          <div className="pipeline">
            <PipelineStep n="01" title="Ingest" desc="Extract document text" active/><div className="pipeline-line"/><PipelineStep n="02" title="Chunk" desc="Split into text segments"/><div className="pipeline-line"/><PipelineStep n="03" title="Embed" desc="Generate vector embeddings"/><div className="pipeline-line"/><PipelineStep n="04" title="Index" desc="Persist in ChromaDB"/>
          </div>
        </section>

        <section className="panel" id="knowledge">
          <div className="section-heading"><div><h2>Knowledge base</h2><p>Manage indexed source files and test retrieval from their content.</p></div><button className="secondary-button" onClick={refresh}><RefreshCw size={15}/> Refresh</button></div>
          <form className="search-form" id="semantic-search" onSubmit={runSearch}><div className="search-input-wrap"><Search size={18}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search your documents, e.g. project deadlines or requirements…"/></div><button className="primary-button" type="submit" disabled={searching||query.trim().length<2}>{searching?<LoaderCircle className="spin" size={16}/>:<Search size={16}/>} Search</button></form>
          {results.length>0&&<div className="results-block"><div className="results-heading"><strong>Retrieval results</strong><span>{results.length} relevant chunk(s) · similarity distance shown by the API</span></div>{results.map((r,i)=><div className="result-card" key={r.id}><div className="result-top"><span className="result-number">0{i+1}</span><strong>{r.source}</strong><span className="chunk-tag">Chunk {r.chunk_index+1}</span></div><p>{r.text}</p></div>)}</div>}
          {results.length===0&&<div className="empty-search"><div className="empty-icon"><Search size={20}/></div><strong>Search indexed knowledge</strong><span>Ask about a project detail to retrieve matching passages from uploaded documents. This is retrieval, not AI-generated risk analysis.</span></div>}
          <div className="table-wrap"><table><thead><tr><th>SOURCE DOCUMENT</th><th>TYPE</th><th>INDEXED CHUNKS</th><th>STATUS</th><th></th></tr></thead><tbody>{docs.map(d=><tr key={d.id}><td><div className="doc-cell"><div className="doc-icon"><FileText size={17}/></div><div><strong>{d.name}</strong><span>Indexed in local knowledge base</span></div></div></td><td><span className="type-tag">{d.file_type.toUpperCase()}</span></td><td>{d.chunks}</td><td><span className="indexed-status"><span/>Indexed</span></td><td><button className="row-action" title="Remove document from index" onClick={()=>removeDoc(d)}><Trash2 size={15}/></button></td></tr>)}</tbody></table>{docs.length===0&&<div className="table-empty"><Files size={22}/><strong>No documents indexed yet</strong><span>Upload a PDF, DOCX, CSV, or TXT file to get started.</span></div>}</div>
        </section>

        

        <section className="panel milestone3-panel" id="documentation-generation">
          <div className="section-heading"><div><div className="eyebrow"><span className="eyebrow-dot"/> PROJECT INTELLIGENCE</div><h2>Documentation Generation</h2><p>Generate project documentation from the currently indexed documents, with source traceability.</p></div><span className="step-pill">DOCUMENTATION</span></div>
          <div className="m3-grid">
            <div className="m3-card" style={{gridColumn:'1 / -1'}}><div className="m3-card-head"><FileText size={18}/><strong>Project Documentation</strong></div><p>User stories, evidence-backed risk register and action items. Missing fields remain “Not specified”.</p><button className="secondary-button" disabled={m3Busy||!stats.document_count} onClick={()=>loadM3('documentation',setM3Docs)}>Generate documentation</button>{m3Docs&&<><div className="m3-counts"><span>{m3Docs.user_stories.length} stories</span><span>{m3Docs.risk_register.length} risks</span><span>{m3Docs.action_items.length} actions</span><span>{m3Docs.potential_conflicts?.length||0} conflicts</span></div><button className="text-link m3-download" onClick={()=>downloadPDF(m3Docs,'project-documentation.pdf','Project Documentation Report')}>Download PDF documentation</button><M3List title="User stories" items={m3Docs.user_stories} field="description"/><M3List title="Risk register" items={m3Docs.risk_register} field="risk_description"/><M3List title="Action items" items={m3Docs.action_items} field="task"/><M3Conflicts items={m3Docs.potential_conflicts}/></>}</div>
          </div>
        </section>

        <section className="panel milestone3-panel" id="project-health">
          <div className="section-heading"><div><div className="eyebrow"><span className="eyebrow-dot"/> PROJECT INTELLIGENCE</div><h2>Project Health</h2><p>One consolidated view of the overall score, five health dimensions, evidence and scoring methodology.</p></div><span className="step-pill">HEALTH ANALYSIS</span></div>
          <div className="health-overview-grid">
            <div className="m3-card health-overall-card"><div className="m3-card-head"><Activity size={18}/><strong>Overall Project Health</strong></div>
              <div className="health-score"><strong>{(m3Health||m4Insights?.project_health)?.overall_score ?? '—'}</strong><span>/ 100 · {(m3Health||m4Insights?.project_health)?.status || 'Awaiting calculation'}</span></div>
              <p>Calculated by the existing backend health-scoring logic from the indexed project evidence.</p>
              <button className="secondary-button" disabled={m3Busy||!stats.document_count} onClick={()=>loadM3('health-score',setM3Health)}>{m3Busy?'Calculating…':'Calculate health score'}</button>
              {(m3Health||m4Insights?.project_health)?.recommendations?.length>0&&<div className="health-recommendations"><strong>Recommended attention</strong>{(m3Health||m4Insights.project_health).recommendations.map((r,i)=><p key={i}>{r.recommendation}</p>)}</div>}
            </div>
            <div className="m3-card health-radar-card"><div className="m3-card-head"><Gauge size={18}/><strong>Project Health Radar</strong></div>
              <RadarChart dimensions={dashboardDimensions((m3Health||m4Insights?.project_health)?.dimensions || {})} overallScore={(m3Health||m4Insights?.project_health)?.overall_score} />
              <div className="radar-legend"><span><i className="legend-blue"/>Schedule</span><span><i className="legend-amber"/>Risk</span><span><i className="legend-teal"/>Scope</span><span><i className="legend-red"/>Blockers</span><span><i className="legend-purple"/>Quality</span></div>
              <p className="radar-caption">Quality uses the existing deliverable-progress evidence score as a proxy; no separate quality calculation is introduced.</p>
            </div>
          </div>
          <div className="m3-card health-detail-card"><div className="m3-card-head"><Activity size={18}/><strong>Detailed Health Calculation & Evidence</strong></div>
            <p>Individual scores, evidence explanations and the existing scoring methodology.</p>
            {(m3Health||m4Insights?.project_health)?.dimensions ? Object.entries((m3Health||m4Insights.project_health).dimensions).map(([k,v])=><div className="dimension" key={k}><div><span>{k.replaceAll('_',' ')}</span><strong>{v.score}/100</strong></div><div className="score-track"><i style={{width:`${v.score}%`}}/></div><small>{v.reason}</small></div>) : <div className="agent-empty"><Activity size={19}/><strong>Health analysis is ready</strong><span>Upload project documents and calculate the score to view dimension-level evidence.</span></div>}
            {(m3Health||m4Insights?.project_health)?.scoring_method&&<p className="m3-note">{(m3Health||m4Insights.project_health).scoring_method}</p>}
            {(m3Health||m4Insights?.project_health)&&<button className="text-link m3-download" onClick={()=>downloadPDF(m3Health||m4Insights.project_health,'project-health-score.pdf','Project Health Score Report')}>Download health report</button>}
          </div>
        </section>

        <section className="panel milestone3-panel" id="project-assistant">
          <div className="section-heading"><div><div className="eyebrow"><span className="eyebrow-dot"/> PROJECT INTELLIGENCE</div><h2>Project Assistant</h2><p>Ask questions about the complete project. Answers use retrieved project evidence and source references.</p></div><span className="step-pill">RAG ASSISTANT</span></div>
          <div className="m3-grid"><div className="m3-card m3-chat-card"><div className="m3-card-head"><Sparkles size={18}/><strong>Conversational Project Assistant</strong></div><p>Relevant ChromaDB passages are retrieved first and returned with source references.</p><div className="chat-history">{chatHistory.length===0&&<div className="chat-empty">Try: “What are our biggest project risks?” or “Who owns pending tasks?”</div>}{chatHistory.map((m,i)=><div className={`chat-message ${m.role}`} key={i}><strong>{m.role==='user'?'You':'Project Assistant'}</strong><p>{m.content}</p>{m.sources?.length>0&&<div className="chat-sources">{m.sources.slice(0,5).map((src,j)=><span key={j}>{src.source} · chunk {src.chunk_index}</span>)}</div>}</div>)}</div><form className="chat-form" onSubmit={askProject}><input value={chatQuestion} onChange={e=>setChatQuestion(e.target.value)} placeholder="Ask about risks, milestones, blockers…"/><button className="primary-button" disabled={m3Busy||chatQuestion.trim().length<2}>Ask</button></form><div className="m3-note">Without OPENAI_API_KEY, the assistant returns retrieved evidence passages only; it will not fabricate a generated answer.</div></div></div>
        </section>

        <section className="panel milestone3-panel" id="rag-validation">
          <div className="section-heading"><div><div className="eyebrow"><span className="eyebrow-dot"/> SYSTEM VALIDATION</div><h2>RAG Validation</h2><p>Validate retrieval coverage, multi-document evidence and potentially unavailable facts.</p></div><span className="step-pill">VALIDATION</span></div>
          <div className="m3-card"><div className="m3-card-head"><CheckCircle2 size={18}/><strong>RAG Validation Results</strong></div><p>Corpus-based retrieval checks for explicit facts, cross-document coverage and potentially unavailable facts.</p><button className="secondary-button" disabled={m3Busy||!stats.document_count} onClick={()=>loadM3('validation',setM3Validation)}>Run validation checks</button>{m3Validation&&<><div className="m3-counts"><span>{m3Validation.summary.pass} pass</span><span>{m3Validation.summary.review} review</span><span>{m3Validation.summary.total} total</span></div>{m3Validation.cases.map((c,i)=><div className="validation-case" key={i}><div><strong>{c.category}</strong><span className={c.status==='PASS'?'pass':'review'}>{c.status}</span></div><p>{c.question}</p><small>Expected: {c.expected_answer}</small><small>Actual: {c.actual_answer}</small><small>Sources: {c.sources.join(', ')||'None retrieved'}</small></div>)}<p className="m3-note">{m3Validation.limitations}</p><button className="text-link m3-download" onClick={()=>downloadPDF(m3Validation,'rag-validation-results.pdf','RAG Validation Report')}>Download validation report</button></>}</div>
        </section>

        <section className="bottom-grid" id="architecture">
          <div className="panel architecture-panel"><div className="section-heading"><div><h2>Milestone 1 architecture</h2><p>Implemented data flow</p></div><span className="small-icon"><Layers3 size={18}/></span></div><div className="architecture-flow"><ArchNode icon={Files} title="Source files" desc="PDF · DOCX · CSV · TXT"/><div className="flow-arrow"><ArrowUpRight size={16}/></div><ArchNode icon={FileText} title="Ingestion API" desc="Extract + normalize"/><div className="flow-arrow"><ArrowUpRight size={16}/></div><ArchNode icon={Sparkles} title="RAG preparation" desc="Chunk + embed"/><div className="flow-arrow"><ArrowUpRight size={16}/></div><ArchNode icon={Database} title="ChromaDB" desc="Persistent vectors"/></div><div className="architecture-foot"><CheckCircle2 size={15}/> Solid-line stages are implemented in this milestone.</div></div>
          <div className="panel scope-panel" id="scope"><div className="section-heading"><div><h2>Milestone scope</h2><p>Progress against the source brief</p></div></div><div className="scope-list"><ScopeRow done title="RAG & project-management study notes" tag="DOCUMENTED"/><ScopeRow done title="Architecture and data model" tag="DOCUMENTED"/><ScopeRow done title="Multi-format document ingestion" tag="IMPLEMENTED"/><ScopeRow done title="Chunking, embeddings & vector index" tag="IMPLEMENTED"/><ScopeRow done title="Risk agents & delivery forecasting" tag="IMPLEMENTED"/><ScopeRow done title="Health scoring & generated documents" tag="IMPLEMENTED"/></div></div>
        </section>
        <footer><div className="footer-brand"><div className="brand-mark tiny"><Activity size={15}/></div><strong>ProjectIQ</strong><span>Milestones 1–4 integrated</span></div><span>Local development · React + FastAPI + ChromaDB</span></footer>
      </div>
    </main>
  </div>
}


function dashboardDimensions(source={}) {
  // These are aliases over the existing Milestone 3 API scores, not new calculations.
  const mappings = [
    ['Schedule','timeline_schedule_risk','Schedule risk evidence score.'],
    ['Risk','dependency_status','Dependency-related risk evidence score.'],
    ['Scope','scope_clarity','Scope clarity evidence score.'],
    ['Blockers','blocker_count_severity','Blocker count/severity evidence score.'],
    ['Quality','deliverable_progress','Deliverable-progress evidence proxy; a separate quality score is not calculated by the current backend.'],
  ]
  return Object.fromEntries(mappings.filter(([,key])=>source[key]).map(([label,key,note])=>[label,{...source[key],reason:label==='Quality'?`${note} ${source[key].reason||''}`:source[key].reason}]))
}

function RadarChart({dimensions={},overallScore,onSelect=()=>{}}) {
  const entries = Object.entries(dimensions)
  if (entries.length !== 5) return <div className="radar-empty">The five-dimension chart will appear when all five health scores are available from the project-health API.</div>
  const cx=160, cy=145, radius=102, n=5
  const point=(r,i)=>{const a=(-Math.PI/2)+(2*Math.PI*i/n);return [cx+Math.cos(a)*r,cy+Math.sin(a)*r]}
  const polygon=(r)=>entries.map((_,i)=>point(r,i).join(',')).join(' ')
  const values=entries.map(([,v])=>Math.max(0,Math.min(100,Number(v.score)||0)))
  const data=values.map((v,i)=>point(radius*v/100,i).join(',')).join(' ')
  return <div className="radar-wrap"><svg className="radar-svg" viewBox="0 0 320 300" role="img" aria-label="Radar chart of Schedule, Risk, Scope, Blockers and Quality project health dimensions">
    {[25,50,75,100].map(v=><polygon key={v} points={polygon(radius*v/100)} className="radar-grid"/>)}
    {entries.map(([key],i)=>{const [x,y]=point(radius,i);const [lx,ly]=point(radius+25,i);return <g key={key} className="radar-axis-group" onClick={()=>onSelect(key)}><line x1={cx} y1={cy} x2={x} y2={y} className="radar-axis"/><text x={lx} y={ly} className="radar-label" textAnchor={lx<cx-10?'end':lx>cx+10?'start':'middle'} dominantBaseline="middle">{key}</text></g>})}
    <polygon points={data} className="radar-area"/>{values.map((v,i)=>{const [x,y]=point(radius*v/100,i);return <circle key={i} cx={x} cy={y} r="4.5" className={`radar-point radar-point-${i}`}/>})}
    <text x={cx} y={cy-5} textAnchor="middle" className="radar-score">{overallScore ?? '—'}</text><text x={cx} y={cy+12} textAnchor="middle" className="radar-score-label">API SCORE AVG</text>
  </svg></div>
}

function Stat({icon:Icon,label,value,note,color,small}) { return <div className="stat-card"><div className={`stat-icon ${color}`}><Icon size={19}/></div><div className="stat-label">{label}</div><div className={`stat-value ${small?'smaller':''}`}>{value}</div><div className="stat-note">{note}</div></div> }
function PipelineStep({n,title,desc,active}) { return <div className={`pipeline-step ${active?'current':''}`}><div className="step-number">{n}</div><div><strong>{title}</strong><span>{desc}</span></div></div> }
function ArchNode({icon:Icon,title,desc}) { return <div className="arch-node"><div className="arch-icon"><Icon size={17}/></div><strong>{title}</strong><span>{desc}</span></div> }
function AgentResult({title,items,empty}) { return <div className="agent-result"><div className="agent-result-heading"><strong>{title}</strong><span>{items?.length || 0} finding(s)</span></div>{items?.length ? items.map((item,i)=><div className="finding" key={`${item.source}-${item.chunk_index}-${i}`}><div className="finding-meta"><span>{item.source}</span><span>Chunk {item.chunk_index}</span>{item.severity&&<span className={`severity ${item.severity==='Review'?'severity-review':'severity-watch'}`}>{item.severity}</span>}</div><p>{item.evidence}</p></div>) : <p className="no-findings">{empty}</p>}</div> }
function ScopeRow({done,title,tag}) { return <div className="scope-row"><span className={`scope-check ${done?'done':''}`}>{done?<CheckCircle2 size={16}/>:<div className="empty-circle"/>}</span><div className="scope-text"><strong>{title}</strong><span className={`scope-tag ${done?'tag-done':'tag-later'}`}>{tag}</span></div></div> }

function M3List({title,items,field}) { return <details className="m3-list"><summary>{title} ({items?.length||0})</summary>{items?.slice(0,20).map((x,i)=><div className="m3-item" key={i}><p>{x[field]}</p><small>{x.sources?.map(s=>`${s.source} · chunk ${s.chunk_index}`).join(' | ')}</small>{x.responsible_person&&<small>Owner: {x.responsible_person} · Due: {x.due_date} · Status: {x.status}</small>}{x.severity&&<small>Severity: {x.severity} · Likelihood: {x.likelihood} · Impact: {x.impact}</small>}</div>)}</details> }

function M3Conflicts({items=[]}) { return <details className="m3-list"><summary>Potential conflicting statements ({items.length})</summary>{items.map((x,i)=><div className="m3-item" key={i}><p><strong>Topic:</strong> {x.topic}</p><p><strong>Statement A:</strong> {x.statement_a}</p><small>{x.sources_a?.map(s=>s.source).join(', ')}</small><p><strong>Statement B:</strong> {x.statement_b}</p><small>{x.sources_b?.map(s=>s.source).join(', ')}</small><small>{x.resolution}</small></div>)}</details> }
