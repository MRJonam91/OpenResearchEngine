"""Integrity diagnostics and portable, checksummed workspace backups."""

from __future__ import annotations

from contextlib import closing
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import sqlite3
import stat
import tempfile
from zipfile import BadZipFile, ZIP_DEFLATED, ZipFile

from .store import ResearchStore, _now

MAX_BACKUP_BYTES = 2 * 1024 * 1024 * 1024
MAX_MEMBERS = 100000


def _checksum(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def diagnose(store: ResearchStore) -> dict:
    issues = []
    with store.connect() as db:
        integrity = db.execute("PRAGMA quick_check").fetchone()[0]
        if integrity != "ok":
            issues.append({"kind": "database", "error": integrity})
        if db.execute("PRAGMA foreign_key_check").fetchone():
            issues.append({"kind": "database", "error": "Broken foreign key"})
        missing = db.execute("SELECT COUNT(*) FROM passage p LEFT JOIN passage_fts f ON f.passage_id = p.id AND f.text = p.text WHERE f.passage_id IS NULL").fetchone()[0]
        if missing:
            issues.append({"kind": "search_index", "error": f"{missing} passages missing from text index"})
        versions = db.execute("SELECT id, sha256 FROM source_version ORDER BY id").fetchall()
        counts = {name: db.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0] for name in ("source", "source_version", "passage", "claim")}
    for version in versions:
        try:
            store.original_path(version["sha256"])
        except (ValueError, OSError) as exc:
            issues.append({"kind": "original", "version_id": version["id"], "error": str(exc)})
    return {"healthy": not issues, "counts": counts, "issues": issues}


def backup_workspace(store: ResearchStore, output: str | Path) -> dict:
    output = Path(output).expanduser().resolve()
    if output.exists():
        raise FileExistsError("Backup output already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        with tempfile.TemporaryDirectory(prefix="sourcepilot-snapshot-") as temporary:
            snapshot = Path(temporary) / "research.sqlite3"
            with store.connect() as source, closing(sqlite3.connect(snapshot)) as target:
                source.backup(target)
            with closing(sqlite3.connect(snapshot)) as db:
                hashes = [row[0] for row in db.execute("SELECT DISTINCT sha256 FROM source_version")]
                db.execute("UPDATE source_version SET object_path = 'objects/' || substr(sha256, 1, 2) || '/' || sha256")
                db.commit()
            files = {"research.sqlite3": snapshot}
            for digest in hashes:
                files[f"objects/{digest[:2]}/{digest}"] = store.original_path(digest)
            total = sum(path.stat().st_size for path in files.values())
            if total > MAX_BACKUP_BYTES or len(files) > MAX_MEMBERS - 1:
                raise ValueError("Workspace exceeds the backup size/member limit")
            manifest = {"format": 1, "created_at": _now(), "files": {name: {"sha256": _checksum(path), "size": path.stat().st_size} for name, path in files.items()}}
            with output.open("xb") as stream:
                created = True
                with ZipFile(stream, "w", compression=ZIP_DEFLATED) as archive:
                    archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
                    for name, path in files.items():
                        archive.write(path, name)
        return {"backup": str(output), "sha256": _checksum(output), "files": len(files)}
    except Exception:
        if created:
            output.unlink(missing_ok=True)
        raise


def _valid_member(name: str) -> bool:
    if name in {"research.sqlite3", "manifest.json"}:
        return True
    match = re.fullmatch(r"objects/([0-9a-f]{2})/([0-9a-f]{64})", name)
    return bool(match and match[1] == match[2][:2])


def restore_workspace(archive_path: str | Path, destination: str | Path) -> ResearchStore:
    destination = Path(destination).expanduser().resolve()
    if destination.exists():
        raise FileExistsError("Restore destination already exists; choose a new directory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="sourcepilot-restore-", dir=destination.parent) as temporary:
            staging = Path(temporary)
            with ZipFile(archive_path) as archive:
                members = archive.infolist()
                names = [info.filename for info in members]
                if len(names) != len(set(names)) or len(names) > MAX_MEMBERS or any(not _valid_member(name) for name in names):
                    raise ValueError("Backup contains unexpected or duplicate members")
                if sum(info.file_size for info in members) > MAX_BACKUP_BYTES:
                    raise ValueError("Backup expanded size exceeds the limit")
                if any(stat.S_ISLNK(info.external_attr >> 16) for info in members):
                    raise ValueError("Backup symbolic links are not allowed")
                if archive.getinfo("manifest.json").file_size > 16 * 1024 * 1024:
                    raise ValueError("Backup manifest exceeds the size limit")
                manifest = json.loads(archive.read("manifest.json"))
                expected = manifest.get("files") if isinstance(manifest, dict) else None
                if not isinstance(expected, dict) or manifest.get("format") != 1 or set(expected) != set(names) - {"manifest.json"} or "research.sqlite3" not in expected:
                    raise ValueError("Invalid backup manifest")
                for name, metadata in expected.items():
                    if not isinstance(metadata, dict) or not isinstance(metadata.get("size"), int) or metadata["size"] < 0 or not re.fullmatch(r"[0-9a-f]{64}", str(metadata.get("sha256", ""))):
                        raise ValueError("Invalid backup file metadata")
                    if archive.getinfo(name).file_size != metadata["size"]:
                        raise ValueError("Backup size mismatch")
                    target = staging / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(name) as source, target.open("xb") as output:
                        shutil.copyfileobj(source, output, length=1024 * 1024)
                    if _checksum(target) != metadata["sha256"]:
                        raise ValueError("Backup checksum mismatch")
            with closing(sqlite3.connect((staging / "research.sqlite3").as_uri() + "?mode=ro", uri=True)) as db:
                db.execute("PRAGMA trusted_schema = OFF")
                if db.execute("PRAGMA quick_check").fetchone()[0] != "ok" or db.execute("PRAGMA foreign_key_check").fetchone():
                    raise ValueError("Backup database integrity check failed")
                if db.execute("SELECT 1 FROM sqlite_master WHERE type IN ('trigger', 'view')").fetchone():
                    raise ValueError("Backup database has unsupported executable schema")
                hashes = [row[0] for row in db.execute("SELECT DISTINCT sha256 FROM source_version")]
                object_names = {f"objects/{digest[:2]}/{digest}" for digest in hashes if re.fullmatch(r"[0-9a-f]{64}", digest)}
                if len(object_names) != len(hashes) or object_names != set(expected) - {"research.sqlite3"}:
                    raise ValueError("Backup originals do not match database references")
            # Claim the new directory without replacing any existing user directory.
            destination.mkdir()
            try:
                shutil.move(str(staging / "research.sqlite3"), destination / "research.sqlite3")
                if (staging / "objects").exists():
                    shutil.move(str(staging / "objects"), destination / "objects")
                store = ResearchStore(destination)
                result = diagnose(store)
                if not result["healthy"]:
                    raise ValueError("Restored workspace failed integrity checks")
                return store
            except Exception:
                shutil.rmtree(destination)
                raise
    except (BadZipFile, KeyError, json.JSONDecodeError, sqlite3.DatabaseError, TypeError) as exc:
        raise ValueError("Invalid or damaged backup archive") from exc
