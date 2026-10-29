"""Memory-probe reuse hook (prestage_hooks.patch_probe) on the pinned trainer's startup_memory_probe, CPU with mocks."""
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.environ["TRAINER"])
registry = Path(tempfile.mkdtemp(prefix="probe_registry_", dir=os.environ["FX"]))
os.environ["R1_PROBE_REGISTRY"] = str(registry)
os.environ.pop("STUDENT_MEMORY_PROBE_CACHE", None)
import torch
from student_pilot import ddp_training
from student_pilot.common import canonical_bytes

assert getattr(ddp_training.startup_memory_probe, "__name__", "") == "startup_memory_probe"
assert ddp_training.startup_memory_probe.__module__ == "prestage_hooks", "probe hook not installed"
TOTAL, WORLD = 80 * 10**9, 4
rows = [{"qid": f"q{i}"} for i in range(10)]
audits = {f"q{i}": {"qid": f"q{i}", "sequence_tokens": 100 + i, "visual_tokens": 50 + (i * 7) % 10,
                    "assistant_tokens_including_eos": 30 + (i * 3) % 10} for i in range(10)}
base = {"world_size": WORLD, "effective_batch_size": 32, "max_microbatch_size": 8, "memory_fraction": 0.9,
        "memory_fit_safety_factor": 1.15, "seed": 17, "learning_rate": 1e-4, "parallel": "fsdp", "lora_rank": 32}
protocol = {"student": "qwen35", "base_sha256": "b" * 64, "runtime": [{"path": "x", "sha256": "c" * 64}], "versions": {"torch": "t"}}
topology = {"nnodes": 1, "local_world_size": WORLD}
calls = []


def report(rank):
    return {"rank": rank, "trials": [{"microbatch": size, "fits": True, "seconds": float(size),
                                      "peak_allocated_bytes": 5 * 10**9 * size, "total_memory_bytes": TOTAL}
                                     for size in (1, 2, 4, 8)]}


def fake_probe(model, processor, rows, audits, settings, rank, lease_check):
    calls.append(rank)
    return report(rank)


def run(settings, rank=0, free=TOTAL, checkpoint=None, topo=None):
    with patch.object(ddp_training, "memory_probe", side_effect=fake_probe), \
            patch.object(ddp_training, "gather", side_effect=lambda value, world: [  # every rank's own report, other values agree
                {**value, "rank": r} if isinstance(value, dict) and "trials" in value else value for r in range(world)]), \
            patch.object(torch.cuda, "get_device_properties", return_value=SimpleNamespace(name="H100 test", total_memory=TOTAL)), \
            patch.object(torch.cuda, "mem_get_info", return_value=(free, TOTAL)), \
            patch.object(torch.cuda, "memory_reserved", return_value=0):
        return ddp_training.startup_memory_probe(None, None, rows, audits, settings, rank, lambda: None, protocol,
                                                 topo or topology, checkpoint)


results = {}
probe, context = run(base)
results["1_miss_measures_and_records"] = calls == [0] and context is None and len(list(registry.glob("*.json"))) == 1
probe, context = run(base, rank=2)
results["2_same_config_reuses"] = calls == [0] and probe["rank"] == 2 and "reused_measured_probe" in probe and context is None
probe, _ = run({**base, "seed": 18, "learning_rate": 2e-4})
results["3_seed_and_lr_do_not_change_the_key"] = calls == [0] and "reused_measured_probe" in probe
probe, _ = run({**base, "max_microbatch_size": 4})
results["4_memory_setting_change_measures_again"] = calls == [0, 0] and "reused_measured_probe" not in probe
probe, _ = run(base, free=10**9)
results["5_insufficient_free_memory_measures"] = calls == [0, 0, 0] and "reused_measured_probe" not in probe
probe, _ = run({**base, "lora_rank": 64})
first = calls == [0, 0, 0, 0] and "reused_measured_probe" not in probe
probe, _ = run({**base, "lora_rank": 64})
results["6_lora_change_measures_then_reuses"] = first and calls == [0, 0, 0, 0] and "reused_measured_probe" in probe
other = Path(tempfile.mkdtemp(prefix="probe_registry_empty_", dir=os.environ["FX"]))
checkpoint_dir = Path(tempfile.mkdtemp(prefix="checkpoint_", dir=os.environ["FX"]))
(checkpoint_dir / "artifacts").mkdir()
data = canonical_bytes({"ranks": [report(rank) for rank in range(WORLD)]})
(checkpoint_dir / "artifacts/memory_probe.json").write_bytes(data)
import hashlib
pin = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
os.environ["R1_PROBE_REGISTRY"], os.environ["RESUME_FROM"] = str(other), str(checkpoint_dir)
multi = {"nnodes": 2, "local_world_size": 2}
probe, _ = run({**base, "effective_batch_size": 16}, rank=1, checkpoint={"files": {"artifacts/memory_probe.json": pin}, "step": 5})
results["7a_one_node_resume_measures_afresh"] = calls == [0, 0, 0, 0, 1] and "reused_measured_probe" not in probe
calls[:] = [0, 0, 0, 0]
os.environ["R1_PROBE_REGISTRY"] = str(Path(tempfile.mkdtemp(prefix="probe_registry_empty2_", dir=os.environ["FX"])))
probe, _ = run({**base, "effective_batch_size": 16}, rank=1, checkpoint={"files": {"artifacts/memory_probe.json": pin}, "step": 5}, topo=multi)
results["7_resume_reuses_the_checkpoint_pinned_probe"] = calls == [0, 0, 0, 0] and "reused_measured_probe" in probe
(checkpoint_dir / "artifacts/memory_probe.json").write_bytes(data.replace(b"80000000000", b"40000000000"))
probe, _ = run({**base, "effective_batch_size": 16}, rank=1, checkpoint={"files": {"artifacts/memory_probe.json": pin}, "step": 5}, topo=multi)
results["8_changed_checkpoint_probe_is_not_reused"] = calls == [0, 0, 0, 0, 1] and "reused_measured_probe" not in probe
print(json.dumps(results, indent=1))
print("PROBE_TEST", "PASS" if all(results.values()) else "FAIL")
