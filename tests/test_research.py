from pathlib import Path

import pytest

from sourcepilot.store import ResearchStore
from sourcepilot.research import ResearchService


def _research(tmp_path: Path):
    store = ResearchStore(tmp_path / "research")
    first = store.import_bytes("one.txt", b"The trial enrolled 120 people.\n", "upload:one.txt")
    second = store.import_bytes("two.txt", b"The trial enrolled 90 people.\n", "upload:two.txt")
    first_passage = store.list_passages(first["source_id"])[0]["id"]
    second_passage = store.list_passages(second["source_id"])[0]["id"]
    return ResearchService(store), first_passage, second_passage


def test_search_returns_real_passage_and_handles_punctuation(tmp_path: Path):
    research, first, _ = _research(tmp_path)
    results = research.search("enrolled 120")
    assert [item["id"] for item in results] == [first]
    assert research.search('"nonexistent:-') == []


def test_claim_review_retains_support_and_challenge(tmp_path: Path):
    research, first, second = _research(tmp_path)
    claim = research.create_claim("The trial enrolled 120 people.", first)
    research.add_evidence(claim["id"], second, "challenges")
    reviewed = research.review_claim(claim["id"], "uncertain", "Sources disagree on the cohort.")

    assert reviewed["status"] == "uncertain"
    assert reviewed["reviewed_at"]
    assert reviewed["disputed"] is True
    assert {item["stance"] for item in reviewed["evidence"]} == {"supports", "challenges"}
    assert [item["origin"] for item in reviewed["evidence"]] == ["upload:one.txt", "upload:two.txt"]


def test_report_excludes_unreviewed_and_rejected_by_default(tmp_path: Path):
    research, first, second = _research(tmp_path)
    accepted = research.create_claim("The trial enrolled 120 people.", first)
    research.add_evidence(accepted["id"], second, "challenges")
    research.review_claim(accepted["id"], "uncertain", "Counts differ.")
    proposed = research.create_claim("This is a proposal.", first)
    rejected = research.create_claim("This was rejected.", first)
    research.review_claim(rejected["id"], "rejected", "Incorrect.")

    report = research.render_report()
    assert "The trial enrolled 120 people." in report
    assert "This is a proposal." not in report
    assert "This was rejected." not in report
    assert "upload:one.txt" in report
    assert "upload:two.txt" in report
    assert "lines 1-1" in report
    assert "SHA-256" in report
    assert "Challenges" in report
    assert "This is a proposal." in research.render_report(include_proposed=True)
    assert proposed["id"] in [claim["id"] for claim in research.list_claims()]


def test_review_rejects_invalid_status(tmp_path: Path):
    research, first, _ = _research(tmp_path)
    claim = research.create_claim("A claim", first)
    with pytest.raises(ValueError, match="status"):
        research.review_claim(claim["id"], "verified")
