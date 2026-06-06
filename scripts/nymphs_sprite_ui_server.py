#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


class SpriteUiServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(self, server_address, handler_class, root: Path):
        super().__init__(server_address, handler_class)
        self.root = root.resolve()
        self.ui_dir = self.root / "ui"
        self.output_sources = self._output_sources()

    def _output_sources(self) -> list[tuple[str, Path]]:
        home = Path.home()
        data_root = Path(os.environ.get("NYMPHS_DATA_ROOT", home / "NymphsData")).expanduser()
        sources = [
            ("sprite", Path(os.environ.get("NYMPHS_SPRITE_OUTPUTS_ROOT", data_root / "outputs" / "nymphs-sprite"))),
            ("zimage", data_root / "outputs" / "zimage"),
            ("zimage-legacy", home / "Z-Image" / "outputs"),
            ("zimage-dev", home / "NymphsModules" / "zimage" / "outputs"),
            ("module", self.root / "outputs"),
        ]
        resolved: list[tuple[str, Path]] = []
        seen: set[Path] = set()
        for source_id, root in sources:
            try:
                path = root.expanduser().resolve()
            except OSError:
                continue
            if path not in seen:
                seen.add(path)
                resolved.append((source_id, path))
        return resolved


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

        if path == "/api/outputs":
            query = parse_qs(parsed.query)
            try:
                limit = int((query.get("limit") or ["80"])[0])
            except ValueError:
                limit = 80
            self._send_outputs(limit)
            return

        if path.startswith("/outputs/"):
            self._send_output_file(path.removeprefix("/outputs/"))
            return

        self.send_error(404, "Not found")

    def _send_outputs(self, limit: int) -> None:
        records: list[dict] = []
        seen: set[Path] = set()
        limit = max(1, min(limit, 200))
        for source_id, root in self.server.output_sources:
            if not root.is_dir():
                continue
            for path in root.rglob("*"):
                if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
                    continue
                try:
                    resolved = path.resolve()
                    rel = resolved.relative_to(root).as_posix()
                except OSError:
                    continue
                if resolved in seen:
                    continue
                seen.add(resolved)
                stat = resolved.stat()
                metadata = self._metadata_for(resolved)
                folder = Path(rel).parent.as_posix()
                if folder == ".":
                    folder = ""
                records.append(
                    {
                        "name": metadata.get("item_label") or metadata.get("batch_label") or resolved.name,
                        "path": str(resolved),
                        "relative_path": rel,
                        "folder": folder,
                        "url": f"/outputs/{source_id}/{self._quote_path(rel)}",
                        "metadata_path": str(resolved.with_suffix(".json")) if resolved.with_suffix(".json").is_file() else "",
                        "batch_id": metadata.get("batch_id", ""),
                        "batch_type": metadata.get("batch_type", ""),
                        "batch_label": metadata.get("batch_label", ""),
                        "item_label": metadata.get("item_label", ""),
                        "item_index": metadata.get("item_index", 0),
                        "created": metadata.get("created") or metadata.get("created_at") or stat.st_mtime,
                        "mtime": stat.st_mtime,
                        "size": stat.st_size,
                        "mime_type": mimetypes.guess_type(resolved.name)[0] or "image/png",
                        "metadata": metadata,
                        "source": source_id,
                    }
                )

        records.sort(key=lambda item: float(item.get("mtime") or 0), reverse=True)
        self._send_bytes(json.dumps({"outputs": records[:limit]}, separators=(",", ":")).encode("utf-8"), "application/json")

    def _metadata_for(self, path: Path) -> dict:
        metadata_path = path.with_suffix(".json")
        if not metadata_path.is_file():
            return {}
        try:
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}

    def _send_output_file(self, route: str) -> None:
        if not route:
            self.send_error(400, "Missing output path")
            return

        source_id, _, relative = route.partition("/")
        if not source_id or not relative:
            self.send_error(404, "Not found")
            return

        root = dict(self.server.output_sources).get(source_id)
        if not root:
            self.send_error(404, "Not found")
            return

        candidate = (root / unquote(relative)).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            self.send_error(404, "Not found")
            return

        content_type = mimetypes.guess_type(str(candidate))[0] or "application/octet-stream"
        self._send_file(candidate, content_type)

    def _quote_path(self, value: str) -> str:
        from urllib.parse import quote

        return quote(value, safe="/")

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
