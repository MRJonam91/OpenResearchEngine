const s = { token: "", sources: [], claims: [], passages: [], versions: [], comparison: null, source: null, claim: null, passage: null, ai: null, aiBusy: false, tab: "sources" };
const $ = id => document.getElementById(id);
const statusLabel = value => ({ proposed: "da revisionare", approved: "approvata", uncertain: "incerta", rejected: "respinta" })[value] || value;

function el(tag, className = "", text = "") {
  const item = document.createElement(tag);
  item.className = className;
  item.textContent = text;
  return item;
}

function message(text, error = false) {
  $("import-status").textContent = text;
  $("import-status").classList.toggle("error", error);
}

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (options.method && options.method !== "GET") headers["X-SourcePilot-Token"] = s.token;
  if (options.json !== undefined) {
    headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(options.json);
  }
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    let detail = `Errore HTTP ${response.status}`;
    try { detail = (await response.json()).detail || detail; } catch (_) { /* Non JSON response. */ }
    if (Array.isArray(detail)) detail = detail.map(item => `${item.loc?.slice(1).join(".") || "Richiesta"}: ${item.msg}`).join("; ");
    throw new Error(detail);
  }
  return response.json();
}

function aiControls() {
  $("index-ai").disabled = s.aiBusy || !s.ai?.embeddings.available;
  $("suggest-ai").disabled = s.aiBusy || !s.ai?.analysis.available || !s.source;
  $("assess-ai").disabled = s.aiBusy || !s.ai?.analysis.available || s.sources.length < 2;
  $("refresh-ai").disabled = s.aiBusy;
  $("semantic-option").disabled = !s.ai?.embeddings.available;
}

function aiStatus() {
  if (!s.ai) return;
  const parts = Object.entries(s.ai).map(([kind, item]) => `${kind === "analysis" ? "Analisi" : "Semantica"}: ${!item.configured ? "non configurata" : item.available ? item.model : item.error}`);
  $("ai-status").textContent = parts.join(" · ");
  aiControls();
}

async function checkAI() {
  try { s.ai = await api("/api/ai/status"); aiStatus(); }
  catch (error) { $("ai-status").textContent = error.message; }
}

async function runAI(label, action) {
  if (s.aiBusy) return;
  s.aiBusy = true; aiControls();
  $("ai-status").textContent = label;
  $("ai-status").setAttribute("aria-busy", "true");
  try { await action(); }
  catch (error) { message(error.message, true); }
  finally { s.aiBusy = false; $("ai-status").removeAttribute("aria-busy"); aiStatus(); }
}

function coverageText(coverage) {
  if (coverage.left) return `Prima fonte: ${coverageText(coverage.left)} · Seconda fonte: ${coverageText(coverage.right)}`;
  const retrieved = coverage.retrieval_limit ? ` · ${coverage.retrieved_passages}/${coverage.matching_passages} corrispondenze recuperate (massimo ${coverage.retrieval_limit})` : "";
  return `${coverage.selected_passages}/${coverage.total_passages} passaggi della fonte · ${coverage.complete ? "contesto completo" : `contesto parziale (${coverage.truncated_passages} passaggi abbreviati)`}${retrieved}`;
}

