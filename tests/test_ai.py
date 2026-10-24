from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Thread

import pytest

from sourcepilot.research import ResearchService
from sourcepilot.store import ResearchStore


@pytest.fixture
def provider():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def answer(self, value):
            encoded = json.dumps(value).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def do_GET(self):
            self.answer({"models": [{"name": "embed:test", "digest": self.server.digest}, {"name": "writer:test", "digest": "b" * 64}]})

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if self.path == "/api/show":
                self.answer({"capabilities": ["embedding"] if payload["model"] == "embed:test" else ["completion"]})
            elif self.path == "/api/embed":
                self.server.embed_batches += 1
                assert payload["truncate"] is False
                self.answer({"model": "embed:test", "embeddings": [[1.0, 0.0] if any(word in text.lower() for word in ("cats", "feline")) else [0.0, 1.0] for text in payload["input"]]})
            elif self.path == "/api/generate":
                self.answer({"model": "writer:test", "response": json.dumps(self.server.reply), "done": True, "done_reason": "stop"})

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.digest = "a" * 64
    server.embed_batches = 0
    server.reply = {"claims": [{"text": "Cats are mammals.", "passage_id": 1, "quote": "Cats are small mammals."}]}
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()
    thread.join()


def service(tmp_path, provider):
    from sourcepilot.ai import AIService, OllamaClient

    store = ResearchStore(tmp_path / "workspace")
    a = store.import_bytes("cats.txt", b"Cats are small mammals.", "upload:cats.txt")
    b = store.import_bytes("budget.txt", b"The fiscal budget is 12 units.", "upload:budget.txt")
    ai = AIService(store, OllamaClient(f"http://127.0.0.1:{provider.server_port}"), model="writer:test", embedding_model="embed:test")
    return store, ai, a, b


def test_semantic_index_ranks_synonym_caches_and_changes_model_identity(tmp_path, provider):
    store, ai, a, _ = service(tmp_path, provider)
    first = ai.index()
    assert first["indexed"] == first["total"] == 2
    batches = provider.embed_batches
    assert ai.index()["newly_indexed"] == 0
    assert provider.embed_batches == batches
    result = ai.semantic_search("feline")
    assert result["results"][0]["source_id"] == a["source_id"]
    assert result["coverage"]["complete"] is True
    provider.digest = "c" * 64
    with pytest.raises(ValueError, match="index"):
        ai.semantic_search("feline")
    assert ai.index()["newly_indexed"] == 2


def test_latest_search_and_index_coverage_are_explicit(tmp_path, provider):
    store, ai, a, _ = service(tmp_path, provider)
    assert ai.index(limit=1)["remaining"] == 1
    result = ai.semantic_search("feline")
    assert result["coverage"]["complete"] is False
    store.import_bytes("cats.txt", b"Revised evidence about cats.", "upload:cats.txt")
    ai.index()
    latest = ai.semantic_search("feline")
    assert all(row["version_id"] != a["version_id"] for row in latest["results"])
    history = ai.semantic_search("feline", include_history=True)
    assert any(row["version_id"] == a["version_id"] for row in history["results"])
    assert history["coverage"]["complete"] is True


def test_ai_suggestion_is_preview_then_explicit_idempotent_proposed_claim(tmp_path, provider):
    store, ai, a, _ = service(tmp_path, provider)
    run = ai.suggest(a["source_id"])
    assert ResearchService(store).list_claims() == []
    assert run["model_digest"] == "b" * 64
    assert run["coverage"]["complete"] is True
    claim = ai.accept(run["id"], 0)
    assert claim["status"] == "proposed"
    assert claim["evidence"][0]["passage_id"] == 1
    assert claim["provenance"]["run_id"] == run["id"]
    assert ai.accept(run["id"], 0)["id"] == claim["id"]


@pytest.mark.parametrize("passage_id,quote", [(999, "Cats are small mammals."), (1, "Invented quotation"), (2, "The fiscal budget is 12 units.")])
def test_invalid_or_out_of_scope_model_citations_never_persist(tmp_path, provider, passage_id, quote):
    store, ai, a, _ = service(tmp_path, provider)
    provider.reply = {"claims": [{"text": "Untrusted proposal", "passage_id": passage_id, "quote": quote}]}
    with pytest.raises(ValueError, match="citation|quote"):
        ai.suggest(a["source_id"])
    with store.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM analysis_run").fetchone()[0] == 0
    assert ResearchService(store).list_claims() == []


