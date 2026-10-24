# SourcePilot 1.0 — Guida / User guide

## Italiano

### Installazione e avvio

Requisiti: Python 3.11–3.14 con SQLite FTS5, browser moderno. Su Windows esegui `./run.ps1` dalla cartella del repository. Il primo avvio crea `.venv`, installa il progetto con i vincoli di `requirements.lock` e avvia [localhost](http://127.0.0.1:8765). I successivi avvii richiedono solo le dipendenze già installate, salvo aggiornamenti. Per installare manualmente:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c requirements.lock -e .
.\.venv\Scripts\python.exe -m sourcepilot serve --workspace .\workspace
```

Su Linux/macOS usa `python3 -m venv .venv`, attiva l'ambiente con `. .venv/bin/activate`, quindi `python -m pip install -c requirements.lock -e .` e `sourcepilot serve --workspace ./workspace`. È disponibile anche il wheel della release, installabile con `python -m pip install percorso/sourcepilot-1.0.0-py3-none-any.whl`.

Il server ascolta solo `127.0.0.1`. Usa `--port` o `-Port` in PowerShell per scegliere una porta diversa; `--workspace`/`-Workspace` per un'altra cartella. Ferma con `Ctrl+C`. Tieni il servizio sul computer locale.

### Importare, cercare e revisionare

1. Seleziona file o una cartella nel browser; vengono caricati solo i file scelti, senza accesso generale al disco. La CLI può importare una cartella ricorsivamente. Formati: TXT/Markdown/HTML UTF-8, DOCX (paragrafi e tabelle), PDF con testo selezionabile. Limite 20 MB per elemento; DOCX ha un ulteriore limite di espansione di 80 MB. Non sono supportati OCR, vecchi `.doc`, PDF cifrati o pagine che richiedono JavaScript/login.
2. Puoi importare URL HTTP/HTTPS pubblici su porte standard: HTML, testo, PDF o DOCX. Gli originali sono conservati per hash, con origine e data. Reimportare la stessa origine con contenuto diverso crea una nuova versione; le vecchie citazioni restano legate ai passaggi originali.
3. Apri una fonte e scegli la versione. La ricerca testuale usa FTS5 con i termini della query in AND (massimo 12 termini); per impostazione predefinita cerca solo nell'ultima versione di ogni fonte. La casella cronologia include quelle precedenti.
4. Seleziona un passaggio, scrivi un'affermazione verificabile e crea una bozza. Collega altri passaggi come supporto, contrasto o contesto. *Confronta due fonti* mostra i risultati per fonte; non decide quale sia corretta.
5. Revisiona come approvata, incerta o respinta, con nota facoltativa. Le modifiche effettive a testo o prove riportano l'affermazione a *da revisionare* e registrano lo stato precedente. Deve rimanere almeno una prova collegata.
6. Esporta Markdown o PDF. Il report predefinito include solo approvate e incerte e mantiene stato, prove, origine, data, SHA-256 completo, posizione, ID di passaggio e versione. I PDF usano Bitstream Vera: se manca un carattere, l'errore è esplicito e puoi esportare Markdown. I report possono contenere percorsi locali ed estratti: rileggili prima di condividerli.

### AI locale opzionale

Installa e avvia Ollama secondo le sue istruzioni e prepara separatamente modelli con capacità `completion` e `embedding`. SourcePilot verifica le capacità e il digest dei modelli locali e rifiuta endpoint esterni e modelli remoti. Non scarica modelli. Le licenze dei modelli restano separate.

```powershell
.\run.ps1 -Model 'qwen2.5-coder:7b' -EmbeddingModel 'all-minilm:latest'
```

Oppure usa `sourcepilot serve --model NOME --embedding-model NOME`. Variabili equivalenti: `SOURCEPILOT_AI_MODEL`, `SOURCEPILOT_EMBEDDING_MODEL`, `SOURCEPILOT_OLLAMA_URL` (predefinito `http://127.0.0.1:11434`, solo loopback).

*Indicizza per significato* elabora fino a 100 passaggi a clic; ripeti finché l'indice è completo. I passaggi lunghi vengono divisi in finestre sovrapposte e i vettori aggregati; modello e digest identificano la cache. Un cambio di modello richiede un nuovo indice. La ricerca semantica mostra la copertura dell'indice e non passa silenziosamente alla ricerca testuale.

*Proponi dall'ultima versione* analizza fino a 24 passaggi, 16.000 caratteri totali e 2.000 per passaggio. La preview mostra copertura e parti abbreviate. Ogni proposta deve citare un passaggio presente e un testo esatto del contesto. *Accetta come bozza* crea un'affermazione ancora da revisionare, conservando la provenienza del modello/esecuzione. L'accettazione ripetuta non crea duplicati.

Il confronto AI può proporre disaccordi candidati, con citazioni da entrambe le fonti. Analizza al massimo 24 passaggi e 8.000 caratteri per fonte; se usi una query, recupera fino a 100 corrispondenze per fonte. La copertura distingue totale della fonte, corrispondenze, passaggi recuperati e analizzati. Citazioni valide non garantiscono che il modello abbia capito soggetto, periodo o significato: la valutazione resta umana. Nessun risultato AI viene approvato automaticamente.

### Workspace, aggiornamento e backup

Il workspace contiene `research.sqlite3` e `objects/`. Include testo e metadati in chiaro, più cache e contesti AI se abilitati. Non inserirlo nel repository. Prima di aggiornare da alfa/beta, ferma il server e copia l'intera cartella; le migrazioni sono additive ma il ritorno a versioni precedenti richiede il backup precedente.

*Verifica dati* controlla database, riferimenti, indice testuale e hash degli originali. *Backup* scarica un ZIP con snapshot SQLite consistente, originali e manifest con checksum. Limite complessivo 2 GB espansi. Per ripristinare, ferma il server e scegli una cartella nuova:

```sh
sourcepilot backup --workspace ./workspace --output ./backup.zip
sourcepilot restore ./backup.zip ./workspace-restored
sourcepilot doctor --workspace ./workspace-restored
```

Backup e report rifiutano la sovrascrittura. Il ripristino verifica archivio, percorsi, hash e database; i checksum rilevano alterazioni ma non autenticano chi ha creato un backup. Conserva i backup in un luogo protetto.

### CLI e API

`python -m sourcepilot` equivale al comando `sourcepilot`. I comandi workspace accettano `--workspace PATH`; vedi anche `--help`:

```sh
sourcepilot import ./documents --workspace ./workspace
sourcepilot import-url https://example.org --workspace ./workspace
sourcepilot search "budget" --include-history --workspace ./workspace
sourcepilot versions 1 --workspace ./workspace
sourcepilot compare 1 2 "budget" --workspace ./workspace
sourcepilot claim "A specific statement" --passage 1 --workspace ./workspace
sourcepilot evidence 1 2 --stance challenges --workspace ./workspace
sourcepilot review 1 --status uncertain --note "Sources disagree" --workspace ./workspace
sourcepilot edit 1 "Corrected statement" --workspace ./workspace
sourcepilot revisions 1 --workspace ./workspace
sourcepilot remove-evidence 1 2 --workspace ./workspace
sourcepilot report --output ./report.pdf --workspace ./workspace
sourcepilot index --embedding-model all-minilm:latest --workspace ./workspace
sourcepilot semantic "municipal spending" --embedding-model all-minilm:latest --workspace ./workspace
sourcepilot suggest 1 --model qwen2.5-coder:7b --workspace ./workspace
sourcepilot assess 1 2 --query budget --model qwen2.5-coder:7b --workspace ./workspace
sourcepilot accept 1 0 --workspace ./workspace
sourcepilot ai-run 1 --workspace ./workspace
```

Il suffisso `.pdf` sceglie PDF; `--format pdf|markdown` lo rende esplicito. `--include-proposed` aggiunge deliberatamente le bozze. CLI: codice 0 successo, 2 errore, 3 problemi rilevati da `doctor`.

L'API locale restituisce JSON. `GET /api/bootstrap` fornisce il token per `X-SourcePilot-Token` richiesto da POST/PATCH/DELETE. Gli errori di validazione sono 422, input non accettabili 400, richieste troppo grandi 413. I payload JSON sono limitati a 64 KiB prima del parsing.

| Operazione | Endpoint |
| --- | --- |
| Importazione | `POST /api/import` (byte, header `X-File-Name` URL-encoded), `POST /api/import-url` (`{"url":"..."}`) |
| Fonti | `GET /api/sources`, `/api/sources/{id}/versions`, `/api/sources/{id}/passages?version_id=...` |
| Originale | `GET /api/sources/{id}/versions/{version}/original` |
| Ricerca/confronto | `GET /api/search?q=...`, `GET /api/compare?left_id=1&right_id=2&q=...` |
| Affermazioni | `GET/POST /api/claims`, `PATCH /api/claims/{id}`, `PATCH /api/claims/{id}/text` |
| Prove/revisioni | `POST /api/claims/{id}/evidence`, `DELETE /api/claims/{id}/evidence/{passage}`, `GET /api/claims/{id}/revisions` |
| Manutenzione | `GET /api/workspace/health`, `POST /api/workspace/backup` |
| AI | `GET /api/ai/status`, `POST /api/ai/index`, `/api/ai/search`, `/api/ai/sources/{id}/suggest`, `/api/ai/assess` |
| Esecuzioni AI | `GET /api/ai/runs/{id}`, `POST /api/ai/runs/{id}/accept/{index}` (indice da 0) |
| Report | `GET /api/report.md`, `GET /api/report.pdf` |

### Problemi comuni

- Porta occupata: scegli `--port 8766`. Browser con vecchi file dopo aggiornamento: ricarica la pagina.
- Modello non disponibile: avvia Ollama, verifica nome e capacità; il flusso manuale continua a funzionare.
- Indice parziale: ripeti l'indicizzazione; non confondere similarità semantica con supporto probatorio.
- Originale mancante/alterato: esegui `doctor` e ripristina una copia integra. Non modificare direttamente il database o gli oggetti.
- Python troppo vecchio o SQLite senza FTS5: usa una distribuzione Python supportata.

## English

SourcePilot 1.0 supports Python 3.11–3.14. Windows: run `./run.ps1`. Linux/macOS: create/activate a virtual environment, install with `python -m pip install -c requirements.lock -e .`, and run `sourcepilot serve --workspace ./workspace`. Open [127.0.0.1:8765](http://127.0.0.1:8765); stop with `Ctrl+C`. `--workspace` and `--port` choose data location and port. CI covers Windows/Linux on Python 3.11/3.14; macOS is not in the matrix.

Import selected files/folders or public standard-port HTTP/HTTPS URLs. Supported: UTF-8 TXT/Markdown/HTML, DOCX paragraphs/tables, and text-selectable PDFs, up to 20 MB each; DOCX expansion is capped at 80 MB. No OCR, legacy `.doc`, encrypted PDFs, or browser-rendered/login-only pages. Originals, source versions, full hashes, and passage locators are retained. Reimporting changed content under the same origin creates a version; existing citations keep their original passage IDs.

Text search uses SQLite FTS5 with AND over up to 12 query terms, latest versions by default. Select history explicitly to include older versions. Create claims from passages, attach supporting/challenging/contextual evidence, and review as approved, uncertain, or rejected. Statement/evidence changes reset review; every claim retains at least one evidence link. Side-by-side comparison groups passages by source. Default Markdown/PDF reports include approved and uncertain claims; `--include-proposed` adds drafts explicitly. PDF uses the embedded Vera font and errors on unsupported glyphs; Markdown retains Unicode. Exports may include local paths and excerpts.

Optional AI requires your separately installed Ollama runtime and local models with `completion`/`embedding` capabilities. Use `--model NAME`, `--embedding-model NAME`, and optionally `--ollama-url` (loopback only), or `SOURCEPILOT_AI_MODEL`, `SOURCEPILOT_EMBEDDING_MODEL`, `SOURCEPILOT_OLLAMA_URL`. The PowerShell launcher accepts `-Model`/`-EmbeddingModel`. SourcePilot never downloads models. Check model licenses separately.

Indexing processes up to 100 passages per batch, with overlapping windows for long text and model/digest-specific caches. Repeat until complete; semantic search reports indexed/total coverage and never silently falls back to text search. Claim proposals use up to 24 passages, 16,000 context characters, and 2,000 per passage. AI comparison uses up to 24 passages and 8,000 characters per side, optionally retrieving up to 100 query matches. Coverage shows source totals, matches, retrieved/analyzed passages, and truncation. Exact-quote and passage-ID checks reject invented/out-of-context citations; they do not establish factual correctness. Explicit acceptance creates an idempotent proposed claim with model/run provenance. Human review remains required.

Workspaces contain plaintext SQLite data and originals, plus optional embedding/analysis caches. Stop the server and copy the complete workspace before upgrading; migrations are additive, and rollback needs the earlier backup. The commands above demonstrate `backup`, `restore`, and `doctor`; restore into a new directory while the server is stopped. Backups contain a consistent database snapshot, originals, and a checksum manifest, with a 2 GB expanded limit. They reject traversal, unexpected members, and altered hashes; checksums do not authenticate the archive's author. Backups and reports refuse overwrite. Protect backup files using OS permissions.

The CLI examples and API table above apply to both languages. `python -m sourcepilot` is equivalent to `sourcepilot`; use `--help` for command arguments. CLI exits: 0 success, 2 error, 3 integrity issues from `doctor`. Local API writes require the per-run `X-SourcePilot-Token` from `/api/bootstrap`; validation errors return 422, unacceptable input 400, oversized bodies 413. JSON is limited to 64 KiB before parsing. Keep the server on loopback.

If a port is occupied, choose another. If Ollama is offline or the model lacks the required capability, check your runtime/model and continue with the manual workflow. Repeat indexing when coverage is partial. Run `doctor` for missing/altered originals and restore a known-good backup. Use a supported Python distribution with SQLite FTS5. Consult [SUPPORT](../SUPPORT.md) and [SECURITY](../SECURITY.md) for reports.
