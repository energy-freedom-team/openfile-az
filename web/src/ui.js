// UI state + DOM handles for the openfile-az browser app.
// Kept small and separate from app.js so bootstrap logic and state are easy
// to reason about.

export const state = {
  configSource: "form",              // "form" | "yaml"
  configForm: {
    cmteId: "",
    cmteName: "",
    candidate: "",
    treasurer: "",
    address: "",
    office: "",
    officeType: "candidate",
    startBalance: "0",
    period: "Q1",
  },
  files: {
    config: null,
    donors: null,
    disbursements: null,
    debts: null,
    sig: null,
  },
  sigMode: "cursive",                // "cursive" | "image"
};

export const els = {};

export function uiInit() {
  // Cache element refs once the DOM is ready.
  els.statusDot        = document.getElementById("statusDot");
  els.statusText       = document.getElementById("statusText");
  els.btnGenerate      = document.getElementById("btnGenerate");
  els.btnGenerateText  = document.getElementById("btnGenerateText");
  els.btnSpinner       = document.getElementById("btnSpinner");
  els.results          = document.getElementById("results");
  els.resultList       = document.getElementById("resultList");
  els.buildInfo        = document.getElementById("buildInfo");

  // Tab switching between "Fill in form" and "Load YAML"
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      const target = tab.dataset.tab;
      document.querySelectorAll(".tab").forEach((t) => {
        const active = t === tab;
        t.classList.toggle("active", active);
        t.setAttribute("aria-selected", active ? "true" : "false");
      });
      document.querySelectorAll(".tab-panel").forEach((p) => {
        p.classList.toggle("hidden", p.dataset.panel !== target);
      });
      state.configSource = target;
    });
  });

  // Signature mode toggle: show/hide image drop zone
  document.querySelectorAll('input[name="sigMode"]').forEach((r) => {
    r.addEventListener("change", () => {
      state.sigMode = r.value;
      document.getElementById("dropSig").classList.toggle(
        "hidden", r.value !== "image",
      );
    });
  });
}
