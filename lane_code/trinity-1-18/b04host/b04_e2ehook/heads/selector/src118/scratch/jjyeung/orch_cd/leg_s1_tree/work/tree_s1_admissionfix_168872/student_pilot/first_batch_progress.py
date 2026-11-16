import math
import os
from pathlib import Path
import re
import resource
import time
import uuid

from .p3_provenance import digest, file_pin, load, pinned, write


def publish(path, value):
    path = Path(path)
    temporary = path.with_name(path.stem+"."+uuid.uuid4().hex+".json")
    write(temporary, value)
    with temporary.open("rb") as handle:
        os.fsync(handle.fileno())
    os.link(temporary, path)


class PhaseJournal:
    def __init__(self, directory, binding):
        self.root = Path(directory).resolve()
        self.binding = binding

    def run(self, name, action):
        if not re.fullmatch("[a-z_]+", name):
            raise ValueError("Invalid admission phase")
        marker = self.root / f"phase_{name}.complete.json"
        if marker.exists():
            value = load(marker)
            payload = Path(value.get("payload", {}).get("path", "."))
            if (value.get("schema") != "s1-admission-phase-v1" or value.get("binding") != self.binding
                    or marker.is_symlink() or payload.is_symlink() or not payload.resolve().is_relative_to(self.root)):
                raise ValueError("Admission phase binding differs")
            result = load(pinned(value["payload"]))
            for pin in result["outputs"]:
                pinned(pin)
            return result, True
        directory = self.root / (name+"_"+uuid.uuid4().hex)
        directory.mkdir()
        started = time.perf_counter()
        result = action(directory)
        result["resources"] = dict(seconds=time.perf_counter()-started,
                                   peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        for pin in result["outputs"]:
            pinned(pin)
        write(directory / "result.json", result)
        publish(marker, dict(schema="s1-admission-phase-v1", binding=self.binding,
                             payload=file_pin(directory / "result.json")))
        return result, False


class RankJournal:
    def __init__(self, directory, binding, plans):
        self.root = Path(directory).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.binding = {**binding, "plans_sha256": digest(plans)}
        self.plans = plans

    def expected(self, rank):
        return [dict(step=step, microstep=microstep, rank=rank, stream=stream, index=int(indices[rank]))
                for step, plan in enumerate(self.plans, 1)
                for microstep, (stream, indices) in enumerate(plan)]

    def validate(self, rank, value):
        if (value.get("schema") != "c1-first-batch-rank-v1" or value.get("binding") != self.binding
                or value.get("rank") != rank):
            raise ValueError("First-batch rank binding differs")
        records = value.get("records", [])
        keys = ("step", "microstep", "rank", "stream", "index")
        if (not records or [{key: row.get(key) for key in keys} for row in records] != self.expected(rank)
                or any(row.get("finite") is not True or type(row.get("loss")) not in (int, float)
                       or not math.isfinite(row["loss"]) or not isinstance(row.get("components"), dict)
                       or not row["components"] or "qid" not in row
                       or type(row.get("tokens")) is not int or row["tokens"] < 1
                       or type(row.get("effective_tokens")) is not int or row["effective_tokens"] < row["tokens"]
                       or any(type(part) not in (int, float) or not math.isfinite(part)
                              for part in row["components"].values()) for row in records)):
            raise ValueError("First-batch rank is partial, nonfinite or belongs to another row plan")
        return value

    def load(self, rank):
        path = self.root / f"rank_{rank:03d}.complete.json"
        if not path.exists():
            return None
        if path.is_symlink():
            raise ValueError("First-batch completion must not be a link")
        marker = load(path)
        pin = marker.get("payload", {})
        payload = Path(pin.get("path", "."))
        if (marker.get("schema") != "c1-first-batch-completion-v1"
                or payload.is_symlink() or not payload.resolve().is_relative_to(self.root)):
            raise ValueError("First-batch completion payload is outside its journal")
        return self.validate(rank, load(pinned(pin)))

    def save(self, rank, records, resources):
        value = self.validate(rank, dict(schema="c1-first-batch-rank-v1", rank=rank, binding=self.binding,
                                        records=records, resources=resources))
        path = self.root / f"rank_{rank:03d}_{digest(value)}.json"
        write(path, value)
        publish(self.root / f"rank_{rank:03d}.complete.json",
                dict(schema="c1-first-batch-completion-v1", payload=file_pin(path)))
        return value
