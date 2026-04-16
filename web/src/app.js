// openfile-az — browser app
// ---------------------------------------------------------------------------
// Loads Pyodide, extracts the openfile_az Python package from core.zip into
// the Pyodide virtual filesystem, wires file loads → Python → downloads.
// Nothing is sent to a server. All processing happens in this browser tab.
// ---------------------------------------------------------------------------

import { state, els, uiInit } from "./ui.js";

// --- Pyodide loading --------------------------------------------------------

// Prefer locally-bundled Pyodide (for true offline + self-host). The build
// script places it under ./vendor/pyodide/. If missing, we fall back to the
// official CDN so a dev-mode `python -m http.server` still works.
const PYODIDE_LOCAL = "./vendor/pyodide/";
const PYODIDE_CDN   = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/";

async function headOk(url) {
  try {
    const r = await fetch(url, { method: "HEAD", cache: "no-store" });
    return r.ok;
  } catch { return false; }
}

async function pickPyodideBase() {
  if (await headOk(PYODIDE_LOCAL + "pyodide.js")) return PYODIDE_LOCAL;
  return PYODIDE_CDN;
}

async function loadPyodideRuntime() {
  const base = await pickPyodideBase();
  // Dynamically inject the Pyodide loader
  await new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = base + "pyodide.js";
    s.onload = resolve;
    s.onerror = () => reject(new Error("failed to load pyodide.js from " + base));
    document.head.appendChild(s);
  });
  // eslint-disable-next-line no-undef
  const pyodide = await loadPyodide({ indexURL: base });
  return pyodide;
}

async function installPythonPackages(pyodide) {
  setStatus("loading", "Installing Python packages (pypdf, pandas, openpyxl, reportlab)…");
  await pyodide.loadPackage(["micropip"]);
  const micropip = pyodide.pyimport("micropip");
  // Core deps. All of these have pre-built Pyodide wheels.
  await micropip.install([
    "pypdf",
    "pandas",
    "openpyxl",
    "reportlab",
    "pyyaml",
  ]);
}

async function loadCoreZip(pyodide) {
  setStatus("loading", "Loading openfile-az core…");
  const resp = await fetch("./core.zip", { cache: "default" });
  if (!resp.ok) throw new Error("core.zip not found — did you run the build script?");
  const buf = new Uint8Array(await resp.arrayBuffer());
  // Write to Pyodide FS and unpack
  pyodide.FS.writeFile("/tmp/core.zip", buf);
  await pyodide.runPythonAsync(`
import sys, zipfile, os
os.makedirs("/pkgs", exist_ok=True)
with zipfile.ZipFile("/tmp/core.zip") as z:
    z.extractall("/pkgs")
if "/pkgs" not in sys.path:
    sys.path.insert(0, "/pkgs")
import openfile_az
print("openfile_az", openfile_az.__version__, "loaded (AZ form rev", openfile_az.__az_form_revision__, ")")
  `);
}

// --- DOM utilities (XSS-safe) ----------------------------------------------

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else if (k.startsWith("data-")) node.setAttribute(k, v);
    else if (k === "href" || k === "src" || k === "download" || k === "type") node.setAttribute(k, v);
    else node[k] = v;
  }
  for (const c of children) {
    if (c == null) continue;
    node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
  }
  return node;
}

function clearChildren(parent) {
  while (parent.firstChild) parent.removeChild(parent.firstChild);
}

// --- UI state helpers -------------------------------------------------------

function setStatus(stateName, text) {
  els.statusDot.dataset.state = stateName;
  els.statusText.textContent = text;
}

function updateGenerateReadiness() {
  // Enable the Generate button when Pyodide is ready AND we have the
  // minimum required inputs (files OR manual entries for donors + disbursements).
  const hasDonors = (state.files.donors.length > 0) || (state.manualEntries.donors.length > 0);
  const hasDisb   = (state.files.disbursements.length > 0) || (state.manualEntries.disbursements.length > 0);
  const hasConfig = state.configSource === "form" ? state.configForm.cmteId : state.files.config;
  const minReady  = window.openfileAz.pyodideReady && hasDonors && hasDisb && hasConfig;
  els.btnGenerate.disabled = !minReady;
}

// --- File plumbing ----------------------------------------------------------

