from app import milestone3


def sample_records(monkeypatch):
    items = [
        {'text':'Project objective: deliver a student portal.', 'sources':[{'source':'brief.txt','chunk_index':1}]},
        {'text':'Risk: API integration is delayed because credentials are pending.', 'sources':[{'source':'notes.docx','chunk_index':2}]},
        {'text':'Action item: assigned to Neha to confirm access by 18 November 2026.', 'sources':[{'source':'notes.docx','chunk_index':3}]},
        {'text':'Milestone 1 deliverable completed and demonstrated.', 'sources':[{'source':'status.pdf','chunk_index':1}]},
    ]
    monkeypatch.setattr(milestone3, 'records', lambda: (items, 3, 4))
    return items


def test_documentation_is_grounded_and_marks_missing_fields(monkeypatch):
    sample_records(monkeypatch)
    result = milestone3.generate_docs()
    assert result['documents_scanned'] == 3
    assert result['risk_register'][0]['sources'][0]['source'] == 'notes.docx'
    assert result['action_items'][0]['responsible_person'] == 'Neha'
    assert result['action_items'][0]['due_date'] == '18 November 2026'
    assert result['risk_register'][0]['impact'] == 'Not specified'


def test_health_score_has_explainable_dimensions(monkeypatch):
    sample_records(monkeypatch)
    result = milestone3.health_score()
    assert 0 <= result['overall_score'] <= 100
    assert set(result['dimensions']) == {'scope_clarity','timeline_schedule_risk','blocker_count_severity','deliverable_progress','dependency_status'}
    assert all(v['reason'] for v in result['dimensions'].values())


def test_empty_health_score():
    from unittest.mock import patch
    with patch.object(milestone3, 'records', return_value=([],0,0)):
        assert 'error' in milestone3.health_score()


def test_assistant_returns_retrieved_sources_without_api_key(monkeypatch):
    captured = {}
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    # Return one grounded result and verify follow-up context is included in retrieval.
    monkeypatch.setattr(milestone3, 'search', lambda q, limit=7: (captured.update(query=q) or [
        {'source':'brief.pdf','chunk_index':1,'text':'The release date is not specified.','distance':0.12}
    ]))
    result = milestone3.answer_question('What about the release date?', [{'role':'user','content':'Tell me about the schedule.'}])
    assert result['mode'] == 'retrieval-only'
    assert result['sources'][0]['source'] == 'brief.pdf'
    assert 'schedule' in captured['query']


def test_conflict_detection_keeps_both_source_references():
    items = [
        {'text':'Milestone 1 login prototype is completed and demonstrated.','sources':[{'source':'status.pdf','chunk_index':1}]},
        {'text':'Milestone 1 login prototype is still incomplete and awaiting review.','sources':[{'source':'meeting.docx','chunk_index':2}]},
    ]
    conflicts = milestone3.find_conflicts(items)
    assert conflicts
    assert conflicts[0]['sources_a'][0]['source'] == 'status.pdf'
    assert conflicts[0]['sources_b'][0]['source'] == 'meeting.docx'


def test_validation_reports_formats_and_conflicts(monkeypatch):
    sample_records(monkeypatch)
    monkeypatch.setattr(milestone3, 'list_documents', lambda: [
        {'file_type':'pdf'}, {'file_type':'docx'}, {'file_type':'txt'}
    ])
    monkeypatch.setattr(milestone3, 'search', lambda q, limit=5: [
        {'source':'brief.txt','chunk_index':0,'text':'Project objective: deliver a student portal.','distance':0.1},
        {'source':'notes.docx','chunk_index':1,'text':'Risk: API integration is delayed because credentials are pending.','distance':0.2},
    ][:limit])
    result = milestone3.validate_rag()
    categories = {case['category'] for case in result['cases']}
    assert {'Explicit fact','Risk / blocker','Multi-document retrieval','Potentially unavailable fact','Multi-format coverage','Conflicting information'} <= categories
    assert set(result['format_coverage']) == {'pdf','docx','txt'}
    assert result['summary']['total'] == len(result['cases'])
