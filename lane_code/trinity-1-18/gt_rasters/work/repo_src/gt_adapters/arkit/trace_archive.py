"""Durable, redacted capture of teacher-model trajectories.

The archive records provider-visible data.  It does not infer or claim access to
private reasoning that a provider did not expose in a native response.
"""
from __future__ import annotations

import contextlib
import base64
import binascii
import hashlib
import json
import mimetypes
import os
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Iterator
_BEARER = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]+=*", re.I)
_EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "application/pdf": ".pdf"}
_PATH_IN_TEXT = re.compile(r"(?<![A-Za-z0-9._/-])(/[^\s'\"<>]+)")
_DATA_ROOT = Path("/data2/jjyeung/agent_project_data/vsi_distill_training_20260917")
def _fsync_dir(path: Path) -> None:
    """Make a newly created directory entry durable where the filesystem supports it."""
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
def _secret_key(key: Any) -> bool:
    """Redact credential fields without mistaking native token counts for secrets."""
    normalized = str(key).lower().replace("-", "_")
    if normalized in {"api_key", "apikey", "access_token", "token", "auth", "authorization",
                      "password", "secret", "credential"}:
        return True
    return normalized.endswith(("_api_key", "_access_token", "_auth_token", "_authorization",
                                "_password", "_secret", "_credential"))
