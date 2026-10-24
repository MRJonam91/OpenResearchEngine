"""Command line interface and local server entry point."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import sqlite3

from .ingest import SUPPORTED_EXTENSIONS
from .research import ResearchService
from .store import ResearchStore
from .schemas import MAX_IDENTIFIER
from . import __version__


def _print(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _identifier(value: str) -> int:
    number = int(value)
    if not 1 <= number <= MAX_IDENTIFIER:
        raise argparse.ArgumentTypeError("Identifier must be between 1 and 2**63-1")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sourcepilot")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    def common(command: str):
        sub = commands.add_parser(command)
        sub.add_argument("--workspace", type=Path, default=Path.cwd() / "workspace")
        return sub

    serve = common("serve")
    serve.add_argument("--port", type=int, default=8765)

    def ai_options(command):
        command.add_argument("--model", default=os.getenv("SOURCEPILOT_AI_MODEL", ""))
        command.add_argument("--embedding-model", default=os.getenv("SOURCEPILOT_EMBEDDING_MODEL", ""))
        command.add_argument("--ollama-url", default=os.getenv("SOURCEPILOT_OLLAMA_URL", "http://127.0.0.1:11434"))

    ai_options(serve)
    import_parser = common("import")
    import_parser.add_argument("path", type=Path)
    url_parser = common("import-url")
    url_parser.add_argument("url")
    search_parser = common("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--include-history", action="store_true")
    versions_parser = common("versions")
    versions_parser.add_argument("source_id", type=_identifier)
    compare_parser = common("compare")
    compare_parser.add_argument("left_id", type=_identifier)
    compare_parser.add_argument("right_id", type=_identifier)
    compare_parser.add_argument("query")
    claim_parser = common("claim")
    claim_parser.add_argument("text")
    claim_parser.add_argument("--passage", type=_identifier, required=True)
    review_parser = common("review")
    review_parser.add_argument("claim_id", type=_identifier)
    review_parser.add_argument("--status", required=True, choices=["proposed", "approved", "rejected", "uncertain"])
    review_parser.add_argument("--note", default="")
    edit_parser = common("edit")
    edit_parser.add_argument("claim_id", type=_identifier)
    edit_parser.add_argument("text")
    revisions_parser = common("revisions")
    revisions_parser.add_argument("claim_id", type=_identifier)
    evidence_parser = common("evidence")
    evidence_parser.add_argument("claim_id", type=_identifier)
    evidence_parser.add_argument("passage_id", type=_identifier)
    evidence_parser.add_argument("--stance", required=True, choices=["supports", "challenges", "context"])
    remove_parser = common("remove-evidence")
    remove_parser.add_argument("claim_id", type=_identifier)
    remove_parser.add_argument("passage_id", type=_identifier)
    report_parser = common("report")
    report_parser.add_argument("--output", type=Path, required=True)
    report_parser.add_argument("--format", choices=["markdown", "pdf"])
    report_parser.add_argument("--include-proposed", action="store_true")
    common("doctor")
    backup_parser = common("backup")
    backup_parser.add_argument("--output", type=Path, required=True)
    restore_parser = commands.add_parser("restore")
    restore_parser.add_argument("archive", type=Path)
    restore_parser.add_argument("destination", type=Path)
    for name in ("ai-status", "index", "semantic", "suggest", "assess", "accept", "ai-run"):
        command = common(name)
        ai_options(command)
        if name == "index":
            command.add_argument("--limit", type=int, default=100)
            command.add_argument("--include-history", action="store_true")
        elif name == "semantic":
            command.add_argument("query")
            command.add_argument("--include-history", action="store_true")
        elif name == "suggest":
            command.add_argument("source_id", type=_identifier)
        elif name == "assess":
            command.add_argument("left_id", type=_identifier)
            command.add_argument("right_id", type=_identifier)
            command.add_argument("--query", default="")
        elif name in {"accept", "ai-run"}:
            command.add_argument("run_id", type=_identifier)
            if name == "accept":
                command.add_argument("index", type=int)
    args = parser.parse_args(argv)
    try:
        if args.command == "serve":
            import uvicorn
            from .api import create_app

            uvicorn.run(create_app(args.workspace, model=args.model, embedding_model=args.embedding_model, ollama_url=args.ollama_url), host="127.0.0.1", port=args.port, proxy_headers=False)
            return 0
        if args.command == "restore":
            from .maintenance import restore_workspace

            restored = restore_workspace(args.archive, args.destination)
            _print({"workspace": str(restored.workspace)})
            return 0
        store = ResearchStore(args.workspace)
        research = ResearchService(store)
        if args.command in {"ai-status", "index", "semantic", "suggest", "assess", "accept", "ai-run"}:
            from .ai import AIService, OllamaClient

            ai = AIService(store, OllamaClient(args.ollama_url), model=args.model, embedding_model=args.embedding_model)
            if args.command == "ai-status":
                _print(ai.status())
            elif args.command == "index":
                _print(ai.index(args.limit, args.include_history))
            elif args.command == "semantic":
                _print(ai.semantic_search(args.query, args.include_history))
            elif args.command == "suggest":
                _print(ai.suggest(args.source_id))
            elif args.command == "assess":
                _print(ai.assess(args.left_id, args.right_id, args.query))
            elif args.command == "accept":
                _print(ai.accept(args.run_id, args.index))
            else:
                _print(ai.get_run(args.run_id))
            return 0
        if args.command == "import":
            path = args.path.expanduser().resolve(strict=True)
            if path.is_dir():
                results = []
                for file in path.rglob("*"):
                    if file.is_file() and file.suffix.lower() in SUPPORTED_EXTENSIONS:
                        try:
                            results.append(store.import_file(file))
                        except (ValueError, OSError) as exc:
                            results.append({"path": str(file), "error": str(exc)})
                _print(results)
            else:
                _print(store.import_file(path))
        elif args.command == "import-url":
            _print(store.import_url(args.url))
        elif args.command == "search":
            _print(research.search(args.query, include_history=args.include_history))
        elif args.command == "versions":
            _print(store.list_versions(args.source_id))
        elif args.command == "compare":
            _print(research.compare(args.left_id, args.right_id, args.query))
        elif args.command == "claim":
            _print(research.create_claim(args.text, args.passage))
        elif args.command == "review":
            _print(research.review_claim(args.claim_id, args.status, args.note))
        elif args.command == "edit":
            _print(research.edit_claim(args.claim_id, args.text))
        elif args.command == "revisions":
            _print(research.list_revisions(args.claim_id))
        elif args.command == "evidence":
            _print(research.add_evidence(args.claim_id, args.passage_id, args.stance))
        elif args.command == "remove-evidence":
            _print(research.remove_evidence(args.claim_id, args.passage_id))
        elif args.command == "report":
            args.output.parent.mkdir(parents=True, exist_ok=True)
            format_name = args.format or ("pdf" if args.output.suffix.lower() == ".pdf" else "markdown")
            if format_name == "pdf":
                rendered = research.render_pdf_report(args.include_proposed)
                with args.output.open("xb") as output:
                    output.write(rendered)
            else:
                rendered = research.render_report(args.include_proposed)
                with args.output.open("x", encoding="utf-8") as output:
                    output.write(rendered)
            _print({"report": str(args.output.resolve())})
        elif args.command == "doctor":
            from .maintenance import diagnose

            result = diagnose(store)
            _print(result)
            return 0 if result["healthy"] else 3
        elif args.command == "backup":
            from .maintenance import backup_workspace

            _print(backup_workspace(store, args.output))
        return 0
    except (ValueError, OSError, sqlite3.DatabaseError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
