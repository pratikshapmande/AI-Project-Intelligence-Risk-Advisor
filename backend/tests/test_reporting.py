from app.reporting import build_pdf_report


def test_pdf_report_is_a_real_pdf_with_report_content():
    pdf = build_pdf_report("Project Health Report", {
        "overall_score": 82,
        "status": "Healthy",
        "dimensions": {"schedule": {"score": 80, "reason": "Milestones are on track"}},
        "risks": [{"risk_description": "Dependency delay", "severity": "Medium"}],
    })
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 500
