#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


class SpriteUiServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(self, server_address, handler_class, root: Path):
        super().__init__(server_address, handler_class)
        self.root = root.resolve()
        self.ui_dir = self.root / "ui"


class SpriteUiHandler(BaseHTTPRequestHandler):
    server: SpriteUiServer

    def log_message(self, fmt: str, *args) -> None:
        print(f"[nymphs-sprite-ui] {self.address_string()} {fmt % args}", flush=True)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path in {"", "/", "/nymph"}:
            self._send_file(self.server.ui_dir / "manager.html", "text/html; charset=utf-8", no_cache=True)
            return

        if path == "/health":
            self._send_bytes(b'{"status":"healthy"}', "application/json")
            return

        if path == "/server_info":
            payload = {
                "status": "healthy",
                "module": "nymphs-sprite",
                "ui": "nymph",
            }
            self._send_bytes(json.dumps(payload).encode("utf-8"), "application/json")
            return

        if path.startswith("/ui/"):
            self._send_static(self.server.ui_dir, path.removeprefix("/ui/"))
            return

        self.send_error(404, "Not found")

    def _send_static(self, root: Path, relative: str) -> None:
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            self.send_error(404, "Not found")
            return

        content_type = mimetypes.guess_type(str(candidate))[0] or "application/octet-stream"
        self._send_file(candidate, content_type)

    def _send_file(self, path: Path, content_type: str, *, no_cache: bool = False) -> None:
        if not path.is_file():
            self.send_error(404, "Not found")
            return

        self._send_bytes(path.read_bytes(), content_type, no_cache=no_cache)

    def _send_bytes(self, body: bytes, content_type: str, *, no_cache: bool = False) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if no_cache:
            self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the Nymphs Sprite Manager UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8098)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    manager_html = root / "ui" / "manager.html"
    if not manager_html.is_file():
        raise SystemExit(f"missing UI entrypoint: {manager_html}")

    server = SpriteUiServer((args.host, args.port), SpriteUiHandler, root)
    print(f"[nymphs-sprite-ui] serving {root} at http://{args.host}:{args.port}/nymph", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
