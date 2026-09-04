"""Dev server for the map.

Plain `python -m http.server` lets the browser cache app.js and style.css, so
edits appear not to take effect — the page keeps running the old script against
new data. This sends no-store on everything, which is the right trade for a
local dev server: the 11MB points.bin re-reads from disk, not the network.

    python web/serve.py [port]
"""
import functools
import http.server
import json
import os
import socketserver
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
ROOT = os.path.dirname(os.path.abspath(__file__))
APP_TAG = '<script src="app.js"></script>'


def carto_key() -> str:
    """The CARTO basemap key, from the environment or the project .env.

    Kept local rather than imported from src/config.py so the dev server stays a
    single file with no path juggling.
    """
    if os.environ.get("CARTO_KEY"):
        return os.environ["CARTO_KEY"]
    path = os.path.join(os.path.dirname(ROOT), ".env")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("CARTO_KEY="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    return ""


CARTO_KEY = carto_key()


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # index.html is rewritten in flight to carry the CARTO key, so the key
        # stays in .env and out of the tracked app.js.
        if CARTO_KEY and self.path.split("?")[0] in ("/", "/index.html"):
            self.send_index()
            return
        super().do_GET()

    def send_index(self):
        with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f:
            html = f.read()
        inject = f"<script>window.CARTO_KEY = {json.dumps(CARTO_KEY)};</script>\n"
        body = html.replace(APP_TAG, inject + APP_TAG).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, fmt, *args):  # quieter than the default
        if "GET" in (args[0] if args else ""):
            return
        super().log_message(fmt, *args)


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    handler = functools.partial(NoCacheHandler, directory=ROOT)
    with socketserver.TCPServer(("127.0.0.1", PORT), handler) as httpd:
        print(f"Serving {ROOT} at http://127.0.0.1:{PORT}  (no-store)")
        print("  CARTO basemap key: " + ("loaded from .env" if CARTO_KEY else
              "MISSING — tiles will be watermarked"))
        httpd.serve_forever()
