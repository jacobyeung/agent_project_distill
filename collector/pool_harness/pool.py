"""Incremental worker loop and target-driven resizable process controller."""

from __future__ import annotations

import math
import os
import subprocess
import threading
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from episode_custody import FailureEvent

from .atomicfs import AlreadyExists, StateError, link_lock, publish_json_exclusive, read_json, replace_json, safe_component
from .state import (
    ClaimOutcome,
    ClaimResult,
    Episode,
    EpisodeQueue,
    PoolConfig,
    TargetStore,
)


class PoolBlocked(StateError):
    """Only orphan claims remain, so explicit recovery is required."""


class _HeartbeatPump:
    def __init__(
        self,
        queue: EpisodeQueue,
        worker_id: str,
        episode_id: str,
        interval: float,
    ):
        self.queue = queue
        self.worker_id = worker_id
        self.episode_id = episode_id
        self.interval = interval
        self.stop_event = threading.Event()
        self.failed_event = FailureEvent()
        self.error: BaseException | None = None
        self.thread = threading.Thread(
            target=self._run,
            name=f"heartbeat-{worker_id}",
            daemon=False,
        )

    def _run(self) -> None:
        try:
            while not self.stop_event.wait(self.interval):
                self.queue.heartbeats.publish(
                    self.worker_id,
                    state="running",
                    episode_id=self.episode_id,
                )
        except BaseException as exc:
            self.error = exc
            self.failed_event.set()

    def __enter__(self) -> "_HeartbeatPump":
        self.thread.start()
        return self

    def __exit__(self, *_args: object) -> None:
        self.stop_event.set()
        self.thread.join()
        if self.error is not None:
            raise StateError(f"heartbeat publisher failed: {self.error}") from self.error


RunEpisode = Callable[[Episode, ClaimResult, threading.Event], None]


class WorkerLoop:
    """Claim and run exactly one episode at a time until retirement/exhaustion."""

    def __init__(
        self,
        queue: EpisodeQueue,
        *,
        worker_id: str,
        slot: int,
        run_episode: RunEpisode,
    ):
        safe_component(worker_id, "worker_id")
        self.queue = queue
        self.worker_id = worker_id
        self.slot = slot
        self.run_episode = run_episode

    def _exit(self, reason: str, return_code: int) -> int:
        self.queue.heartbeats.publish(
            self.worker_id,
            state=reason,
            episode_id=None,
        )
        self.queue.publish_exit_receipt(
            self.worker_id,
            reason=reason,
            slot=self.slot,
            return_code=return_code,
        )
        return return_code

    def run(self) -> int:
        claim = None
        try:
            self.queue.heartbeats.publish(
                self.worker_id, state="claim_boundary", episode_id=None,
            )
            while True:
                claim = self.queue.claim_next(self.worker_id, self.slot)
                if claim.outcome is ClaimOutcome.RETIRE:
                    return self._exit("retired", 0)
                if claim.outcome is ClaimOutcome.SCAN_EXHAUSTED:
                    return self._exit("scan_exhausted", 0)
                assert claim.episode is not None
                self.queue.heartbeats.publish(
                    self.worker_id,
                    state="running",
                    episode_id=claim.episode.episode_id,
                )
                with _HeartbeatPump(
                    self.queue,
                    self.worker_id,
                    claim.episode.episode_id,
                    self.queue.target_store.config.heartbeat_seconds,
                ) as pump:
                    self.run_episode(claim.episode, claim, pump.failed_event)
                if not self.queue.valid_trace(claim.episode):
                    raise StateError(
                        "episode runner returned without a valid trace: "
                        f"{claim.episode.episode_id}"
                    )
                self.queue.heartbeats.publish(
                    self.worker_id,
                    state="claim_boundary",
                    episode_id=None,
                )
        except Exception as exc:
            from trace_archive import error_details
            frames = traceback.extract_tb(exc.__traceback__)
            origin = frames[-1] if frames else None
            replace_json(self.queue.state_root / "worker_errors" / f"{self.worker_id}.json", {
                "schema": "req226-worker-error-v1", "worker_id": self.worker_id,
                "exception_type": type(exc).__name__, "message": str(exc),
                "origin": [Path(origin.filename).name, origin.name, origin.lineno] if origin else None,
                "episode_id": claim.episode.episode_id if claim and claim.episode else None,
                "error": error_details(exc), "traceback": traceback.format_exc(),
            })
            try:
                self._exit("worker_error", 1)
            except Exception:
                pass
            raise