function showAnalysis(run) {
  const panel = $("analysis-results"); panel.replaceChildren(); panel.hidden = false;
  panel.append(el("h3", "", run.kind === "claims" ? "Proposte da verificare" : "Possibili contraddizioni da verificare"));
  panel.append(el("p", "minor-note", `${run.model} · esecuzione ${run.id} · ${coverageText(run.coverage)}`));
  const items = run.result.claims || run.result.candidates;
  if (!items.length) panel.append(el("p", "empty", "Nessuna proposta prodotta per questo contesto."));
  items.forEach((item, index) => {
    const card = el("article", "proposal-card");
    if (run.kind === "claims") {
      const source = run.context.find(passage => passage.id === item.passage_id);
      card.append(el("h4", "", item.text), el("blockquote", "", item.quote), el("p", "passage-meta", `${source.title} · ${source.locator} · passaggio ${item.passage_id}`));
      const accept = el("button", "", "Accetta come bozza da revisionare"); accept.type = "button";
      accept.onclick = async () => {
        accept.disabled = true;
        try {
          s.claim = await api(`/api/ai/runs/${run.id}/accept/${index}`, {method:"POST"});
          s.tab = "claims"; await refresh(); passages();
          accept.textContent = "Bozza creata — revisione necessaria";
        } catch (error) { message(error.message, true); accept.disabled = false; }
      };
      card.append(accept);
    } else {
      card.append(el("p", "", item.reason));
      for (const side of ["left", "right"]) {
        const passage = run.context[side].find(p => p.id === item[`${side}_passage_id`]);
        card.append(el("blockquote", "", item[`${side}_quote`]), el("p", "passage-meta", `${passage.title} · ${passage.locator} · passaggio ${passage.id}`));
      }
    }
    panel.append(card);
  });
}

async function refresh() {
  [s.sources, s.claims] = await Promise.all([api("/api/sources"), api("/api/claims")]);
  $("source-count").textContent = s.sources.length;
  $("claim-count").textContent = s.claims.length;
  if (s.claim) s.claim = s.claims.find(item => item.id === s.claim.id) || null;
  for (const [id, preferred] of [["compare-left", 0], ["compare-right", 1]]) {
    const select = $(id);
    const previous = select.value;
    select.replaceChildren();
    for (const source of s.sources) {
      const option = el("option", "", source.title); option.value = source.source_id;
      select.append(option);
    }
    if (s.sources.some(source => String(source.source_id) === previous)) select.value = previous;
    else if (s.sources[preferred]) select.value = s.sources[preferred].source_id;
  }
  collection();
  review();
  aiControls();
}

function collection() {
  const list = $("collection-list");
  list.replaceChildren();
  for (const tab of ["sources", "claims"]) {
    const button = $(`${tab}-tab`);
    button.classList.toggle("active", s.tab === tab);
    button.setAttribute("aria-selected", String(s.tab === tab));
  }
  const items = s.tab === "sources" ? s.sources : s.claims;
  if (!items.length) {
    list.append(el("p", "empty", s.tab === "sources" ? "Nessuna fonte importata. Scegli un file o una cartella." : "Nessuna affermazione. Seleziona un passaggio per crearne una."));
    return;
  }
  for (const item of items) {
    const button = el("button", "collection-item");
    button.type = "button";
    button.classList.toggle("active", s.tab === "sources" ? s.source === item.source_id : s.claim?.id === item.id);
    button.append(el("span", "item-title", s.tab === "sources" ? item.title : item.text));
    button.append(el("span", "item-meta", s.tab === "sources" ? `${item.kind} · ${item.origin}` : `${statusLabel(item.status)} · ${item.evidence.length} passaggi`));
    button.onclick = () => s.tab === "sources" ? chooseSource(item.source_id) : chooseClaim(item.id);
    list.append(button);
  }
}

async function chooseSource(id) {
  $("analysis-results").hidden = true;
  s.comparison = null;
  s.source = id;
  s.versions = await api(`/api/sources/${id}/versions`);
  const select = $("version-select");
  select.replaceChildren();
  for (const [index, version] of s.versions.entries()) {
    const option = el("option", "", `${index === 0 ? "Ultima" : `Storica ${index + 1}`} · ${version.imported_at} · ${version.sha256.slice(0, 12)}`);
    option.value = version.version_id;
    select.append(option);
  }
  $("version-controls").hidden = !s.versions.length;
  await loadVersion();
  $("search-input").value = "";
  const source = s.sources.find(item => item.source_id === id);
  $("passage-context").textContent = `${source.title} · ${s.passages.length} ${s.passages.length === 1 ? "passaggio" : "passaggi"} · ${s.versions.length} ${s.versions.length === 1 ? "versione" : "versioni"}`;
  collection();
  passages();
  aiControls();
}

