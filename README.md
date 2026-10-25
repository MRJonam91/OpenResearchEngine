# SourcePilot — Open Research Engine

> Research any topic. Every claim has a source.

[Release 1.0.0](https://github.com/MRJonam91/OpenResearchEngine/releases/tag/v1.0.0) · [CI](https://github.com/MRJonam91/OpenResearchEngine/actions/workflows/test.yml)

## Italiano

SourcePilot **1.0.0** è un'applicazione di ricerca locale per un solo utente. Conserva fonti originali, trova passaggi e costruisce affermazioni con citazioni verificabili. Web app, API e CLI condividono il workspace SQLite; la persona decide quali affermazioni approvare.

### Avvio rapido (Windows)

Serve Python **3.11–3.14**. In PowerShell, dalla cartella del repository:

```powershell
.\run.ps1
```

Apri `http://127.0.0.1:8765`. Il primo avvio crea `.venv` e installa le dipendenze. Il workspace predefinito è `./workspace`; per sceglierne uno diverso: `.\run.ps1 -Workspace 'D:\Research\MioWorkspace' -Port 8765`. Ferma il server con `Ctrl+C`.

Su Linux/macOS: crea e attiva un ambiente virtuale Python, esegui `python -m pip install -c requirements.lock -e .`, poi `sourcepilot serve --workspace ./workspace`. Windows e Linux sono verificati in CI con Python 3.11 e 3.14; macOS usa lo stesso percorso ma non è incluso nella matrice CI.

### Funzioni 1.0

- Importa TXT, Markdown, HTML, DOCX e PDF con testo selezionabile (massimo 20 MB), file o cartelle scelti nel browser, oppure URL pubblici HTTP/HTTPS.
- Conserva originali e versioni; mostra i passaggi con posizione, data di importazione e hash SHA-256. La ricerca testuale SQLite FTS5 usa la versione più recente, con opzione esplicita per cercare nella cronologia.
- Permette di creare, correggere e revisionare affermazioni, collegare prove che supportano/contrastano/contestualizzano, e confrontare due fonti affiancate.
- Esporta report Markdown e PDF con citazioni a livello di passaggio. Solo affermazioni approvate o incerte entrano nel report predefinito.
- Espone API locali e CLI per automazioni personali.
- Aggiunge ricerca semantica, proposte di affermazioni e candidati disaccordi con Ollama locale opzionale; ogni citazione proposta deve corrispondere a un passaggio e a una citazione testuale esatta.
- Controlla l'integrità e crea backup ZIP portabili con checksum e ripristino in una nuova cartella.

Il flusso manuale funziona senza Ollama. Per l'AI, avvia il runtime e scegli modelli già installati: `.\run.ps1 -Model 'qwen2.5-coder:7b' -EmbeddingModel 'all-minilm:latest'`. Non vengono scaricati modelli automaticamente. La copertura analizzata è visibile; una proposta accettata diventa una bozza da revisionare. Una citazione indica la provenienza del testo, non la sua verità.

OCR, ricerca autonoma sul web e hosting multiutente sono oltre la 1.0. Il PDF segnala caratteri non rappresentabili dal font; Markdown conserva Unicode. Prima di aggiornare, ferma il server e copia l'intero workspace. Dati e report possono contenere documenti e percorsi locali in chiaro. [Guida 1.0](docs/USER_GUIDE.md) · [Architettura](docs/ARCHITECTURE.md) · [Roadmap](docs/ROADMAP.md) · [Changelog](CHANGELOG.md).

## English

SourcePilot **1.0.0** is a local research application for one user. It retains originals, finds locatable passages, and builds claims with inspectable citations. The web app, API, and CLI share a SQLite workspace; people make review decisions.

### Quick start (Windows)

Install Python **3.11–3.14**. In PowerShell from the repository:

```powershell
.\run.ps1
```

Open `http://127.0.0.1:8765`. First run creates `.venv` and installs dependencies. Default workspace is `./workspace`; to choose another: `.\run.ps1 -Workspace 'D:\Research\MyWorkspace' -Port 8765`. Stop with `Ctrl+C`.

On Linux/macOS, create and activate a Python virtual environment, run `python -m pip install -c requirements.lock -e .`, then `sourcepilot serve --workspace ./workspace`. CI checks Windows and Linux with Python 3.11 and 3.14; macOS follows the same installation path but is outside the CI matrix.

### Version 1.0 features

- Imports TXT, Markdown, HTML, DOCX, and text-selectable PDF (20 MB per item), browser-selected files/folders, or public HTTP/HTTPS URLs.
- Retains originals and source versions; displays passage locators, import times, and SHA-256 hashes. SQLite FTS5 text search uses the latest version by default, with an explicit history option.
- Creates, edits, and reviews claims; attaches supporting, challenging, or contextual evidence; compares two sources side by side.
- Exports passage-cited Markdown and PDF reports. Only approved or uncertain claims appear by default.
- Provides a local API and CLI for personal automation.
- Adds optional local Ollama semantic search, cited claim proposals, and candidate disagreements. Each model citation must identify a supplied passage and an exact quote.
- Provides integrity diagnostics and portable checksummed ZIP backup/restore into a new directory.

The manual workflow works without Ollama. To enable AI, start your local runtime and configure already-installed models with `--model` and `--embedding-model` on `sourcepilot serve`, or use the PowerShell example above. Models are never downloaded automatically. Analysis coverage is shown, and accepted suggestions become proposed claims requiring review. A citation establishes provenance, not factual correctness.

OCR, autonomous web discovery, and shared hosting are beyond 1.0. Unsupported PDF glyphs produce an explicit error; Markdown preserves Unicode. Stop the server and copy the complete workspace before upgrading. Workspaces and exports may contain plaintext documents and local paths. [1.0 guide](docs/USER_GUIDE.md) · [Architecture](docs/ARCHITECTURE.md) · [Roadmap](docs/ROADMAP.md) · [Changelog](CHANGELOG.md).

## Licenza e contributi / License and contributions

Codice originale / original code: [GPL-3.0-or-later](LICENSE). [NOTICE](NOTICE), [dipendenze / dependencies](THIRD_PARTY_NOTICES.md), [asset / assets](ASSETS.md). Nomi e marchi non sono concessi automaticamente dalla licenza software / names and trademarks are not automatically licensed.

[Contribuire / Contribute](CONTRIBUTING.md) · [Sicurezza / Security](SECURITY.md) · [Assistenza / Support](SUPPORT.md).

## Sostieni il progetto / Support development

Puoi sostenere manutenzione e sviluppo tramite [GitHub Sponsors](https://github.com/sponsors/MRJonam91), [Ko-fi](https://ko-fi.com/mrjonam), [Buy Me a Coffee](https://buymeacoffee.com/mrjonam) o [PayPal](https://paypal.me/manorollo). Il supporto è volontario e non attribuisce licenze o diritti aggiuntivi.

Voluntary support through the links above helps maintenance and development and grants no additional licenses or project rights.

## Sviluppo / Development

```sh
python -m pip install -c requirements.lock -e ".[test]"
python -m pytest -q
node --check sourcepilot/static/app.js
```

[Piano implementazione 1.0 / Implementation plan](docs/superpowers/plans/2026-10-24-v1.md)
