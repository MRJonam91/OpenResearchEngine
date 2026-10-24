"""Browser-origin and Host boundaries for a loopback-only service."""

from pathlib import Path

from fastapi.testclient import TestClient

from sourcepilot.api import create_app


def test_unknown_host_cannot_read_bootstrap_token(tmp_path: Path):
    client = TestClient(create_app(tmp_path / "workspace"))
    response = client.get("/api/bootstrap", headers={"Host": "attacker.example"})
    assert response.status_code == 400


def test_cross_origin_write_rejected_even_with_valid_token(tmp_path: Path):
    client = TestClient(create_app(tmp_path / "workspace"))
    token = client.get("/api/bootstrap").json()["write_token"]
    response = client.post(
        "/api/import",
        headers={"X-SourcePilot-Token": token, "X-File-Name": "note.txt", "Origin": "https://attacker.example"},
        content=b"Some text.",
    )
    assert response.status_code == 403
    assert client.get("/api/sources").json() == []


def test_same_origin_and_token_can_write(tmp_path: Path):
    client = TestClient(create_app(tmp_path / "workspace"))
    token = client.get("/api/bootstrap").json()["write_token"]
    response = client.post(
        "/api/import",
        headers={"X-SourcePilot-Token": token, "X-File-Name": "note.txt", "Origin": "http://testserver"},
        content=b"Some text.",
    )
    assert response.status_code == 200
