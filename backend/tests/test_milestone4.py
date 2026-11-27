from app import milestone4


def test_insights_dashboard_aggregates_milestone3_outputs(monkeypatch):
    monkeypatch.setattr(milestone4, "generate_docs", lambda: {
        "user_stories": [
            {"description": "Build reporting", "sources": [{"source": "brief.txt", "chunk_index": 0}]},
            {"description": "Build reporting", "sources": []},
        ],
        "risk_register": [{"risk_description": "Schedule may slip", "severity": "Medium"}],
        "action_items": [{"task": "Confirm owner", "responsible_person": "Not specified"}],
        "documents_scanned": 3,
        "chunks_scanned": 12,
    })
    monkeypatch.setattr(milestone4, "health_score", lambda: {
        "overall_score": 72, "status": "Needs Attention", "dimensions": {},
        "scoring_method": "test"
    })
    payload = milestone4.build_insights_payload()
    assert payload["project_health"]["overall_score"] == 72
    assert len(payload["scope_summary"]) == 1
    assert payload["counts"] == {
        "scope_items": 2, "risks": 1, "action_items": 1, "blockers": 0,
        "documents_scanned": 3, "chunks_scanned": 12,
    }
    assert payload["risks"][0]["risk_description"] == "Schedule may slip"
    assert payload["blockers"] == []


def test_incremental_endpoint_is_declared():
    from app.main import app
    paths = {route.path for route in app.routes}
    assert "/api/milestone4/insights" in paths
    assert "/api/milestone4/documents/incremental-upload" in paths

