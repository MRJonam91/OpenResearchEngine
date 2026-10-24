"""Loopback web API for the local research workspace."""

from __future__ import annotations

import json
import os
from pathlib import Path
from secrets import token_urlsafe
import shutil
import tempfile
from urllib.parse import unquote, urlsplit

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.background import BackgroundTask

from .ingest import MAX_IMPORT_BYTES
from .research import ResearchService
from .schemas import ClaimInput, EvidenceInput, ReviewInput, RouteIdentifier, TextInput, URLInput
from .http_limits import RequestBodyLimit
from .store import ResearchStore


def create_app(workspace: str | Path, *, model: str | None = None, embedding_model: str | None = None, ollama_url: str | None = None) -> FastAPI:
    store = ResearchStore(workspace)
    research = ResearchService(store)
    write_token = token_urlsafe(32)
    app = FastAPI(title="SourcePilot", version="1.0.0", docs_url=None, redoc_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])
    app.add_middleware(RequestBodyLimit)
    static = Path(__file__).with_name("static")
    app.mount("/static", StaticFiles(directory=static), name="static")

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=400, content={"detail": str(exc)})

    def require_write_token(request: Request) -> None:
        if request.headers.get("x-sourcepilot-token") != write_token:
            raise HTTPException(status_code=403, detail="Write token required")
        origin = request.headers.get("origin")
        if origin:
            try:
                parsed = urlsplit(origin)
                valid = parsed.scheme == request.url.scheme and parsed.netloc.lower() == request.headers.get("host", "").lower() and not (parsed.path or parsed.query or parsed.fragment)
            except ValueError:
                valid = False
            if not valid:
                raise HTTPException(status_code=403, detail="Cross-origin write is not allowed")

    from .ai import AIService, OllamaClient
    from .ai_api import mount_ai_routes

    ai = AIService(
        store, OllamaClient(ollama_url or os.getenv("SOURCEPILOT_OLLAMA_URL", "http://127.0.0.1:11434")),
        model=model if model is not None else os.getenv("SOURCEPILOT_AI_MODEL", ""),
        embedding_model=embedding_model if embedding_model is not None else os.getenv("SOURCEPILOT_EMBEDDING_MODEL", ""),
    )
    mount_ai_routes(app, ai, require_write_token)

    @app.get("/")
    def index():
        return FileResponse(static / "index.html")

    @app.get("/api/bootstrap")
    def bootstrap():
        return Response(
            content=json.dumps({"write_token": write_token, "workspace": str(store.workspace)}),
            media_type="application/json",
            headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"},
        )

    @app.get("/api/sources")
    def sources():
        return store.list_sources()

    @app.get("/api/workspace/health")
    def workspace_health():
        from .maintenance import diagnose

        return diagnose(store)

    @app.post("/api/workspace/backup", dependencies=[Depends(require_write_token)])
    def workspace_backup():
        from .maintenance import backup_workspace

        directory = tempfile.mkdtemp(prefix="sourcepilot-backup-")
        try:
            output = Path(directory) / "sourcepilot-backup.zip"
            backup_workspace(store, output)
            return FileResponse(output, filename=output.name, media_type="application/zip", background=BackgroundTask(shutil.rmtree, directory))
        except Exception:
            shutil.rmtree(directory)
            raise

    @app.get("/api/sources/{source_id}/passages")
    def passages(source_id: RouteIdentifier, version_id: RouteIdentifier | None = None):
        return store.list_passages(source_id, version_id)

    @app.get("/api/sources/{source_id}/versions")
    def versions(source_id: RouteIdentifier):
        return store.list_versions(source_id)

    @app.get("/api/sources/{source_id}/versions/{version_id}/original")
    def original(source_id: RouteIdentifier, version_id: RouteIdentifier):
        try:
            version = store.get_version(source_id, version_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        try:
            path = store.original_path(version["sha256"])
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return FileResponse(
            path, media_type="application/octet-stream", filename=version["title"],
            headers={"X-Content-Type-Options": "nosniff"},
        )

    @app.post("/api/import", dependencies=[Depends(require_write_token)])
    async def import_upload(request: Request):
        try:
            length = int(request.headers.get("content-length", "0"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid content length") from exc
        if length > MAX_IMPORT_BYTES:
            raise HTTPException(status_code=413, detail="File exceeds 20 MB")
        name = Path(unquote(request.headers.get("x-file-name", "")).replace("\\", "/")).name
        relative = unquote(request.headers.get("x-relative-path", name)).replace("\\", "/")
        if not name or relative.startswith("/") or ".." in relative.split("/"):
            raise HTTPException(status_code=400, detail="Invalid file name")
        chunks = []
        total = 0
        async for chunk in request.stream():
            total += len(chunk)
            if total > MAX_IMPORT_BYTES:
                raise HTTPException(status_code=413, detail="File exceeds 20 MB")
            chunks.append(chunk)
        data = b"".join(chunks)
        return store.import_bytes(name, data, f"upload:{relative}")

    @app.post("/api/import-url", dependencies=[Depends(require_write_token)])
    def import_url(payload: URLInput):
        return store.import_url(payload.url)

    @app.get("/api/search")
    def search(q: str = "", include_history: bool = False, source_id: RouteIdentifier | None = None):
        return research.search(q, include_history=include_history, source_id=source_id)

    @app.get("/api/compare")
    def compare(left_id: RouteIdentifier, right_id: RouteIdentifier, q: str):
        return research.compare(left_id, right_id, q)

    @app.get("/api/claims")
    def claims():
        return research.list_claims()

    @app.post("/api/claims", dependencies=[Depends(require_write_token)])
    def create_claim(payload: ClaimInput):
        return research.create_claim(payload.text, payload.passage_id)

    @app.patch("/api/claims/{claim_id}", dependencies=[Depends(require_write_token)])
    def review_claim(claim_id: RouteIdentifier, payload: ReviewInput):
        return research.review_claim(claim_id, payload.status, payload.note)

    @app.patch("/api/claims/{claim_id}/text", dependencies=[Depends(require_write_token)])
    def edit_claim(claim_id: RouteIdentifier, payload: TextInput):
        return research.edit_claim(claim_id, payload.text)

    @app.get("/api/claims/{claim_id}/revisions")
    def revisions(claim_id: RouteIdentifier):
        return research.list_revisions(claim_id)

    @app.post("/api/claims/{claim_id}/evidence", dependencies=[Depends(require_write_token)])
    def add_evidence(claim_id: RouteIdentifier, payload: EvidenceInput):
        return research.add_evidence(claim_id, payload.passage_id, payload.stance)

    @app.delete("/api/claims/{claim_id}/evidence/{passage_id}", dependencies=[Depends(require_write_token)])
    def remove_evidence(claim_id: RouteIdentifier, passage_id: RouteIdentifier):
        return research.remove_evidence(claim_id, passage_id)

    @app.get("/api/report.md")
    def report(include_proposed: bool = False):
        return PlainTextResponse(
            research.render_report(include_proposed),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="sourcepilot-report.md"'},
        )

    @app.get("/api/report.pdf")
    def report_pdf(include_proposed: bool = False):
        return Response(
            research.render_pdf_report(include_proposed),
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="sourcepilot-report.pdf"', "X-Content-Type-Options": "nosniff"},
        )

    return app
