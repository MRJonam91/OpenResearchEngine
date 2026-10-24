# SourcePilot 0.2.0b1 — guida locale / local guide

Guida storica / Historical guide. Per la versione attuale / for the current version, see [1.0 guide](USER_GUIDE.md).

## Italiano

### Installazione e aggiornamento

Richiede Python 3.14+. In Windows PowerShell, `.\run.ps1` crea l'ambiente virtuale, installa il progetto e avvia `http://127.0.0.1:8765`. Con `-Workspace PATH` scegli dove conservare dati e originali; con `-Port NUMERO` cambi la porta. Il server ascolta solo `127.0.0.1`.

Prima di aprire un workspace della versione alfa nella beta, **ferma il server e copia l'intera cartella del workspace**, inclusi `research.sqlite3` e `objects/`, in una posizione di backup. Il database viene migrato all'apertura senza cancellare fonti, passaggi e affermazioni; una versione alfa non deve riaprire un workspace migrato senza ripristinare il backup. Non mettere il workspace sotto Git né pubblicarlo.

### Flusso nel browser

1. Importa file, una cartella selezionata, o un URL pubblico. La selezione della cartella carica i file supportati nel workspace locale; non concede accesso generale al file system.
2. Seleziona una fonte per vedere i passaggi. Il selettore delle versioni permette di aprire gli import precedenti e scaricarne l'originale. La ricerca usa solo l'ultima versione, salvo la casella *Includi versioni precedenti*.
3. Apri *Confronta due fonti*, seleziona due fonti e un termine: i passaggi corrispondenti sono mostrati affiancati. Non è una diagnosi automatica di contraddizione.
4. Usa un passaggio per creare un'affermazione; collega altre prove come supporto, contrasto o contesto. Puoi modificare il testo, il ruolo delle prove e la revisione. Modifiche al testo o alle prove riportano lo stato a *da revisionare*; il report non la includerà finché non verrà nuovamente approvata o marcata incerta.
5. Esporta Markdown o PDF. I report predefiniti includono affermazioni approvate e incerte, non bozze e respinte. Ogni prova rimanda a un passaggio e alla versione della fonte.

### CLI e API

Esegui i comandi con `python -m sourcepilot` nell'ambiente installato. Tutti accettano `--workspace PATH`:

```powershell
python -m sourcepilot import .\documenti --workspace .\workspace
python -m sourcepilot search "stima" --include-history --workspace .\workspace
python -m sourcepilot versions 1 --workspace .\workspace
python -m sourcepilot compare 1 2 "stima" --workspace .\workspace
python -m sourcepilot claim "Affermazione verificabile" --passage 1 --workspace .\workspace
python -m sourcepilot edit 1 "Testo corretto" --workspace .\workspace
python -m sourcepilot revisions 1 --workspace .\workspace
python -m sourcepilot evidence 1 2 --stance challenges --workspace .\workspace
python -m sourcepilot remove-evidence 1 2 --workspace .\workspace
python -m sourcepilot review 1 --status uncertain --note "Fonti discordanti" --workspace .\workspace
python -m sourcepilot report --output .\report.pdf --workspace .\workspace
```

`report` non sovrascrive un file esistente; `.pdf` produce PDF, altrimenti Markdown, oppure usa `--format pdf|markdown`. `--include-proposed` include esplicitamente le bozze. L'API locale espone `/api/sources`, `/api/search`, `/api/compare`, `/api/claims`, `/api/report.md` e `/api/report.pdf`; le scritture richiedono il token della sessione restituito da `/api/bootstrap`. Non esporre il servizio oltre il computer locale.

### Limiti

Ricerca testuale SQLite FTS5, non semantica. Nessuna estrazione AI, OCR, classificazione automatica di verità o contraddizioni, account o hosting multiutente. I PDF importati devono contenere testo selezionabile. Dimensione massima 20 MB per import. Gli URL sono limitati a pagine pubbliche HTTP/HTTPS su porte standard; i contenuti importati vanno comunque trattati come non attendibili. Il PDF usa un font latino incorporato: se un carattere non è rappresentabile, l'export segnala un errore esplicito; il report Markdown resta disponibile. La cronologia registra testo, stato e nota precedenti e l'azione sulle prove, ma non una copia completa dei collegamenti a ogni revisione.

## English

### Install and upgrade

Requires Python 3.14+. On Windows PowerShell, `.\run.ps1` creates the virtual environment, installs the project, and serves `http://127.0.0.1:8765`. Use `-Workspace PATH` for data location and `-Port NUMBER` for the port. The server binds only to `127.0.0.1`.

Before opening an alpha workspace in the beta, **stop the server and copy the entire workspace**, including `research.sqlite3` and `objects/`, to a backup location. The database migrates on open without deleting sources, passages, or claims; do not reopen a migrated workspace with the alpha version unless you restore the backup. Do not commit or publish the workspace.

### Browser workflow

1. Import selected files, a selected folder, or a public URL. Folder selection uploads supported files to the local workspace; it does not grant general filesystem access.
2. Select a source to inspect passages. The version selector opens older imports and downloads their originals. Search uses latest versions unless *Include previous versions* is checked.
3. Open *Compare two sources*, choose two sources and a query. Matching passages appear side by side; this is not automatic contradiction detection.
4. Create a claim from a passage and link supporting, challenging, or contextual evidence. Edit its statement, evidence roles, and review. Statement or evidence changes reset it to *proposed* until reviewed again.
5. Export Markdown or PDF. By default, reports include approved and uncertain claims, not proposed or rejected ones. Each evidence item identifies its passage and source version.

### CLI and API

Run the commands above with `python -m sourcepilot` in the installed environment; all accept `--workspace PATH`. `report` refuses to overwrite a file. A `.pdf` output selects PDF; other suffixes select Markdown, or use `--format pdf|markdown`. `--include-proposed` explicitly includes drafts. The loopback API exposes `/api/sources`, `/api/search`, `/api/compare`, `/api/claims`, `/api/report.md`, and `/api/report.pdf`; writes need the per-run token returned by `/api/bootstrap`. Do not expose the service beyond the local machine.

### Limits

Search is SQLite FTS5 text search, not semantic. There is no AI extraction, OCR, automatic truth/contradiction judgement, accounts, or multi-user hosting. Imported PDFs need selectable text. Imports are limited to 20 MB each. URLs are restricted to public HTTP/HTTPS pages on standard ports; imported content remains untrusted. PDF output embeds a Latin font: an unsupported character produces an explicit error, while Markdown export remains available. Revision history records previous statement, status, note, and evidence actions, but not a complete snapshot of every evidence link at each revision.