function wireDropZone(zoneId, inputId, stateKey, previewId) {
  const zone  = document.getElementById(zoneId);
  const input = document.getElementById(inputId);
  const preview = previewId ? document.getElementById(previewId) : null;

  zone.addEventListener("click", () => input.click());
  zone.addEventListener("dragover", (e) => { e.preventDefault(); zone.classList.add("dragover"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("dragover");
    if (e.dataTransfer.files.length) {
      input.files = e.dataTransfer.files;
      input.dispatchEvent(new Event("change"));
    }
  });

  input.addEventListener("change", async () => {
    const newFiles = Array.from(input.files);
    if (!newFiles.length) return;

    // Multi-file categories (donors, disbursements, debts) accumulate;
    // single-file categories (config, sig) replace.
    const isMulti = Array.isArray(state.files[stateKey]);
    if (isMulti) {
      state.files[stateKey].push(...newFiles);
    } else {
      state.files[stateKey] = newFiles[0];
    }

    zone.classList.add("filled");
    if (preview) {
      preview.hidden = false;
      if (isMulti) {
        const all = state.files[stateKey];
        const totalKB = all.reduce((s, f) => s + f.size, 0) / 1024;
        preview.textContent = `${all.length} file(s), ${totalKB.toFixed(1)} kB total: ${all.map(f => f.name).join(", ")}`;
        // Preview the most recently added file's column mapping
        if (window.openfileAz.pyodideReady && ["donors","disbursements","debts"].includes(stateKey)) {
          previewMapping(stateKey, newFiles[newFiles.length - 1], preview);
        }
      } else {
        const f = newFiles[0];
        preview.textContent = `${f.name} (${(f.size/1024).toFixed(1)} kB)`;
      }
    }
    updateGenerateReadiness();
  });
}


// --- Manual entry forms ------------------------------------------------------

function wireManualEntry(btnId, formId, tableId, stateKey, displayCols) {
  const btn   = document.getElementById(btnId);
  const form  = document.getElementById(formId);
  const table = document.getElementById(tableId);
  const tbody = table.querySelector("tbody");

  btn.addEventListener("click", () => {
    // Collect all data-field inputs from the form
    const entry = {};
    let hasRequired = true;
    for (const inp of form.querySelectorAll("[data-field]")) {
      const key = inp.dataset.field;
      const val = inp.value.trim();
      entry[key] = val;
      if (inp.required && !val) hasRequired = false;
    }
    if (!hasRequired) {
      alert("Please fill in all required fields.");
      return;
    }

    state.manualEntries[stateKey].push(entry);

    // Render the row in the preview table
    table.hidden = false;
    const tr = document.createElement("tr");
    for (const col of displayCols) {
      const td = document.createElement("td");
      td.textContent = entry[col] || "";
      tr.appendChild(td);
    }
    // Remove button
    const tdDel = document.createElement("td");
    const btnRm = document.createElement("button");
    btnRm.className = "btn-remove";
    btnRm.textContent = "remove";
    btnRm.addEventListener("click", () => {
      const idx = state.manualEntries[stateKey].indexOf(entry);
      if (idx >= 0) state.manualEntries[stateKey].splice(idx, 1);
      tr.remove();
      if (!tbody.children.length) table.hidden = true;
      updateGenerateReadiness();
    });
    tdDel.appendChild(btnRm);
    tr.appendChild(tdDel);
    tbody.appendChild(tr);

    // Clear the form inputs for the next entry
    for (const inp of form.querySelectorAll("[data-field]")) {
      if (inp.tagName === "SELECT") continue; // keep dropdowns at current selection
      inp.value = "";
    }
    updateGenerateReadiness();
  });
}

async function previewMapping(kind, file, previewEl) {
  const pyodide = window.openfileAz.pyodide;
  const buf = new Uint8Array(await file.arrayBuffer());
  pyodide.FS.writeFile(`/tmp/preview_${kind}`, buf);
  const ext = file.name.split(".").pop().toLowerCase();
  const detectFn = {
    donors: "detect_donor_columns",
    disbursements: "detect_disbursement_columns",
    debts: "detect_debt_columns",
  }[kind];

  try {
    const py = await pyodide.runPythonAsync(`
import pandas as pd, json
from openfile_az.column_mapper import ${detectFn}
path = "/tmp/preview_${kind}"
ext = "${ext}"
df = pd.read_excel(path) if ext in ("xlsx", "xls") else pd.read_csv(path)
r = ${detectFn}(df.columns.tolist())
json.dumps({
  "rows": int(len(df)),
  "cols": list(df.columns),
  "mapping": r.mapping,
  "missing": r.missing,
  "ambiguous": r.ambiguous,
  "extras": r.extras,
  "complete": r.is_complete(),
})
    `);
    const info = JSON.parse(py);
    let cls = info.complete ? "ok" : "warn";
    let txt = `${info.rows} rows · ${Object.keys(info.mapping).length}/${info.cols.length} columns mapped`;
    if (!info.complete) {
      txt += ` · MISSING: ${info.missing.join(", ")}`;
      cls = "err";
    } else if (info.ambiguous && Object.keys(info.ambiguous).length) {
      txt += ` · ambiguous: ${Object.keys(info.ambiguous).join(", ")}`;
    }
    previewEl.className = `preview ${cls}`;
    previewEl.textContent = txt;
  } catch (e) {
    previewEl.className = "preview err";
    previewEl.textContent = `Error reading file: ${e.message}`;
  }
}

// --- Generate ---------------------------------------------------------------

async function generate() {
  els.btnGenerate.disabled = true;
  els.btnSpinner.hidden = false;
  els.btnGenerateText.textContent = "Generating…";
  els.results.hidden = true;
  clearChildren(els.resultList);

  try {
    const pyodide = window.openfileAz.pyodide;

    // Write all user files into Pyodide FS
    const files = state.files;
    for (const [key, f] of Object.entries(files)) {
      if (!f) continue;
      const buf = new Uint8Array(await f.arrayBuffer());
      pyodide.FS.writeFile(`/work/${key}__${f.name}`, buf);
    }

    // NOTE: Full generation pipeline depends on schedule_builder v0.2
    //       consuming (config, donors_df, disbursements_df, debts_df). Until
    //       v0.2 ships, this call verifies the modules load cleanly.
    const resultJson = await pyodide.runPythonAsync(`
import json, os
os.makedirs("/out", exist_ok=True)
from openfile_az import __version__, __az_form_revision__
from openfile_az import column_mapper, pdf_filler, templates  # smoke imports
json.dumps({
  "status": "scaffold-only",
  "version": __version__,
  "form_rev": __az_form_revision__,
  "message": "Web UI scaffold is live. Full browser generation lands in v0.3 once schedule_builder is refactored (v0.2).",
})
    `);

    const result = JSON.parse(resultJson);
    renderResults(result);
  } catch (e) {
    console.error(e);
    alert("Generation failed: " + e.message);
  } finally {
    els.btnSpinner.hidden = true;
    els.btnGenerateText.textContent = "Generate filing";
    els.btnGenerate.disabled = false;
  }
}

function renderResults(result) {
  els.results.hidden = false;

  if (result.status === "scaffold-only") {
    const subText = `${result.message}  ·  openfile-az v${result.version} · AZ form rev ${result.form_rev}`;
    const li = el("li", {}, [
      el("div", {}, [
        el("strong", { text: "Ready for v0.3 wiring" }),
        el("br"),
        el("span", {
          text: subText,
          style: "color:var(--fg-muted);font-size:.85rem;display:block;margin-top:.25rem",
        }),
      ]),
    ]);
    els.resultList.appendChild(li);
    return;
  }

  for (const f of result.files || []) {
    const blob = new Blob(
      [Uint8Array.from(atob(f.b64), (c) => c.charCodeAt(0))],
      { type: f.mime },
    );
    const url = URL.createObjectURL(blob);
    const item = el("li", {}, [
      el("span", { text: `${f.name} · ${(f.size / 1024).toFixed(0)} kB` }),
      el("a", { href: url, download: f.name, text: "Download" }),
    ]);
    els.resultList.appendChild(item);
  }
}

// --- Bootstrap --------------------------------------------------------------

async function boot() {
  uiInit();

  // Wire drop zones (multi-file for donors/disbursements/debts)
  wireDropZone("dropConfig", "fileConfig", "config", null);
  wireDropZone("dropDonors", "fileDonors", "donors", "previewDonors");
  wireDropZone("dropDisb",   "fileDisb",   "disbursements", "previewDisb");
  wireDropZone("dropDebts",  "fileDebts",  "debts", "previewDebts");
  wireDropZone("dropSig",    "fileSig",    "sig", null);

  // Wire manual-entry forms
  wireManualEntry("btnAddDonor", "formDonor", "tableDonor", "donors",
                  ["date", "last", "amount", "kind", "donor_type"]);
  wireManualEntry("btnAddDisb",  "formDisb",  "tableDisb",  "disbursements",
                  ["date", "payee", "amount", "category"]);
  wireManualEntry("btnAddDebt",  "formDebt",  "tableDebt",  "debts",
                  ["date_incurred", "creditor", "amount_outstanding", "type_of_debt"]);

  // Form → state
  const cfgIds = [
    "cfgCmteId","cfgCmteName","cfgCandidate","cfgTreasurer","cfgAddress",
    "cfgOffice","cfgOfficeType","cfgStartBalance","cfgPeriod",
  ];
  for (const id of cfgIds) {
    document.getElementById(id).addEventListener("input", (e) => {
      const key = id.replace(/^cfg/, "");
      state.configForm[key.charAt(0).toLowerCase() + key.slice(1)] = e.target.value;
      updateGenerateReadiness();
    });
  }

  els.btnGenerate.addEventListener("click", generate);

  // Load Pyodide (async — page is usable during load)
  try {
    setStatus("loading", "Loading Python runtime (first visit: ~10s, cached thereafter)…");
    const pyodide = await loadPyodideRuntime();
    window.openfileAz.pyodide = pyodide;
    await installPythonPackages(pyodide);
    await loadCoreZip(pyodide);
    pyodide.FS.mkdir("/work");
    window.openfileAz.pyodideReady = true;
    setStatus("ready", "Ready. Fill in committee info, load spreadsheets, generate.");
  } catch (e) {
    console.error(e);
    setStatus("error", "Failed to load Python runtime: " + e.message);
  }

  updateGenerateReadiness();

  // Populate build info in footer (set at build time by build.py)
  if (window.openfileAz.buildInfo) {
    els.buildInfo.textContent = window.openfileAz.buildInfo;
  }
}

boot().catch((e) => {
  console.error("boot failed", e);
  setStatus("error", e.message);
});