def test_candidate_disagreement_requires_citations_from_both_sides(tmp_path, provider):
    _, ai, a, b = service(tmp_path, provider)
    provider.reply = {"candidates": [{"left_passage_id": 1, "right_passage_id": 2, "left_quote": "Cats are small mammals.", "right_quote": "The fiscal budget is 12 units.", "reason": "This is only a candidate for human review."}]}
    result = ai.assess(a["source_id"], b["source_id"], "")
    assert len(result["result"]["candidates"]) == 1
    provider.reply["candidates"][0]["right_passage_id"] = 1
    with pytest.raises(ValueError, match="citation"):
        ai.assess(a["source_id"], b["source_id"], "")


def test_provider_rejects_remote_endpoint_and_wrong_model_capability(provider):
    from sourcepilot.ai import OllamaClient

    with pytest.raises(ValueError, match="loopback"):
        OllamaClient("https://example.org")
    client = OllamaClient(f"http://127.0.0.1:{provider.server_port}")
    with pytest.raises(ValueError, match="completion"):
        client.model_info("embed:test", "completion")
    with pytest.raises(ValueError, match="Ollama"):
        OllamaClient("http://127.0.0.1:1", timeout=0.1).model_info("missing", "completion")


def test_ai_api_requires_token_and_accepts_validated_proposal(tmp_path, provider):
    from fastapi.testclient import TestClient
    from sourcepilot.api import create_app

    store, _, a, _ = service(tmp_path, provider)
    app = create_app(store.workspace, model="writer:test", embedding_model="embed:test", ollama_url=f"http://127.0.0.1:{provider.server_port}")
    client = TestClient(app)
    token = client.get("/api/bootstrap").json()["write_token"]
    assert client.post("/api/ai/index", json={}).status_code == 403
    headers = {"X-SourcePilot-Token": token}
    assert client.post("/api/ai/index", json={}, headers=headers).json()["indexed"] == 2
    assert client.post("/api/ai/search", json={"query": "feline"}, headers=headers).json()["results"][0]["source_id"] == a["source_id"]
    run = client.post(f"/api/ai/sources/{a['source_id']}/suggest", headers=headers).json()
    response = client.post(f"/api/ai/runs/{run['id']}/accept/0", headers=headers)
    assert response.json()["status"] == "proposed"
    assert "Draft origin: AI" not in client.get("/api/report.md").text


def test_ai_rejects_blank_statement_despite_valid_quote(tmp_path, provider):
    _, ai, a, _ = service(tmp_path, provider)
    provider.reply["claims"][0]["text"] = "   "
    with pytest.raises(ValueError, match="schema"):
        ai.suggest(a["source_id"])


def test_filtered_assessment_reports_full_source_coverage(tmp_path, provider):
    store, ai, a, b = service(tmp_path, provider)
    store.import_bytes("cats.txt", b"Unique shared finding.\n\n" + b"Unrelated paragraph.\n\n" * 120, "upload:cats.txt")
    store.import_bytes("budget.txt", b"Unique shared finding.\n\n" + b"Other paragraph.\n\n" * 120, "upload:budget.txt")
    provider.reply = {"candidates": []}
    run = ai.assess(a["source_id"], b["source_id"], "Unique")
    coverage = run["coverage"]["left"]
    assert coverage["total_passages"] == 121
    assert coverage["matching_passages"] == coverage["retrieved_passages"] == coverage["selected_passages"] == 1
    assert coverage["retrieval_limit"] == 100
    assert coverage["complete"] is False


@pytest.mark.parametrize("vector", [[0, 0], [float('nan'), 1], [float('inf')], [True, 1], [], "bad"])
def test_invalid_embedding_vectors_are_rejected(vector):
    from sourcepilot.ollama import normalized
    with pytest.raises(ValueError, match="embedding"):
        normalized(vector)


def test_model_invalid_json_and_schema_are_rejected(tmp_path, provider):
    _, ai, a, _ = service(tmp_path, provider)
    provider.reply = {"claims": [], "unexpected": "not permitted"}
    with pytest.raises(ValueError, match="schema"):
        ai.suggest(a["source_id"])
    ai.client.request = lambda *args: {"response": "{broken", "done": True}
    with pytest.raises(ValueError, match="JSON"):
        ai.client.generate("writer:test", "system", "prompt", {})