class Archive:
    """One append-only archive for one collector attempt.

    ``root`` must be a fresh, attempt-specific directory. ``assets_root`` is
    the shared immutable blob store, and ``trusted_roots`` bounds file assets.
    """

    def __init__(self, root: Path, identity: dict[str, Any], *, assets_root: Path | None = None,
                 trusted_roots: tuple[Path, ...] = ()):
        self.root = Path(root)
        self._lock = threading.Lock()
        self._event_id = 0
        self.trusted_roots = tuple(Path(p).resolve() for p in trusted_roots) or (_DATA_ROOT.resolve(),)
        self.assets_root = Path(assets_root or os.environ.get(
            "R1308_ARCHIVE_BLOBS_ROOT", _DATA_ROOT / "archive_blobs")).resolve()
        self.root.mkdir(parents=True, exist_ok=False)
        self.events_dir = self.root / "events"
        self.assets_dir = self.assets_root
        self.staging_dir = self.assets_root / ".staging"
        self.retired_staging_dir = self.assets_root / ".retired_staging"
        self.events_dir.mkdir()
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.staging_dir.mkdir(exist_ok=True)
        self.retired_staging_dir.mkdir(exist_ok=True)
        self.journal_path = self.root / "journal.jsonl"
        self.artifact_refs_path = self.root / "artifact_refs.jsonl"
        with self.artifact_refs_path.open("xb") as handle:
            handle.flush()
            os.fsync(handle.fileno())
        self._write_new(self.root / "identity.json", self._snapshot(identity))
        with self.journal_path.open("xb") as handle:
            handle.flush()
            os.fsync(handle.fileno())
        _fsync_dir(self.root)
    @staticmethod
    def _write_new(path: Path, value: Any) -> None:
        data = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        with path.open("xb") as handle:
            handle.write(data)
            handle.write(b"\n")
            handle.flush()
            os.fsync(handle.fileno())
    @staticmethod
    def _redact_string(value: str) -> str:
        return _BEARER.sub("Bearer [REDACTED]", value)

    def _trusted(self, path: Path) -> Path:
        try:
            resolved = path.resolve(strict=True)
        except FileNotFoundError as error:
            raise ValueError(f"asset path does not exist: {path}") from error
        if not resolved.is_file() or not any(resolved.is_relative_to(root) for root in self.trusted_roots):
            raise ValueError(f"asset path is outside trusted roots: {path}")
        return resolved
    def _referenced_path(self, value: str) -> None:
        """Archive permitted paths mentioned inside text without changing that text."""
        for match in _PATH_IN_TEXT.finditer(value):
            try:
                path = self._trusted(Path(match.group(1).rstrip(".,;:)]}")))
            except ValueError:
                continue
            self.asset(path)
    @staticmethod
    def _base64_bytes(value: str) -> tuple[bytes, bool, bool]:
        padded = value + "=" * (-len(value) % 4)
        try:
            return base64.b64decode(padded, validate=True), False, value.endswith("=")
        except binascii.Error:
            return base64.urlsafe_b64decode(padded), True, value.endswith("=")

    def _inline_snapshot(self, value: dict[str, Any]) -> dict[str, Any] | None:
        data = value.get("data")
        if not isinstance(data, str):
            return None
        try:
            payload, urlsafe, padded = self._base64_bytes(data)
        except (ValueError, binascii.Error):
            return None
        mime = value.get("mime_type") or value.get("mimeType") or "application/octet-stream"
        if not isinstance(mime, str):
            mime = "application/octet-stream"
        result = {str(key): self._snapshot(item) for key, item in value.items() if key != "data"}
        result["data"] = {"archive_asset": self.asset(payload, mime), "encoding": "base64",
                          "urlsafe": urlsafe, "padded": padded}
        return result

    @staticmethod
    def _stage_blob(path: Path, payload: bytes) -> None:
        with path.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())

    @staticmethod
    def _verify_blob(path: Path, digest: str) -> None:
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"existing immutable asset is corrupt: {path}")

    def _snapshot(self, value: Any) -> Any:
        """Convert provider objects to a JSON snapshot before their owners can mutate them."""
        if value is None or isinstance(value, (bool, int, float)):
            return value
        if isinstance(value, str):
            self._referenced_path(value)
            return self._redact_string(value)
        if isinstance(value, Path):
            return self.asset(value)
        if isinstance(value, bytes):
            return {"archive_asset": self.asset(value), "encoding": "bytes"}
        if hasattr(value, "model_dump"):
            return self._snapshot(value.model_dump(mode="json", exclude_none=False))
        if hasattr(value, "tolist") and type(value).__module__.startswith("numpy"):
            return self._snapshot(value.tolist())
        if hasattr(value, "item") and type(value).__module__.startswith("numpy"):
            return self._snapshot(value.item())
        if isinstance(value, dict):
            if "inline_data" in value and isinstance(value["inline_data"], dict):
                inline = self._inline_snapshot(value["inline_data"])
                if inline is not None:
                    return {str(key): inline if key == "inline_data" else self._snapshot(item)
                            for key, item in value.items()}
            if "inlineData" in value and isinstance(value["inlineData"], dict):
                inline = self._inline_snapshot(value["inlineData"])
                if inline is not None:
                    return {str(key): inline if key == "inlineData" else self._snapshot(item)
                            for key, item in value.items()}
            return {str(key): "[REDACTED]" if _secret_key(key) else self._snapshot(item)
                    for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._snapshot(item) for item in value]
        if hasattr(value, "__dict__"):
            return self._snapshot(vars(value))
        return repr(value)

    def asset(self, source: Path | str | bytes, mime: str | None = None) -> dict[str, Any]:
        """Store a content-addressed asset without overwriting an existing artifact."""
        source_path = None
        if isinstance(source, (Path, str)):
            path = self._trusted(Path(source))
            payload = path.read_bytes()
            mime = mime or mimetypes.guess_type(path.name)[0]
            source_path = str(path)
        elif not isinstance(source, bytes):
            raise TypeError("asset source must be a Path or bytes")
        else:
            payload = source
        mime = mime or "application/octet-stream"
        digest = hashlib.sha256(payload).hexdigest()
        suffix = _EXTENSIONS.get(mime, "")
        target = self.assets_dir / f"{digest}{suffix}"
        if target.exists():
            self._verify_blob(target, digest)
        else:
            stage = self.staging_dir / f"{digest}.{uuid.uuid4().hex}.part"
            retired = self.retired_staging_dir / f"{stage.name}.retained"
            try:
                self._stage_blob(stage, payload)
                try:
                    os.link(stage, target)
                    _fsync_dir(self.assets_dir)
                except FileExistsError:
                    self._verify_blob(target, digest)
            finally:
                if stage.exists():
                    os.rename(stage, retired)
                    _fsync_dir(self.retired_staging_dir)
        ref = {"path": str(target), "sha256": digest, "bytes": len(payload), "mime": mime}
        ledger_row = dict(ref, source_path=source_path)
        line = json.dumps(ledger_row, sort_keys=True, separators=(",", ":")) + "\n"
        with self._lock:
            with self.artifact_refs_path.open("ab") as handle:
                handle.write(line.encode("utf-8"))
                handle.flush()
                os.fsync(handle.fileno())
        return ref

    def event(self, kind: str, payload: Any) -> dict[str, Any]:
        """Persist one event and its journal receipt before returning it."""
        if not kind or "/" in kind or "\\" in kind:
            raise ValueError("event kind must be a simple nonempty label")
        snapshot = self._snapshot(payload)
        with self._lock:
            self._event_id += 1
            receipt = {"id": self._event_id, "kind": kind, "time_ns": time.time_ns(), "payload": snapshot}
            event_path = self.events_dir / f"{self._event_id:08d}_{kind}.json"
            self._write_new(event_path, receipt)
            line = json.dumps({"id": receipt["id"], "kind": kind, "path": str(event_path.relative_to(self.root))},
                              sort_keys=True, separators=(",", ":")) + "\n"
            with self.journal_path.open("ab") as handle:
                handle.write(line.encode("utf-8"))
                handle.flush()
                os.fsync(handle.fileno())
        return {"id": receipt["id"], "kind": kind, "path": str(event_path.relative_to(self.root))}


