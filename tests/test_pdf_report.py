"""PDF report parity and traceability."""

from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from pypdf import PdfReader
import pytest

from sourcepilot.__main__ import main
from sourcepilot.api import create_app
from sourcepilot.research import ResearchService
from sourcepilot.store import ResearchStore


def _workspace(tmp_path: Path):
    store = ResearchStore(tmp_path / "workspace")
    source = store.import_bytes("città.txt", "La città cresce del 3%.\n".encode(), "upload:città.txt")
    passage = store.list_passages(source["source_id"])[0]["id"]
    research = ResearchService(store)
    approved = research.create_claim("La città cresce.", passage)
    research.review_claim(approved["id"], "approved", "Verificato nel documento.")
    proposed = research.create_claim("Una bozza non revisionata.", passage)
    return store, research, approved["id"], proposed["id"]


def _text(data: bytes) -> str:
    return "\n".join(page.extract_text() for page in PdfReader(BytesIO(data)).pages)


def test_pdf_includes_reviewed_claim_and_locatable_citation(tmp_path: Path):
    _, research, approved_id, _ = _workspace(tmp_path)
    data = research.render_pdf_report()
    assert data.startswith(b"%PDF-")
    text = _text(data)
    assert f"Claim {approved_id}" in text
    assert "La città cresce." in text
    assert "Verificato nel documento." in text
    assert "città.txt" in text
    assert "SHA-256" in text
    assert "version 1" in text
    assert "bozza non revisionata" not in text


def test_pdf_and_markdown_use_same_inclusion_rule(tmp_path: Path):
    _, research, _, proposed_id = _workspace(tmp_path)
    assert f"Claim {proposed_id}" not in _text(research.render_pdf_report())
    assert f"Claim {proposed_id}" in _text(research.render_pdf_report(include_proposed=True))
    assert f"Claim {proposed_id}" in research.render_report(include_proposed=True)


def test_pdf_api_is_downloadable(tmp_path: Path):
    store, _, _, _ = _workspace(tmp_path)
    response = TestClient(create_app(store.workspace)).get("/api/report.pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].startswith("attachment;")
    assert response.content.startswith(b"%PDF-")


def test_pdf_rejects_unrenderable_glyph_instead_of_omitting_it(tmp_path: Path):
    store, research, approved_id, _ = _workspace(tmp_path)
    research.edit_claim(approved_id, "La città cresce 中文.")
    research.review_claim(approved_id, "approved")
    with pytest.raises(ValueError, match="PDF font does not support"):
        research.render_pdf_report()
    output = tmp_path / "unsupported.pdf"
    assert main(["report", "--workspace", str(store.workspace), "--output", str(output)]) == 2
    assert not output.exists()


def test_pdf_cli_refuses_to_overwrite(tmp_path: Path):
    store, _, _, _ = _workspace(tmp_path)
    output = tmp_path / "report.pdf"
    args = ["report", "--workspace", str(store.workspace), "--output", str(output)]
    assert main(args) == 0
    first = output.read_bytes()
    assert first.startswith(b"%PDF-")
    assert main(args) == 2
    assert output.read_bytes() == first


def test_pdf_retains_embedded_font_license(tmp_path: Path):
    _, research, _, _ = _workspace(tmp_path)
    reader = PdfReader(BytesIO(research.render_pdf_report()))
    assert b"Copyright (c) 2003 by Bitstream" in reader.attachments["Bitstream-Vera-LICENSE.txt"][0]
