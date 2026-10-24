import json
from pathlib import Path

from fastapi.testclient import TestClient

from sourcepilot.api import create_app
from sourcepilot.__main__ import main


def test_api_upload_search_review_and_report(tmp_path: Path):
    app = create_app(tmp_path / "research")
    client = TestClient(app)
    token = client.get("/api/bootstrap").json()["write_token"]
    headers = {"X-SourcePilot-Token": token}

    assert client.post("/api/import", content=b"Evidence says 42 items.\n", headers={"X-File-Name": "note.txt"}).status_code == 403
    imported = client.post("/api/import", content=b"Evidence says 42 items.\n", headers={**headers, "X-File-Name": "note.txt"})
    assert imported.status_code == 200
    source_id = imported.json()["source_id"]
    passage_id = client.get(f"/api/sources/{source_id}/passages").json()[0]["id"]
    assert client.get("/api/search", params={"q": "42 items"}).json()[0]["id"] == passage_id

    claim = client.post("/api/claims", json={"text": "There are 42 items.", "passage_id": passage_id}, headers=headers)
    assert claim.status_code == 200
    claim_id = claim.json()["id"]
    reviewed = client.patch(f"/api/claims/{claim_id}", json={"status": "approved", "note": "Checked."}, headers=headers)
    assert reviewed.json()["status"] == "approved"
    report = client.get("/api/report.md")
    assert "There are 42 items." in report.text
    assert "note.txt" in report.text


def test_cli_round_trip_and_no_report_overwrite(tmp_path: Path, capsys):
    workspace = tmp_path / "research"
    original = tmp_path / "note.txt"
    original.write_text("The budget is 12.\n", encoding="utf-8")
    assert main(["import", str(original), "--workspace", str(workspace)]) == 0
    imported = json.loads(capsys.readouterr().out)
    assert main(["search", "budget", "--workspace", str(workspace)]) == 0
    result = json.loads(capsys.readouterr().out)[0]
    assert main(["claim", "The budget is 12.", "--passage", str(result["id"]), "--workspace", str(workspace)]) == 0
    claim = json.loads(capsys.readouterr().out)
    assert main(["review", str(claim["id"]), "--status", "approved", "--workspace", str(workspace)]) == 0
    capsys.readouterr()
    report = tmp_path / "result.md"
    assert main(["report", "--output", str(report), "--workspace", str(workspace)]) == 0
    assert "The budget is 12." in report.read_text(encoding="utf-8")
    assert main(["report", "--output", str(report), "--workspace", str(workspace)]) == 2
    assert imported["status"] == "ready"


def test_streamed_upload_stops_at_size_limit(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("sourcepilot.api.MAX_IMPORT_BYTES", 12)
    client = TestClient(create_app(tmp_path / "research"))
    token = client.get("/api/bootstrap").json()["write_token"]
    response = client.post(
        "/api/import",
        content=iter([b"first chunk", b" and more"]),
        headers={"X-SourcePilot-Token": token, "X-File-Name": "large.txt"},
    )
    assert response.status_code == 413
    assert client.get("/api/sources").json() == []
