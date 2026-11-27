"""Milestone 3 project-level documentation, health scoring and grounded RAG.

All deterministic outputs are extracted from indexed evidence. Optional OpenAI
answer synthesis is enabled only when OPENAI_API_KEY is configured.
"""
import os, re, json, urllib.request
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass
from collections import defaultdict
from .store import get_collection, search, list_documents

RISK = re.compile(r'\b(risk|delay(?:ed)?|blocked|blocker|overdue|dependency|dependenc(?:y|ies)|issue|challenge|at risk|pending|unresolved|slippage)\b', re.I)
ACTION = re.compile(r'\b(action item|follow[- ]?up|assigned to|owner:|responsible:|will (?:complete|deliver|send|review|fix|update)|must (?:complete|deliver|send|review|fix|update)|todo|to-do)\b', re.I)
SCOPE = re.compile(r'\b(requirement|objective|goal|scope|deliverable|milestone|feature|must support|shall)\b', re.I)
BLOCK = re.compile(r'\b(blocked|blocker|unresolved|awaiting|waiting for|decision needed|pending approval|not decided|overdue)\b', re.I)

def records():
    c=get_collection(); data=c.get(include=['documents','metadatas'])
    grouped=defaultdict(list)
    for chunk,meta in zip(data.get('documents') or [], data.get('metadatas') or []):
        meta=meta or {}; grouped[meta.get('source','Unknown')].append((chunk,meta))
    out=[]
    for source, chunks in grouped.items():
        for chunk,meta in chunks:
            for s in re.split(r'(?<=[.!?])\s+|\n+', chunk):
                s=' '.join(s.split()).strip(' -•|')
                if len(s)>=18:
                    out.append({'text':s,'source':source,'chunk_index':int(meta.get('chunk_index',0))+1})
    # exact sentence dedup across project docs while preserving all citations
    merged={}
    for r in out:
        k=r['text'].lower()
        if k not in merged: merged[k]={'text':r['text'],'sources':[]}
        ref={'source':r['source'],'chunk_index':r['chunk_index']}
        if ref not in merged[k]['sources']: merged[k]['sources'].append(ref)
    return list(merged.values()), len(grouped), sum(len(v) for v in grouped.values())

def _refs(item): return item.get('sources',[{'source':'Unknown','chunk_index':None}])
def _base(item): return {'evidence':item['text'],'sources':_refs(item)}

def find_conflicts(items):
    """Flag explicit opposite project states about a shared topic; never resolve silently."""
    positive=re.compile(r"\b(completed|complete|approved|available|on track|resolved|delivered)\b",re.I)
    negative=re.compile(r"\b(not completed|incomplete|not approved|unavailable|delayed|blocked|pending|unresolved|at risk)\b",re.I)
    conflicts=[]
    for i,a in enumerate(items):
        for b in items[i+1:]:
            ta,tb=a['text'],b['text']
            # Need a shared project subject beyond generic status words.
            words=lambda t:{w.lower() for w in re.findall(r"[A-Za-z]{4,}",t) if w.lower() not in {'completed','complete','approved','available','delayed','blocked','pending','unresolved','project','status','milestone','deliverable','not','with','from','that','this'}}
            common=words(ta)&words(tb)
            if len(common)<2: continue
            def polarity(t):
                if negative.search(t): return -1
                if positive.search(t): return 1
                return 0
            opposite=polarity(ta)*polarity(tb)==-1
            if opposite:
                conflicts.append({'topic':' / '.join(sorted(common)[:5]),'statement_a':ta,'sources_a':_refs(a),'statement_b':tb,'sources_b':_refs(b),'resolution':'Conflicting source statements detected. Confirm the latest authoritative status with the project owner; no statement was selected automatically.'})
            if len(conflicts)>=30: return conflicts
    return conflicts

