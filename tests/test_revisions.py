from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sourcepilot.api import create_app
from sourcepilot.research import ResearchService
from sourcepilot.store import ResearchStore


def _claim(tmp_path: Path):
    store = ResearchStore(tmp_path / "workspace")
    item = store.import_bytes("notes.txt", b"First passage.\n\nSecond passage.\n", "upload:notes.txt")
    first, second = [row["id"] for row in store.list_passages(item["source_id"])]
    service = ResearchService(store)
    claim = service.create_claim("Initial statement.", first)
    return store, service, claim["id"], first, second


def test_statement_edit_resets_approval_and_records_previous_text(tmp_path: Path):
    _, research, claim_id, _, _ = _claim(tmp_path)
    research.review_claim(claim_id, "approved", "Checked against source.")
    edited = research.edit_claim(claim_id, "Corrected statement.")
    assert edited["text"] == "Corrected statement."
    assert edited["status"] == "proposed"
    assert edited["note"] == ""
    assert edited["reviewed_at"] is None
    revisions = research.list_revisions(claim_id)
    assert [(row["action"], row["previous_text"], row["previous_status"]) for row in revisions] == [
        ("edit", "Initial statement.", "approved"),
        ("review", "Initial statement.", "proposed"),
    ]


def test_evidence_can_change_stance_and_be_removed_but_not_last_link(tmp_path: Path):
    _, research, claim_id, first, second = _claim(tmp_path)
    research.add_evidence(claim_id, second, "challenges")
    assert research.get_claim(claim_id)["disputed"] is True
    research.add_evidence(claim_id, second, "context")
    assert research.get_claim(claim_id)["disputed"] is False
    research.remove_evidence(claim_id, second)
    with pytest.raises(ValueError, match="last evidence"):
        research.remove_evidence(claim_id, first)
    assert [row["passage_id"] for row in research.get_claim(claim_id)["evidence"]] == [first]


def test_alpha_workspace_migrates_without_changing_claim_ids(tmp_path: Path):
    store, research, claim_id, first, _ = _claim(tmp_path)
    with store.connect() as db:
        db.execute("DROP TABLE IF EXISTS claim_revision")
        db.execute("PRAGMA user_version = 0")
    reopened = ResearchService(ResearchStore(store.workspace))
    assert reopened.get_claim(claim_id)["evidence"][0]["passage_id"] == first
    reopened.edit_claim(claim_id, "Changed after migration.")
    assert reopened.list_revisions(claim_id)[0]["previous_text"] == "Initial statement."


def test_api_rejects_unauthorized_evidence_removal(tmp_path: Path):
    store, research, claim_id, _, second = _claim(tmp_path)
    research.add_evidence(claim_id, second, "context")
    client = TestClient(create_app(store.workspace))
    assert client.delete(f"/api/claims/{claim_id}/evidence/{second}").status_code == 403
    token = client.get("/api/bootstrap").json()["write_token"]
    response = client.delete(f"/api/claims/{claim_id}/evidence/{second}", headers={"X-SourcePilot-Token": token})
    assert response.status_code == 200
    assert len(response.json()["evidence"]) == 1


def test_evidence_changes_invalidate_prior_review(tmp_path: Path):
    _, research, claim_id, first, second = _claim(tmp_path)
    research.review_claim(claim_id, "approved", "Reviewed original evidence.")
    added = research.add_evidence(claim_id, second, "challenges")
    assert added["status"] == "proposed"
    assert added["note"] == ""
    assert research.list_revisions(claim_id)[0]["action"].startswith("evidence:add:")

    research.review_claim(claim_id, "approved")
    changed = research.add_evidence(claim_id, second, "context")
    assert changed["status"] == "proposed"
    assert research.list_revisions(claim_id)[0]["action"].startswith("evidence:stance:")

    research.review_claim(claim_id, "approved")
    removed = research.remove_evidence(claim_id, second)
    assert removed["status"] == "proposed"
    assert research.list_revisions(claim_id)[0]["action"].startswith("evidence:remove:")
    count = len(research.list_revisions(claim_id))
    research.add_evidence(claim_id, first, "supports")
    assert len(research.list_revisions(claim_id)) == count
