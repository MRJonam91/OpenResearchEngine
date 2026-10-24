# Third-party notices / Componenti di terzi

Le dipendenze non sono vendorizzate nel sorgente. Le distribuzioni installate mantengono i propri avvisi e licenze. La lista esatta dell'ambiente verificato è in `requirements.lock`; i pacchetti delle dipendenze includono i testi vincolanti. Nessun modello o documento di terzi è incluso nella release.

Dependencies are not vendored in this source tree. Installed distributions retain their own notices and licenses. `requirements.lock` records the tested environment; dependency packages contain the governing license texts. No model weights or third-party research documents are shipped.

| Component | License | Source |
| --- | --- | --- |
| FastAPI | MIT | https://github.com/fastapi/fastapi |
| Pydantic / pydantic-core | MIT | https://github.com/pydantic/pydantic |
| Starlette | BSD-3-Clause | https://github.com/Kludex/starlette |
| Uvicorn | BSD-3-Clause | https://github.com/encode/uvicorn |
| pypdf | BSD-3-Clause | https://github.com/py-pdf/pypdf |
| ReportLab | BSD-style, upstream license.txt | https://hg.reportlab.com/hg-public/reportlab |
| Pillow | MIT-CMU | https://github.com/python-pillow/Pillow |
| Bitstream Vera fonts, supplied by ReportLab | Bitstream Vera font license | ReportLab `fonts/bitstream-vera-license.txt` |
| AnyIO | MIT | https://github.com/agronholm/anyio |
| h11 | MIT | https://github.com/python-hyper/h11 |
| Click | BSD-3-Clause | https://github.com/pallets/click |
| OpenTelemetry API | Apache-2.0 | https://github.com/open-telemetry/opentelemetry-python |
| charset-normalizer | MIT | https://github.com/jawah/charset_normalizer |
| idna | BSD-3-Clause | https://github.com/kjd/idna |
| typing-extensions | PSF-2.0 | https://github.com/python/typing_extensions |
| typing-inspection, annotated-types, annotated-doc | MIT | Installed distribution metadata/licenses |

Development tools (pytest, HTTPX2, build, pip-audit and their dependencies) keep their own licenses and are not bundled into the application wheel. SQLite, XML, ZIP, TLS and HTTP facilities are supplied by Python and the system runtime.

The original application code uses GPL-3.0-or-later. Runtime dependencies remain under their permissive licenses and font software remains separately licensed. Review upstream licenses again when changing dependencies or redistributing a complete environment. Model licenses depend on the chosen Ollama model and must be checked separately; a local runtime does not change those terms.