async function loadVersion() {
  const versionId = $("version-select").value;
  s.passages = await api(`/api/sources/${s.source}/passages?version_id=${encodeURIComponent(versionId)}`);
  $("original-link").href = `/api/sources/${s.source}/versions/${versionId}/original`;
}

function chooseClaim(id) {
  s.claim = s.claims.find(item => item.id === id) || null;
  s.passage = null;
  collection();
  review();
  passages();
}

function passageCard(passage) {
  const card = el("article", "passage-card");
  card.classList.toggle("selected", s.passage?.id === passage.id);
  card.append(el("div", "passage-meta", `${passage.title} · ${passage.locator} · passaggio ${passage.id} · versione ${passage.version_id}`));
  card.append(el("p", "passage-text", passage.text));
  if (passage.score !== undefined) card.append(el("p", "minor-note", `Similarità semantica: ${passage.score.toFixed(3)}`));
  const actions = el("div", "passage-actions");
  if (s.claim) {
    for (const [stance, title] of [["supports", "Supporta"], ["challenges", "Contrasta"], ["context", "Contesto"]]) {
      const button = el("button", "", title);
      button.type = "button";
      button.onclick = async () => {
        try {
          s.claim = await api(`/api/claims/${s.claim.id}/evidence`, { method: "POST", json: { passage_id: passage.id, stance } });
          await refresh(); message("Prova aggiornata. La revisione è di nuovo necessaria.");
        } catch (error) { message(error.message, true); }
      };
      actions.append(button);
    }
  } else {
    const button = el("button", "", "Usa per una nuova affermazione");
    button.type = "button";
    button.onclick = () => { s.passage = passage; passages(); review(); $("claim-text").focus(); };
    actions.append(button);
  }
  card.append(actions);
  return card;
}

function passages() {
  if (s.comparison) { showComparison(s.comparison); return; }
  const list = $("passage-list");
  list.hidden = false;
  $("compare-results").hidden = true;
  list.replaceChildren();
  if (!s.passages.length) {
    list.append(el("p", "empty", "Nessun passaggio da mostrare. Importa una fonte o modifica la ricerca."));
    return;
  }
  for (const passage of s.passages) list.append(passageCard(passage));
}

function showComparison(result) {
  s.comparison = result;
  const container = $("compare-results");
  container.replaceChildren();
  for (const side of [result.left, result.right]) {
    const column = el("section", "compare-side");
    column.append(el("h3", "", side.source.title));
    column.append(el("p", "minor-note", `${side.passages.length} ${side.passages.length === 1 ? "passaggio" : "passaggi"} · ultima versione ${side.source.sha256.slice(0, 12)}`));
    if (!side.passages.length) column.append(el("p", "empty", "Nessun passaggio corrispondente."));
    for (const passage of side.passages) column.append(passageCard(passage));
    container.append(column);
  }
  $("passage-list").hidden = true;
  container.hidden = false;
  $("version-controls").hidden = true;
  $("passage-context").textContent = `Confronto per “${result.query}” · risultati per fonte, non una verifica automatica`;
}

