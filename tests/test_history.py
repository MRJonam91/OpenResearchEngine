from pathlib import Path

from fastapi.testclient import TestClient

from sourcepilot.api import create_app
from sourcepilot.research import ResearchService
from sourcepilot.store import ResearchStore


def test_search_defaults_to_latest_version_and_history_is_explicit(tmp_path: Path):
    source = tmp_path / "changing.txt"
    source.write_text("Older statement only.\n", encoding="utf-8")
    store = ResearchStore(tmp_path / "workspace")
    first = store.import_file(source)
    old_passage = store.list_passages(first["source_id"])[0]["id"]
    source.write_text("Newer statement only.\n", encoding="utf-8")
    second = store.import_file(source)
    research = ResearchService(store)

    assert research.search("Older") == []
    assert [row["id"] for row in research.search("Older", include_history=True)] == [old_passage]
    assert [item["version_id"] for item in store.list_versions(first["source_id"])] == [second["version_id"], first["version_id"]]


def test_original_download_is_version_bound_and_attachment(tmp_path: Path):
    store = ResearchStore(tmp_path / "workspace")
    first = store.import_bytes("page.html", b"<p>Original text</p>", "upload:page.html")
    second = store.import_bytes("other.txt", b"Other text", "upload:other.txt")
    client = TestClient(create_app(store.workspace))
    response = client.get(f"/api/sources/{first['source_id']}/versions/{first['version_id']}/original")
    assert response.content == b"<p>Original text</p>"
    assert response.headers["content-disposition"].startswith("attachment;")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert client.get(f"/api/sources/{second['source_id']}/versions/{first['version_id']}/original").status_code == 404


def test_claim_citation_survives_new_source_version(tmp_path: Path):
    source = tmp_path / "note.txt"
    source.write_text("Evidence from first edition.\n", encoding="utf-8")
    store = ResearchStore(tmp_path / "workspace")
    first = store.import_file(source)
    old_passage = store.list_passages(first["source_id"])[0]["id"]
    research = ResearchService(store)
    claim = research.create_claim("The first edition says this.", old_passage)
    research.review_claim(claim["id"], "approved")
    source.write_text("Different second edition.\n", encoding="utf-8")
    store.import_file(source)

    assert research.get_claim(claim["id"])["evidence"][0]["text"] == "Evidence from first edition."
    assert "Evidence from first edition." in research.render_report()
