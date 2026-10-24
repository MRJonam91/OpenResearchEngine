# Contribuire / Contributing

Apri una issue con problema, comportamento atteso e un esempio sintetico riproducibile. Prima di una modifica ampia confrontati sullo scopo. I contributi devono preservare provenienza, citazioni e revisione umana. Non allegare workspace reali o documenti senza diritto di distribuirli.

Open an issue with the problem, expected behavior and a reproducible synthetic example. Discuss scope before a large change. Contributions must preserve provenance, citations and human review. Do not submit real workspaces or documents you cannot distribute.

```text
python -m venv .venv
python -m pip install -c requirements.lock -e ".[test]"
python -m pytest -q
node --check sourcepilot/static/app.js
```

Activate the virtual environment first, or use its Python executable directly. Test behavior and failure cases; include migration tests for database changes. Update Italian and English user documentation together. Keep generated data and model weights outside Git. Follow `CODE_OF_CONDUCT.md` and use the private process in `SECURITY.md` for vulnerabilities.

By submitting a contribution you confirm you have the right to distribute it under GPL-3.0-or-later, preserve required third-party attribution, and do not include confidential material. Sign off commits with `git commit -s` to record this certification; this does not transfer your copyright.