function review() {
  const panel = $("review-panel");
  panel.replaceChildren();
  if (!s.claim) {
    panel.append(el("h3", "", "Nuova affermazione"));
    panel.append(el("p", "minor-note", "Scrivi una proposizione verificabile. Il passaggio selezionato sarà la prima prova a supporto."));
    if (s.passage) {
      const excerpt = el("div", "selected-evidence");
      excerpt.append(el("strong", "", `${s.passage.title} · ${s.passage.locator}`));
      excerpt.append(el("span", "", s.passage.text));
      panel.append(excerpt);
    } else panel.append(el("p", "empty", "Seleziona un passaggio per iniziare."));
    const form = el("form");
    const label = el("label", "", "Affermazione"); label.htmlFor = "claim-text";
    const textarea = el("textarea"); textarea.id = "claim-text"; textarea.rows = 4; textarea.required = true; textarea.maxLength = 5000;
    const submit = el("button", "primary", "Crea affermazione"); submit.type = "submit"; submit.disabled = !s.passage;
    form.append(label, textarea, submit);
    form.onsubmit = async event => {
      event.preventDefault();
      if (submit.disabled) return;
      submit.disabled = true;
      try {
        s.claim = await api("/api/claims", { method: "POST", json: { text: textarea.value, passage_id: s.passage.id } });
        s.passage = null; s.tab = "claims";
        await refresh(); passages();
      } catch (error) { message(error.message, true); submit.disabled = false; }
    };
    panel.append(form);
    return;
  }
  const claim = s.claim;
  const newButton = el("button", "ghost", "Nuova affermazione");
  newButton.type = "button";
  newButton.onclick = () => { s.claim = null; collection(); passages(); review(); };
  panel.append(newButton, el("h3", "", claim.text), el("span", "review-status", statusLabel(claim.status)));
  if (claim.provenance?.kind === "ai") panel.append(el("p", "minor-note", `Bozza iniziale AI: ${claim.provenance.model} · esecuzione ${claim.provenance.run_id}. Verifica testo e prove prima di approvare.`));
  if (claim.disputed) panel.append(el("p", "minor-note", "Sono presenti passaggi che supportano e contrastano questa affermazione."));
  const edit = el("details", "edit-claim");
  edit.append(el("summary", "", "Modifica affermazione"));
  const editForm = el("form");
  const editLabel = el("label", "", "Testo dell'affermazione"); editLabel.htmlFor = "edit-claim-text";
  const editText = el("textarea"); editText.id = "edit-claim-text"; editText.rows = 4; editText.maxLength = 5000; editText.required = true; editText.value = claim.text;
  const editSubmit = el("button", "", "Salva testo e richiedi nuova revisione"); editSubmit.type = "submit";
  editForm.append(editLabel, editText, editSubmit);
  editForm.onsubmit = async event => {
    event.preventDefault();
    try {
      s.claim = await api(`/api/claims/${claim.id}/text`, { method: "PATCH", json: { text: editText.value } });
      await refresh(); message("Testo aggiornato. La revisione è di nuovo necessaria.");
    } catch (error) { message(error.message, true); }
  };
  edit.append(editForm);
  panel.append(edit);
  panel.append(el("label", "", `Passaggi collegati (${claim.evidence.length})`));
  for (const evidence of claim.evidence) {
    const row = el("div", "evidence-row");
    const stance = el("select");
    stance.setAttribute("aria-label", `Ruolo del passaggio ${evidence.passage_id}`);
    for (const [value, title] of [["supports", "Supporta"], ["challenges", "Contrasta"], ["context", "Contesto"]]) {
      const option = el("option", "", title); option.value = value; option.selected = value === evidence.stance; stance.append(option);
    }
    stance.onchange = async () => {
      try {
        s.claim = await api(`/api/claims/${claim.id}/evidence`, { method: "POST", json: { passage_id: evidence.passage_id, stance: stance.value } });
        await refresh(); message("Ruolo della prova aggiornato. La revisione è di nuovo necessaria.");
      } catch (error) { message(error.message, true); }
    };
    row.append(stance);
    row.append(el("span", "", evidence.text));
    row.append(el("small", "", `${evidence.title} · ${evidence.locator} · SHA-256 ${evidence.sha256.slice(0, 16)}`));
    if (claim.evidence.length > 1) {
      const remove = el("button", "ghost", "Scollega passaggio"); remove.type = "button";
      remove.onclick = async () => {
        try {
          s.claim = await api(`/api/claims/${claim.id}/evidence/${evidence.passage_id}`, { method: "DELETE" });
          await refresh(); message("Prova scollegata. La revisione è di nuovo necessaria.");
        } catch (error) { message(error.message, true); }
      };
      row.append(remove);
    }
    panel.append(row);
  }
  const form = el("form");
  const label = el("label", "", "Stato della revisione"); label.htmlFor = "review-status";
  const select = el("select"); select.id = "review-status";
  for (const [value, title] of [["proposed", "Da revisionare"], ["approved", "Approvata"], ["uncertain", "Incerta"], ["rejected", "Respinta"]]) {
    const option = el("option", "", title); option.value = value; option.selected = value === claim.status; select.append(option);
  }
  const noteLabel = el("label", "", "Nota di revisione"); noteLabel.htmlFor = "review-note";
  const note = el("textarea"); note.id = "review-note"; note.rows = 3; note.maxLength = 5000; note.value = claim.note;
  const submit = el("button", "primary", "Salva revisione"); submit.type = "submit";
  form.append(label, select, noteLabel, note, submit);
  form.onsubmit = async event => {
    event.preventDefault();
    try {
      s.claim = await api(`/api/claims/${claim.id}`, { method: "PATCH", json: { status: select.value, note: note.value } });
      await refresh(); message("Revisione salvata.");
    } catch (error) { message(error.message, true); }
  };
  panel.append(form);
  const history = el("details", "revision-history");
  history.append(el("summary", "", "Cronologia revisioni"));
  history.ontoggle = async () => {
    if (!history.open) return;
    try {
      const revisions = await api(`/api/claims/${claim.id}/revisions`);
      history.querySelectorAll(".revision-entry, .empty").forEach(item => item.remove());
      if (!revisions.length) history.append(el("p", "empty", "Nessuna revisione precedente."));
      for (const revision of revisions) {
        const entry = el("div", "revision-entry");
        entry.append(el("strong", "", `${revision.action === "edit" ? "Modifica" : revision.action.startsWith("evidence:") ? "Prova modificata" : "Revisione"} · ${revision.changed_at}`));
        entry.append(el("span", "", `${revision.previous_text} · ${statusLabel(revision.previous_status)}`));
        if (revision.action.startsWith("evidence:")) entry.append(el("small", "", revision.action));
        if (revision.previous_note) entry.append(el("small", "", revision.previous_note));
        history.append(entry);
      }
    } catch (error) { message(error.message, true); }
  };
  panel.append(history);
}