@dataclass
class _ActiveWorker:
    worker_id: str
    slot: int
    shard_hint: str
    process: subprocess.Popen[bytes]
    log_handle: object


CommandFactory = Callable[[str, int, str], Sequence[str]]


class PoolController:
    """Poll the target, reap, census, and spawn at most one worker per stagger."""

    def __init__(
        self,
        queue: EpisodeQueue,
        target_store: TargetStore,
        *,
        run_epoch: str,
        command_factory: CommandFactory,
        log_root: Path,
        popen_factory: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
    ):
        safe_component(run_epoch, "run_epoch")
        self.queue = queue
        self.target_store = target_store
        self.config: PoolConfig = target_store.config
        self.run_epoch = run_epoch
        self.command_factory = command_factory
        self.log_root = log_root
        self.popen_factory = popen_factory
        self.active: dict[int, _ActiveWorker] = {}
        self.failures: list[str] = []
        self.last_spawn_monotonic = -math.inf
        self.blocked_path = queue.state_root / "BLOCKED.json"
        self.blocked = read_json(self.blocked_path) if self.blocked_path.exists() else None
        self.failure_events = [read_json(path) for path in sorted((queue.state_root / "worker_failures").glob("*.json"))]

    def _generation_path(self, slot: int) -> Path:
        return self.target_store.state_root / "generations" / f"{slot}.json"

    def _next_generation(self, slot: int) -> int:
        path = self._generation_path(slot)
        with link_lock(self.target_store.lock_dir, f"GENERATION_{slot}"):
            generation = 1
            if path.exists():
                value = read_json(path)
                if (
                    not isinstance(value, dict)
                    or value.get("schema") != "resizable-pool-generation-v1"
                    or value.get("slot") != slot
                    or not isinstance(value.get("generation"), int)
                ):
                    raise StateError(f"invalid generation state: {path}")
                generation = value["generation"] + 1
            replace_json(path, {
                "generation": generation,
                "schema": "resizable-pool-generation-v1",
                "slot": slot,
            })
            return generation

    def _reap(self) -> None:
        for slot, active in list(self.active.items()):
            return_code = active.process.poll()
            if return_code is None:
                continue
            active.log_handle.close()
            receipt_error = None
            try:
                receipt = self.queue.read_exit_receipt(active.worker_id)
                if receipt.get("return_code") != return_code:
                    raise StateError("exit receipt return-code mismatch")
            except Exception as exc:
                receipt_error = type(exc).__name__
                self.failures.append(f"{active.worker_id}: {exc}")
            if return_code:
                self.failures.append(f"{active.worker_id}: rc={return_code}")
            if return_code or receipt_error:
                error_path = self.queue.state_root / "worker_errors" / f"{active.worker_id}.json"
                error = read_json(error_path) if error_path.is_file() else {}
                episodes = [episode for episode in self.queue.catalog.episodes
                            if not self.queue.valid_trace(episode)
                            and (self.queue._read_claim(episode) or {}).get("worker_id") == active.worker_id]
                event = {
                    "schema": "req226-worker-failure-v1", "worker_id": active.worker_id,
                    "return_code": return_code, "receipt_error": receipt_error,
                    "exception_type": error.get("exception_type"), "origin": error.get("origin"),
                    "error_receipt": str(error_path) if error else None, "error": error,
                    "wall_time_ns": time.time_ns(), "slot": active.slot,
                    "episode_ids": [episode.episode_id for episode in episodes],
                    "question_ids": sorted({str(episode.payload.get("row", {}).get("id", episode.episode_id)) for episode in episodes}),
                }
                # Persist failure evidence before retiring any claim or spawning a successor.
                publish_json_exclusive(self.queue.state_root / "worker_failures" / f"{active.worker_id}.json", event)
                self.failure_events.append(event)
                for episode in episodes:
                    self.queue.recover_orphan(episode.episode_id,
                        expected_worker_id=active.worker_id,
                        owner_is_alive=lambda _claim: active.process.poll() is None,
                        proof={"controller_epoch": self.run_epoch, "worker_id": active.worker_id,
                               "pid": active.process.pid, "return_code": return_code,
                               "failure_receipt": str(self.queue.state_root / "worker_failures" / f"{active.worker_id}.json")})
            del self.active[slot]

    def stop(self) -> None:
        """Gracefully stop and reap only this controller's owned workers."""
        for active in self.active.values():
            if active.process.poll() is None:
                active.process.terminate()
        for slot, active in list(self.active.items()):
            active.process.wait(timeout=60)
            active.log_handle.close()
            del self.active[slot]

    def _check_failures(self, desired: int) -> None:
        counts: dict[str, int] = {}
        now_ns = time.time_ns()
        recent = set()
        for event in self.failure_events:
            for question in event.get("question_ids", []):
                counts[question] = counts.get(question, 0) + 1
            if 0 <= now_ns - event.get("wall_time_ns", 0) <= 300_000_000_000:
                recent.add(event["worker_id"])
        strikes = sorted(question for question, count in counts.items() if count >= 3)
        reason = "question_infrastructure_three_strikes" if strikes else (
            "worker_failure_storm" if len(recent) > max(1, desired) / 2 else None)
        if reason and not self.blocked:
            self.blocked = {"schema": "r1314-pool-blocked-v1", "reason": reason,
                "question_failure_counts": counts, "three_strike_questions": strikes,
                "recent_failed_workers": sorted(recent), "window_seconds": 300,
                "target_workers": desired, "wall_time_ns": now_ns, "run_epoch": self.run_epoch}
            try:
                publish_json_exclusive(self.blocked_path, self.blocked)
            except AlreadyExists:
                self.blocked = read_json(self.blocked_path)

    def _choose_shard(self, census: dict[str, object]) -> str | None:
        by_shard = census["by_shard"]
        assert isinstance(by_shard, dict)
        owner_counts: dict[str, int] = {}
        for active in self.active.values():
            owner_counts[active.shard_hint] = owner_counts.get(active.shard_hint, 0) + 1
        candidates = []
        for shard, raw in by_shard.items():
            assert isinstance(raw, dict)
            remaining = int(raw["unclaimed"])
            if (
                remaining > 0
                and owner_counts.get(str(shard), 0)
                < self.config.max_owners_per_shard
            ):
                candidates.append((remaining, str(shard)))
        return max(candidates, default=(0, ""))[1] or None

    def _spawn(self, slot: int, shard_hint: str) -> str:
        generation = self._next_generation(slot)
        worker_id = (
            f"{self.config.pool_id}-{self.run_epoch}-{shard_hint}-"
            f"{slot}-g{generation}"
        )
        safe_component(worker_id, "worker_id")
        self.log_root.mkdir(parents=True, exist_ok=True)
        log_path = self.log_root / f"{worker_id}.log"
        handle = log_path.open("xb", buffering=0)
        try:
            process = self.popen_factory(
                list(self.command_factory(worker_id, slot, shard_hint)),
                stdout=handle,
                stderr=subprocess.STDOUT,
                start_new_session=False,
                env=dict(os.environ),
            )
        except Exception:
            handle.close()
            raise
        self.active[slot] = _ActiveWorker(
            worker_id=worker_id,
            slot=slot,
            shard_hint=shard_hint,
            process=process,
            log_handle=handle,
        )
        return worker_id

    def tick(self, now_monotonic: float | None = None) -> dict[str, object]:
        now = time.monotonic() if now_monotonic is None else now_monotonic
        self._reap()
        target = self.target_store.read()
        desired = target.effective(self.target_store.storm_marker.exists())
        self._check_failures(desired)
        if self.blocked:
            self.stop()
        census = self.queue.census()
        if (
            not self.blocked and len(self.active) < desired
            and now - self.last_spawn_monotonic
            >= self.config.spawn_stagger_seconds
        ):
            shard = self._choose_shard(census)
            free_slots = [
                slot for slot in range(desired) if slot not in self.active
            ]
            if shard is not None and free_slots:
                self._spawn(free_slots[0], shard)
                self.last_spawn_monotonic = now
        return {
            "active": len(self.active),
            "census": census,
            "desired": desired,
            "failures": tuple(self.failures),
            "blocked": self.blocked,
        }

    def run(self) -> int:
        while True:
            status = self.tick()
            census = status["census"]
            assert isinstance(census, dict)
            if self.blocked:
                return 2
            if not self.active and census["valid_complete"] == census["total"]:
                return 0
            time.sleep(self.config.poll_seconds)
