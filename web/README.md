# web/ — browser version (coming soon)

This directory will contain the [Pyodide](https://pyodide.org)-powered single-page app that runs openfile-az entirely in the browser. No server, no data upload, no tracking.

**Planned contents:**
- `index.html` — drag-drop UI for committee config + spreadsheets
- `app.js` — Pyodide bootstrap + Python module loading + file download wiring
- `styles.css` — Tailwind-first styling
- `core.zip` — build artifact: the openfile_az Python package bundled as a zip, extracted into Pyodide's virtual filesystem on page load

The hosted build lives at [azfile.energyfreedom.team](https://azfile.energyfreedom.team).

**Why Pyodide?** The same Python code that runs locally via `pip install openfile-az` runs unchanged in the browser via WebAssembly. Your donor data never leaves your device — turn off your wifi after the page loads and the tool still works.
