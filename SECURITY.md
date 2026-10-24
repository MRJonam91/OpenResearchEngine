# Sicurezza / Security

La versione 1.0 è un'applicazione locale per un solo utente. Mantieni il server su loopback; non usare port forwarding, proxy pubblici o hosting condiviso. Il token di sessione protegge le scritture nel browser e non sostituisce un sistema di account. Il workspace e i backup contengono documenti e percorsi originali in chiaro: proteggili con i permessi del sistema operativo e non allegarli alle issue.

Version 1.0 is a local single-user application. Keep it on loopback; do not use public forwarding/proxies or shared hosting. The session token protects browser writes and is not an account system. Workspaces and backups contain plaintext documents and original paths: protect them with OS permissions and do not attach them to issues.

Report vulnerabilities through GitHub's **Report a vulnerability** option when available. Otherwise open a minimal issue requesting a private reporting channel, without exploit details, credentials or user data. Supported fixes target the latest 1.0.x release. There is no guaranteed response-time SLA.

Imported documents and model output are untrusted. Ollama use is opt-in and restricted to the configured loopback runtime and installed local models. Validate the model's own license and privacy settings. Exact quote validation establishes a citation, not the truth of a generated statement. Review all claims and report content before sharing. Exports can contain local source paths and excerpts.
