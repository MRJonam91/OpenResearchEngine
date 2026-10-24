# SourcePilot local alpha

Guida storica 0.1 / Historical 0.1 guide. Per la versione attuale / for the current version, see [1.0 guide](USER_GUIDE.md).

## Start on Windows

Requires Python 3.14 or newer. From this repository in PowerShell:

```powershell
.\run.ps1
```

The first run creates `.venv`, installs the Python dependencies, and starts the server on `http://127.0.0.1:8765`. Open that address in a browser. Stop it with `Ctrl+C`. The default data workspace is `./workspace`, which Git ignores. To use another location:

```powershell
.\run.ps1 -Workspace 'D:\Research\MyWorkspace' -Port 8765
```

Alternatively, install manually with `python -m venv .venv`, `.venv\Scripts\python.exe -m pip install -e .`, and `.venv\Scripts\python.exe -m sourcepilot serve --workspace workspace`.

## Browser workflow

1. Choose individual files or a folder. The browser uploads selected files to the local server, which stores the original bytes in the chosen workspace. Folder paths are used only as source labels. You can also import one public HTTP/HTTPS URL.
2. Select a source or search its extracted text. Results show source title and passage locator.
3. Select a passage, write an assertion, and create a claim. Its initial status is `proposed`.
4. Search again to attach more passages as supporting, challenging, or contextual evidence. Both supporting and challenging passages make the claim visibly disputed.
5. Review the claim as approved, uncertain, or rejected, with an optional note.
6. Export Markdown. The default report includes only approved and uncertain claims. Each footnote records source origin, import time, SHA-256 prefix, locator, passage ID, and version ID.

## CLI

Each command takes `--workspace PATH`. Examples:

```powershell
$sp = '.venv\Scripts\python.exe'
& $sp -m sourcepilot import .\docs --workspace .\workspace
& $sp -m sourcepilot search 'citation' --workspace .\workspace
& $sp -m sourcepilot claim 'A specific proposition' --passage 1 --workspace .\workspace
& $sp -m sourcepilot evidence 1 2 --stance challenges --workspace .\workspace
& $sp -m sourcepilot review 1 --status uncertain --note 'Sources disagree.' --workspace .\workspace
& $sp -m sourcepilot report --output .\report.md --workspace .\workspace
```

`import` accepts a file or walks a folder recursively. It reports errors separately for each supported file in a folder. `report` refuses to overwrite an existing file. `import-url URL` is also available.

## Data and limitations

The workspace holds `research.sqlite3` and `objects/<sha-prefix>/<sha256>`. Imported originals are content-addressed and retained; reimporting changed bytes creates a new source version. The browser cannot read arbitrary disk paths: it receives only files selected by the user. The CLI can read paths given to it. The server listens on loopback and requires a per-run token for write requests.

This alpha uses SQLite full-text search. It does not yet provide semantic search, automated claim extraction, automated contradiction detection, OCR, PDF report export, or model integration. PDF import requires selectable text. The importer caps each item at 20 MB; URL imports accept public standard-port HTTP/HTTPS HTML or plain text and time out after 15 seconds.

This is a single-user local alpha. Back up the workspace directory before moving machines or upgrading the schema; migrations and a workspace export/import flow are not implemented yet.
