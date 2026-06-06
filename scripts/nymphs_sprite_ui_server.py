#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import shutil
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

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path == "/api/outputs/delete":
            self._delete_outputs()
            return

        if path == "/api/outputs/move":
            self._move_outputs()
            return

        if path == "/api/outputs/folder/delete":
            self._delete_output_folder()
            return

        self.send_error(404, "Not found")

    def _send_outputs(self, limit: int) -> None:
        self._send_json({"outputs": self._output_records(limit)})

    def _metadata_for(self, path: Path) -> dict:
        metadata_path = path.with_suffix(".json")
        if not metadata_path.is_file():
            return {}
        try:
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}

    def _json_payload(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _send_json_error(self, status: int, detail: str) -> None:
        self._send_json({"detail": detail}, status=status)

    def _output_records(self, limit: int = 80) -> list[dict]:
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
                records.append(self._output_record(source_id, root, resolved, rel))

        records.sort(key=lambda item: float(item.get("mtime") or 0), reverse=True)
        return records[:limit]

    def _output_record(self, source_id: str, root: Path, path: Path, rel: str) -> dict:
        stat = path.stat()
        metadata = self._metadata_for(path)
        folder = Path(rel).parent.as_posix()
        if folder == ".":
            folder = ""
        return {
            "name": metadata.get("item_label") or metadata.get("batch_label") or path.name,
            "path": str(path),
            "relative_path": rel,
            "folder": folder,
            "url": f"/outputs/{source_id}/{self._quote_path(rel)}",
            "metadata_path": str(path.with_suffix(".json")) if path.with_suffix(".json").is_file() else "",
            "batch_id": metadata.get("batch_id", ""),
            "batch_type": metadata.get("batch_type", ""),
            "batch_label": metadata.get("batch_label", ""),
            "item_label": metadata.get("item_label", ""),
            "item_index": metadata.get("item_index", 0),
            "created": metadata.get("created") or metadata.get("created_at") or stat.st_mtime,
            "mtime": stat.st_mtime,
            "size": stat.st_size,
            "mime_type": mimetypes.guess_type(path.name)[0] or "image/png",
            "metadata": metadata,
            "source": source_id,
        }

    def _source_root(self, source_id: str) -> Path | None:
        return dict(self.server.output_sources).get(source_id)

    def _safe_output_path(self, source_id: str, relative_path: str) -> tuple[Path, Path, str]:
        root = self._source_root(source_id)
        if not root:
            raise ValueError("Output source was not found.")
        candidate = (root / relative_path).resolve()
        try:
            rel = candidate.relative_to(root).as_posix()
        except ValueError as exc:
            raise ValueError("Output path is invalid.") from exc
        if not candidate.is_file():
            raise ValueError("Output was not found.")
        if candidate.suffix.lower() not in IMAGE_SUFFIXES:
            raise ValueError("Output is not an image.")
        return root, candidate, rel

    def _resolve_output_ref(self, item) -> tuple[str, Path, Path, str]:
        if isinstance(item, str):
            source_id = ""
            relative_path = item.strip()
            absolute_path = item.strip()
        elif isinstance(item, dict):
            source_id = str(item.get("source") or "").strip()
            relative_path = str(item.get("relative_path") or item.get("path") or "").strip()
            absolute_path = str(item.get("path") or "").strip()
        else:
            raise ValueError("Output reference is invalid.")

        if source_id and relative_path:
            root, path, rel = self._safe_output_path(source_id, relative_path)
            return source_id, root, path, rel

        if absolute_path:
            try:
                candidate = Path(absolute_path).expanduser().resolve()
            except OSError as exc:
                raise ValueError("Output path is invalid.") from exc
            for candidate_source_id, root in self.server.output_sources:
                try:
                    rel = candidate.relative_to(root).as_posix()
                except ValueError:
                    continue
                if candidate.is_file() and candidate.suffix.lower() in IMAGE_SUFFIXES:
                    return candidate_source_id, root, candidate, rel

        if relative_path:
            for candidate_source_id, root in self.server.output_sources:
                try:
                    resolved = (root / relative_path).resolve()
                    rel = resolved.relative_to(root).as_posix()
                except (OSError, ValueError):
                    continue
                if resolved.is_file() and resolved.suffix.lower() in IMAGE_SUFFIXES:
                    return candidate_source_id, root, resolved, rel

        raise ValueError("Output was not found.")

    def _requested_outputs(self, payload: dict) -> list:
        requested = payload.get("items")
        if requested is None:
            requested = payload.get("paths") or payload.get("relative_paths") or []
        if not isinstance(requested, list):
            raise ValueError("paths must be a list.")
        requested = [item for item in requested if str(item).strip()]
        if len(requested) > 200:
            raise ValueError("Too many outputs selected.")
        return requested

    def _remove_empty_parents(self, root: Path, parent: Path) -> None:
        while parent != root and root in parent.parents:
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent

    def _safe_output_folder_name(self, value: str) -> str:
        folder = re.sub(r"[^A-Za-z0-9._ -]+", "-", value.strip()).strip(" .-_")
        folder = re.sub(r"\s+", " ", folder)[:80].strip()
        if not folder:
            raise ValueError("Folder name is required.")
        if folder in {".", ".."}:
            raise ValueError("Invalid folder name.")
        return folder

    def _output_collision_path(self, path: Path) -> Path:
        if not path.exists():
            return path
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        for index in range(1, 1000):
            candidate = parent / f"{stem}-{index}{suffix}"
            if not candidate.exists():
                return candidate
        raise ValueError("Could not create a unique output filename.")

    def _delete_outputs(self) -> None:
        payload = self._json_payload()
        try:
            requested = self._requested_outputs(payload)
        except ValueError as exc:
            self._send_json_error(400, str(exc))
            return
        if not requested:
            self._send_json({"status": "ok", "removed": 0, "metadata_removed": 0, "outputs": self._output_records()})
            return

        removed = 0
        metadata_removed = 0
        removed_paths: list[str] = []
        seen: set[Path] = set()
        for item in requested:
            try:
                _, root, path, rel = self._resolve_output_ref(item)
            except ValueError:
                continue
            if path in seen:
                continue
            seen.add(path)
            metadata_path = path.with_suffix(".json")
            try:
                path.unlink()
            except Exception:
                continue
            removed += 1
            removed_paths.append(rel)
            if metadata_path.is_file():
                try:
                    metadata_path.unlink()
                    metadata_removed += 1
                except Exception:
                    pass
            self._remove_empty_parents(root, path.parent)

        self._send_json(
            {
                "status": "ok",
                "removed": removed,
                "metadata_removed": metadata_removed,
                "removed_paths": removed_paths,
                "outputs": self._output_records(),
            }
        )

    def _move_outputs(self) -> None:
        payload = self._json_payload()
        try:
            requested = self._requested_outputs(payload)
            folder = self._safe_output_folder_name(str(payload.get("folder") or payload.get("folder_name") or ""))
        except ValueError as exc:
            self._send_json_error(400, str(exc))
            return
        if not requested:
            self._send_json({"status": "ok", "folder": folder, "moved": 0, "metadata_moved": 0, "outputs": self._output_records()})
            return

        moved = 0
        metadata_moved = 0
        moved_paths: list[str] = []
        seen: set[Path] = set()
        for item in requested:
            try:
                _, root, path, _ = self._resolve_output_ref(item)
            except ValueError:
                continue
            if path in seen:
                continue
            seen.add(path)
            destination_dir = (root / folder).resolve()
            try:
                destination_dir.relative_to(root)
            except ValueError:
                continue
            destination_dir.mkdir(parents=True, exist_ok=True)
            target = self._output_collision_path(destination_dir / path.name)
            metadata_path = path.with_suffix(".json")
            try:
                path.rename(target)
            except Exception:
                continue
            moved += 1
            try:
                moved_paths.append(target.relative_to(root).as_posix())
            except ValueError:
                moved_paths.append(target.name)
            if metadata_path.is_file():
                metadata_target = self._output_collision_path(target.with_suffix(".json"))
                try:
                    metadata_path.rename(metadata_target)
                    metadata_moved += 1
                except Exception:
                    pass
            self._remove_empty_parents(root, path.parent)

        self._send_json(
            {
                "status": "ok",
                "folder": folder,
                "moved": moved,
                "metadata_moved": metadata_moved,
                "moved_paths": moved_paths,
                "outputs": self._output_records(),
            }
        )

    def _delete_output_folder(self) -> None:
        payload = self._json_payload()
        raw_folder = str(payload.get("folder") or payload.get("folder_name") or "").strip()
        if not raw_folder:
            self._send_json_error(400, "Folder name is required.")
            return
        if "/" in raw_folder or "\\" in raw_folder:
            self._send_json_error(400, "Only top-level managed output folders can be deleted.")
            return
        try:
            folder = self._safe_output_folder_name(raw_folder)
        except ValueError as exc:
            self._send_json_error(400, str(exc))
            return
        if folder != raw_folder:
            self._send_json_error(400, "Only top-level managed output folders can be deleted.")
            return

        removed = 0
        for _, root in self.server.output_sources:
            folder_dir = (root / folder).resolve()
            if folder_dir.parent != root or not folder_dir.is_dir():
                continue
            removed += len([path for path in folder_dir.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES])
            try:
                shutil.rmtree(folder_dir)
            except Exception:
                pass

        self._send_json({"status": "ok", "folder": folder, "removed": removed, "outputs": self._output_records()})

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
