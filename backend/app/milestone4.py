"""Milestone 4 project insights aggregation.

All summaries are derived from the currently indexed project corpus. This module
reuses the Milestone 2/3 extractors; it does not replace their logic.
"""
from datetime import datetime, timezone
from .milestone3 import generate_docs, health_score


def build_insights_payload():
    documentation = generate_docs()
    health = health_score()
    stories = documentation.get("user_stories", [])
    risks = documentation.get("risk_register", [])
    actions = documentation.get("action_items", [])
    blockers = [item for item in actions if (item.get("status") or "").strip().lower() == "open"]
    scope_lines = []
    seen = set()
    for item in stories:
        text = (item.get("description") or "").strip()
        if text and text.lower() not in seen:
            seen.add(text.lower())
            scope_lines.append({
                "summary": text,
                "sources": item.get("sources", [])
            })
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_health": health,
        "scope_summary": scope_lines[:12],
        "risks": risks[:20],
        "action_items": actions[:20],
        "blockers": blockers[:20],
        "counts": {
            "scope_items": len(stories),
            "risks": len(risks),
            "action_items": len(actions),
            "blockers": len(blockers),
            "documents_scanned": documentation.get("documents_scanned", 0),
            "chunks_scanned": documentation.get("chunks_scanned", 0),
        },
        "source_notice": "Insights are consolidated from the currently indexed documents. Verify evidence and resolve flagged conflicts with the project team."
    }
