"""Utilities for rendering application report payloads as real PDF files."""
from __future__ import annotations

import json
from datetime import datetime
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    KeepTogether,
)
from xml.sax.saxutils import escape


def _display(value: Any) -> str:
    if value is None or value == "":
        return "Not specified"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2, default=str)
    return str(value)


def _paragraph(value: Any, style: ParagraphStyle) -> Paragraph:
    # Paragraph parses a small XML-like markup language; escape all source data.
    return Paragraph(escape(_display(value)).replace("\n", "<br/>"), style)


def _make_table(rows: list[list[Any]], styles) -> Table:
    wrapped = [[_paragraph(cell, styles["table_cell"]) for cell in row] for row in rows]
    usable_width = A4[0] - (34 * mm)
    table = Table(wrapped, repeatRows=1, hAlign="LEFT",
                  colWidths=[usable_width / max(1, len(rows[0]))] * len(rows[0]))
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#172B4D")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    return table


def build_pdf_report(title: str, data: dict[str, Any]) -> bytes:
    """Render arbitrary report JSON into a readable, structured PDF document."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=17 * mm, leftMargin=17 * mm,
        topMargin=19 * mm, bottomMargin=18 * mm,
        title=title, author="AI Project Intelligence & Risk Advisor",
    )
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle("ReportTitle", parent=base["Title"], fontSize=19,
                                 leading=24, textColor=colors.HexColor("#17365D"),
                                 alignment=TA_CENTER, spaceAfter=8),
        "subtitle": ParagraphStyle("ReportSubtitle", parent=base["Normal"],
                                    fontSize=8, textColor=colors.HexColor("#64748B"),
                                    alignment=TA_CENTER, spaceAfter=16),
        "h1": ParagraphStyle("SectionHeading", parent=base["Heading2"],
                             fontSize=13, leading=16, textColor=colors.HexColor("#1D4E89"),
                             spaceBefore=12, spaceAfter=6, keepWithNext=True),
        "h2": ParagraphStyle("SubHeading", parent=base["Heading3"],
                             fontSize=10, leading=13, textColor=colors.HexColor("#334155"),
                             spaceBefore=7, spaceAfter=4, keepWithNext=True),
        "body": ParagraphStyle("ReportBody", parent=base["BodyText"],
                               fontSize=8.5, leading=12, spaceAfter=5,
                               wordWrap="CJK"),
        "table_cell": ParagraphStyle("TableCell", parent=base["BodyText"],
                                     fontSize=7.2, leading=9, wordWrap="CJK"),
    }
    story = [
        _paragraph(title, styles["title"]),
        Paragraph("AI Project Intelligence &amp; Risk Advisor", styles["subtitle"]),
        Paragraph(f"Generated: {datetime.now().astimezone().strftime('%d %b %Y, %I:%M %p %Z')}", styles["subtitle"]),
    ]

    def render_value(key: str, value: Any, depth: int = 0):
        heading_style = styles["h1"] if depth == 0 else styles["h2"]
        label = key.replace("_", " ").strip().title() or "Details"
        if isinstance(value, dict):
            story.append(Paragraph(escape(label), heading_style))
            if not value:
                story.append(_paragraph("No data available.", styles["body"]))
            for child_key, child_value in value.items():
                render_value(str(child_key), child_value, depth + 1)
        elif isinstance(value, list):
            story.append(Paragraph(escape(label), heading_style))
            if not value:
                story.append(_paragraph("No items available.", styles["body"]))
            elif all(isinstance(item, dict) for item in value):
                keys = []
                for item in value:
                    for item_key in item:
                        if item_key not in keys:
                            keys.append(item_key)
                if keys:
                    rows = [[k.replace("_", " ").title() for k in keys]]
                    for item in value:
                        rows.append([_display(item.get(k)) for k in keys])
                    story.append(_make_table(rows, styles))
                else:
                    story.append(_paragraph(value, styles["body"]))
            else:
                for index, item in enumerate(value, 1):
                    story.append(KeepTogether([
                        Paragraph(f"Item {index}", styles["h2"]),
                        _paragraph(item, styles["body"]),
                    ]))
        else:
            story.append(Paragraph(escape(label), styles["h2"]))
            story.append(_paragraph(value, styles["body"]))

    for key, value in data.items():
        render_value(str(key), value)
    if len(story) <= 3:
        story.append(_paragraph("No report data was supplied.", styles["body"]))

    def footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
        canvas.line(17 * mm, 13 * mm, A4[0] - 17 * mm, 13 * mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(17 * mm, 8 * mm, "AI Project Intelligence & Risk Advisor")
        canvas.drawRightString(A4[0] - 17 * mm, 8 * mm, f"Page {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
