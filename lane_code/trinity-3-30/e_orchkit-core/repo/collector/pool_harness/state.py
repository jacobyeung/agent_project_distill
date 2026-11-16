"""Durable target, heartbeat, claim, receipt, and orphan-recovery state."""

from __future__ import annotations

import hashlib
from itertools import chain
import os
import random
import socket
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable

from .atomicfs import (
    AlreadyExists,
    LockTimeout,
    StateError,
    canonical_bytes,
    durable_unlink,
    link_lock,
    publish_json_exclusive,
    prepared_json_exclusive,
    read_json,
    replace_json,
    safe_component,
)


TARGET_SCHEMA = "req116-worker-target-v2"
CONFIG_SCHEMA = "resizable-pool-config-v1"


@dataclass(frozen=True)
class PoolConfig:
    pool_id: str
    total_workers_max: int
    spawn_stagger_seconds: float = 45.0
    poll_seconds: float = 2.0
    heartbeat_seconds: float = 10.0
    heartbeat_timeout_seconds: float = 60.0
    max_owners_per_shard: int = 4

    def __post_init__(self) -> None:
        safe_component(self.pool_id, "pool_id")
        if isinstance(self.total_workers_max, bool) or not (
            isinstance(self.total_workers_max, int)
            and 1 <= self.total_workers_max <= 1024
        ):
            raise StateError("total_workers_max must be an integer within 1..1024")
        for name in (
            "spawn_stagger_seconds",
            "poll_seconds",
            "heartbeat_seconds",
            "heartbeat_timeout_seconds",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                raise StateError(f"{name} must be positive")
        if (
            isinstance(self.max_owners_per_shard, bool)
            or not isinstance(self.max_owners_per_shard, int)
            or self.max_owners_per_shard < 1
        ):
            raise StateError("max_owners_per_shard must be a positive integer")

    @classmethod
    def from_json(cls, path: Path) -> "PoolConfig":
        value = read_json(path)
        expected = {
            "heartbeat_seconds",
            "heartbeat_timeout_seconds",
            "max_owners_per_shard",
            "poll_seconds",
            "pool_id",
            "schema",
            "spawn_stagger_seconds",
            "total_workers_max",
        }
        if not isinstance(value, dict) or set(value) != expected:
            raise StateError("pool-config field census mismatch")
        if value.pop("schema") != CONFIG_SCHEMA:
            raise StateError("pool-config schema mismatch")
        return cls(**value)


@dataclass(frozen=True)
class Target:
    total_workers: int
    storm_workers: int

    def validate(self, ceiling: int) -> None:
        if (
            isinstance(self.total_workers, bool)
            or not isinstance(self.total_workers, int)
            or not 0 <= self.total_workers <= ceiling
        ):
            raise StateError(f"total_workers must be within 0..{ceiling}")
        if (
            isinstance(self.storm_workers, bool)
            or not isinstance(self.storm_workers, int)
            or not 1 <= self.storm_workers <= ceiling
        ):
            raise StateError(f"storm_workers must be within 1..{ceiling}")
        if self.total_workers and self.storm_workers > self.total_workers:
            raise StateError("storm_workers cannot exceed a nonzero total_workers")

    def effective(self, storm_active: bool) -> int:
        if self.total_workers == 0:
            return 0
        return self.storm_workers if storm_active else self.total_workers

    def as_json(self) -> dict[str, Any]:
        return {
            "schema": TARGET_SCHEMA,
            "storm_workers": self.storm_workers,
            "total_workers": self.total_workers,
        }


class TargetStore:
    """The mutable v2 target serialized with every claim-boundary decision."""

    def __init__(self, state_root: Path, config: PoolConfig):
        self.state_root = state_root
        self.config = config
        self.path = state_root / "WORKER_TARGET.json"
        self.storm_marker = state_root / "429_STORM_ACTIVE"
        self.lock_dir = state_root / "locks"

    def cap_lock(self):
        return link_lock(self.lock_dir, "POOL_CAP", poll_seconds=0.1)

    def read(self) -> Target:
        value = read_json(self.path)
        if not isinstance(value, dict) or set(value) != {
            "schema", "storm_workers", "total_workers"
        }:
            raise StateError("worker-target field census mismatch")
        if value["schema"] != TARGET_SCHEMA:
            raise StateError("worker-target schema mismatch")
        target = Target(
            total_workers=value["total_workers"],
            storm_workers=value["storm_workers"],
        )
        target.validate(self.config.total_workers_max)
        return target

    def write(self, target: Target) -> None:
        target.validate(self.config.total_workers_max)
        with self.cap_lock():
            replace_json(self.path, target.as_json())

    def effective(self) -> int:
        target = self.read()
        return target.effective(self.storm_marker.exists())

    def set_storm(self, active: bool) -> None:
        with self.cap_lock():
            if active:
                try:
                    publish_json_exclusive(
                        self.storm_marker,
                        {"schema": "resizable-pool-storm-v1"},
                    )
                except AlreadyExists:
                    if not self.storm_marker.is_file():
                        raise
            elif self.storm_marker.exists():
                durable_unlink(self.storm_marker)


@dataclass(frozen=True)
class Episode:
    episode_id: str
    shard: str
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.episode_id, str) or not self.episode_id:
            raise StateError("episode_id must be a nonempty string")
        safe_component(self.shard, "shard")
        if not isinstance(self.payload, dict):
            raise StateError("episode payload must be an object")

    @property
    def key(self) -> str:
        return hashlib.sha256(self.episode_id.encode("utf-8")).hexdigest()


