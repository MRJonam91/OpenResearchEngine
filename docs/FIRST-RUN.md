# Prima prova senza AI / First run without AI

## Italiano

Obiettivo: importare una fonte, trovare un passaggio, revisionare un'affermazione ed esportare un report citato. L'esempio usa una biblioteca inventata; non dimostra la correttezza di fatti reali. Non servono Ollama, un modello, una chiave API o documenti personali.

1. Installa Python 3.11–3.14, clona questa repository e apri PowerShell nella sua cartella. Se usi il [sorgente 1.0.0](https://github.com/MRJonam91/OpenResearchEngine/releases/tag/v1.0.0), scarica separatamente il file fittizio collegato al punto 3: è stato aggiunto dopo la release.
2. Avvia `./run.ps1 -Workspace ./workspace-trial`. Il primo avvio installa le dipendenze e richiede internet; il percorso manuale seguente usa file locali. Apri `http://127.0.0.1:8765`.
3. Importa [examples/first-source.txt](../examples/first-source.txt) tramite la selezione file. Cerca `Northbridge`, apri la fonte e seleziona il passaggio con l'orario.
4. Crea l'affermazione `The fictional Northbridge Library opens at 09:00 on weekdays.` collegandola al passaggio. Prima è una bozza: controlla il testo e approvala per questa dimostrazione.
5. Esporta Markdown. Verifica che il report mostri l'affermazione, la fonte, il passaggio e l'hash. Se non approvi la bozza, il report predefinito la esclude.

Risultato da valutare: riesci a tornare dal report alla prova originale? Il tempo dipende dall'installazione e dal computer. Non sono inclusi ricerca autonoma sul web, OCR o verifica automatica della verità. Workspace e report contengono testo e percorsi in chiaro: tienili locali e rileggili prima di condividere.

Hai incontrato un ostacolo? Segnala sistema operativo, versione Python, passaggio e risultato atteso in [Support](../SUPPORT.md), usando solo il file fittizio. Non caricare workspace o documenti personali. [Guida completa](USER_GUIDE.md).

## English

Goal: import a source, locate a passage, review a claim and export a cited report. The library is fictional; the example does not establish real-world facts. No Ollama model, API key or personal documents are required.

1. Install Python 3.11–3.14, clone this repository and open PowerShell in its folder. If using the [1.0.0 source](https://github.com/MRJonam91/OpenResearchEngine/releases/tag/v1.0.0), download the fictional file linked in step 3 separately: it was added after that release.
2. Run `./run.ps1 -Workspace ./workspace-trial` and open `http://127.0.0.1:8765`. First installation needs internet for dependencies; this manual workflow then uses local files.
3. Import [examples/first-source.txt](../examples/first-source.txt) using the file picker. Search for `Northbridge`, open the source and select the passage containing the opening time.
4. Create `The fictional Northbridge Library opens at 09:00 on weekdays.` with that passage as evidence. Inspect the proposed claim and approve it for this demonstration.
5. Export Markdown and check its claim, source, passage and hash. A claim left proposed is excluded from the default report.

Success means you can trace the report back to the original passage. Setup time depends on your computer. Autonomous web discovery, OCR and automatic truth verification are outside this workflow. Workspaces and reports contain plaintext and local paths; keep them local and review exports before sharing.

Report your OS, Python version, the step and expected result through [Support](../SUPPORT.md), using only the fictional file. Do not upload personal documents or workspaces. [Full guide](USER_GUIDE.md).
