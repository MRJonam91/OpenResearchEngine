"""SQLite-backed source store with immutable original objects."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import re
import sqlite3
import tempfile
from typing import Iterator

from .ingest import MAX_IMPORT_BYTES, extract_passages, fetch_url


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ResearchStore:
    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace).expanduser().resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.objects = self.workspace / "objects"
        self.objects.mkdir(exist_ok=True)
        self.database = self.workspace / "research.sqlite3"
        with self.connect() as db:
            schema_version = db.execute("PRAGMA user_version").fetchone()[0]
            if schema_version > 3:
                raise ValueError("Workspace was created by a newer SourcePilot version")
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS source (
                    id INTEGER PRIMARY KEY, kind TEXT NOT NULL, origin TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS source_version (
                    id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL REFERENCES source(id),
                    sha256 TEXT NOT NULL, imported_at TEXT NOT NULL, object_path TEXT NOT NULL,
                    mime_type TEXT NOT NULL, status TEXT NOT NULL, error TEXT,
                    UNIQUE(source_id, sha256)
                );
                CREATE TABLE IF NOT EXISTS passage (
                    id INTEGER PRIMARY KEY, version_id INTEGER NOT NULL REFERENCES source_version(id),
                    position INTEGER NOT NULL, locator TEXT NOT NULL, text TEXT NOT NULL,
                    UNIQUE(version_id, position)
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS passage_fts USING fts5(text, passage_id UNINDEXED);
                CREATE TABLE IF NOT EXISTS claim (
                    id INTEGER PRIMARY KEY, text TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'proposed',
                    note TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, reviewed_at TEXT
                );
                CREATE TABLE IF NOT EXISTS evidence_link (
                    claim_id INTEGER NOT NULL REFERENCES claim(id),
                    passage_id INTEGER NOT NULL REFERENCES passage(id),
                    stance TEXT NOT NULL, PRIMARY KEY(claim_id, passage_id)
                );
                CREATE TABLE IF NOT EXISTS claim_revision (
                    id INTEGER PRIMARY KEY, claim_id INTEGER NOT NULL REFERENCES claim(id),
                    action TEXT NOT NULL, previous_text TEXT NOT NULL,
                    previous_status TEXT NOT NULL, previous_note TEXT NOT NULL,
                    previous_reviewed_at TEXT, changed_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS embedding (
                    passage_id INTEGER NOT NULL REFERENCES passage(id), model_key TEXT NOT NULL,
                    vector_json TEXT NOT NULL, created_at TEXT NOT NULL,
                    PRIMARY KEY(passage_id, model_key)
                );
                CREATE TABLE IF NOT EXISTS analysis_run (
                    id INTEGER PRIMARY KEY, kind TEXT NOT NULL, model TEXT NOT NULL,
                    model_digest TEXT NOT NULL, prompt_version TEXT NOT NULL,
                    input_sha256 TEXT NOT NULL, input_json TEXT NOT NULL,
                    result_json TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS accepted_suggestion (
                    run_id INTEGER NOT NULL REFERENCES analysis_run(id), item_index INTEGER NOT NULL,
                    claim_id INTEGER NOT NULL UNIQUE REFERENCES claim(id),
                    PRIMARY KEY(run_id, item_index)
                );
                CREATE INDEX IF NOT EXISTS source_version_latest ON source_version(source_id, id);
                CREATE INDEX IF NOT EXISTS revision_claim ON claim_revision(claim_id, id);
                CREATE INDEX IF NOT EXISTS embedding_model ON embedding(model_key, passage_id);
                """
            )
            db.execute("PRAGMA user_version = 3")

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.database, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def import_file(self, path: str | Path) -> dict:
        file_path = Path(path).expanduser().resolve(strict=True)
        if not file_path.is_file():
            raise ValueError("Import path must name a file")
        if file_path.stat().st_size > MAX_IMPORT_BYTES:
            raise ValueError("File exceeds the 20 MB limit")
        return self.import_bytes(file_path.name, file_path.read_bytes(), str(file_path), kind="file")

    def import_url(self, url: str) -> dict:
        name, data, final_url = fetch_url(url)
        return self.import_bytes(name, data, final_url, kind="url")

    def import_bytes(self, name: str, data: bytes, origin: str, kind: str = "upload") -> dict:
        passages = extract_passages(name, data)
        digest = sha256(data).hexdigest()
        object_path = self.objects / digest[:2] / digest
        with self.connect() as db:
            row = db.execute("SELECT id FROM source WHERE origin = ?", (origin,)).fetchone()
            if row:
                source_id = row["id"]
                version = db.execute(
                    "SELECT * FROM source_version WHERE source_id = ? AND sha256 = ?",
                    (source_id, digest),
                ).fetchone()
                if version:
                    self.original_path(digest)
                    return self._version_summary(db, version["id"])
            else:
                source_id = db.execute(
                    "INSERT INTO source(kind, origin, title, created_at) VALUES (?, ?, ?, ?)",
                    (kind, origin, name, _now()),
                ).lastrowid
            object_path.parent.mkdir(parents=True, exist_ok=True)
            if object_path.exists():
                self.original_path(digest)
            else:
                with tempfile.NamedTemporaryFile(dir=object_path.parent, delete=False) as output:
                    temporary = Path(output.name)
                    output.write(data)
                try:
                    temporary.replace(object_path)
                finally:
                    temporary.unlink(missing_ok=True)
            version_id = db.execute(
                "INSERT INTO source_version(source_id, sha256, imported_at, object_path, mime_type, status) "
                "VALUES (?, ?, ?, ?, ?, 'ready')",
                (source_id, digest, _now(), f"objects/{digest[:2]}/{digest}", Path(name).suffix.lower()),
            ).lastrowid
            for position, (locator, text) in enumerate(passages, 1):
                passage_id = db.execute(
                    "INSERT INTO passage(version_id, position, locator, text) VALUES (?, ?, ?, ?)",
                    (version_id, position, locator, text),
                ).lastrowid
                db.execute(
                    "INSERT INTO passage_fts(text, passage_id) VALUES (?, ?)", (text, passage_id)
                )
            return self._version_summary(db, version_id)

    def _version_summary(self, db: sqlite3.Connection, version_id: int) -> dict:
        row = db.execute(
            "SELECT sv.id AS version_id, sv.source_id, sv.sha256, sv.imported_at, "
            "sv.object_path, sv.status, s.title, s.origin, s.kind "
            "FROM source_version sv JOIN source s ON s.id = sv.source_id WHERE sv.id = ?",
            (version_id,),
        ).fetchone()
        result = dict(row)
        result["object_path"] = str(self.objects / result["sha256"][:2] / result["sha256"])
        return result

    def original_path(self, digest: str) -> Path:
        """Locate by content identity, never by a stale or arbitrary stored path."""
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Original integrity check failed: invalid SHA-256")
        path = (self.objects / digest[:2] / digest).resolve()
        if not path.is_relative_to(self.objects.resolve()):
            raise ValueError("Original integrity check failed: path outside workspace")
        if not path.is_file():
            raise FileNotFoundError("Original file is missing")
        if path.stat().st_size > MAX_IMPORT_BYTES or sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("Original integrity check failed: SHA-256 mismatch")
        return path

    def list_sources(self) -> list[dict]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT s.id AS source_id, s.kind, s.origin, s.title, sv.id AS version_id, "
                "sv.sha256, sv.imported_at, sv.status FROM source s "
                "JOIN source_version sv ON sv.id = (SELECT MAX(id) FROM source_version WHERE source_id = s.id) "
                "ORDER BY s.id DESC"
            ).fetchall()
            return [dict(row) for row in rows]

    def list_versions(self, source_id: int) -> list[dict]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT sv.id AS version_id, sv.source_id, sv.sha256, sv.imported_at, sv.status, "
                "sv.error, COUNT(p.id) AS passage_count FROM source_version sv "
                "LEFT JOIN passage p ON p.version_id = sv.id WHERE sv.source_id = ? "
                "GROUP BY sv.id ORDER BY sv.id DESC",
                (source_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_version(self, source_id: int, version_id: int) -> dict:
        with self.connect() as db:
            row = db.execute(
                "SELECT sv.id AS version_id, sv.source_id, sv.sha256, sv.imported_at, "
                "sv.object_path, sv.status, s.title, s.origin, s.kind "
                "FROM source_version sv JOIN source s ON s.id = sv.source_id "
                "WHERE sv.id = ? AND s.id = ?",
                (version_id, source_id),
            ).fetchone()
            if row is None:
                raise ValueError("Source version does not exist")
            return dict(row)

    def list_passages(self, source_id: int, version_id: int | None = None) -> list[dict]:
        with self.connect() as db:
            if version_id is None:
                version = db.execute(
                    "SELECT MAX(id) AS id FROM source_version WHERE source_id = ?", (source_id,)
                ).fetchone()
                version_id = version["id"]
            rows = db.execute(
                "SELECT p.id, p.version_id, p.position, p.locator, p.text, sv.sha256, "
                "sv.imported_at, s.title, s.origin FROM passage p "
                "JOIN source_version sv ON sv.id = p.version_id "
                "JOIN source s ON s.id = sv.source_id "
                "WHERE p.version_id = ? AND s.id = ? ORDER BY p.position",
                (version_id, source_id),
            ).fetchall()
            return [dict(row) for row in rows]

    def searchable_passages(self, include_history: bool = False) -> list[dict]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT p.id, p.version_id, p.locator, p.text, s.id AS source_id, s.title, "
                "s.origin, sv.sha256, sv.imported_at FROM passage p "
                "JOIN source_version sv ON sv.id = p.version_id JOIN source s ON s.id = sv.source_id "
                "WHERE ? OR sv.id = (SELECT MAX(id) FROM source_version WHERE source_id = s.id) ORDER BY p.id",
                (int(include_history),),
            ).fetchall()
            return [dict(row) for row in rows]
