"""Search, human claim review, and evidence relationships."""

from __future__ import annotations

import re

from .store import ResearchStore, _now

STANCES = {"supports", "challenges", "context"}
STATUSES = {"proposed", "approved", "rejected", "uncertain"}


def _search_expression(query: str) -> str:
    if len(query) > 2000:
        raise ValueError("Search query exceeds 2000 characters")
    return " AND ".join('"' + term + '"' for term in re.findall(r"\w+", query, flags=re.UNICODE)[:12])


class ResearchService:
    def __init__(self, store: ResearchStore):
        self.store = store

    def search(self, query: str, limit: int = 50, include_history: bool = False, source_id: int | None = None) -> list[dict]:
        expression = _search_expression(query)
        if not expression:
            return []
        with self.store.connect() as db:
            rows = db.execute(
                "SELECT p.id, p.version_id, p.locator, p.text, s.id AS source_id, s.title, "
                "s.origin, sv.sha256, sv.imported_at FROM passage_fts f "
                "JOIN passage p ON p.id = f.passage_id "
                "JOIN source_version sv ON sv.id = p.version_id "
                "JOIN source s ON s.id = sv.source_id "
                "WHERE passage_fts MATCH ? "
                "AND (? OR sv.id = (SELECT MAX(id) FROM source_version WHERE source_id = s.id)) "
                "AND (? IS NULL OR s.id = ?) "
                "ORDER BY bm25(passage_fts), p.id LIMIT ?",
                (expression, int(include_history), source_id, source_id, max(1, min(limit, 100))),
            ).fetchall()
            return [dict(row) for row in rows]

    def count_matches(self, query: str, source_id: int) -> int:
        expression = _search_expression(query)
        if not expression:
            return 0
        with self.store.connect() as db:
            return db.execute(
                "SELECT COUNT(*) FROM passage_fts f JOIN passage p ON p.id = f.passage_id "
                "JOIN source_version sv ON sv.id = p.version_id WHERE passage_fts MATCH ? "
                "AND sv.source_id = ? AND sv.id = (SELECT MAX(id) FROM source_version WHERE source_id = ?)",
                (expression, source_id, source_id),
            ).fetchone()[0]

    def compare(self, left_id: int, right_id: int, query: str) -> dict:
        if not query.strip():
            raise ValueError("Comparison query is required")
        if left_id == right_id:
            raise ValueError("Choose two different sources")
        sources = {row["source_id"]: row for row in self.store.list_sources()}
        if left_id not in sources or right_id not in sources:
            raise ValueError("Source does not exist")
        return {
            "query": query.strip(),
            "left": {"source": sources[left_id], "passages": self.search(query, limit=20, source_id=left_id)},
            "right": {"source": sources[right_id], "passages": self.search(query, limit=20, source_id=right_id)},
        }

    def create_claim(self, text: str, passage_id: int) -> dict:
        text = text.strip()
        if not text or len(text) > 5000:
            raise ValueError("Claim text must contain 1 to 5000 characters")
        with self.store.connect() as db:
            if not db.execute("SELECT 1 FROM passage WHERE id = ?", (passage_id,)).fetchone():
                raise ValueError("Passage does not exist")
            claim_id = db.execute(
                "INSERT INTO claim(text, created_at) VALUES (?, ?)", (text, _now())
            ).lastrowid
            db.execute(
                "INSERT INTO evidence_link(claim_id, passage_id, stance) VALUES (?, ?, 'supports')",
                (claim_id, passage_id),
            )
        return self.get_claim(claim_id)

    def add_evidence(self, claim_id: int, passage_id: int, stance: str) -> dict:
        if stance not in STANCES:
            raise ValueError("Evidence stance must be supports, challenges, or context")
        with self.store.connect() as db:
            prior = db.execute("SELECT * FROM claim WHERE id = ?", (claim_id,)).fetchone()
            if prior is None:
                raise ValueError("Claim does not exist")
            if not db.execute("SELECT 1 FROM passage WHERE id = ?", (passage_id,)).fetchone():
                raise ValueError("Passage does not exist")
            existing = db.execute(
                "SELECT stance FROM evidence_link WHERE claim_id = ? AND passage_id = ?",
                (claim_id, passage_id),
            ).fetchone()
            if existing is None or existing["stance"] != stance:
                action = f"evidence:add:{passage_id}:{stance}" if existing is None else f"evidence:stance:{passage_id}:{existing['stance']}->{stance}"
                self._record_revision(db, prior, action)
                db.execute(
                    "INSERT INTO evidence_link(claim_id, passage_id, stance) VALUES (?, ?, ?) "
                    "ON CONFLICT(claim_id, passage_id) DO UPDATE SET stance = excluded.stance",
                    (claim_id, passage_id, stance),
                )
                db.execute(
                    "UPDATE claim SET status = 'proposed', note = '', reviewed_at = NULL WHERE id = ?",
                    (claim_id,),
                )
        return self.get_claim(claim_id)

    def remove_evidence(self, claim_id: int, passage_id: int) -> dict:
        with self.store.connect() as db:
            link = db.execute(
                "SELECT stance FROM evidence_link WHERE claim_id = ? AND passage_id = ?",
                (claim_id, passage_id),
            ).fetchone()
            if link is None:
                raise ValueError("Evidence link does not exist")
            count = db.execute(
                "SELECT COUNT(*) FROM evidence_link WHERE claim_id = ?", (claim_id,)
            ).fetchone()[0]
            if count <= 1:
                raise ValueError("Cannot remove the last evidence link")
            prior = db.execute("SELECT * FROM claim WHERE id = ?", (claim_id,)).fetchone()
            self._record_revision(db, prior, f"evidence:remove:{passage_id}:{link['stance']}")
            db.execute(
                "DELETE FROM evidence_link WHERE claim_id = ? AND passage_id = ?",
                (claim_id, passage_id),
            )
            db.execute(
                "UPDATE claim SET status = 'proposed', note = '', reviewed_at = NULL WHERE id = ?",
                (claim_id,),
            )
        return self.get_claim(claim_id)

    @staticmethod
    def _record_revision(db, prior, action: str) -> None:
        db.execute(
            "INSERT INTO claim_revision(claim_id, action, previous_text, previous_status, "
            "previous_note, previous_reviewed_at, changed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (prior["id"], action, prior["text"], prior["status"], prior["note"], prior["reviewed_at"], _now()),
        )

    def edit_claim(self, claim_id: int, text: str) -> dict:
        text = text.strip()
        if not text or len(text) > 5000:
            raise ValueError("Claim text must contain 1 to 5000 characters")
        with self.store.connect() as db:
            prior = db.execute("SELECT * FROM claim WHERE id = ?", (claim_id,)).fetchone()
            if prior is None:
                raise ValueError("Claim does not exist")
            if prior["text"] != text:
                self._record_revision(db, prior, "edit")
                db.execute(
                    "UPDATE claim SET text = ?, status = 'proposed', note = '', reviewed_at = NULL WHERE id = ?",
                    (text, claim_id),
                )
        return self.get_claim(claim_id)

    def review_claim(self, claim_id: int, status: str, note: str = "") -> dict:
        if status not in STATUSES:
            raise ValueError("Invalid claim status")
        if len(note) > 5000:
            raise ValueError("Review note exceeds 5000 characters")
        with self.store.connect() as db:
            prior = db.execute("SELECT * FROM claim WHERE id = ?", (claim_id,)).fetchone()
            if prior is None:
                raise ValueError("Claim does not exist")
            if prior["status"] == status and prior["note"] == note:
                return self.get_claim(claim_id)
            self._record_revision(db, prior, "review")
            reviewed_at = _now() if status != "proposed" else None
            db.execute(
                "UPDATE claim SET status = ?, note = ?, reviewed_at = ? WHERE id = ?",
                (status, note, reviewed_at, claim_id),
            )
        return self.get_claim(claim_id)

    def list_revisions(self, claim_id: int) -> list[dict]:
        with self.store.connect() as db:
            if not db.execute("SELECT 1 FROM claim WHERE id = ?", (claim_id,)).fetchone():
                raise ValueError("Claim does not exist")
            rows = db.execute(
                "SELECT * FROM claim_revision WHERE claim_id = ? ORDER BY id DESC", (claim_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    def get_claim(self, claim_id: int) -> dict:
        with self.store.connect() as db:
            row = db.execute("SELECT * FROM claim WHERE id = ?", (claim_id,)).fetchone()
            if row is None:
                raise ValueError("Claim does not exist")
            claim = dict(row)
            evidence = db.execute(
                "SELECT e.stance, p.id AS passage_id, p.text, p.locator, p.version_id, "
                "s.id AS source_id, s.title, s.origin, sv.sha256, sv.imported_at "
                "FROM evidence_link e JOIN passage p ON p.id = e.passage_id "
                "JOIN source_version sv ON sv.id = p.version_id "
                "JOIN source s ON s.id = sv.source_id "
                "WHERE e.claim_id = ? ORDER BY e.rowid",
                (claim_id,),
            ).fetchall()
            claim["evidence"] = [dict(item) for item in evidence]
            stances = {item["stance"] for item in claim["evidence"]}
            claim["disputed"] = "supports" in stances and "challenges" in stances
            origin = db.execute(
                "SELECT a.run_id, r.model, r.model_digest, r.prompt_version FROM accepted_suggestion a "
                "JOIN analysis_run r ON r.id = a.run_id WHERE a.claim_id = ?", (claim_id,),
            ).fetchone()
            claim["provenance"] = {"kind": "ai", **dict(origin)} if origin else {"kind": "human"}
            return claim

    def list_claims(self) -> list[dict]:
        with self.store.connect() as db:
            ids = [row["id"] for row in db.execute("SELECT id FROM claim ORDER BY id DESC")]
        return [self.get_claim(claim_id) for claim_id in ids]

    def render_report(self, include_proposed: bool = False) -> str:
        from .report import render_report

        return render_report(self.list_claims(), include_proposed)

    def render_pdf_report(self, include_proposed: bool = False) -> bytes:
        from .report import render_pdf_report

        return render_pdf_report(self.list_claims(), include_proposed)