class EpisodeCatalog:
    def __init__(self, episodes: Iterable[Episode]):
        self.episodes = tuple(episodes)
        ids = [episode.episode_id for episode in self.episodes]
        keys = [episode.key for episode in self.episodes]
        if not ids or len(ids) != len(set(ids)) or len(keys) != len(set(keys)):
            raise StateError("episode catalog must be nonempty with unique ids")
        self.by_key = {episode.key: episode for episode in self.episodes}

    @classmethod
    def from_json(cls, path: Path) -> "EpisodeCatalog":
        value = read_json(path)
        if not isinstance(value, dict) or set(value) != {"episodes", "schema"}:
            raise StateError("episode-catalog field census mismatch")
        if value["schema"] != "resizable-pool-episodes-v1":
            raise StateError("episode-catalog schema mismatch")
        rows = value["episodes"]
        if not isinstance(rows, list):
            raise StateError("episode-catalog episodes must be a list")
        episodes = []
        for row in rows:
            if not isinstance(row, dict) or set(row) != {
                "episode_id", "payload", "shard"
            }:
                raise StateError("episode row field census mismatch")
            episodes.append(Episode(**row))
        return cls(episodes)


class ClaimOutcome(Enum):
    CLAIMED = "claimed"
    RETIRE = "retire"
    SCAN_EXHAUSTED = "scan_exhausted"


@dataclass(frozen=True)
class ClaimResult:
    outcome: ClaimOutcome
    episode: Episode | None = None
    claim_path: Path | None = None


class HeartbeatStore:
    def __init__(self, state_root: Path):
        self.root = state_root / "heartbeats"

    def path(self, worker_id: str) -> Path:
        safe_component(worker_id, "worker_id")
        return self.root / f"{worker_id}.json"

    def publish(
        self,
        worker_id: str,
        *,
        state: str,
        episode_id: str | None,
    ) -> None:
        safe_component(worker_id, "worker_id")
        replace_json(self.path(worker_id), {
            "episode_id": episode_id,
            "host": socket.gethostname(),
            "monotonic_ns": time.monotonic_ns(),
            "pid": os.getpid(),
            "schema": "resizable-pool-heartbeat-v1",
            "state": state,
            "wall_time_ns": time.time_ns(),
            "worker_id": worker_id,
        })

    def live_workers(self, timeout_seconds: float, now_ns: int | None = None) -> set[str]:
        now_ns = time.time_ns() if now_ns is None else now_ns
        result: set[str] = set()
        if not self.root.exists():
            return result
        for path in self.root.iterdir():
            if not path.is_file() or path.suffix != ".json":
                continue
            value = read_json(path)
            if (
                isinstance(value, dict)
                and value.get("schema") == "resizable-pool-heartbeat-v1"
                and isinstance(value.get("wall_time_ns"), int)
                and now_ns - value["wall_time_ns"]
                <= int(timeout_seconds * 1_000_000_000)
            ):
                result.add(str(value.get("worker_id")))
        return result


