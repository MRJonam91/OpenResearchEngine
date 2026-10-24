from pathlib import Path

import pytest

from sourcepilot.store import ResearchStore


def test_import_preserves_original_and_line_locators(tmp_path: Path):
    original = tmp_path / "note.txt"
    original.write_text("First claim.\n\nSecond paragraph.\n", encoding="utf-8")
    store = ResearchStore(tmp_path / "research")

    imported = store.import_file(original)
    passages = store.list_passages(imported["source_id"])

    assert imported["status"] == "ready"
    assert [p["locator"] for p in passages] == ["lines 1-1", "lines 3-3"]
    assert [p["text"] for p in passages] == ["First claim.", "Second paragraph."]
    assert Path(imported["object_path"]).read_bytes() == original.read_bytes()


def test_same_origin_same_bytes_reuses_version_but_changed_bytes_do_not(tmp_path: Path):
    original = tmp_path / "note.md"
    original.write_text("Older evidence.\n", encoding="utf-8")
    store = ResearchStore(tmp_path / "research")
    first = store.import_file(original)
    repeated = store.import_file(original)
    original.write_text("New evidence.\n", encoding="utf-8")
    changed = store.import_file(original)

    assert repeated["version_id"] == first["version_id"]
    assert changed["source_id"] == first["source_id"]
    assert changed["version_id"] != first["version_id"]
    assert Path(first["object_path"]).read_text(encoding="utf-8") == "Older evidence.\n"
    assert [p["text"] for p in store.list_passages(first["source_id"], first["version_id"])] == ["Older evidence."]


def test_html_omits_script_and_keeps_visible_text(tmp_path: Path):
    store = ResearchStore(tmp_path / "research")
    item = store.import_bytes("page.html", b"<h1>Findings</h1><script>ignore me</script><p>Verified text.</p>", "upload:page.html")
    text = " ".join(p["text"] for p in store.list_passages(item["source_id"]))
    assert "Findings" in text
    assert "Verified text." in text
    assert "ignore me" not in text


def test_empty_and_unsupported_file_are_rejected(tmp_path: Path):
    store = ResearchStore(tmp_path / "research")
    with pytest.raises(ValueError, match="empty"):
        store.import_bytes("blank.txt", b"", "upload:blank.txt")
    with pytest.raises(ValueError, match="Unsupported"):
        store.import_bytes("picture.png", b"png", "upload:picture.png")
    assert store.list_sources() == []


def test_url_import_rejects_local_and_non_http_targets(tmp_path: Path):
    store = ResearchStore(tmp_path / "research")
    with pytest.raises(ValueError, match="HTTP or HTTPS"):
        store.import_url("file:///C:/private.txt")
    with pytest.raises(ValueError, match="public"):
        store.import_url("http://127.0.0.1/private")


def test_blank_pdf_reports_missing_extractable_text(tmp_path: Path):
    from io import BytesIO
    from pypdf import PdfWriter

    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    writer.write(output)
    store = ResearchStore(tmp_path / "research")
    with pytest.raises(ValueError, match="no extractable text"):
        store.import_bytes("scan.pdf", output.getvalue(), "upload:scan.pdf")


def test_markdown_list_items_have_separate_locators(tmp_path: Path):
    store = ResearchStore(tmp_path / "research")
    item = store.import_bytes("list.md", b"- First point.\n- Second point.\n", "upload:list.md")
    passages = store.list_passages(item["source_id"])
    assert [(p["locator"], p["text"]) for p in passages] == [
        ("lines 1-1", "- First point."),
        ("lines 2-2", "- Second point."),
    ]
