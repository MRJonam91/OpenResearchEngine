"""Deterministic Markdown report with traceable passage citations."""

from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer


def _escape(value: str) -> str:
    return re.sub(r"([\\`*_\[\]<>|])", r"\\\1", value).replace("\n", " ")


def render_report(claims: list[dict], include_proposed: bool = False) -> str:
    included = [
        claim for claim in reversed(claims)
        if claim["status"] in {"approved", "uncertain"}
        or (include_proposed and claim["status"] == "proposed")
    ]
    lines = ["# Research report", "", "Claims below retain their review state and passage-level citations.", ""]
    footnotes: dict[int, dict] = {}
    if not included:
        lines += ["No reviewed claims are available for this report.", ""]
    for claim in included:
        lines += [f"## Claim {claim['id']}: {_escape(claim['text'])}", ""]
        state = claim["status"].capitalize()
        if claim["disputed"]:
            state += " · Disputed evidence"
        lines += [f"Status: {state}", ""]
        provenance = claim.get("provenance", {})
        if provenance.get("kind") == "ai":
            lines += [f"Draft origin: AI; model {_escape(provenance['model'])}; digest {provenance['model_digest']}; run {provenance['run_id']}; prompt {provenance['prompt_version']}", ""]
        if claim["note"]:
            lines += [f"Review note: {_escape(claim['note'])}", ""]
        for evidence in claim["evidence"]:
            passage_id = evidence["passage_id"]
            footnotes[passage_id] = evidence
            stance = evidence["stance"].capitalize()
            lines += [f"- {stance}: {_escape(evidence['text'])} [^p{passage_id}]", ""]
    if footnotes:
        lines += ["## Sources", ""]
        for passage_id, evidence in footnotes.items():
            identity = (
                f"{_escape(evidence['title'])}; {_escape(evidence['origin'])}; "
                f"imported {evidence['imported_at']}; SHA-256 {evidence['sha256']}; "
                f"{_escape(evidence['locator'])}; passage {passage_id}, version {evidence['version_id']}"
            )
            lines.append(f"[^p{passage_id}]: {identity}")
        lines.append("")
    return "\n".join(lines)


def _pdf_font() -> None:
    if "SourcePilotVera" not in pdfmetrics.getRegisteredFontNames():
        fonts = Path(reportlab.__file__).parent / "fonts"
        pdfmetrics.registerFont(TTFont("SourcePilotVera", str(fonts / "Vera.ttf")))
        pdfmetrics.registerFont(TTFont("SourcePilotVeraBold", str(fonts / "VeraBd.ttf")))
        pdfmetrics.registerFontFamily("SourcePilotVera", normal="SourcePilotVera", bold="SourcePilotVeraBold")


def _check_pdf_glyphs(claims: list[dict]) -> None:
    glyphs = pdfmetrics.getFont("SourcePilotVera").face.charToGlyph
    for claim in claims:
        values = [claim["text"], claim["note"]]
        values.extend(str(value) for value in claim.get("provenance", {}).values())
        for evidence in claim["evidence"]:
            values.extend(str(evidence[key]) for key in ("text", "title", "origin", "locator"))
        for value in values:
            for character in value:
                if character not in "\r\n\t" and ord(character) not in glyphs:
                    raise ValueError(f"PDF font does not support U+{ord(character):04X}; export Markdown for this text")


def render_pdf_report(claims: list[dict], include_proposed: bool = False) -> bytes:
    """Produce a print-ready PDF from the same reviewed claims as Markdown."""
    _pdf_font()
    included = [
        claim for claim in reversed(claims)
        if claim["status"] in {"approved", "uncertain"}
        or (include_proposed and claim["status"] == "proposed")
    ]
    _check_pdf_glyphs(included)
    ink = colors.HexColor("#17191d")
    blue = colors.HexColor("#002fa7")
    muted = colors.HexColor("#616773")
    title = ParagraphStyle("Title", fontName="SourcePilotVeraBold", fontSize=19, leading=25, textColor=ink, spaceAfter=13)
    heading = ParagraphStyle("Heading", fontName="SourcePilotVeraBold", fontSize=11, leading=16, textColor=blue, spaceBefore=17, spaceAfter=7)
    body = ParagraphStyle("Body", fontName="SourcePilotVera", fontSize=8.8, leading=14, textColor=ink, spaceAfter=7, alignment=TA_LEFT)
    small = ParagraphStyle("Small", parent=body, fontSize=7.4, leading=11, textColor=muted, spaceAfter=5)
    stream = BytesIO()
    document = SimpleDocTemplate(stream, pagesize=A4, topMargin=52, bottomMargin=52, leftMargin=54, rightMargin=54)
    story = [Paragraph("Research report", title), Paragraph("Human-reviewed claims and passage-level citations. Citations identify a source; they do not certify its truth.", small), HRFlowable(width="100%", thickness=0.7, color=blue), Spacer(1, 10)]
    footnotes: dict[int, dict] = {}
    if not included:
        story.append(Paragraph("No reviewed claims are available for this report.", body))
    for claim in included:
        story.append(Paragraph(f"Claim {claim['id']}: {escape(claim['text'])}", heading))
        state = claim["status"].capitalize()
        if claim["disputed"]:
            state += " · Disputed evidence"
        story.append(Paragraph(f"Status: {escape(state)}", small))
        provenance = claim.get("provenance", {})
        if provenance.get("kind") == "ai":
            story.append(Paragraph(escape(f"Draft origin: AI; model {provenance['model']}; digest {provenance['model_digest']}; run {provenance['run_id']}; prompt {provenance['prompt_version']}"), small))
        if claim["note"]:
            story.append(Paragraph(f"Review note: {escape(claim['note'])}", small))
        for evidence in claim["evidence"]:
            passage_id = evidence["passage_id"]
            footnotes[passage_id] = evidence
            text = escape(evidence["text"]).replace("\n", "<br/>")
            story.append(Paragraph(f"{evidence['stance'].capitalize()}: {text} [p{passage_id}]", body))
    if footnotes:
        story.append(Paragraph("Sources", heading))
        for passage_id, evidence in footnotes.items():
            identity = (
                f"[p{passage_id}] {evidence['title']}; {evidence['origin']}; "
                f"imported {evidence['imported_at']}; SHA-256 {evidence['sha256']}; "
                f"{evidence['locator']}; passage {passage_id}, version {evidence['version_id']}"
            )
            story.append(Paragraph(escape(identity), small))

    def page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont("SourcePilotVera", 7)
        canvas.setFillColor(muted)
        canvas.drawString(54, 29, "SourcePilot · Local research report")
        canvas.drawRightString(A4[0] - 54, 29, str(doc.page))
        canvas.restoreState()

    document.build(story, onFirstPage=page_number, onLaterPages=page_number)
    from pypdf import PdfWriter

    writer = PdfWriter(clone_from=BytesIO(stream.getvalue()))
    font_license = Path(reportlab.__file__).parent / "fonts" / "bitstream-vera-license.txt"
    writer.add_attachment("Bitstream-Vera-LICENSE.txt", font_license.read_bytes())
    output = BytesIO()
    writer.write(output)
    return output.getvalue()