async function upload(files) {
  const picked = Array.from(files);
  if (!picked.length) return;
  let imported = 0;
  const failures = [];
  for (const file of picked) {
    message(`Importazione ${imported + failures.length + 1}/${picked.length}: ${file.name}`);
    try {
      await api("/api/import", { method: "POST", headers: { "X-File-Name": encodeURIComponent(file.name), "X-Relative-Path": encodeURIComponent(file.webkitRelativePath || file.name) }, body: file });
      imported++;
    } catch (error) { failures.push(`${file.name}: ${error.message}`); }
  }
  await refresh();
  if (s.sources.length && !s.source) await chooseSource(s.sources[0].source_id);
  message(`${imported} file importati.${failures.length ? `\n${failures.join("\n")}` : ""}`, failures.length > 0);
}

$("pick-files").onclick = () => $("file-input").click();
$("pick-folder").onclick = () => $("folder-input").click();
$("file-input").onchange = event => upload(event.target.files);
$("folder-input").onchange = event => upload(event.target.files);
$("version-select").onchange = async () => {
  try {
    await loadVersion();
    const source = s.sources.find(item => item.source_id === s.source);
    $("passage-context").textContent = `${source.title} · ${s.passages.length} passaggi · versione ${$("version-select").value}`;
    passages();
  } catch (error) { message(error.message, true); }
};
for (const tab of ["sources", "claims"]) $(`${tab}-tab`).onclick = () => { s.tab = tab; collection(); };
$("search-form").onsubmit = async event => {
  event.preventDefault();
  const submit = event.currentTarget.querySelector("button");
  if (submit.disabled) return;
  submit.disabled = true;
  try {
    const query = $("search-input").value.trim();
    let coverage = "";
    if (query && $("search-mode").value === "semantic") {
      const result = await api("/api/ai/search", {method:"POST", json:{query, include_history:$("include-history").checked}});
      s.passages = result.results;
      coverage = ` · semantica · indice ${result.coverage.indexed}/${result.coverage.total}${result.coverage.complete ? "" : " (parziale)"}`;
    } else s.passages = query ? await api(`/api/search?q=${encodeURIComponent(query)}&include_history=${$("include-history").checked}`) : [];
    s.comparison = null;
    s.source = null;
    $("analysis-results").hidden = true;
    aiControls();
    $("version-controls").hidden = true;
    $("passage-context").textContent = query ? `${s.passages.length} risultati per “${query}”${coverage}` : "Inserisci una parola da cercare.";
    collection(); passages();
  } catch (error) { message(error.message, true); }
  finally { submit.disabled = false; }
};
$("compare-form").onsubmit = async event => {
  event.preventDefault();
  try {
    const params = new URLSearchParams({ left_id: $("compare-left").value, right_id: $("compare-right").value, q: $("compare-query").value.trim() });
    showComparison(await api(`/api/compare?${params}`));
  } catch (error) { message(error.message, true); }
};
$("url-form").onsubmit = async event => {
  event.preventDefault();
  const submit = event.currentTarget.querySelector("button");
  if (submit.disabled) return;
  submit.disabled = true;
  const url = $("url-input").value.trim();
  try {
    message(`Importazione URL: ${url}`);
    await api("/api/import-url", { method: "POST", json: { url } });
    $("url-input").value = "";
    await refresh(); await chooseSource(s.sources[0].source_id);
    message("URL importato.");
  } catch (error) { message(error.message, true); }
  finally { submit.disabled = false; }
};