class EpisodeQueue:
    """Atomic episode claims; normal scans never reclaim an orphaned claim."""

    def __init__(
        self,
        state_root: Path,
        catalog: EpisodeCatalog,
        target_store: TargetStore,
        valid_trace: Callable[[Episode], bool],
    ):
        self.state_root = state_root
        self.catalog = catalog
        self.target_store = target_store
        self.valid_trace = valid_trace
        self.claim_root = state_root / "claims"
        self.receipt_root = state_root / "exit_receipts"
        self.heartbeats = HeartbeatStore(state_root)

    def claim_path(self, episode: Episode) -> Path:
        return self.claim_root / f"{episode.key}.json"

    def _read_claim(self, episode: Episode) -> dict[str, Any] | None:
        path = self.claim_path(episode)
        return read_json(path) if path.exists() else None

    def require_drained(self) -> dict[str, Any]:
        """Verify predecessor death and return the host attestations that covered it."""
        from attest_host_drained import covering_attestation, load_attestations

        records = [(p, read_json(p)) for directory in (self.state_root / "worker_starts",
                                                     self.heartbeats.root, self.claim_root)
                   for p in directory.glob("*.json")]
        attestations = None
        evidence = {}
        for path, record in records:
            worker = record.get("worker_id")
            if record.get("host") != socket.gethostname():
                # A remote exit receipt proves that worker crossed its final boundary.
                if worker and (self.receipt_root / f"{worker}.json").is_file():
                    self.read_exit_receipt(worker)
                    continue
                if attestations is None:
                    attestations = load_attestations(self.state_root)
                covered = covering_attestation(attestations, record, path)
                if covered is not None:
                    entry = evidence.setdefault(covered["attestation"], covered)
                    if worker not in entry["workers"]:
                        entry["workers"].append(worker)
                    continue
                raise StateError("predecessor drainage unverified on foreign host")
            pid = record.get("pid")
            if type(pid) is not int or pid <= 0:
                raise StateError("predecessor drainage lacks a valid PID")
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                continue
            except PermissionError:
                pass
            raise StateError(f"predecessor worker remains live; drain first: {worker}")
        return {"drain_evidence": list(evidence.values())}

    def claim_next(self, worker_id: str, slot: int) -> ClaimResult:
        safe_component(worker_id, "worker_id")
        if isinstance(slot, bool) or not isinstance(slot, int) or slot < 0:
            raise StateError("slot must be a nonnegative integer")
        if slot >= self.target_store.effective():
            return ClaimResult(ClaimOutcome.RETIRE)
        worker_lock = f"WORKER_{worker_id}"
        with link_lock(self.target_store.lock_dir, worker_lock):
            timeouts = 0
            episodes = self.catalog.episodes
            offset = slot % len(episodes) if episodes else 0
            for episode in chain(episodes[offset:], episodes[:offset]):
                # Catalog/terminal I/O must never serialize other claimants.
                if self.claim_path(episode).exists() or self.valid_trace(episode):
                    continue
                path = self.claim_path(episode)
                while True:
                    if path.exists():
                        break
                    try:
                        with prepared_json_exclusive(path, {
                                "claimed_monotonic_ns": time.monotonic_ns(),
                                "claimed_wall_time_ns": time.time_ns(),
                                "episode_id": episode.episode_id,
                                "host": socket.gethostname(),
                                "pid": os.getpid(),
                                "schema": "resizable-pool-claim-v1",
                                "worker_id": worker_id,
                            }) as publish:
                            with self.target_store.cap_lock():
                                target = self.target_store.read()
                                if slot >= target.effective(self.target_store.storm_marker.exists()):
                                    return ClaimResult(ClaimOutcome.RETIRE)
                                publish()
                        return ClaimResult(ClaimOutcome.CLAIMED, episode, path)
                    except AlreadyExists:
                        break
                    except LockTimeout as exc:
                        timeouts += 1
                        delay = random.uniform(1, 5)
                        publish_json_exclusive(self.state_root / "worker_telemetry" / worker_id / f"{uuid.uuid4().hex}.json", {
                            "schema": "r1314-claim-lock-timeout-v1", "worker_id": worker_id,
                            "episode_id": episode.episode_id, "timeout_number": timeouts,
                            "retry_limit": 20, "backoff_seconds": delay if timeouts <= 20 else None,
                            "wall_time_ns": time.time_ns(), "message": str(exc),
                        })
                        if timeouts > 20:
                            raise
                        time.sleep(delay)
            return ClaimResult(ClaimOutcome.SCAN_EXHAUSTED)

    def publish_exit_receipt(
        self,
        worker_id: str,
        *,
        reason: str,
        slot: int,
        return_code: int,
    ) -> Path:
        safe_component(worker_id, "worker_id")
        if reason not in {"retired", "scan_exhausted", "worker_error"}:
            raise StateError(f"invalid worker exit reason: {reason}")
        return publish_json_exclusive(
            self.receipt_root / f"{worker_id}.json",
            {
                "census": self.census(),
                "reason": reason,
                "return_code": return_code,
                "schema": "resizable-pool-exit-v1",
                "slot": slot,
                "worker_id": worker_id,
            },
        )

    def read_exit_receipt(self, worker_id: str) -> dict[str, Any]:
        safe_component(worker_id, "worker_id")
        value = read_json(self.receipt_root / f"{worker_id}.json")
        if (
            not isinstance(value, dict)
            or value.get("schema") != "resizable-pool-exit-v1"
            or value.get("worker_id") != worker_id
        ):
            raise StateError(f"invalid exit receipt for {worker_id}")
        return value

    def census(self) -> dict[str, Any]:
        live = self.heartbeats.live_workers(
            self.target_store.config.heartbeat_timeout_seconds
        )
        by_shard: dict[str, dict[str, int]] = {}
        totals = {
            "claimed_live": 0,
            "claimed_orphan": 0,
            "unclaimed": 0,
            "valid_complete": 0,
        }
        for episode in self.catalog.episodes:
            row = by_shard.setdefault(
                episode.shard,
                {name: 0 for name in totals},
            )
            if self.valid_trace(episode):
                status = "valid_complete"
            else:
                claim = self._read_claim(episode)
                if claim is None:
                    status = "unclaimed"
                elif claim.get("worker_id") in live:
                    status = "claimed_live"
                else:
                    status = "claimed_orphan"
            totals[status] += 1
            row[status] += 1
        return {
            **totals,
            "by_shard": by_shard,
            "total": len(self.catalog.episodes),
        }

    def recover_orphan(
        self,
        episode_id: str,
        *,
        expected_worker_id: str,
        owner_is_alive: Callable[[dict[str, Any]], bool],
        proof: dict[str, Any],
    ) -> Path:
        """Explicitly recover one dead owner's claim; never called by claim_next."""
        safe_component(expected_worker_id, "expected_worker_id")
        episode = next(
            (item for item in self.catalog.episodes if item.episode_id == episode_id),
            None,
        )
        if episode is None:
            raise StateError(f"unknown episode for recovery: {episode_id!r}")
        if not isinstance(proof, dict) or not proof:
            raise StateError("orphan recovery requires a nonempty proof object")
        with link_lock(self.target_store.lock_dir, f"RECOVER_{episode.key}"):
            with self.target_store.cap_lock():
                claim_path = self.claim_path(episode)
                if (not claim_path.exists()
                        or read_json(claim_path).get("worker_id") != expected_worker_id):
                    for receipt in (self.state_root / "orphan_recoveries").glob(f"{episode.key}-*.json"):
                        saved = read_json(receipt)
                        if (saved.get("episode_id") == episode_id
                                and saved.get("expected_worker_id") == expected_worker_id
                                and saved.get("proof") == proof):
                            return receipt
                    if not claim_path.exists():
                        raise StateError("missing claim without matching recovery evidence")
                claim_bytes = claim_path.read_bytes()
                claim = read_json(claim_path)
                if claim.get("worker_id") != expected_worker_id:
                    raise StateError("orphan recovery owner mismatch")
                if self.valid_trace(episode):
                    raise StateError("refusing recovery after a valid trace exists")
                if owner_is_alive(claim):
                    raise StateError("refusing recovery while owner is alive")
                claim_sha = hashlib.sha256(claim_bytes).hexdigest()
                receipt = (
                    self.state_root / "orphan_recoveries"
                    / f"{episode.key}-{claim_sha}.json"
                )
                payload = {
                    "claim_sha256": claim_sha,
                    "episode_id": episode.episode_id,
                    "expected_worker_id": expected_worker_id,
                    "proof": proof,
                    "schema": "resizable-pool-orphan-recovery-v1",
                }
                try:
                    publish_json_exclusive(receipt, payload)
                except AlreadyExists:
                    if canonical_bytes(read_json(receipt)) != canonical_bytes(payload):
                        raise StateError("orphan-recovery receipt collision")
                durable_unlink(claim_path)
                return receipt
