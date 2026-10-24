from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sourcepilot.api import create_app
from sourcepilot.research import ResearchService
from sourcepilot.store import ResearchStore


def test_compare_groups_latest_passages_by_source(tmp_path: Path):
    store = ResearchStore(tmp_path / "workspace")
    left = store.import_bytes("first.txt", b"The estimate is 10 units.\n", "upload:first.txt")
    right = store.import_bytes("second.txt", b"The estimate is 14 units.\n", "upload:second.txt")
    store.import_bytes("first.txt", b"The revised estimate is 12 units.\n", "upload:first.txt")
    research = ResearchService(store)

    compared = research.compare(left["source_id"], right["source_id"], "estimate")
    assert compared["left"]["source"]["title"] == "first.txt"
    assert [p["text"] for p in compared["left"]["passages"]] == ["The revised estimate is 12 units."]
    assert [p["text"] for p in compared["right"]["passages"]] == ["The estimate is 14 units."]
    assert compared["left"]["passages"][0]["source_id"] == left["source_id"]


def test_compare_requires_two_existing_sources_and_query(tmp_path: Path):
    store = ResearchStore(tmp_path / "workspace")
    first = store.import_bytes("first.txt", b"Some evidence.\n", "upload:first.txt")
    research = ResearchService(store)
    with pytest.raises(ValueError, match="two different"):
        research.compare(first["source_id"], first["source_id"], "evidence")
    with pytest.raises(ValueError, match="does not exist"):
        research.compare(first["source_id"], 999, "evidence")
    with pytest.raises(ValueError, match="query"):
        research.compare(first["source_id"], 999, " ")


def test_compare_api_returns_grouped_results(tmp_path: Path):
    store = ResearchStore(tmp_path / "workspace")
    left = store.import_bytes("a.txt", b"Growth is 3 percent.\n", "upload:a.txt")
    right = store.import_bytes("b.txt", b"Growth is 4 percent.\n", "upload:b.txt")
    client = TestClient(create_app(store.workspace))
    response = client.get("/api/compare", params={"left_id": left["source_id"], "right_id": right["source_id"], "q": "Growth"})
    assert response.status_code == 200
    assert response.json()["right"]["passages"][0]["text"] == "Growth is 4 percent."
