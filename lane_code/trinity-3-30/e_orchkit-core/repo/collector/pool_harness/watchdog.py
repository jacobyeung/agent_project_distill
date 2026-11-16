"""Health-gated target ramping and automatic true-429 storm downscale."""

from __future__ import annotations

import secrets
import time
from pathlib import Path
from typing import Any

from .atomicfs import StateError, publish_json_exclusive, read_json, replace_json
from .state import Target, TargetStore
from .telemetry import RollingGauge


class HealthGateError(StateError):
    """A requested upscale violates the clean health window."""


class HealthWatchdog:
    def __init__(
        self,
        target_store: TargetStore,
        gauge: RollingGauge,
        *,
        health_watch_seconds: float = 900.0,
        burst_window_seconds: float = 60.0,
        burst_count: int = 2,
        ramp_step: int = 1,
    ):
        if health_watch_seconds <= 0 or burst_window_seconds <= 0:
            raise StateError("watchdog windows must be positive")
        if burst_count < 1 or ramp_step < 1:
            raise StateError("burst_count and ramp_step must be positive")
        self.target_store = target_store
        self.gauge = gauge
        self.health_watch_seconds = health_watch_seconds
        self.burst_window_seconds = burst_window_seconds
        self.burst_count = burst_count
        self.ramp_step = ramp_step
        self.state_path = target_store.state_root / "watchdog" / "state.json"
        self.event_root = target_store.state_root / "watchdog" / "events"

    def _state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {
                "last_acted_429_wall_ns": None,
                "next_ramp_wall_ns": 0,
                "schema": "resizable-pool-watchdog-state-v1",
            }
        value = read_json(self.state_path)
        if (
            not isinstance(value, dict)
            or value.get("schema") != "resizable-pool-watchdog-state-v1"
        ):
            raise StateError("watchdog state is malformed")
        return value

    def _write_state(self, value: dict[str, Any]) -> None:
        replace_json(self.state_path, value)

    def _intent(self, action: str, payload: dict[str, Any], now_ns: int) -> Path:
        return publish_json_exclusive(
            self.event_root / f"{now_ns}-{secrets.token_hex(8)}.json",
            {
                "action": action,
                "payload": payload,
                "phase": "intent",
                "schema": "resizable-pool-watchdog-event-v1",
                "wall_time_ns": now_ns,
            },
        )

    def observe(self, now_wall_ns: int | None = None) -> str:
        """Apply a fresh burst downscale or clear storm after a clean watch."""
        now_ns = time.time_ns() if now_wall_ns is None else now_wall_ns
        state = self._state()
        snapshot = self.gauge.snapshot(
            window_seconds=self.burst_window_seconds,
            now_wall_ns=now_ns,
        )
        latest = snapshot["latest_true_429_wall_ns"]
        if (
            snapshot["true_429_count"] >= self.burst_count
            and latest is not None
            and (
                state["last_acted_429_wall_ns"] is None
                or latest > state["last_acted_429_wall_ns"]
            )
        ):
            target = self.target_store.read()
            downscaled = Target(
                total_workers=target.storm_workers,
                storm_workers=target.storm_workers,
            )
            self._intent(
                "true_429_downscale",
                {
                    "from_total": target.total_workers,
                    "to_total": downscaled.total_workers,
                    "true_429_count": snapshot["true_429_count"],
                },
                now_ns,
            )
            self.target_store.write(downscaled)
            self.target_store.set_storm(True)
            state["last_acted_429_wall_ns"] = latest
            state["next_ramp_wall_ns"] = (
                now_ns + int(self.health_watch_seconds * 1_000_000_000)
            )
            self._write_state(state)
            return "downscaled"

        if (
            self.target_store.storm_marker.exists()
            and now_ns >= state["next_ramp_wall_ns"]
            and snapshot["true_429_count"] == 0
        ):
            self._intent("clear_storm_after_clean_watch", {}, now_ns)
            self.target_store.set_storm(False)
            return "storm_cleared"
        return "watching"

    def request_ramp(self, new_total: int, now_wall_ns: int | None = None) -> None:
        """Raise by at most one configured step after the prior 15-minute watch."""
        now_ns = time.time_ns() if now_wall_ns is None else now_wall_ns
        state = self._state()
        target = self.target_store.read()
        if self.target_store.storm_marker.exists():
            raise HealthGateError("cannot ramp while the storm marker is active")
        if now_ns < state["next_ramp_wall_ns"]:
            raise HealthGateError("the prior ramp's health watch is still active")
        if new_total <= target.total_workers:
            raise HealthGateError("request_ramp only accepts an upscale")
        if new_total > target.total_workers + self.ramp_step:
            raise HealthGateError("requested upscale exceeds one ramp step")
        snapshot = self.gauge.snapshot(
            window_seconds=self.burst_window_seconds,
            now_wall_ns=now_ns,
        )
        if snapshot["true_429_count"]:
            raise HealthGateError("recent true 429 blocks ramping")
        next_target = Target(
            total_workers=new_total,
            storm_workers=target.storm_workers,
        )
        next_target.validate(self.target_store.config.total_workers_max)
        self._intent(
            "ramp_up",
            {"from_total": target.total_workers, "to_total": new_total},
            now_ns,
        )
        # Publish the next health gate before the upscale. A crash between
        # these writes can delay capacity, but can never permit two ramp
        # steps without an intervening health watch.
        state["next_ramp_wall_ns"] = (
            now_ns + int(self.health_watch_seconds * 1_000_000_000)
        )
        self._write_state(state)
        self.target_store.write(next_target)