def generate_docs():
    items,dc,cc=records()
    stories=[]; risks=[]; actions=[]; blockers=[]
    for it in items:
        t=it['text']; base=_base(it)
        if SCOPE.search(t):
            stories.append({**base,'title':t[:100], 'description':t,
                'user_story':f"As a [user role not specified], I need: {t} (business outcome not specified in source documents).",
                'acceptance_criteria':['Not specified in source documents']})
        if RISK.search(t):
            severity='High' if re.search(r'\b(blocked|overdue|critical|severe|miss(?:ed)? deadline)\b',t,re.I) else ('Medium' if re.search(r'\b(delay|delayed|at risk|dependency|issue)\b',t,re.I) else 'Low')
            likelihood='High' if re.search(r'\b(blocked|overdue|already delayed|will miss)\b',t,re.I) else 'Not specified'
            risks.append({**base,'risk_description':t,'severity':severity,'likelihood':likelihood,
                'impact':'Not specified','mitigation':'Review the cited issue with the project owner and agree a dated mitigation/action; specific mitigation is not specified in source documents.'})
        if ACTION.search(t) or BLOCK.search(t):
            owner=re.search(r'\b(?:assigned to|owner|responsible)\s*[:：]?\s*([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)',t)
            date=re.search(r'\b(?:by|due|deadline)\s+(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?|\d{1,2}\s+\w+(?:\s+\d{4})?|\w+\s+\d{1,2}(?:,\s*\d{4})?)',t,re.I)
            action={'task':t,'responsible_person':owner.group(1).strip() if owner else 'Not specified',
                    'due_date':date.group(1) if date else 'Not specified','status':'Open' if BLOCK.search(t) else 'Not specified',**base}
            actions.append(action)
    def dedup(rows,key):
        seen=set(); out=[]
        for x in rows:
            k=x[key].lower()
            if k not in seen: seen.add(k); out.append(x)
        return out
    stories=dedup(stories,'description'); risks=dedup(risks,'risk_description'); actions=dedup(actions,'task')
    return {'project_level':True,'documents_scanned':dc,'chunks_scanned':cc,
        'user_stories':stories[:100], 'risk_register':risks[:100], 'action_items':actions[:100],
        'potential_conflicts':find_conflicts(items),
        'notice':'Generated by evidence-based extraction. Missing owners, dates, acceptance criteria and impacts are explicitly marked Not specified. Review before formal project use.'}

