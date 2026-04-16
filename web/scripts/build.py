#!/usr/bin/env python3
"""Build the static web bundle for self-hosted deployment.

Produces ./web/dist/ containing:
  - index.html, app.js, ui.js, styles.css        (from web/src/)
  - core.zip                                     (zipped openfile_az package)
  - templates/donors_template.xlsx, etc.         (copied from examples/)
  - vendor/pyodide/                              (optional — see --with-pyodide)
  - build-info.json                              (version, git sha, timestamp)

Usage:
  python3 web/scripts/build.py                    # minimal build, Pyodide from CDN
  python3 web/scripts/build.py --with-pyodide    # bundle Pyodide locally (~10MB)

With --with-pyodide the resulting dist/ runs entirely offline — ship it on
a USB stick, unzip it, double-click index.html.
"""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
WEB_SRC = REPO / "web" / "src"
WEB_DIST = REPO / "web" / "dist"
PACKAGE = REPO / "openfile_az"
EXAMPLES = REPO / "examples"

PYODIDE_VERSION = "0.26.4"
PYODIDE_CDN = f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE_VERSION}/full/"
PYODIDE_RELEASE = (
    f"https://github.com/pyodide/pyodide/releases/download/"
    f"{PYODIDE_VERSION}/pyodide-{PYODIDE_VERSION}.tar.bz2"
)


def log(msg):
    print(f"[build] {msg}")


def clean_dist():
    if WEB_DIST.exists():
        shutil.rmtree(WEB_DIST)
    WEB_DIST.mkdir(parents=True)


def copy_static():
    for name in ("index.html", "app.js", "ui.js", "styles.css"):
        src = WEB_SRC / name
        if src.exists():
            shutil.copy2(src, WEB_DIST / name)
            log(f"copied {name}")


def make_core_zip():
    """Zip the openfile_az package (minus bytecode + caches) for Pyodide to import."""
    out = WEB_DIST / "core.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(PACKAGE):
            # Skip caches
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".pytest_cache")]
            for f in files:
                if f.endswith((".pyc", ".pyo", ".DS_Store")):
                    continue
                full = Path(root) / f
                arc = full.relative_to(REPO)
                zf.write(full, arc)
    log(f"wrote {out} ({out.stat().st_size/1024:.1f} kB)")


def copy_templates():
    tdir = WEB_DIST / "templates"
    tdir.mkdir(parents=True, exist_ok=True)
    for name in ("donors_template.xlsx", "disbursements_template.xlsx", "debts_template.xlsx"):
        src = EXAMPLES / name
        if src.exists():
            shutil.copy2(src, tdir / name)
            log(f"copied template {name}")


def copy_samples():
    """Copy the synthetic sample dataset into dist/samples/ so the browser
    app can link to 'Try with sample data' downloads."""
    sdir = WEB_DIST / "samples"
    src_dir = EXAMPLES / "samples"
    if not src_dir.exists():
        log(f"WARN: {src_dir} not found — run web/scripts/generate_samples.py first")
        return
    sdir.mkdir(parents=True, exist_ok=True)
    for p in src_dir.iterdir():
        if p.is_file() and p.suffix.lower() in (".yaml", ".yml", ".csv", ".xlsx"):
            shutil.copy2(p, sdir / p.name)
            log(f"copied sample {p.name}")


def bundle_pyodide():
    """Download Pyodide and extract into dist/vendor/pyodide/ for offline use."""
    vendor = WEB_DIST / "vendor" / "pyodide"
    vendor.mkdir(parents=True, exist_ok=True)
    log(f"downloading Pyodide {PYODIDE_VERSION} (~12MB compressed)…")

    with tempfile.NamedTemporaryFile(suffix=".tar.bz2", delete=False) as tmp:
        urllib.request.urlretrieve(PYODIDE_RELEASE, tmp.name)
        log("extracting…")
        with tarfile.open(tmp.name) as tf:
            # The tarball has a top-level 'pyodide/' dir — flatten it into vendor/pyodide/
            for m in tf.getmembers():
                stripped = m.name.split("/", 1)[-1] if "/" in m.name else ""
                if not stripped:
                    continue
                m.name = stripped
                try:
                    tf.extract(m, vendor, filter="data")
                except TypeError:
                    tf.extract(m, vendor)
    log(f"Pyodide bundled at {vendor}")


def write_build_info(with_pyodide: bool):
    version = "unknown"
    pkg_init = PACKAGE / "__init__.py"
    if pkg_init.exists():
        for line in pkg_init.read_text().splitlines():
            if line.startswith("__version__"):
                version = line.split("=", 1)[1].strip().strip('"').strip("'")
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO, stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        sha = "no-git"
    info = {
        "version": version,
        "git_sha": sha,
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pyodide_bundled": with_pyodide,
        "pyodide_version": PYODIDE_VERSION,
    }
    (WEB_DIST / "build-info.json").write_text(json.dumps(info, indent=2))

    # Inject display-friendly version string into index.html via a small
    # inline <script> appended just before </head>.
    display = f"v{version} · {sha}"
    idx = WEB_DIST / "index.html"
    html = idx.read_text()
    inject = f"<script>window.openfileAz = window.openfileAz || {{}}; window.openfileAz.buildInfo = {json.dumps(display)};</script>"
    html = html.replace("</head>", inject + "\n</head>", 1)
    idx.write_text(html)
    log(f"build info: {info}")


def main():
    ap = argparse.ArgumentParser(description="Build openfile-az web bundle.")
    ap.add_argument("--with-pyodide", action="store_true",
                    help="Bundle Pyodide runtime locally for fully-offline use (~12MB download).")
    args = ap.parse_args()

    clean_dist()
    copy_static()
    make_core_zip()
    copy_templates()
    copy_samples()
    if args.with_pyodide:
        bundle_pyodide()
    write_build_info(args.with_pyodide)

    log("done.")
    log(f"output: {WEB_DIST}")
    log("preview locally: python3 web/scripts/serve.py")


if __name__ == "__main__":
    sys.exit(main() or 0)
