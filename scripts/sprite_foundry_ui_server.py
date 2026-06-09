#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import mimetypes
import os
import re
import shutil
import struct
import subprocess
import time
import zlib
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
POSE_SET_FILENAME = "pose_set.json"


class SpriteFoundryUiServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(self, server_address, handler_class, root: Path):
        super().__init__(server_address, handler_class)
        self.root = root.resolve()
        self.ui_dir = self.root / "ui"
        home = Path.home()
        data_root = Path(os.environ.get("NYMPHS_DATA_ROOT", home / "NymphsData")).expanduser()
        self.output_root = Path(
            os.environ.get("SPRITE_FOUNDRY_OUTPUTS_ROOT", data_root / "outputs" / "nymphs-sprite")
        ).expanduser().resolve()
        self.output_sources = self._output_sources()

    def _output_sources(self) -> list[tuple[str, Path]]:
        sources = [
            ("outputs", self.output_root),
        ]
        resolved: list[tuple[str, Path]] = []
        seen: set[Path] = set()
        for source_id, path in sources:
            try:
                root = path.expanduser().resolve()
            except OSError:
                continue
            if root in seen:
                continue
            seen.add(root)
            resolved.append((source_id, root))
        return resolved


class SpriteFoundryUiHandler(BaseHTTPRequestHandler):
    server: SpriteFoundryUiServer

    def log_message(self, fmt: str, *args) -> None:
        print(f"[nymphs-sprite-ui] {self.address_string()} {fmt % args}", flush=True)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path in {"", "/", "/nymph"}:
            self._send_file(self.server.ui_dir / "manager.html", "text/html; charset=utf-8", no_cache=True)
            return
        if path == "/health":
            self._send_json({"status": "healthy"})
            return
        if path == "/server_info":
            self._send_json(
                {
                    "status": "healthy",
                    "module": "nymphs-sprite",
                    "ui": "nymph",
                    "output_root": str(self.server.output_root),
                    "output_sources": [{"id": source_id, "root": str(root)} for source_id, root in self.server.output_sources],
                }
            )
            return
        if path == "/active_task":
            self._send_json({"status": "idle", "stage": "Idle", "detail": "Waiting for Foundry run.", "progress_percent": 0})
            return
        if path == "/api/status":
            self._send_status_text()
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
            self._send_json({"outputs": self._output_records(limit)})
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
        if path == "/api/outputs/contact-sheet":
            self._save_contact_sheet()
            return
        if path == "/api/pose-lab/refs":
            self._create_openpose_guide(self._json_payload())
            return
        self.send_error(404, "Not found")

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

    def _send_text(self, text: str, status: int = 200) -> None:
        body = text.encode("utf-8", errors="replace")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _send_status_text(self) -> None:
        script = self.server.root / "scripts" / "sprite_foundry_status.sh"
        if not script.is_file():
            self._send_text("detail=Status script was not found.\n", status=404)
            return
        env = os.environ.copy()
        env.setdefault("SPRITE_FOUNDRY_INSTALL_DIR", str(self.server.root))
        try:
            result = subprocess.run(
                [str(script)],
                cwd=str(self.server.root),
                env=env,
                text=True,
                capture_output=True,
                timeout=12,
                check=False,
            )
        except Exception as exc:
            self._send_text(f"detail=Could not run status script: {exc}\n", status=500)
            return
        text = result.stdout or result.stderr or "detail=Status script produced no output.\n"
        self._send_text(text, status=200 if result.returncode == 0 else 500)

    def _metadata_for(self, path: Path) -> dict:
        metadata_path = path.with_suffix(".json")
        if not metadata_path.is_file():
            return {}
        try:
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}

    def _output_record(self, path: Path, rel: str) -> dict:
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
            "url": f"/outputs/{quote(rel, safe='/')}",
            "metadata_path": str(path.with_suffix(".json")) if path.with_suffix(".json").is_file() else "",
            "provider": metadata.get("provider", "nymphs-sprite"),
            "mode": metadata.get("mode", ""),
            "batch_id": metadata.get("batch_id", ""),
            "batch_type": metadata.get("batch_type", ""),
            "batch_label": metadata.get("batch_label", ""),
            "item_label": metadata.get("item_label", ""),
            "item_index": metadata.get("item_index", 0),
            "item_total": metadata.get("item_total", 0),
            "created": metadata.get("created") or metadata.get("created_at") or stat.st_mtime,
            "mtime": stat.st_mtime,
            "size": stat.st_size,
            "mime_type": mimetypes.guess_type(path.name)[0] or "image/png",
            "metadata": metadata,
            "source": "nymphs-sprite",
            "managed": True,
        }

    def _output_records(self, limit: int = 80) -> list[dict]:
        self.server.output_root.mkdir(parents=True, exist_ok=True)
        records = []
        limit = max(1, min(limit, 200))
        for source_id, root in self.server.output_sources:
            if not root.is_dir():
                continue
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                if path.suffix.lower() not in IMAGE_SUFFIXES and path.name != POSE_SET_FILENAME:
                    continue
                try:
                    resolved = path.resolve()
                    rel = resolved.relative_to(root).as_posix()
                except (OSError, ValueError):
                    continue
                record = self._output_record(resolved, rel)
                record["source"] = source_id
                record["url"] = f"/outputs/{source_id}/{quote(rel, safe='/')}"
                record["relative_path"] = rel
                record["folder"] = f"{source_id}/{record['folder']}".rstrip("/")
                record["managed"] = True
                records.append(record)
        records.sort(key=lambda item: float(item.get("mtime") or 0), reverse=True)
        return records[:limit]

    def _source_root(self, source_id: str) -> Path | None:
        return dict(self.server.output_sources).get(source_id)

    def _safe_output_path(self, source_id: str, relative_path: str) -> tuple[Path, Path, str]:
        root = self._source_root(source_id)
        if root is None:
            raise ValueError("Output source was not found.")
        candidate = (root / relative_path).resolve()
        try:
            rel = candidate.relative_to(root).as_posix()
        except ValueError as exc:
            raise ValueError("Output path is invalid.") from exc
        if not candidate.is_file():
            raise ValueError("Output was not found.")
        if candidate.suffix.lower() not in IMAGE_SUFFIXES and candidate.name != POSE_SET_FILENAME:
            raise ValueError("Output is not a managed output.")
        return root, candidate, rel

    def _resolve_output_ref(self, item) -> tuple[str, Path, Path, str]:
        if isinstance(item, dict):
            if str(item.get("managed", "true")).lower() == "false":
                raise ValueError("Manual browser-local outputs are not managed.")
            source_id = str(item.get("source") or "outputs").strip()
            relative_path = str(item.get("relative_path") or "").strip()
            absolute_path = str(item.get("path") or "").strip()
        else:
            source_id = "outputs"
            relative_path = str(item).strip()
            absolute_path = str(item).strip()
        if not relative_path and not absolute_path:
            raise ValueError("Output reference is empty.")
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
                if candidate.is_file() and (candidate.suffix.lower() in IMAGE_SUFFIXES or candidate.name == POSE_SET_FILENAME):
                    return candidate_source_id, root, candidate, rel
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
        for index in range(1, 1000):
            candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
            if not candidate.exists():
                return candidate
        raise ValueError("Could not create a unique output filename.")

    def _remove_empty_parents(self, parent: Path, root: Path) -> None:
        while parent != root and root in parent.parents:
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent

    def _delete_outputs(self) -> None:
        payload = self._json_payload()
        try:
            requested = self._requested_outputs(payload)
        except ValueError as exc:
            self._send_json_error(400, str(exc))
            return
        removed = 0
        metadata_removed = 0
        removed_paths = []
        seen: set[Path] = set()
        for item in requested:
            try:
                source_id, root, path, rel = self._resolve_output_ref(item)
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
            self._remove_empty_parents(path.parent, root)
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
        moved = 0
        metadata_moved = 0
        moved_paths = []
        seen: set[Path] = set()
        for item in requested:
            try:
                source_id, root, path, _ = self._resolve_output_ref(item)
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
            moved_paths.append(f"{source_id}/{target.relative_to(root).as_posix()}")
            if metadata_path.is_file():
                metadata_target = self._output_collision_path(target.with_suffix(".json"))
                try:
                    metadata_path.rename(metadata_target)
                    metadata_moved += 1
                except Exception:
                    pass
            self._remove_empty_parents(path.parent, root)
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
        folder_dir = (self.server.output_root / folder).resolve()
        if folder_dir.parent != self.server.output_root or not folder_dir.is_dir():
            self._send_json({"status": "ok", "folder": folder, "removed": 0, "outputs": self._output_records()})
            return
        removed = len([path for path in folder_dir.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES])
        try:
            shutil.rmtree(folder_dir)
        except Exception:
            pass
        self._send_json({"status": "ok", "folder": folder, "removed": removed, "outputs": self._output_records()})

    def _save_contact_sheet(self) -> None:
        payload = self._json_payload()
        image_data = str(payload.get("image_data") or "")
        if not image_data.startswith("data:image/png;base64,"):
            self._send_json_error(400, "PNG image data is required.")
            return
        try:
            import base64

            data = base64.b64decode(image_data.split(",", 1)[1], validate=True)
        except Exception:
            self._send_json_error(400, "Contact sheet image data is invalid.")
            return
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            self._send_json_error(400, "Contact sheet must be a PNG.")
            return
        subject_id = self._safe_slug(str(payload.get("subject_id") or "selected"), "selected")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        target_dir = (self.server.output_root / "contact_sheets" / subject_id / timestamp).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        target = self._output_collision_path(target_dir / "selected-contact-sheet.png")
        target.write_bytes(data)
        metadata = {
            "provider": "Nymphs Sprite",
            "mode": "selected_contact_sheet",
            "batch_id": f"contact-sheet-{int(time.time())}",
            "batch_label": "Selected Contact Sheet",
            "batch_type": "contact_sheet",
            "item_label": "Selected Contact Sheet",
            "item_index": 1,
            "item_total": 1,
            "subject_id": subject_id,
            "source_count": int(payload.get("source_count") or 0),
            "source_paths": payload.get("source_paths") if isinstance(payload.get("source_paths"), list) else [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        target.with_suffix(".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        rel = target.relative_to(self.server.output_root).as_posix()
        record = self._output_record(target, rel)
        record["source"] = "outputs"
        record["url"] = f"/outputs/outputs/{quote(rel, safe='/')}"
        record["folder"] = f"outputs/{record['folder']}".rstrip("/")
        self._send_json({"status": "ok", "outputs": [record]})

    def _safe_slug(self, value: str, fallback: str = "item") -> str:
        slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip(".-_")
        return (slug or fallback)[:96]

    def _direction_names(self, direction_count: int) -> list[str]:
        if direction_count == 16:
            return [
                "front", "front_front_left", "front_left", "left_front_left",
                "left", "left_back_left", "back_left", "back_back_left",
                "back", "back_back_right", "back_right", "right_back_right",
                "right", "right_front_right", "front_right", "front_front_right",
            ]
        return ["front", "front_left", "left", "back_left", "back", "back_right", "right", "front_right"]

    def _direction_yaw(self, name: str) -> float:
        yaws = {
            "front": 0,
            "front_front_left": -22.5,
            "front_left": -45,
            "left_front_left": -67.5,
            "left": -90,
            "left_back_left": -112.5,
            "back_left": -135,
            "back_back_left": -157.5,
            "back": 180,
            "back_back_right": 157.5,
            "back_right": 135,
            "right_back_right": 112.5,
            "right": 90,
            "right_front_right": 67.5,
            "front_right": 45,
            "front_front_right": 22.5,
        }
        return math.radians(yaws.get(name, 0))

    def _png_chunk(self, chunk_type: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)

    def _write_rgb_png(self, path: Path, width: int, height: int, pixels: bytearray) -> None:
        rows = []
        stride = width * 3
        for y in range(height):
            rows.append(b"\x00" + bytes(pixels[y * stride : (y + 1) * stride]))
        data = b"".join(
            [
                b"\x89PNG\r\n\x1a\n",
                self._png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
                self._png_chunk(b"IDAT", zlib.compress(b"".join(rows), level=9)),
                self._png_chunk(b"IEND", b""),
            ]
        )
        path.write_bytes(data)

    def _draw_disk(self, pixels: bytearray, width: int, height: int, x: float, y: float, radius: float, color: tuple[int, int, int]) -> None:
        r = max(1, int(round(radius)))
        cx = int(round(x))
        cy = int(round(y))
        rr = r * r
        for py in range(max(0, cy - r), min(height, cy + r + 1)):
            for px in range(max(0, cx - r), min(width, cx + r + 1)):
                if (px - cx) * (px - cx) + (py - cy) * (py - cy) <= rr:
                    offset = (py * width + px) * 3
                    pixels[offset : offset + 3] = bytes(color)

    def _draw_line(self, pixels: bytearray, width: int, height: int, a: tuple[float, float], b: tuple[float, float], color: tuple[int, int, int], thickness: float) -> None:
        x0, y0 = a
        x1, y1 = b
        steps = max(1, int(max(abs(x1 - x0), abs(y1 - y0))))
        for step in range(steps + 1):
            t = step / steps
            self._draw_disk(pixels, width, height, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, thickness / 2, color)

    def _draw_openpose_rig(self, pixels: bytearray, width: int, height: int, box: tuple[float, float, float, float], yaw: float) -> None:
        x, y, w, h = box
        cx = x + w * 0.5
        cy = y + h * 0.52
        scale = min(w, h) * 0.82
        side = abs(math.sin(yaw))
        facing = math.sin(yaw)
        shoulder = (0.18 - 0.105 * side) * scale
        hip = (0.105 - 0.055 * side) * scale
        depth = facing * 0.045 * scale
        head = (cx + facing * 0.035 * scale, cy - 0.39 * scale)
        neck = (cx + depth * 0.35, cy - 0.29 * scale)
        pelvis = (cx - depth * 0.2, cy + 0.08 * scale)
        mid = (cx, cy - 0.10 * scale)
        left_shoulder = (neck[0] - shoulder, neck[1] + 0.01 * scale)
        right_shoulder = (neck[0] + shoulder, neck[1] - 0.01 * scale)
        left_hip = (pelvis[0] - hip, pelvis[1])
        right_hip = (pelvis[0] + hip, pelvis[1])
        arm_drop = 0.25 * scale
        leg_drop = 0.30 * scale
        left_elbow = (left_shoulder[0] - (0.08 + 0.04 * side) * scale, left_shoulder[1] + arm_drop)
        right_elbow = (right_shoulder[0] + (0.08 + 0.04 * side) * scale, right_shoulder[1] + arm_drop)
        left_wrist = (left_elbow[0] - (0.05 + 0.03 * side) * scale, left_elbow[1] + 0.24 * scale)
        right_wrist = (right_elbow[0] + (0.05 + 0.03 * side) * scale, right_elbow[1] + 0.24 * scale)
        left_knee = (left_hip[0] - (0.03 + 0.04 * side) * scale, left_hip[1] + leg_drop)
        right_knee = (right_hip[0] + (0.03 + 0.04 * side) * scale, right_hip[1] + leg_drop)
        left_ankle = (left_knee[0] - 0.035 * scale, left_knee[1] + 0.29 * scale)
        right_ankle = (right_knee[0] + 0.035 * scale, right_knee[1] + 0.29 * scale)
        # Side views should read as one compressed rig, but keep tiny offsets so limbs are visible.
        if side > 0.82:
            compress = facing * 0.035 * scale
            left_shoulder = (neck[0] - compress, left_shoulder[1])
            right_shoulder = (neck[0] + compress, right_shoulder[1])
            left_hip = (pelvis[0] - compress * 0.7, left_hip[1])
            right_hip = (pelvis[0] + compress * 0.7, right_hip[1])
        colors = {
            "head": (255, 0, 190),
            "torso": (0, 210, 230),
            "left_arm": (255, 156, 0),
            "right_arm": (0, 220, 65),
            "left_leg": (0, 190, 125),
            "right_leg": (0, 80, 230),
            "dot": (245, 255, 0),
            "joint": (255, 0, 210),
        }
        segments = [
            (head, neck, colors["head"]),
            (neck, mid, colors["torso"]),
            (mid, pelvis, colors["torso"]),
            (neck, left_shoulder, colors["left_arm"]),
            (left_shoulder, left_elbow, colors["left_arm"]),
            (left_elbow, left_wrist, colors["left_arm"]),
            (neck, right_shoulder, colors["right_arm"]),
            (right_shoulder, right_elbow, colors["right_arm"]),
            (right_elbow, right_wrist, colors["right_arm"]),
            (pelvis, left_hip, colors["left_leg"]),
            (left_hip, left_knee, colors["left_leg"]),
            (left_knee, left_ankle, colors["left_leg"]),
            (pelvis, right_hip, colors["right_leg"]),
            (right_hip, right_knee, colors["right_leg"]),
            (right_knee, right_ankle, colors["right_leg"]),
        ]
        thickness = max(3, scale * 0.014)
        for a, b, color in segments:
            self._draw_line(pixels, width, height, a, b, color, thickness)
        joints = [head, neck, mid, pelvis, left_shoulder, right_shoulder, left_elbow, right_elbow, left_wrist, right_wrist, left_hip, right_hip, left_knee, right_knee, left_ankle, right_ankle]
        for index, point in enumerate(joints):
            color = colors["joint"] if index % 3 == 0 else colors["dot"]
            self._draw_disk(pixels, width, height, point[0], point[1], max(3, scale * 0.022), color)

    def _draw_openpose_pose(
        self,
        pixels: bytearray,
        width: int,
        height: int,
        box: tuple[float, float, float, float],
        joints: dict,
        canvas_size: float,
    ) -> bool:
        if not isinstance(joints, dict):
            return False
        canvas_size = canvas_size if canvas_size > 0 else 256
        names = [
            "head", "neck", "spine", "pelvis",
            "left_shoulder", "left_elbow", "left_wrist",
            "right_shoulder", "right_elbow", "right_wrist",
            "left_hip", "left_knee", "left_ankle",
            "right_hip", "right_knee", "right_ankle",
        ]
        x, y, w, h = box
        margin = min(w, h) * 0.06
        usable_w = max(1.0, w - margin * 2)
        usable_h = max(1.0, h - margin * 2)
        points: dict[str, tuple[float, float]] = {}
        for name in names:
            raw = joints.get(name)
            if not isinstance(raw, list | tuple) or len(raw) < 2:
                continue
            try:
                px = max(0.0, min(canvas_size, float(raw[0])))
                py = max(0.0, min(canvas_size, float(raw[1])))
            except (TypeError, ValueError):
                continue
            points[name] = (x + margin + px / canvas_size * usable_w, y + margin + py / canvas_size * usable_h)
        if len(points) < 8:
            return False
        colors = {
            "head": (255, 0, 190),
            "torso": (0, 210, 230),
            "left_arm": (255, 156, 0),
            "right_arm": (0, 220, 65),
            "left_leg": (0, 190, 125),
            "right_leg": (0, 80, 230),
            "dot": (245, 255, 0),
            "joint": (255, 0, 210),
        }
        segments = [
            ("head", "neck", colors["head"]),
            ("neck", "spine", colors["torso"]),
            ("spine", "pelvis", colors["torso"]),
            ("neck", "left_shoulder", colors["left_arm"]),
            ("left_shoulder", "left_elbow", colors["left_arm"]),
            ("left_elbow", "left_wrist", colors["left_arm"]),
            ("neck", "right_shoulder", colors["right_arm"]),
            ("right_shoulder", "right_elbow", colors["right_arm"]),
            ("right_elbow", "right_wrist", colors["right_arm"]),
            ("pelvis", "left_hip", colors["left_leg"]),
            ("left_hip", "left_knee", colors["left_leg"]),
            ("left_knee", "left_ankle", colors["left_leg"]),
            ("pelvis", "right_hip", colors["right_leg"]),
            ("right_hip", "right_knee", colors["right_leg"]),
            ("right_knee", "right_ankle", colors["right_leg"]),
        ]
        scale = min(w, h) * 0.82
        thickness = max(3, scale * 0.014)
        for a, b, color in segments:
            if a in points and b in points:
                self._draw_line(pixels, width, height, points[a], points[b], color, thickness)
        for index, name in enumerate(names):
            point = points.get(name)
            if not point:
                continue
            color = colors["joint"] if index % 3 == 0 else colors["dot"]
            self._draw_disk(pixels, width, height, point[0], point[1], max(3, scale * 0.022), color)
        return True

    def _create_openpose_guide(self, payload: dict) -> None:
        subject_id = self._safe_slug(str(payload.get("subject_id") or "guide_candidate"), "guide_candidate")
        body_type = self._safe_slug(str(payload.get("body_type") or "humanoid"), "humanoid")
        direction_count = 16 if str(payload.get("direction_count") or "8") == "16" else 8
        width = height = 512
        directions = self._direction_names(direction_count)
        pose_data = payload.get("pose_data") if isinstance(payload.get("pose_data"), dict) else {}
        pose_directions = pose_data.get("directions") if isinstance(pose_data.get("directions"), dict) else {}
        selected_directions = pose_data.get("selected_directions") if isinstance(pose_data.get("selected_directions"), list) else directions
        selected_directions = [name for name in selected_directions if name in directions]
        if not selected_directions:
            selected_directions = directions
        try:
            pose_canvas_size = float(pose_data.get("canvas_size") or 256)
        except (TypeError, ValueError):
            pose_canvas_size = 256

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        target_dir = (self.server.output_root / "pose_lab" / "refs" / subject_id / timestamp).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        batch_id = f"pose-lab-local-{int(time.time())}"
        created_at = datetime.now(timezone.utc).isoformat()
        pose_set_manifest = {
            "provider": "Nymphs Sprite",
            "mode": "pose_lab_set",
            "batch_id": batch_id,
            "batch_label": "Pose Lab Ref Set",
            "batch_type": "sprite_direction_ref_set",
            "item_label": f"{subject_id} Pose Set",
            "subject_id": subject_id,
            "body_type": body_type,
            "control_type": "pose_skeleton",
            "direction_count": direction_count,
            "selected_directions": selected_directions,
            "directions": directions,
            "pose_data": pose_data,
            "guide_strength": str(payload.get("guide_strength") or "normal"),
            "sprite_prompt_context": str(payload.get("subject_prompt") or ""),
            "created_at": created_at,
            "render_policy": "render_png_refs_on_demand",
            "assets": [],
        }
        target = target_dir / POSE_SET_FILENAME
        target.write_text(json.dumps(pose_set_manifest, indent=2), encoding="utf-8")
        rel = target.relative_to(self.server.output_root).as_posix()
        record = self._output_record(target, rel)
        record["source"] = "outputs"
        record["url"] = f"/outputs/outputs/{quote(rel, safe='/')}"
        record["folder"] = f"outputs/{record['folder']}".rstrip("/")
        self._send_json({"status": "ok", "prompt": "Saved editable Pose Lab JSON set.", "outputs": [record]})

    def _send_output_file(self, relative: str) -> None:
        try:
            source_id, _, rel = unquote(relative).partition("/")
            if not source_id or not rel:
                raise ValueError("Output source is missing.")
            _, path, _ = self._safe_output_path(source_id, rel)
        except ValueError:
            self.send_error(404, "Not found")
            return
        self._send_file(path, mimetypes.guess_type(str(path))[0] or "application/octet-stream")

    def _send_static(self, root: Path, relative: str) -> None:
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            self.send_error(404, "Not found")
            return
        self._send_file(candidate, mimetypes.guess_type(str(candidate))[0] or "application/octet-stream")

    def _send_file(self, path: Path, content_type: str, *, no_cache: bool = False) -> None:
        if not path.is_file():
            self.send_error(404, "Not found")
            return
        body = path.read_bytes()
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
    server = SpriteFoundryUiServer((args.host, args.port), SpriteFoundryUiHandler, root)
    print(f"[nymphs-sprite-ui] serving {root} at http://{args.host}:{args.port}/nymph", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
