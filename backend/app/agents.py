
"""Document-grounded Milestone 2 agents using indexed source chunks.

These are transparent heuristic extractors: every finding includes the source chunk
so users can verify it. They do not claim to be an LLM or infer unsupported facts.
"""
import re
from .store import get_collection

SCOPE_TERMS = re.compile(r"\b(goal|objective|scope|deliverable|milestone|deadline|timeline|due date|owner|assigned to|responsib(?:le|ility)|week \d+|by \w+ \d+)\b", re.I)
RISK_TERMS = re.compile(r"\b(risk|delay|delayed|behind schedule|dependency|depends on|blocked|blocker|challenge|issue|may miss|at risk|pending|overdue|slippage|unavailable)\b", re.I)
BLOCKER_TERMS = re.compile(r"\b(blocked|blocker|pending|unresolved|open issue|awaiting|waiting for|decision needed|action item|follow[- ]?up|to[- ]?do|must confirm|needs approval|not decided)\b", re.I)
ACTION_TERMS = re.compile(r"\b(action item|follow[- ]?up|assigned to|owner:|responsible:|will (?:complete|deliver|send|review|fix|update)|must (?:complete|deliver|send|review|fix|update))\b", re.I)

def analyze_indexed_documents():
    collection = get_collection()
    records = collection.get(include=["documents", "metadatas"])
    docs = records.get("documents") or []
    metas = records.get("metadatas") or []
    scope, risks, blockers, actions = [], [], [], []
    seen = set()
    for chunk, meta in zip(docs, metas):
        meta = meta or {}
        source = meta.get("source", "Unknown")
        # Sentence-level extraction keeps evidence focused and traceable.
        for sentence in re.split(r"(?<=[.!?])\s+|(?<=\|)\s*", chunk):
            sentence = " ".join(sentence.split()).strip(" -•|")
            if len(sentence) < 12:
                continue
            key = (source, sentence.lower())
            if key in seen:
                continue
            seen.add(key)
            evidence = {"source": source, "chunk_index": int(meta.get("chunk_index", 0)) + 1, "evidence": sentence[:600]}
            if SCOPE_TERMS.search(sentence):
                scope.append({**evidence, "category": "Scope / deliverable"})
            if RISK_TERMS.search(sentence):
                risks.append({**evidence, "category": "Schedule / dependency risk",
                              "severity": "Review" if re.search(r"\b(blocked|overdue|miss|delay|at risk)\b", sentence, re.I) else "Watch"})
            if BLOCKER_TERMS.search(sentence):
                blockers.append({**evidence, "category": "Blocker / pending decision"})
            if ACTION_TERMS.search(sentence):
                actions.append({**evidence, "category": "Action item"})
    return {
        "documents_scanned": len({(m or {}).get("source", "Unknown") for m in metas}),
        "chunks_scanned": len(docs),
        "agents": {
            "scope_deliverables": {"status": "completed", "count": len(scope), "items": scope[:40]},
            "risk_forecasting": {"status": "completed", "count": len(risks), "items": risks[:40]},
            "blockers_actions": {"status": "completed", "count": len(blockers) + len(actions),
                                 "blockers": blockers[:40], "action_items": actions[:40]},
        },
        "validation_note": "Rule-based extraction over indexed text. Verify findings against the cited source; a missing finding does not mean no risk exists."
    }
