# Supporto / Support

Per problemi riproducibili usa le [issue](https://github.com/MRJonam91/OpenResearchEngine/issues). Includi versione (`sourcepilot --version`), sistema operativo, comando, errore e un piccolo esempio sintetico. Rimuovi nomi, percorsi personali, token e documenti reali dai log. Per vulnerabilità segui `SECURITY.md`.

For reproducible problems use [issues](https://github.com/MRJonam91/OpenResearchEngine/issues). Include version (`sourcepilot --version`), OS, command, error and a small synthetic example. Remove personal names/paths, tokens and real documents from logs. Follow `SECURITY.md` for vulnerabilities.

Useful diagnostics: `sourcepilot doctor --workspace PATH` checks database/original integrity; `sourcepilot ai-status --workspace PATH --model MODEL --embedding-model MODEL` checks configured model capabilities. A cold model may take longer to load; retry after checking the local runtime. Semantic search needs an index built for the same model digest.

Support is best-effort and voluntary. Donations do not purchase additional rights, guaranteed support or priority decisions.
