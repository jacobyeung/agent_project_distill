"""Trace timing, exact 429 classification, and rolling provider-rate gauges."""

from __future__ import annotations

import re
import secrets
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .atomicfs import StateError, publish_json_exclusive, read_json, replace_json


_HTTP_429 = re.compile(
    r"\bHTTP(?:/\d(?:\.\d)?)?(?:\s+(?:status(?:\s+code)?|error))?"
    r"\s*[:=-]?\s*429\b",
    re.IGNORECASE,
)
_RESOURCE_EXHAUSTED = re.compile(
    r"\bRESOURCE[_\s-]*EXHAUSTED\b|\bResourceExhausted\b",
    re.IGNORECASE,
)


def is_true_429(value: object) -> bool:
    """Require typed HTTP status or exact structured provider status."""
    if isinstance(value, dict):
        status = value.get('http_status')
        provider_status = value.get('provider_status')
    else:
        from transport_admission import exception_http_status
        status = exception_http_status(value)
        provider_status = getattr(value, 'status', None)
    if status is not None:
        return type(status) is int and status == 429
    return provider_status == 'RESOURCE_EXHAUSTED'


@dataclass(frozen=True)
class Span:
    call_id: str
    index: int
    kind: str


class TraceTelemetry:
    """Persist each call start and finish directly in one trace JSON object."""

    def __init__(self, trace_path: Path, initial_trace: dict[str, Any] | None = None):
        self.trace_path = trace_path
        self.lock = threading.Lock()
        if trace_path.exists():
            value = read_json(trace_path)
            if not isinstance(value, dict):
                raise StateError("trace root must be a JSON object")
            self.trace = value
        else:
            self.trace = dict(initial_trace or {})
        telemetry = self.trace.setdefault(
            "runtime_telemetry",
            {"calls": [], "schema": "resizable-pool-call-timing-v1"},
        )
        if (
            not isinstance(telemetry, dict)
            or telemetry.get("schema") != "resizable-pool-call-timing-v1"
            or not isinstance(telemetry.get("calls"), list)
        ):
            raise StateError("trace runtime_telemetry is malformed")
        self._persist()

    @property
    def calls(self) -> list[dict[str, Any]]:
        return self.trace["runtime_telemetry"]["calls"]

    def _persist(self) -> None:
        replace_json(self.trace_path, self.trace)

    def begin(self, kind: str, name: str) -> Span:
        if kind not in {"provider", "tool"} or not isinstance(name, str) or not name:
            raise StateError("call kind/name is invalid")
        with self.lock:
            index = len(self.calls)
            call_id = f"{index}-{secrets.token_hex(8)}"
            self.calls.append({
                "call_id": call_id,
                "elapsed_seconds": None,
                "end_monotonic_ns": None,
                "kind": kind,
                "name": name,
                "start_monotonic_ns": time.monotonic_ns(),
            })
            self._persist()
            return Span(call_id=call_id, index=index, kind=kind)

    def end(
        self,
        span: Span,
        *,
        input_tokens: int | None = None,
        error: object | None = None,
    ) -> dict[str, Any]:
        with self.lock:
            try:
                row = self.calls[span.index]
            except IndexError as exc:
                raise StateError("unknown telemetry span") from exc
            if row.get("call_id") != span.call_id or row["end_monotonic_ns"] is not None:
                raise StateError("telemetry span mismatch or duplicate end")
            end_ns = time.monotonic_ns()
            row["end_monotonic_ns"] = end_ns
            row["elapsed_seconds"] = (
                end_ns - int(row["start_monotonic_ns"])
            ) / 1_000_000_000
            row["error"] = None if error is None else str(error)
            row["true_429"] = is_true_429(error) if error is not None else False
            if span.kind == "provider":
                if input_tokens is None:
                    if error is None:
                        raise StateError(
                            "successful provider call is missing input-token usage"
                        )
                elif (
                    isinstance(input_tokens, bool)
                    or not isinstance(input_tokens, int)
                    or input_tokens < 0
                ):
                    raise StateError(
                        "provider input_tokens must be null or a nonnegative integer"
                    )
                row["input_tokens"] = input_tokens
            elif input_tokens is not None:
                raise StateError("tool spans cannot carry provider input tokens")
            self._persist()
            return dict(row)


class RollingGauge:
    """Immutable provider-call events with a rolling per-minute snapshot."""

    def __init__(self, state_root: Path):
        self.event_root = state_root / "rate_events"

    def record_provider(self, call: dict[str, Any], wall_time_ns: int | None = None) -> Path:
        required = {
            "call_id",
            "elapsed_seconds",
            "end_monotonic_ns",
            "input_tokens",
            "kind",
            "start_monotonic_ns",
            "true_429",
        }
        if (
            not isinstance(call, dict)
            or not required.issubset(call)
            or call["kind"] != "provider"
            or call["end_monotonic_ns"] is None
        ):
            raise StateError("provider call is incomplete for rate telemetry")
        wall_time_ns = time.time_ns() if wall_time_ns is None else wall_time_ns
        name = f"{wall_time_ns}-{secrets.token_hex(8)}.json"
        return publish_json_exclusive(self.event_root / name, {
            "call_id": call["call_id"],
            "input_tokens": call["input_tokens"],
            "schema": "resizable-pool-rate-event-v1",
            "true_429": bool(call["true_429"]),
            "wall_time_ns": wall_time_ns,
        })

    def snapshot(
        self,
        *,
        window_seconds: float = 60.0,
        now_wall_ns: int | None = None,
    ) -> dict[str, Any]:
        if window_seconds <= 0:
            raise StateError("rolling window must be positive")
        now_wall_ns = time.time_ns() if now_wall_ns is None else now_wall_ns
        cutoff = now_wall_ns - int(window_seconds * 1_000_000_000)
        rows = []
        if self.event_root.exists():
            for path in self.event_root.iterdir():
                if not path.is_file() or path.suffix != ".json":
                    continue
                value = read_json(path)
                if (
                    isinstance(value, dict)
                    and value.get("schema") == "resizable-pool-rate-event-v1"
                    and isinstance(value.get("wall_time_ns"), int)
                    and cutoff < value["wall_time_ns"] <= now_wall_ns
                ):
                    rows.append(value)
        factor = 60.0 / window_seconds
        true_rows = [row for row in rows if row.get("true_429") is True]
        return {
            "input_tokens_per_minute": sum(
                int(row["input_tokens"] or 0) for row in rows
            ) * factor,
            "missing_usage_count": sum(
                row.get("input_tokens") is None for row in rows
            ),
            "latest_true_429_wall_ns": max(
                (int(row["wall_time_ns"]) for row in true_rows),
                default=None,
            ),
            "requests_per_minute": len(rows) * factor,
            "true_429_count": len(true_rows),
            "window_seconds": window_seconds,
        }
