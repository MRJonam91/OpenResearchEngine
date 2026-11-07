import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from sourcepilot.api import create_app
from sourcepilot.__main__ import main
from sourcepilot.report import render_json_report
from sourcepilot.research import ResearchService
from sourcepilot.store import ResearchStore


def test_delete_claim_cleans_up(tmp_path: Path):
    store = ResearchStore(tmp_path / "workspace")
    imported = store.import_bytes("notes.txt", b"First fact.\n\nSecond fact.\n", "upload:notes.txt")
    passages = store.list_passages(imported["source_id"])
    research = ResearchService(store)

    claim = research.create_claim("First fact assertion.", passages[0]["id"])
    research.add_evidence(claim["id"], passages[1]["id"], "context")
    research.review_claim(claim["id"], "approved", "Good claim.")

    assert len(research.list_revisions(claim["id"])) >= 2
    assert len(research.list_claims()) == 1

    res = research.delete_claim(claim["id"])
    assert res == {"deleted": True, "claim_id": claim["id"]}
    assert len(research.list_claims()) == 0

    with pytest.raises(ValueError, match="does not exist"):
        research.get_claim(claim["id"])

    with pytest.raises(ValueError, match="does not exist"):
        research.delete_claim(claim["id"])


def test_delete_source_lifecycle(tmp_path: Path):
    store = ResearchStore(tmp_path / "workspace")
    imported = store.import_bytes("sample.txt", b"Independent content for deletion test.", "upload:sample.txt")
    source_id = imported["source_id"]
    digest = imported["sha256"]
    obj_file = store.objects / digest[:2] / digest
    assert obj_file.is_file()

    # Successful deletion when no claims reference it
    result = store.delete_source(source_id)
    assert result == {"deleted": True, "source_id": source_id}
    assert store.list_sources() == []
    assert store.list_passages(source_id) == []
    # Verify disk object was removed as no other versions reference it
    assert not obj_file.exists()

    with pytest.raises(ValueError, match="Source does not exist"):
        store.delete_source(source_id)


def test_delete_source_blocked_by_referenced_claim(tmp_path: Path):
    store = ResearchStore(tmp_path / "workspace")
    imported = store.import_bytes("linked.txt", b"Evidence linked to claim.", "upload:linked.txt")
    passages = store.list_passages(imported["source_id"])
    research = ResearchService(store)
    research.create_claim("Evidence proposition.", passages[0]["id"])

    with pytest.raises(ValueError, match="referenced by 1 claim"):
        store.delete_source(imported["source_id"])


def test_json_report_export(tmp_path: Path):
    store = ResearchStore(tmp_path / "workspace")
    imported = store.import_bytes("data.txt", b"Crucial data point 42.\n", "upload:data.txt")
    passages = store.list_passages(imported["source_id"])
    research = ResearchService(store)
    claim = research.create_claim("Crucial data is 42.", passages[0]["id"])
    research.review_claim(claim["id"], "approved", "Verified.")

    # 1. Direct function
    json_str = research.render_json_report()
    data = json.loads(json_str)
    assert data["title"] == "SourcePilot Research Report"
    assert data["total_claims"] == 1
    assert data["claims"][0]["id"] == claim["id"]

    # 2. REST API
    client = TestClient(create_app(store.workspace))
    resp = client.get("/api/report.json")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    api_data = resp.json()
    assert api_data["total_claims"] == 1

    # 3. CLI
    out_file = tmp_path / "report.json"
    assert main(["report", "--output", str(out_file), "--workspace", str(store.workspace)]) == 0
    assert out_file.exists()
    cli_data = json.loads(out_file.read_text(encoding="utf-8"))
    assert cli_data["total_claims"] == 1


def test_api_and_cli_delete_endpoints(tmp_path: Path, capsys):
    workspace = tmp_path / "workspace"
    app = create_app(workspace)
    client = TestClient(app)
    token = client.get("/api/bootstrap").json()["write_token"]
    headers = {"X-SourcePilot-Token": token}

    imported = client.post("/api/import", content=b"CLI deletion test data.\n", headers={**headers, "X-File-Name": "del.txt"}).json()
    source_id = imported["source_id"]
    passage_id = client.get(f"/api/sources/{source_id}/passages").json()[0]["id"]
    claim = client.post("/api/claims", json={"text": "To be deleted via CLI.", "passage_id": passage_id}, headers=headers).json()
    claim_id = claim["id"]

    # Delete claim via CLI
    assert main(["delete-claim", str(claim_id), "--workspace", str(workspace)]) == 0
    cli_res = json.loads(capsys.readouterr().out)
    assert cli_res["deleted"] is True
    assert client.get("/api/claims").json() == []

    # Delete source via API
    del_resp = client.delete(f"/api/sources/{source_id}", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True
    assert client.get("/api/sources").json() == []


def test_csv_and_tsv_ingest(tmp_path: Path):
    store = ResearchStore(tmp_path / "workspace")
    csv_bytes = b"id,name,value\n1,alpha,10\n2,beta,20\n"
    csv_item = store.import_bytes("table.csv", csv_bytes, "upload:table.csv")
    csv_passages = store.list_passages(csv_item["source_id"])
    assert len(csv_passages) >= 1
    assert "alpha" in csv_passages[0]["text"]

    tsv_bytes = b"col1\tcol2\nval1\tval2\n"
    tsv_item = store.import_bytes("table.tsv", tsv_bytes, "upload:table.tsv")
    tsv_passages = store.list_passages(tsv_item["source_id"])
    assert len(tsv_passages) >= 1
    assert "val1" in tsv_passages[0]["text"]
