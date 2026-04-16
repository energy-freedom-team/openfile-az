#!/usr/bin/env python3
"""Dev-mode local server for the openfile-az web bundle.

Serves ./web/dist/ on http://localhost:8080 with correct MIME types and the
COOP/COEP headers Pyodide needs for shared memory / wasm threading.

Usage:
  python3 web/scripts/serve.py                # serves on :8080
  python3 web/scripts/serve.py --port 9000
  python3 web/scripts/serve.py --dir some/other/dist  # serve a custom dir
"""
from __future__ import annotations
import argparse
import http.server
import os
import socketserver
import sys
import webbrowser
from functools import partial
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
DEFAULT_DIST = REPO / "web" / "dist"


class OpenfileHandler(http.server.SimpleHTTPRequestHandler):
    """Static file handler with Pyodide-friendly headers + nicer MIME coverage."""

    # Additional MIME types Pyodide uses
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".wasm": "application/wasm",
        ".mjs": "text/javascript",
        ".js": "text/javascript",
        ".json": "application/json",
        ".map": "application/json",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".pdf": "application/pdf",
    }

    def end_headers(self):
        # Pyodide 0.24+ is happy without SharedArrayBuffer, but setting these
        # headers keeps forward-compatibility with packages that use it.
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "credentialless")
        self.send_header("Cache-Control", "no-cache")  # dev-mode convenience
        super().end_headers()

    def log_message(self, fmt, *args):
        # Compact, quiet log line
        sys.stderr.write("  " + (fmt % args) + "\n")


def main():
    ap = argparse.ArgumentParser(description="Serve the openfile-az web bundle locally.")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8080)))
    ap.add_argument("--dir", default=str(DEFAULT_DIST), help="Directory to serve.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--no-browser", action="store_true", help="Don't open a browser tab.")
    args = ap.parse_args()

    serve_dir = Path(args.dir).resolve()
    if not serve_dir.exists():
        print(f"error: {serve_dir} does not exist. Did you run `python3 web/scripts/build.py`?",
              file=sys.stderr)
        return 1

    os.chdir(serve_dir)
    handler = partial(OpenfileHandler, directory=str(serve_dir))

    with socketserver.TCPServer((args.host, args.port), handler) as httpd:
        url = f"http://{args.host}:{args.port}/"
        print(f"  openfile-az dev server")
        print(f"  serving {serve_dir}")
        print(f"  at      {url}")
        print(f"  Ctrl-C to stop.\n")
        if not args.no_browser:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  shutting down.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