class JournalList(list):
    """A normal list whose additions are immediately recorded by an Archive."""

    def __init__(self, archive: Archive, kind: str, values: Any = ()):
        super().__init__()
        self.archive, self.kind = archive, kind
        self.extend(values)

    def append(self, value: Any) -> None:
        self.archive.event(self.kind, value)
        super().append(value)

    def extend(self, values: Any) -> None:
        for value in values:
            self.append(value)


def journal_events(archive: Archive, kind: str) -> JournalList:
    return JournalList(archive, kind)


def restore_snapshot(value: Any) -> Any:
    """Rehydrate archived inline-data markers into their provider-visible base64 form."""
    if isinstance(value, list):
        return [restore_snapshot(item) for item in value]
    if not isinstance(value, dict):
        return value
    restored = {key: restore_snapshot(item) for key, item in value.items()}
    if restored.get("encoding") == "bytes":
        return _blob_bytes(restored.get("archive_asset"))
    marker = restored.get("data")
    if not isinstance(marker, dict) or marker.get("encoding") != "base64":
        return restored
    payload = _blob_bytes(marker.get("archive_asset"))
    encoder = base64.urlsafe_b64encode if marker.get("urlsafe") else base64.b64encode
    encoded = encoder(payload).decode("ascii")
    restored["data"] = encoded if marker.get("padded") else encoded.rstrip("=")
    return restored


def _blob_bytes(ref: Any) -> bytes:
    if not isinstance(ref, dict) or not isinstance(ref.get("path"), str) or not isinstance(ref.get("sha256"), str):
        raise ValueError("archive blob marker is malformed")
    payload = Path(ref["path"]).read_bytes()
    if hashlib.sha256(payload).hexdigest() != ref["sha256"]:
        raise ValueError("archive blob digest mismatch")
    return payload


@contextlib.contextmanager
def install_archive(archive: Archive, *, models_cls: type | None = None) -> Iterator[Archive]:
    """Capture Google GenAI model calls without changing their return or raise behavior."""
    if models_cls is None:
        from google.genai.models import Models
        models_cls = Models
    original_call = models_cls.generate_content
    original_stream = models_cls.generate_content_stream

    def request(call_id: str, method: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
        archive.event("provider_request", {"call_id": call_id, "provider": "google", "method": method,
                                            "args": list(args), "kwargs": dict(kwargs)})

    def capture_error(call_id: str, method: str, error: BaseException) -> None:
        archive.event("provider_error", {"call_id": call_id, "provider": "google", "method": method,
                                          "type": type(error).__name__, "message": str(error)})

    def terminal(call_id: str, method: str, status: str, error: BaseException | None = None) -> None:
        payload = {"call_id": call_id, "provider": "google", "method": method, "status": status}
        if error is not None:
            payload.update(type=type(error).__name__, message=str(error))
        archive.event("provider_terminal", payload)

    def generate_content(self: Any, *args: Any, **kwargs: Any) -> Any:
        call_id = uuid.uuid4().hex
        request(call_id, "generate_content", args, kwargs)
        try:
            response = original_call(self, *args, **kwargs)
        except BaseException as error:
            capture_error(call_id, "generate_content", error)
            terminal(call_id, "generate_content", "error", error)
            raise
        archive.event("provider_response", {"call_id": call_id, "provider": "google",
                                             "method": "generate_content", "response": response})
        terminal(call_id, "generate_content", "ok")
        return response

    def generate_content_stream(self: Any, *args: Any, **kwargs: Any) -> Iterator[Any]:
        call_id = uuid.uuid4().hex
        request(call_id, "generate_content_stream", args, kwargs)
        try:
            stream = original_stream(self, *args, **kwargs)
        except BaseException as error:
            capture_error(call_id, "generate_content_stream", error)
            terminal(call_id, "generate_content_stream", "error", error)
            raise

        def captured() -> Iterator[Any]:
            completed = False
            terminaled = False
            try:
                for response in stream:
                    archive.event("provider_chunk", {"call_id": call_id, "provider": "google",
                                                     "method": "generate_content_stream", "response": response})
                    yield response
                completed = True
                terminal(call_id, "generate_content_stream", "ok")
                terminaled = True
            except BaseException as error:
                capture_error(call_id, "generate_content_stream", error)
                terminal(call_id, "generate_content_stream", "error", error)
                terminaled = True
                raise
            finally:
                if not completed:
                    archive.event("provider_interrupted", {"call_id": call_id, "provider": "google",
                                                         "method": "generate_content_stream"})
                    if not terminaled:
                        interruption = RuntimeError("stream interrupted before completion")
                        capture_error(call_id, "generate_content_stream", interruption)
                        terminal(call_id, "generate_content_stream", "error", interruption)

        return captured()

    models_cls.generate_content = generate_content
    models_cls.generate_content_stream = generate_content_stream
    try:
        yield archive
    finally:
        models_cls.generate_content = original_call
        models_cls.generate_content_stream = original_stream
