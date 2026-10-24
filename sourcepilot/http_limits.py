"""Reject oversized requests before JSON parsing or upload buffering."""

from fastapi import HTTPException
from starlette.datastructures import Headers
from starlette.responses import JSONResponse

from .ingest import MAX_IMPORT_BYTES

MAX_JSON_BYTES = 64 * 1024


class RequestBodyLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        limit = MAX_IMPORT_BYTES if scope["path"] == "/api/import" else MAX_JSON_BYTES
        declared = Headers(scope=scope).get("content-length")
        if declared is not None and (not declared.isdigit() or int(declared) > limit):
            status = 413 if declared.isdigit() else 400
            return await JSONResponse({"detail": "Request body exceeds the size limit or has invalid length"}, status_code=status)(scope, receive, send)
        total = 0

        async def bounded_receive():
            nonlocal total
            message = await receive()
            if message["type"] == "http.request":
                total += len(message.get("body", b""))
                if total > limit:
                    raise HTTPException(status_code=413, detail="Request body exceeds the size limit")
            return message

        await self.app(scope, bounded_receive, send)
