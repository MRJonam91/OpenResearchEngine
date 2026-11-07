import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from sourcepilot.api import create_app
from sourcepilot.__main__ import main
from sourcepilot.maintenance import diagnose
from sourcepilot.research import ResearchService
from sourcepilot.store import ResearchStore


def _setup_workspace(tmp_path: Path):
    workspace = tmp_path / "research"
    store = ResearchStore(workspace)
    first = store.import_bytes("source_a.txt", b"First study with 50 participants.\n", "upload:source_a.txt")
    second = store.import_bytes("source_b.txt", b"Second study with 100 participants.\n", "upload:source_b.txt")
    p1 = store.list_passages(first["source_id"])[0]["id"]
    p2 = store.list_passages(second["source_id"])[0]["id"]
    research = ResearchService(store)
    c1 = research.create_claim("There were 50 participants in study A.", p1)
    c2 = research.create_claim("There were 100 participants in study B.", p2)
    research.review_claim(c1["id"], "approved", "Verified from source A.")
    research.review_claim(c2["id"], "uncertain", "Pending further checks.")
    return workspace, store, research, (c1["id"], c2["id"])


def test_list_claims_filter_and_validation(tmp_path: Path):
    _, store, research, (c1_id, c2_id) = _setup_workspace(tmp_path)

    all_claims = research.list_claims()
    assert len(all_claims) == 2

    approved = research.list_claims(status="approved")
    assert len(approved) == 1
    assert approved[0]["id"] == c1_id
    assert approved[0]["status"] == "approved"

    uncertain = research.list_claims(status="uncertain")
    assert len(uncertain) == 1
    assert uncertain[0]["id"] == c2_id

    proposed = research.list_claims(status="proposed")
    assert len(proposed) == 0

    with pytest.raises(ValueError, match="Invalid claim status filter"):
        research.list_claims(status="invalid_status")


def test_api_claims_filter(tmp_path: Path):
    workspace, _, _, (c1_id, c2_id) = _setup_workspace(tmp_path)
    client = TestClient(create_app(workspace))

    all_resp = client.get("/api/claims")
    assert all_resp.status_code == 200
    assert len(all_resp.json()) == 2

    approved_resp = client.get("/api/claims", params={"status": "approved"})
    assert approved_resp.status_code == 200
    claims = approved_resp.json()
    assert len(claims) == 1
    assert claims[0]["id"] == c1_id

    invalid_resp = client.get("/api/claims", params={"status": "unknown"})
    assert invalid_resp.status_code == 400


def test_cli_sources_and_claims_commands(tmp_path: Path, capsys):
    workspace, _, _, (c1_id, c2_id) = _setup_workspace(tmp_path)

    assert main(["sources", "--workspace", str(workspace)]) == 0
    sources = json.loads(capsys.readouterr().out)
    assert len(sources) == 2
    assert {s["title"] for s in sources} == {"source_a.txt", "source_b.txt"}

    assert main(["claims", "--workspace", str(workspace)]) == 0
    claims = json.loads(capsys.readouterr().out)
    assert len(claims) == 2

    assert main(["claims", "--status", "approved", "--workspace", str(workspace)]) == 0
    approved_claims = json.loads(capsys.readouterr().out)
    assert len(approved_claims) == 1
    assert approved_claims[0]["id"] == c1_id


def test_diagnose_includes_claim_status_breakdown(tmp_path: Path):
    _, store, _, _ = _setup_workspace(tmp_path)
    report = diagnose(store)
    assert report["healthy"] is True
    assert "claim_statuses" in report
    assert report["claim_statuses"]["approved"] == 1
    assert report["claim_statuses"]["uncertain"] == 1