$("refresh-ai").onclick = checkAI;
$("index-ai").onclick = () => runAI("Indicizzazione locale in corso…", async () => {
  const result = await api("/api/ai/index", {method:"POST", json:{limit:100, include_history:$("include-history").checked}});
  message(`Indice semantico: ${result.indexed}/${result.total} passaggi. ${result.remaining ? `Restano ${result.remaining} passaggi: ripeti l'indicizzazione.` : "Indice completo."}`);
});
$("suggest-ai").onclick = () => runAI("Preparazione delle proposte citate…", async () => showAnalysis(await api(`/api/ai/sources/${s.source}/suggest`, {method:"POST"})));
$("assess-ai").onclick = () => runAI("Confronto AI delle prove in corso…", async () => showAnalysis(await api("/api/ai/assess", {method:"POST", json:{left_id:Number($("compare-left").value), right_id:Number($("compare-right").value), query:$("compare-query").value.trim()}})));
$("check-workspace").onclick = async event => {
  event.currentTarget.disabled = true;
  try {
    const result = await api("/api/workspace/health");
    message(result.healthy ? `Workspace integro: ${result.counts.source} fonti, ${result.counts.passage} passaggi, ${result.counts.claim} affermazioni.` : result.issues.map(item => item.error).join("; "), !result.healthy);
  } catch (error) { message(error.message, true); }
  finally { $("check-workspace").disabled = false; }
};
$("backup-workspace").onclick = async () => {
  $("backup-workspace").disabled = true; message("Creazione backup verificato…");
  try {
    const response = await fetch("/api/workspace/backup", {method:"POST", headers:{"X-SourcePilot-Token":s.token}});
    if (!response.ok) throw new Error((await response.json()).detail || "Backup non riuscito");
    const url = URL.createObjectURL(await response.blob());
    const link = el("a"); link.href = url; link.download = "sourcepilot-backup.zip"; document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000); message("Backup pronto per il download. Contiene database e originali.");
  } catch (error) { message(error.message, true); }
  finally { $("backup-workspace").disabled = false; }
};

(async () => {
  try {
    const bootstrap = await api("/api/bootstrap");
    s.token = bootstrap.write_token;
    $("workspace-path").textContent = bootstrap.workspace;
    await refresh(); passages();
    if (s.sources.length) await chooseSource(s.sources[0].source_id);
    await checkAI();
  } catch (error) { message(error.message, true); }
})();
