from io import BytesIO
from pathlib import Path
import shutil
import zipfile

from fastapi.testclient import TestClient
import pytest

from sourcepilot.api import create_app
from sourcepilot.ingest import extract_passages, fetch_url
from sourcepilot.store import ResearchStore


def docx_bytes(xml: str) -> bytes:
    data = BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        archive.writestr("word/document.xml", xml)
    return data.getvalue()


def test_docx_preserves_paragraph_and_table_locators():
    document = docx_bytes('''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
        <w:p><w:r><w:t>First finding.</w:t></w:r></w:p>
        <w:tbl><w:tr><w:tc><w:p><w:r><w:t>Budget</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>12</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
        </w:body></w:document>''')
    assert extract_passages("study.docx", document) == [
        ("paragraph 1", "First finding."), ("table 1, row 1", "Budget | 12"),
    ]


def test_docx_rejects_entities_and_expansion_budget(monkeypatch):
    document = docx_bytes('<!DOCTYPE x [<!ENTITY x "unsafe">]><x>&x;</x>')
    with pytest.raises(ValueError, match="entity|DTD"):
        extract_passages("unsafe.docx", document)
    monkeypatch.setattr("sourcepilot.ingest.MAX_DOCUMENT_EXPANDED_BYTES", 10, raising=False)
    with pytest.raises(ValueError, match="expanded"):
        extract_passages("large.docx", docx_bytes("<document>too much text</document>"))


def test_original_remains_downloadable_after_workspace_move(tmp_path: Path):
    store = ResearchStore(tmp_path / "original")
    item = store.import_bytes("note.txt", b"Retained evidence.", "upload:note.txt")
    moved = tmp_path / "moved"
    shutil.move(str(store.workspace), moved)
    client = TestClient(create_app(moved))
    response = client.get(f"/api/sources/{item['source_id']}/versions/{item['version_id']}/original")
    assert response.status_code == 200
    assert response.content == b"Retained evidence."


def test_corrupt_original_is_not_served_or_silently_reused(tmp_path: Path):
    store = ResearchStore(tmp_path / "workspace")
    item = store.import_bytes("note.txt", b"Original evidence.", "upload:note.txt")
    Path(item["object_path"]).write_bytes(b"Tampered evidence.")
    client = TestClient(create_app(store.workspace))
    response = client.get(f"/api/sources/{item['source_id']}/versions/{item['version_id']}/original")
    assert response.status_code == 409
    with pytest.raises(ValueError, match="integrity"):
        store.import_bytes("other.txt", b"Original evidence.", "upload:other.txt")


@pytest.mark.parametrize("payload", [{"text": "A claim", "passage_id": "bad"}, {"text": [], "passage_id": 1}, [], None])
def test_malformed_claim_payload_is_client_error(tmp_path: Path, payload):
    client = TestClient(create_app(tmp_path / "workspace"), raise_server_exceptions=False)
    token = client.get("/api/bootstrap").json()["write_token"]
    response = client.post("/api/claims", json=payload, headers={"X-SourcePilot-Token": token})
    assert response.status_code == 422


def test_url_connects_to_validated_address_not_a_second_dns_answer(monkeypatch):
    class ResponseSocket:
        def sendall(self, data):
            pass

        def makefile(self, *args):
            return BytesIO(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 8\r\n\r\nEvidence")

        def close(self):
            pass

    monkeypatch.setattr("socket.getaddrinfo", lambda *args, **kwargs: [(2, 1, 6, "", ("93.184.216.34", 80))])

    def connect(address, *args, **kwargs):
        assert address == ("93.184.216.34", 80), "Connection must use validated numeric address"
        return ResponseSocket()

    monkeypatch.setattr("socket.create_connection", connect)
    name, data, origin = fetch_url("http://example.org/note")
    assert data == b"Evidence"
    assert name == "note.txt"
    assert origin == "http://example.org/note"


def test_database_identifiers_are_bounded_before_sqlite(tmp_path):
    client = TestClient(create_app(tmp_path / "workspace"), raise_server_exceptions=False)
    token = client.get("/api/bootstrap").json()["write_token"]
    headers = {"X-SourcePilot-Token": token}
    too_large = 2 ** 63
    assert client.post("/api/claims", json={"text": "A claim", "passage_id": too_large}, headers=headers).status_code == 422
    assert client.get(f"/api/sources/{too_large}/versions").status_code == 422
    assert client.get("/api/search", params={"source_id": too_large}).status_code == 422
    assert client.post(f"/api/ai/sources/{too_large}/suggest", headers=headers).status_code == 422


@pytest.mark.parametrize("streamed", [False, True])
def test_json_body_limit_applies_before_parsing(tmp_path, streamed):
    client = TestClient(create_app(tmp_path / "workspace"), raise_server_exceptions=False)
    token = client.get("/api/bootstrap").json()["write_token"]
    data = b'{"text":"' + b'x' * 70000 + b'","passage_id":1}'
    content = iter([data[:35000], data[35000:]]) if streamed else data
    response = client.post("/api/claims", content=content, headers={"X-SourcePilot-Token": token, "Content-Type": "application/json"})
    assert response.status_code == 413
    assert "limit" in response.json()["detail"].lower()
