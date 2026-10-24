"""HTTP adapters for optional local analysis."""

from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import Field

from .ai import AIService
from .schemas import Identifier, Payload, RouteIdentifier


class IndexInput(Payload):
    limit: Annotated[int, Field(strict=True, ge=1, le=500)] = 100
    include_history: Annotated[bool, Field(strict=True)] = False


class SemanticInput(Payload):
    query: Annotated[str, Field(strict=True, min_length=1, max_length=2000)]
    include_history: Annotated[bool, Field(strict=True)] = False


class AssessmentInput(Payload):
    left_id: Identifier
    right_id: Identifier
    query: Annotated[str, Field(strict=True, max_length=2000)] = ""


def mount_ai_routes(app: FastAPI, ai: AIService, require_write_token) -> None:
    writes = [Depends(require_write_token)]

    @app.get("/api/ai/status")
    def status():
        return ai.status()

    @app.post("/api/ai/index", dependencies=writes)
    def index(payload: IndexInput):
        return ai.index(payload.limit, payload.include_history)

    @app.post("/api/ai/search", dependencies=writes)
    def search(payload: SemanticInput):
        return ai.semantic_search(payload.query, payload.include_history)

    @app.post("/api/ai/sources/{source_id}/suggest", dependencies=writes)
    def suggest(source_id: RouteIdentifier):
        return ai.suggest(source_id)

    @app.post("/api/ai/assess", dependencies=writes)
    def assess(payload: AssessmentInput):
        return ai.assess(payload.left_id, payload.right_id, payload.query)

    @app.get("/api/ai/runs/{run_id}")
    def run(run_id: RouteIdentifier):
        return ai.get_run(run_id)

    @app.post("/api/ai/runs/{run_id}/accept/{index}", dependencies=writes)
    def accept(run_id: RouteIdentifier, index: Annotated[int, Field(ge=0, le=11)]):
        return ai.accept(run_id, index)