def health_score():
    items,dc,cc=records()
    if not items: return {'error':'Upload project documents before calculating project health.'}
    scope=[x for x in items if SCOPE.search(x['text'])]
    risk=[x for x in items if RISK.search(x['text'])]
    blockers=[x for x in items if BLOCK.search(x['text'])]
    deliverables=[x for x in items if re.search(r'\b(deliverable|milestone|completed|complete|delivered|remaining)\b',x['text'],re.I)]
    deps=[x for x in items if re.search(r'\b(dependency|depends on|dependent|blocked by|awaiting)\b',x['text'],re.I)]
    def score(val,reason): return {'score':max(0,min(100,int(val))),'reason':reason}
    scope_s= min(100, 35+min(len(scope),8)*8) if scope else 15
    timeline_s=max(10,100-min(len(risk),10)*9)
    blocker_penalty=sum(18 if re.search(r'\b(blocked|overdue|critical)\b',x['text'],re.I) else 8 for x in blockers)
    blocker_s=max(0,100-blocker_penalty)
    progress_s=min(100,25+min(len(deliverables),10)*7) if deliverables else 20
    dep_s=max(10,100-min(len(deps),10)*9)
    dims={
      'scope_clarity':score(scope_s,f'{len(scope)} distinct evidence statements mention scope, goals, requirements or deliverables.' if scope else 'No explicit scope evidence found; clarity cannot be established.'),
      'timeline_schedule_risk':score(timeline_s,f'{len(risk)} risk/schedule-related evidence statements found; each reduces this dimension by 9 points (floor 10).'),
      'blocker_count_severity':score(blocker_s,f'{len(blockers)} blocker/pending statements found; high-severity terms carry a larger penalty.'),
      'deliverable_progress':score(progress_s,f'{len(deliverables)} statements reference deliverables, milestones or completion; completion status is not inferred unless explicit.'),
      'dependency_status':score(dep_s,f'{len(deps)} dependency-related statements found; each reduces this dimension by 9 points (floor 10).')}
    overall=round(sum(x['score'] for x in dims.values())/len(dims))
    status='Healthy' if overall>=75 else ('Needs Attention' if overall>=50 else 'At Risk')
    rec=[]
    for key,val in dims.items():
        if val['score']<70:
            rec.append({'dimension':key,'recommendation':{'scope_clarity':'Confirm and document project objectives, scope boundaries and acceptance criteria.','timeline_schedule_risk':'Review schedule risks, validate dates and create recovery actions with owners.','blocker_count_severity':'Prioritize unresolved blockers and record accountable owners and target resolution dates.','deliverable_progress':'Update each deliverable with verified status, evidence and remaining work.','dependency_status':'Map dependencies, confirm external commitments and track dependency owners.'}[key]})
    evidence=[{'evidence':x['text'],'sources':_refs(x)} for x in (risk+blockers+deps)[:20]]
    return {'overall_score':overall,'status':status,'dimensions':dims,'recommendations':rec,
            'evidence_summary':{'documents_scanned':dc,'chunks_scanned':cc,'scope_statements':len(scope),'risk_statements':len(risk),'blockers':len(blockers),'deliverable_statements':len(deliverables),'dependency_statements':len(deps)},
            'supporting_evidence':evidence,'scoring_method':'Transparent heuristic: scope starts at 35 (+8 per evidence statement, max 100); timeline/dependency start at 100 (-9 per matching statement, floor 10); blockers subtract 18 for blocked/overdue/critical and 8 for other blocker statements; deliverables start at 25 (+7 per matching statement, max 100). Overall is the unweighted mean. Scores measure evidence coverage/signals, not a certified project audit.'}

def answer_question(question, history=None):
    prior_context=' '.join(str(m.get('content','')) for m in (history or [])[-6:] if isinstance(m,dict) and m.get('role') == 'user')
    retrieval_query=(question+' '+prior_context).strip()[-1800:]
    hits=search(retrieval_query, limit=7)
    if not hits: return {'answer':'I could not find supporting information in the currently indexed project documents.','sources':[],'grounded':False,'mode':'retrieval-only'}
    context='\n\n'.join(f"[{i+1}] Source: {h['source']} (chunk {h['chunk_index']+1})\n{h['text']}" for i,h in enumerate(hits))
    key=os.getenv('OPENAI_API_KEY'); model=os.getenv('OPENAI_MODEL','gpt-4o-mini')
    if key:
        prompt=('Answer only from the supplied project evidence. If the evidence does not answer, say so. '
                'Resolve conflicts by describing both statements and their source; do not silently choose. '
                'Cite evidence as [1], [2]. Never invent owners, dates, status or requirements.\n\n'
                f'Conversation context: {json.dumps((history or [])[-6:],ensure_ascii=False)}\n'
                f'Question: {question}\n\nEvidence:\n{context}')
        payload=json.dumps({'model':model,'messages':[{'role':'system','content':'You are a careful project intelligence assistant. Be concise, evidence-grounded, and explicit about unknowns.'},{'role':'user','content':prompt}],'temperature':0.1}).encode()
        req=urllib.request.Request('https://api.openai.com/v1/chat/completions',data=payload,headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=45) as resp: answer=json.loads(resp.read())['choices'][0]['message']['content']
            mode='openai-grounded'
        except Exception as e:
            answer='External answer generation is unavailable; here are the retrieved evidence passages instead. Configure/check OPENAI_API_KEY and connectivity.\n\n'+ '\n'.join(f"• {h['source']}: {h['text']}" for h in hits[:5])
            mode='retrieval-fallback'
    else:
        answer='No LLM key is configured, so this is an extractive evidence response rather than generated interpretation.\n\n'+'\n'.join(f"• {h['source']} (chunk {h['chunk_index']+1}): {h['text']}" for h in hits[:5])
        mode='retrieval-only'
    return {'answer':answer,'sources':[{'source':h['source'],'chunk_index':h['chunk_index']+1,'evidence':h['text'],'distance':h['distance']} for h in hits], 'grounded':True,'mode':mode}

def validate_rag():
    # Validation cases are derived from indexed corpus. This reports retrieval coverage,
    # and explicitly avoids claiming semantic answer correctness without a human gold label.
    items,dc,cc=records()
    cases=[]
    for label,pattern in [('Explicit fact',r'\b(?:deadline|due|owner|assigned to|milestone|deliverable|requirement)\b'),('Risk / blocker',r'\b(?:risk|blocked|blocker|delay|pending|dependency)\b')]:
        match=next((x for x in items if re.search(pattern,x['text'],re.I)),None)
        if match:
            q='What does the project documentation state about '+('project requirements, milestones, owners or deadlines?' if label=='Explicit fact' else 'risks, blockers, delays or dependencies?')
            got=search(q,5)
            found=any(h['source'] in [s['source'] for s in _refs(match)] for h in got)
            cases.append({'category':label,'question':q,'expected_answer':match['text'],'actual_answer':got[0]['text'] if got else 'No passage retrieved','sources':[h['source'] for h in got], 'status':'PASS' if found else 'REVIEW','check':'Source retrieval coverage; relevance requires human review'})
    if len(items)>1:
        q='Summarize the project scope and schedule risks across the uploaded documents.'; got=search(q,7)
        cases.append({'category':'Multi-document retrieval','question':q,'expected_answer':'Relevant evidence should be retrieved across the project corpus.','actual_answer':f'{len(got)} passages retrieved','sources':list(dict.fromkeys(h['source'] for h in got)),'status':'PASS' if len(set(h['source'] for h in got))>=2 else 'REVIEW','check':'Cross-document source coverage'})
    q='What is the exact approved project budget in the documents?'; got=search(q,5)
    cases.append({'category':'Potentially unavailable fact','question':q,'expected_answer':'Assistant should say unavailable unless a source explicitly states the approved budget.','actual_answer':got[0]['text'] if got else 'No passage retrieved','sources':[h['source'] for h in got],'status':'PASS' if not got or not re.search(r'\b(budget|INR|USD|₹|\$)\b', ' '.join(h['text'] for h in got),re.I) else 'REVIEW','check':'Heuristic unsupported-answer guard; inspect before sign-off'})
    formats=sorted({d.get('file_type','').lower() for d in list_documents() if d.get('file_type')})
    cases.append({'category':'Multi-format coverage','question':'Were PDF, DOCX and TXT source formats indexed in this project workspace?','expected_answer':'PDF, DOCX and TXT should all be present for the requested validation scenario.','actual_answer':'Indexed formats: '+(', '.join(formats) if formats else 'None'),'sources':[],'status':'PASS' if {'pdf','docx','txt'}.issubset(set(formats)) else 'REVIEW','check':'Confirms the requested sample file types are present in the corpus'})
    conflicts=find_conflicts(items)
    cases.append({'category':'Conflicting information','question':'Do the project documents contain conflicting status statements that require reconciliation?','expected_answer':'Conflicting statements should be surfaced with both sources, not silently resolved.','actual_answer':f'{len(conflicts)} potential conflict(s) detected','sources':list(dict.fromkeys(s['source'] for c in conflicts for s in c['sources_a']+c['sources_b'])),'status':'PASS' if conflicts else 'REVIEW','check':'Conflict detection is heuristic; human verification required'})
    return {'documents_scanned':dc,'chunks_scanned':cc,'cases':cases,'potential_conflicts':conflicts,'format_coverage':formats,'summary':{'total':len(cases),'pass':sum(x['status']=='PASS' for x in cases),'review':sum(x['status']!='PASS' for x in cases)},'limitations':'Automated checks measure retrieval/source coverage and a conservative no-evidence guard. Conflicting claims and semantic correctness require human-labelled expected answers; do not interpret PASS as proof of answer accuracy.'}
