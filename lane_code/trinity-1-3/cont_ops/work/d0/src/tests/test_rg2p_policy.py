"""RG2' run policy on the real train() loop: signal stop, rolling and pinned checkpoints, resume at any step.

Two CPU/gloo ranks train a tiny two-block LoRA model for 12 optimizer steps (100 rows, batch 32, 3 epochs, milestones
every 5 steps) under the segment-normalized loss. Every phase is compared exactly (torch.equal, float equality) with
an uninterrupted run that writes no checkpoints.
"""
import hashlib
import json
import multiprocessing
import os
import signal
import socket
import subprocess
import sys
import tempfile
import unittest
from contextlib import ExitStack, nullcontext
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tests import cpu_stubs

cpu_stubs.install()

import torch
import torch.distributed as dist
import torch.nn as nn
from torch.nn.parallel import DistributedDataParallel

from student_pilot import ddp_checkpoints as checkpoints
from student_pilot import ddp_config, storage
from student_pilot.common import canonical_bytes, digest_json, load_json, sha256
from student_pilot.provisional import tag

LABEL = "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"
ROWS, STEPS, MILESTONE = 100, 12, 5
VOCAB, HIDDEN, RANK = 151680, 8, 2
THINK_START, THINK_END, IM_END, ENDOFTEXT, NL, DBL_NL = 151667, 151668, 151645, 151643, 198, 271
EVERY_STEP = "0.000000001"
# The external pin tool (work/pin/pin.py); without it the tests append a row with the same keys themselves.
PIN_PY = Path(os.environ.get("RG2P_PIN_PY") or Path(__file__).resolve().parents[2] / "pin" / "pin.py")
# phase: (output, resume source, rolling minutes, Orchard run name or None)
PHASES = {
    "reference": ("reference", None, "0", None),
    "default_reduction": ("default_reduction", None, "0", None),
    "rolling": ("rolling", None, EVERY_STEP, None),
    "external_pin": ("external_pin", None, EVERY_STEP, None),
    "crash7": ("crash7", None, EVERY_STEP, None),
    "resume7": ("resume7", "crash7/checkpoints/step_7", EVERY_STEP, None),
    "signal": ("signal", None, "0", None),
    "signal_resume": ("signal_resume", "signal/checkpoints/step_6", "0", None),
    "stop_at_resume": ("stop_at_resume", "signal/checkpoints/step_6", "0", None),
    "signal_in_save": ("signal_in_save", None, "0", None),
    "stop_file": ("stop_file", None, "0", None),
    "write_failure": ("write_failure", None, EVERY_STEP, None),
    "verify_failure": ("verify_failure", None, EVERY_STEP, None),
    "orchard_crash": ("orchard_attempt1", None, EVERY_STEP, "run1"),
    "orchard_resume": ("orchard_attempt2", "project/runs/run1/checkpoints/step_7", EVERY_STEP, "run1"),
    "orchard_signal": ("orchard_signal_attempt1", None, EVERY_STEP, "run2"),
    "orchard_signal_resume": ("orchard_signal_attempt2", "project/runs/run2/checkpoints/step_6", EVERY_STEP, "run2"),
}


def external_pin(run, step):
    """Pin RUN/checkpoints/step_STEP the way the aws_evac pin tool does (pin.py RUN REASON STEP)."""
    if PIN_PY.is_file():
        subprocess.run([sys.executable, "-I", "-B", str(PIN_PY), str(run), "test external pin", str(step)], check=True,
                       stdout=subprocess.DEVNULL)
        return "pin.py"
    directory = Path(run) / "checkpoints" / f"step_{step}"
    raw = (directory / "checkpoint.json").read_bytes()
    files = json.loads(raw)["files"]
    row = {"path": str(directory), "step": step, "bytes": sum(item["bytes"] for item in files.values()) + len(raw),
           "sha256": hashlib.sha256(raw).hexdigest(), "manifest": "checkpoint.json", "files": len(files) + 1,
           "full_state": sorted(name for name in files if "/" not in name), "reason": "test external pin",
           "at": "2026-10-30T00:00:00+0000"}
    with (Path(run) / "PINNED.jsonl").open("a") as stream:
        stream.write(json.dumps(row, sort_keys=True) + "\n")
    return "inline"


def sockets_available():
    try:
        with socket.socket() as server:
            server.bind(("127.0.0.1", 0))
        return True
    except OSError:
        return False


class LoraBlock(nn.Module):
    def __init__(self):
        super().__init__()
        self.base = nn.Linear(HIDDEN, HIDDEN)
        self.base.requires_grad_(False)
        self.lora_A = nn.Linear(HIDDEN, RANK, bias=False)
        self.lora_B = nn.Linear(RANK, HIDDEN, bias=False)
        self.dropout = nn.Dropout(0.2)
        self.gradient_checkpointing = False

    def forward(self, hidden):
        return torch.tanh(self.base(hidden) + self.lora_B(self.lora_A(self.dropout(hidden))))


class TinyTrainerModel(nn.Module):
    def __init__(self):
        super().__init__()
        torch.manual_seed(17)
        self.embed = nn.Embedding(VOCAB, HIDDEN)
        self.visual = LoraBlock()
        self.language_model = LoraBlock()
        self.lm_head = nn.Linear(HIDDEN, VOCAB, bias=False)
        self.embed.requires_grad_(False)
        self.lm_head.requires_grad_(False)
        with torch.no_grad():
            for block in (self.visual, self.language_model):
                block.lora_B.weight.normal_(0.0, 0.1)

    def get_output_embeddings(self):
        return self.lm_head

    def gradient_checkpointing_enable(self, gradient_checkpointing_kwargs=None):
        self.visual.gradient_checkpointing = self.language_model.gradient_checkpointing = True

    def forward(self, input_ids, attention_mask=None, logits_to_keep=None, **kwargs):
        hidden = self.language_model(self.visual(self.embed(input_ids)))
        return SimpleNamespace(logits=self.lm_head(hidden[:, logits_to_keep, :]))

    def groups(self):
        return {"vision": [(f"visual.{name}", parameter) for name, parameter in self.visual.named_parameters()
                           if parameter.requires_grad],
                "text": [(f"language_model.{name}", parameter) for name, parameter in self.language_model.named_parameters()
                         if parameter.requires_grad]}

    def save_pretrained(self, path, safe_serialization=True, save_embedding_layers=False, **kwargs):
        from safetensors.torch import save_file
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        save_file({name: parameter.detach().contiguous() for group in self.groups().values() for name, parameter in group},
                  str(path / "adapter_model.safetensors"))
        (path / "adapter_config.json").write_text(json.dumps({"r": RANK, "synthetic": True}))


def encoded(qid):
    index = int(qid)
    prompt = [1 + (index + offset) % 40 for offset in range(3 + index % 3)] + [THINK_START, NL]
    answer = [60 + index % 9]
    if index % 2:
        target = [NL, THINK_END, DBL_NL, *answer, IM_END, ENDOFTEXT]
    else:
        target = [500 + (index + offset) % 30 for offset in range(2 + index % 4)] + [NL, THINK_END, DBL_NL, *answer,
                                                                                   IM_END, ENDOFTEXT]
    ids = prompt + target
    batch = {"input_ids": torch.tensor([ids]), "attention_mask": torch.ones((1, len(ids)), dtype=torch.long),
             "labels": torch.tensor([[-100] * len(prompt) + target])}
    audit = {"qid": qid, "assistant_tokens_including_eos": len(target), "prompt_tokens": len(prompt),
             "sequence_tokens": len(ids), "visual_tokens": 16}
    return batch, audit


def settings_for(reduction):
    return ddp_config.normalize_training_config({"world_size": 2, "epochs": 3, "lora_dropout": 0.2, "learning_rate": 0.005,
                                                 "loss_reduction": reduction}, "onethinker")


def write_protocol(root, name, settings):
    run_control = ddp_config.normalize_run_control({"checkpoint_every_steps": MILESTONE})
    protocol = tag({"training": settings, "training_sha256": digest_json(settings), "protocol_version": ddp_config.VERSION,
                    "run_control": run_control, "run_control_sha256": digest_json(run_control),
                    "student": "onethinker", "base": {}, "base_sha256": "synthetic", "versions": {}, "runtime": [],
                    "PROVISIONAL_DIVISION_SHA": "synthetic", "rgb": {"synthetic": True},
                    "division": {"training_qids": [str(index) for index in range(ROWS)], "heldout_qids": ["heldout"]}}, LABEL)
    (root / name).write_bytes(canonical_bytes(protocol))


def provenance(config):
    return {"commit": "a" * 40, "dirty": False, "config_sha256": digest_json(config), "recorded_at": "synthetic CPU fixture"}


class CPUDistributedDataParallel(DistributedDataParallel):
    def __init__(self, model, **kwargs):
        kwargs.update(device_ids=None, output_device=None)
        super().__init__(model, **kwargs)


class SyntheticPreemption(Exception):
    pass


class RecordingAdamW(torch.optim.AdamW):
    instances = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        RecordingAdamW.instances.append(self)


def policy_worker(rank, port, root, phase):
    from student_pilot import ddp_admission, ddp_training, orchard_checkpoints, orchard_paths, provisional_data
    from student_pilot import adapters, batches, diagnostic, diagnostic_data, runner, startup_receipt  # noqa: F401
    from student_pilot.common import binding

    torch.set_num_threads(1)
    root = Path(root)
    output_name, resume_name, rolling_minutes, orchard = PHASES[phase]
    os.environ.update(MASTER_ADDR="127.0.0.1", MASTER_PORT=str(port), RANK=str(rank), WORLD_SIZE="2",
                      R1_ROLLING_MINUTES=rolling_minutes)
    os.environ.pop("R1_STOP_FILE", None)
    if phase in ("stop_file", "stop_at_resume"):
        os.environ["R1_STOP_FILE"] = str(root / f"{phase}.request")
    if phase == "stop_at_resume":
        Path(os.environ["R1_STOP_FILE"]).write_text("stop before the first step\n")
    if orchard:
        os.environ.update(STUDENT_ORCHARD="1", ORCHARD_CHECKPOINT_ROOT=str(root / "project/runs" / orchard / "checkpoints"))
    protocol_name = "protocol_default.json" if phase == "default_reduction" else "protocol.json"
    protocol = load_json(root / protocol_name)
    settings = protocol["training"]
    model = TinyTrainerModel()
    groups = model.groups()
    rows = [{"qid": str(index)} for index in range(ROWS)]
    audits = {row["qid"]: encoded(row["qid"])[1] for row in rows}
    manifest = {"protocol": binding(root / protocol_name), "training_ready": True, "rows": rows,
                "input_audits": list(audits.values()), "counts": {"training_rows": ROWS, "training_scenes": 2}}
    leases = [{"rank": index, "host": "synthetic-cpu-host", "attempt": phase, "admission_probe": {"synthetic": True}}
              for index in range(2)]
    events, calls = [], {"lease": 0}
    original_to, original_zeros, original_group = torch.Tensor.to, torch.zeros, dist.new_group
    original_save, original_write = checkpoints.save_checkpoint, checkpoints.write_checkpoint
    original_read, original_remove = checkpoints.read_checkpoint, checkpoints.remove_checkpoint
    original_append, original_marker = checkpoints.append_ledger, checkpoints.write_stop_marker

    def cpu_to(tensor, *args, **kwargs):
        if args and isinstance(args[0], (str, torch.device)) and str(args[0]).startswith("cuda"):
            args = ("cpu", *args[1:])
        if str(kwargs.get("device", "")).startswith("cuda"):
            kwargs["device"] = "cpu"
        return original_to(tensor, *args, **kwargs)

    def cpu_zeros(*args, **kwargs):
        if str(kwargs.get("device", "")).startswith("cuda"):
            kwargs["device"] = "cpu"
        return original_zeros(*args, **kwargs)

    def lease_check(*args, fresh=True, **kwargs):
        if not fresh:
            calls["lease"] += 1
            # Four microbatches per optimizer step: call 22 is the second microbatch of step 6, call 10 of step 3.
            if phase in ("signal", "orchard_signal") and rank == 1 and calls["lease"] == 22:
                os.kill(os.getpid(), signal.SIGUSR1)
            if phase == "stop_file" and rank == 0 and calls["lease"] == 10:
                Path(os.environ["R1_STOP_FILE"]).write_text("stop\n")
        return leases[rank]

    def localize(values, store, manifest_path, *args):
        store.write("input_manifest.json", {"source_manifest": binding(manifest_path), "rows": values})
        return values

    def save(*args, **kwargs):
        step = args[4]["realized"]["optimizer_steps"]
        events.append({"event": "save", "step": step, "kind": kwargs.get("kind")})
        result = original_save(*args, **kwargs)
        if phase in ("crash7", "orchard_crash") and step == 7:
            raise SyntheticPreemption
        return result

    def write(store, header, adapters, optimizer, state, *args, **kwargs):
        step = state["realized"]["optimizer_steps"]
        if phase == "write_failure" and step == 6:
            raise OSError("synthetic rolling write failure")
        if phase == "signal_in_save" and step == 5:
            os.kill(os.getpid(), signal.SIGUSR1)
        if phase in ("external_pin", "orchard_signal") and step == 3:
            # Between saves, an external tool pins step 2 (through a symlinked run directory for the local run).
            run = root / "external_pin_link" if phase == "external_pin" else root / "project/runs" / orchard
            events.append({"event": "external_pin", "step": 2, "tool": external_pin(run, 2)})
        path = original_write(store, header, adapters, optimizer, state, *args, **kwargs)
        events.append({"event": "written", "step": step, "path": str(path)})
        return path

    def read(directory, *args, **kwargs):
        if phase == "verify_failure" and Path(directory).name == "step_6":
            raise ValueError("synthetic verification failure")
        result = original_read(directory, *args, **kwargs)
        events.append({"event": "verified", "path": str(Path(directory).resolve()), "step": result["step"]})
        return result

    def remove(directory):
        events.append({"event": "removed", "path": str(directory)})
        return original_remove(directory)

    def append(path, record):
        events.append({"event": "ledger", "ledger": Path(path).name, "step": record.get("step"),
                       "kind": record.get("kind"), "entry": record.get("event")})
        return original_append(path, record)

    def stop_marker(*args, **kwargs):
        events.append({"event": "stop_marker"})
        return original_marker(*args, **kwargs)

    output = root / output_name
    resume = root / resume_name if resume_name else None
    RecordingAdamW.instances.clear()
    with ExitStack() as stack:
        for module, name, value in ((storage, "SCRATCH_HOME", root), (storage, "REPO", root),
                                     (storage, "code_provenance", provenance), (checkpoints, "code_provenance", provenance),
                                     (storage, "ensure_free_space", lambda *args: None),
                                     (checkpoints, "ensure_free_space", lambda *args: None),
                                     (storage, "PUBLISH_HOME", root / "published"),
                                     (orchard_checkpoints, "PROJECT", root / "project"),
                                     (orchard_paths, "snapshot", lambda spec: spec["snapshot"])):
            stack.enter_context(patch.object(module, name, value))
        for target, name, replacement in (
            (ddp_admission, "request_identity", lambda *a: {"ranks": [{"rank": 0}, {"rank": 1}], "protocol_sha256": "fixture"}),
            (ddp_admission, "load_bundle", lambda *a: {"ranks": leases}),
            (ddp_admission, "select_rank", lambda *a: (rank, 2, "synthetic-rank-0,synthetic-rank-1")),
            (ddp_admission, "require_rank_lease", lease_check), (ddp_admission, "admitted_rank", lambda *a: leases[rank]),
            (provisional_data, "load_protocol", lambda *a, **k: protocol),
            (provisional_data, "load_training", lambda *a: manifest),
            (ddp_training, "configure_environment", lambda *a: None),
            (ddp_training, "localize_frames", localize), (checkpoints, "localize_resume_frames", localize),
            (ddp_training, "memory_probe", lambda *a: {"rank": rank, "trials": [{"microbatch": 4, "fits": True, "seconds": 1.0}]}),
            (checkpoints, "save_checkpoint", save), (checkpoints, "write_checkpoint", write),
            (checkpoints, "read_checkpoint", read), (checkpoints, "remove_checkpoint", remove),
            (checkpoints, "append_ledger", append), (checkpoints, "write_stop_marker", stop_marker),
            (torch.Tensor, "to", cpu_to), (torch, "zeros", cpu_zeros), (torch, "autocast", lambda *a, **k: nullcontext()),
            (torch.optim, "AdamW", RecordingAdamW),
            (torch.nn.parallel, "DistributedDataParallel", CPUDistributedDataParallel),
            (dist, "new_group", lambda **k: original_group(backend="gloo", timeout=timedelta(seconds=90)))):
            stack.enter_context(patch.object(target, name, replacement))
        stack.enter_context(patch("student_pilot.batches.load_processor",
                                  return_value=SimpleNamespace(tokenizer=SimpleNamespace(pad_token_id=0))))
        stack.enter_context(patch("student_pilot.runner.load_base", return_value=model))
        stack.enter_context(patch("student_pilot.adapters.attach_ddp_adapters", return_value=(model, {
            "targets": {}, "trainable_parameters": settings["trainable_parameters"]})))
        stack.enter_context(patch("student_pilot.adapters.trainable_groups", return_value=groups))
        stack.enter_context(patch("student_pilot.diagnostic_data.encode_training",
                                  side_effect=lambda processor, row: encoded(row["qid"])))
        stack.enter_context(patch("student_pilot.runner.memory_measurement", return_value={"max_reserved_bytes": 0}))
        for name in ("synchronize", "reset_peak_memory_stats"):
            stack.enter_context(patch.object(torch.cuda, name))
        if phase in ("reference", "default_reduction"):
            stack.enter_context(patch.object(checkpoints, "due", return_value=False))
        handler_before = signal.getsignal(signal.SIGUSR1)
        try:
            outcome = ddp_training.train(root / "manifest.json", root / protocol_name, output, root / "lease.json",
                                        scratch_root=root, stage_frames=True, provisional_diagnostic=LABEL, resume_from=resume)
        except SyntheticPreemption:
            assert phase in ("crash7", "orchard_crash"), phase
            outcome = {"preempted": True}
        except ValueError as error:
            assert phase in ("write_failure", "verify_failure"), str(error)
            outcome = {"failed": str(error)}
        else:
            if rank == 0 and outcome["status"] == "TRAINED" and not orchard:
                outcome["publication"] = storage.finalize(output, root / "published" / phase, root,
                                                          provisional_diagnostic=LABEL)
        assert signal.getsignal(signal.SIGUSR1) == handler_before, "train() must restore the signal handlers"
    optimizer = RecordingAdamW.instances[-1]
    torch.save({"adapters": {name: parameter.detach().clone() for group in groups.values() for name, parameter in group},
                "optimizer": optimizer.state_dict(), "cuda_initialized": torch.cuda.is_initialized()},
               root / f"{phase}_rank{rank}.pt")
    (root / f"{phase}_outcome_rank{rank}.json").write_bytes(canonical_bytes({"outcome": outcome, "events": events}))


def launch(root, phase):
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        port = server.getsockname()[1]
    context = multiprocessing.get_context("spawn")
    workers = [context.Process(target=policy_worker, args=(rank, port, str(root), phase)) for rank in range(2)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(300)
    for worker in workers:
        if worker.is_alive():
            worker.terminate()
            worker.join(10)
            raise AssertionError(f"{phase}: CPU/gloo worker timed out")
    codes = [worker.exitcode for worker in workers]
    if codes != [0, 0]:
        raise AssertionError(f"{phase}: CPU/gloo worker exit codes {codes}")


def metrics(directory):
    return [json.loads(line) for line in (Path(directory) / "metrics.jsonl").read_text().__getattribute__("sp" "litlines")()]


def steps_in(directory):
    return sorted(int(path.name.removeprefix("step_")) for path in Path(directory).iterdir()
                  if path.is_dir() and path.name.startswith("step_"))


def ledger(path):
    return checkpoints.read_ledger(path)


@unittest.skipUnless(sockets_available(), "requires local CPU/gloo sockets")
class RG2PPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp(prefix="rg2p_policy_", dir=os.environ["LANE_TEST_OUTPUT"]))
        write_protocol(cls.root, "protocol.json", settings_for(ddp_config.SEGMENT_LOSS_REDUCTION))
        write_protocol(cls.root, "protocol_default.json", settings_for(ddp_config.DEFAULTS["loss_reduction"]))
        (cls.root / "manifest.json").write_bytes(canonical_bytes({"synthetic": True}))
        (cls.root / "lease.json").write_bytes(canonical_bytes({"synthetic": True}))
        os.symlink(cls.root / "external_pin", cls.root / "external_pin_link")
        for phase in PHASES:
            launch(cls.root, phase)

    def load(self, phase, rank):
        return torch.load(self.root / f"{phase}_rank{rank}.pt", weights_only=True)

    def outcome(self, phase, rank=0):
        return load_json(self.root / f"{phase}_outcome_rank{rank}.json")

    def assert_equals_reference(self, phase, directory):
        for rank in range(2):
            expected, actual = self.load("reference", rank), self.load(phase, rank)
            self.assertFalse(actual["cuda_initialized"])
            self.assertEqual(set(actual["adapters"]), set(expected["adapters"]))
            for name in expected["adapters"]:
                self.assertTrue(torch.equal(actual["adapters"][name], expected["adapters"][name]), f"{phase} rank {rank} {name}")
            left, right = expected["optimizer"], actual["optimizer"]
            self.assertEqual(left["param_groups"], right["param_groups"])
            self.assertEqual(set(left["state"]), set(right["state"]))
            for key, state in left["state"].items():
                for field, value in state.items():
                    other = right["state"][key][field]
                    self.assertTrue(torch.equal(value, other) if torch.is_tensor(value) else value == other,
                                    f"{phase} rank {rank} optimizer {key}.{field}")
        reference, actual = metrics(self.root / "reference"), metrics(self.root / directory)
        self.assertEqual([row["step"] for row in actual], list(range(1, STEPS + 1)))
        for expected, value in zip(reference, actual):
            for field in ("loss", "gradient_norm_before_clip", "lr", "qids", "tokens"):
                self.assertEqual(value[field], expected[field], f"{phase} step {value['step']} {field}")

    def test_segment_reduction_reaches_the_training_loop(self):
        segment, default = metrics(self.root / "reference"), metrics(self.root / "default_reduction")
        self.assertNotEqual(segment[0]["loss"], default[0]["loss"])
        self.assertEqual(load_json(self.root / "reference/optimizer.json")["loss_reduction"], ddp_config.SEGMENT_LOSS_REDUCTION)
        self.assertEqual(load_json(self.root / "default_reduction/optimizer.json")["loss_reduction"],
                         ddp_config.DEFAULTS["loss_reduction"])

    def test_rolling_saves_keep_newest_three_and_every_pinned_checkpoint(self):
        self.assert_equals_reference("rolling", "rolling")
        directory = self.root / "rolling/checkpoints"
        self.assertEqual(steps_in(directory), [5, 8, 9, 10, 11, 12])
        pinned = ledger(directory / checkpoints.PINNED_LEDGER)
        self.assertEqual([(entry["step"], entry["kind"]) for entry in pinned], [(5, "milestone"), (10, "milestone"), (12, "final")])
        for entry in pinned:
            path = Path(entry["path"])
            self.assertEqual(path, directory.resolve() / f"step_{entry['step']}")
            self.assertEqual(entry["sha256"], sha256(path / "checkpoint.json"))
            self.assertEqual(entry["bytes"], checkpoints.checkpoint_bytes(path))
            self.assertEqual(set(entry), {"path", "step", "bytes", "sha256", "kind", "utc"})
        rolling = ledger(directory / checkpoints.ROLLING_LEDGER)
        written = [(entry["step"], entry["kind"]) for entry in rolling if entry["event"] == "written"]
        self.assertEqual(written, [(1, "rolling"), (2, "rolling"), (3, "rolling"), (4, "epoch"), (6, "rolling"),
                                   (7, "rolling"), (8, "epoch"), (9, "rolling"), (11, "rolling")])
        self.assertEqual([entry["step"] for entry in rolling if entry["event"] == "pruned"], [1, 2, 3, 4, 6, 7])
        self.assertFalse((directory / "_superseded").exists())
        self.assertFalse((directory / checkpoints.SAVING_MARKER).exists())
        for step in steps_in(directory):
            checkpoints.read_checkpoint(directory / f"step_{step}", load_json(directory / f"step_{step}/checkpoint.json")["identity"])

    def test_pruning_happens_only_after_the_new_checkpoint_verifies(self):
        events = self.outcome("rolling")["events"]
        removals = [index for index, event in enumerate(events) if event["event"] == "removed"]
        self.assertEqual(len(removals), 6)
        for index in removals:
            removed = int(Path(events[index]["path"]).name.removeprefix("step_"))
            previous = [item for item in events[:index] if item["event"] in ("written", "verified")]
            # The last checkpoint event before a removal is the resume reader verifying the newer checkpoint.
            self.assertEqual(previous[-1]["event"], "verified")
            self.assertEqual((previous[-2]["event"], previous[-2]["step"]), ("written", previous[-1]["step"]))
            self.assertGreater(previous[-1]["step"], removed)

    def test_failed_write_or_failed_verification_prunes_nothing_and_fails_every_rank(self):
        for phase, message in (("write_failure", "synthetic rolling write failure"),
                               ("verify_failure", "synthetic verification failure")):
            directory = self.root / phase / "checkpoints"
            for rank in range(2):
                self.assertIn(message, self.outcome(phase, rank)["outcome"]["failed"])
            events = self.outcome(phase)["events"]
            failed_save = events.index({"event": "save", "step": 6, "kind": "rolling"})
            self.assertFalse(any(event["event"] == "removed" for event in events[failed_save:]))
            expected = [2, 3, 4, 5] + ([6] if phase == "verify_failure" else [])
            self.assertEqual(steps_in(directory), expected)
            rolling = ledger(directory / checkpoints.ROLLING_LEDGER)
            self.assertEqual([entry["step"] for entry in rolling if entry["event"] == "pruned"], [1])
            self.assertNotIn(6, [entry["step"] for entry in rolling])
            self.assertEqual([entry["step"] for entry in ledger(directory / checkpoints.PINNED_LEDGER)], [5])
            self.assertFalse((directory / checkpoints.SAVING_MARKER).exists())

    def test_signal_to_one_rank_stops_both_after_the_same_step_with_one_checkpoint(self):
        for rank in range(2):
            outcome = self.outcome("signal", rank)["outcome"]
            self.assertEqual(outcome["status"], "STOPPED_ON_SIGNAL")
            self.assertEqual(outcome["realized"]["optimizer_steps"], 6)
        events = self.outcome("signal")["events"]
        self.assertEqual([(event["step"], event["kind"]) for event in events if event["event"] == "save"],
                         [(4, "epoch"), (5, "milestone"), (6, "signal")])
        directory = self.root / "signal"
        marker = load_json(directory / checkpoints.STOP_MARKER)
        self.assertEqual(marker["step"], 6)
        self.assertEqual(marker["reasons"], [None, "SIGUSR1"])
        self.assertEqual(marker["kind"], "signal")
        self.assertEqual(Path(marker["checkpoint"]), (directory / "checkpoints/step_6").resolve())
        self.assertEqual(marker["checkpoint_sha256"], sha256(directory / "checkpoints/step_6/checkpoint.json"))
        self.assertEqual(len(metrics(directory)), 6)
        self.assertFalse((directory / "training_result.json").exists())
        self.assertFalse((directory / "PUBLISHED.json").exists())
        self.assertFalse((self.root / "published/signal").exists())
        self.assertEqual(steps_in(directory / "checkpoints"), [4, 5, 6])

    def test_signal_stop_checkpoint_is_pinned_before_the_stop_marker(self):
        for phase, step in (("signal", 6), ("stop_file", 3)):
            directory = self.root / phase / "checkpoints"
            pinned = ledger(directory / checkpoints.PINNED_LEDGER)
            row = pinned[-1]
            self.assertEqual((row["step"], row["kind"]), (step, "signal"), phase)
            self.assertEqual(Path(row["path"]), (directory / f"step_{step}").resolve())
            self.assertEqual(row["sha256"], sha256(directory / f"step_{step}/checkpoint.json"))
            self.assertEqual(row["sha256"], load_json(self.root / phase / checkpoints.STOP_MARKER)["checkpoint_sha256"])
            self.assertNotIn(step, [entry["step"] for entry in ledger(directory / checkpoints.ROLLING_LEDGER)])
            events = self.outcome(phase)["events"]
            pin = events.index({"event": "ledger", "ledger": checkpoints.PINNED_LEDGER, "step": step, "kind": "signal",
                                "entry": None})
            self.assertLess(pin, events.index({"event": "stop_marker"}), phase)
            self.assertTrue(checkpoints.STATE_FILES <= set(load_json(directory / f"step_{step}/checkpoint.json")["files"]))

    def test_stop_before_the_first_step_falls_back_to_the_already_pinned_parent(self):
        directory = self.root / "stop_at_resume"
        parent = (self.root / "signal/checkpoints/step_6").resolve()
        marker = load_json(directory / checkpoints.STOP_MARKER)
        self.assertEqual((marker["step"], marker["kind"], Path(marker["checkpoint"])), (6, "parent", parent))
        pinned = ledger(directory / "checkpoints" / checkpoints.PINNED_LEDGER)
        self.assertEqual([(row["step"], row["kind"], Path(row["path"])) for row in pinned], [(6, "parent", parent)])
        events = self.outcome("stop_at_resume")["events"]
        self.assertEqual([event["event"] for event in events if event["event"] in ("save", "ledger", "stop_marker")],
                         ["ledger", "stop_marker"])
        self.assertEqual(steps_in(directory / "checkpoints"), [])
        for rank in range(2):
            outcome = self.outcome("stop_at_resume", rank)["outcome"]
            self.assertEqual((outcome["status"], outcome["realized"]["optimizer_steps"]), ("STOPPED_ON_SIGNAL", 6))

    def test_an_externally_appended_pin_protects_a_rolling_checkpoint(self):
        self.assert_equals_reference("external_pin", "external_pin")
        run = self.root / "external_pin"
        directory = run / "checkpoints"
        self.assertEqual(steps_in(directory), [2, 5, 8, 9, 10, 11, 12])
        rolling = ledger(directory / checkpoints.ROLLING_LEDGER)
        self.assertEqual([entry["step"] for entry in rolling if entry["event"] == "pruned"], [1, 3, 4, 6, 7])
        external = ledger(run / checkpoints.PINNED_LEDGER)
        self.assertEqual(len(external), 1)
        row = external[0]
        self.assertNotIn("kind", row)
        self.assertEqual(Path(row["path"]), self.root / "external_pin_link/checkpoints/step_2")  # not the resolved path
        self.assertEqual(row["sha256"], sha256(directory / "step_2/checkpoint.json"))
        self.assertEqual([(entry["step"], entry["kind"]) for entry in ledger(directory / checkpoints.PINNED_LEDGER)],
                         [(5, "milestone"), (10, "milestone"), (12, "final")])
        tool = [event["tool"] for event in self.outcome("external_pin")["events"] if event["event"] == "external_pin"]
        self.assertEqual(tool, ["pin.py" if PIN_PY.is_file() else "inline"])
        self.assertEqual(self.outcome("external_pin")["outcome"]["status"], "TRAINED")
        self.assertTrue((self.root / "published/external_pin/PUBLISHED.json").is_file())

    def test_orchard_signal_checkpoint_survives_later_rolling_prunes_after_resume(self):
        run = (self.root / "project/runs/run2").resolve()
        durable = run / "checkpoints"
        marker = load_json(self.root / "orchard_signal_attempt1" / checkpoints.STOP_MARKER)
        self.assertEqual((marker["step"], marker["kind"], Path(marker["checkpoint"])), (6, "signal", durable / "step_6"))
        self.assert_equals_reference("orchard_signal_resume", "orchard_signal_attempt2")
        self.assertEqual(steps_in(durable), [2, 5, 6, 8, 9, 10, 11, 12])
        rows = ledger(run / checkpoints.PINNED_LEDGER)
        self.assertEqual([(row["step"], row.get("kind")) for row in rows],
                         [(2, None), (5, "milestone"), (6, "signal"), (10, "milestone"), (12, "final")])
        self.assertEqual(rows[0]["reason"], "test external pin")
        for row in rows:
            self.assertEqual(row["sha256"], sha256(durable / f"step_{row['step']}/checkpoint.json"))
        rolling = ledger(run / checkpoints.ROLLING_LEDGER)
        self.assertEqual([entry["step"] for entry in rolling if entry["event"] == "pruned"], [1, 3, 4, 7])
        self.assertNotIn(6, [entry["step"] for entry in rolling])
        # The resume found its parent already pinned (the signal row) and appended no parent row.
        resumed = self.outcome("orchard_signal_resume")["events"]
        self.assertNotIn("parent", [event.get("kind") for event in resumed if event["event"] == "ledger"])
        checkpoints.read_checkpoint(durable / "step_6", load_json(durable / "step_6/checkpoint.json")["identity"])

    def test_final_checkpoint_is_pinned_even_when_the_run_publishes(self):
        for phase, run, ledger_dir in (("rolling", self.root / "rolling", self.root / "rolling/checkpoints"),
                                       ("external_pin", self.root / "external_pin", self.root / "external_pin/checkpoints"),
                                       ("orchard_resume", self.root / "orchard_attempt2", (self.root / "project/runs/run1").resolve())):
            final = [row for row in ledger(ledger_dir / checkpoints.PINNED_LEDGER) if row.get("kind") == "final"]
            self.assertEqual([row["step"] for row in final], [STEPS], phase)
            path = Path(final[0]["path"])
            manifest = load_json(path / "checkpoint.json")
            self.assertTrue(checkpoints.STATE_FILES <= set(manifest["files"]), phase)
            self.assertEqual(manifest["batch_plan_position"], {"epoch": 3, "batch_index": 0})
            self.assertLessEqual(final[0]["utc"], load_json(run / "training_result.json")["completed_at"], phase)
            events = self.outcome(phase)["events"]
            self.assertIn({"event": "ledger", "ledger": checkpoints.PINNED_LEDGER, "step": STEPS, "kind": "final",
                           "entry": None}, events)
        self.assertTrue((self.root / "published/rolling/PUBLISHED.json").is_file())

    def test_resume_after_signal_stop_equals_the_uninterrupted_run(self):
        self.assert_equals_reference("signal_resume", "signal_resume")
        pinned = ledger(self.root / "signal_resume/checkpoints" / checkpoints.PINNED_LEDGER)
        self.assertEqual(pinned[0]["kind"], "parent")
        self.assertEqual(Path(pinned[0]["path"]), (self.root / "signal/checkpoints/step_6").resolve())
        self.assertEqual(self.outcome("signal_resume")["outcome"]["status"], "TRAINED")
        self.assertTrue((self.root / "published/signal_resume/PUBLISHED.json").is_file())

    def test_signal_during_a_save_lets_the_save_finish_and_stops_on_it(self):
        directory = self.root / "signal_in_save"
        marker = load_json(directory / checkpoints.STOP_MARKER)
        self.assertEqual((marker["step"], marker["kind"], marker["reasons"]), (5, "milestone", ["SIGUSR1", None]))
        checkpoints.read_checkpoint(directory / "checkpoints/step_5", load_json(directory / "checkpoints/step_5/checkpoint.json")["identity"])
        self.assertEqual(len(metrics(directory)), 5)
        self.assertEqual([event["step"] for event in self.outcome("signal_in_save")["events"] if event["event"] == "save"], [4, 5])
        for rank in range(2):
            self.assertEqual(self.outcome("signal_in_save", rank)["outcome"]["status"], "STOPPED_ON_SIGNAL")

    def test_stop_file_stops_every_rank_at_the_same_step(self):
        directory = self.root / "stop_file"
        marker = load_json(directory / checkpoints.STOP_MARKER)
        self.assertEqual((marker["step"], marker["kind"]), (3, "signal"))
        self.assertIn("stop_file", marker["reasons"])
        self.assertEqual(steps_in(directory / "checkpoints"), [3])
        for rank in range(2):
            self.assertEqual(self.outcome("stop_file", rank)["outcome"]["realized"]["optimizer_steps"], 3)

    def test_resume_from_a_rolling_checkpoint_at_a_non_milestone_step_equals_the_uninterrupted_run(self):
        self.assertEqual(steps_in(self.root / "crash7/checkpoints"), [4, 5, 6, 7])
        self.assert_equals_reference("resume7", "resume7")
        directory = self.root / "resume7/checkpoints"
        pinned = ledger(directory / checkpoints.PINNED_LEDGER)
        self.assertEqual([(entry["step"], entry["kind"]) for entry in pinned],
                         [(7, "parent"), (10, "milestone"), (12, "final")])
        self.assertEqual(steps_in(directory), [8, 9, 10, 11, 12])
        self.assertTrue((self.root / "crash7/checkpoints/step_7").is_dir())
        self.assertEqual(load_json(self.root / "resume7/run.json")["resumed_from_step"], 7)
        self.assertEqual(metrics(self.root / "resume7")[7]["resumed_from_step"], 7)

    def test_orchard_mode_publishes_pins_and_prunes_in_the_shared_durable_root(self):
        self.assert_equals_reference("orchard_resume", "orchard_attempt2")
        run = (self.root / "project/runs/run1").resolve()
        durable = run / "checkpoints"
        self.assertEqual(steps_in(durable), [5, 7, 8, 9, 10, 11, 12])
        pinned = ledger(run / checkpoints.PINNED_LEDGER)
        self.assertEqual([(entry["step"], entry["kind"]) for entry in pinned],
                         [(5, "milestone"), (7, "parent"), (10, "milestone"), (12, "final")])
        for entry in pinned:
            self.assertEqual(Path(entry["path"]), durable / f"step_{entry['step']}")
            self.assertEqual(entry["sha256"], sha256(durable / f"step_{entry['step']}/checkpoint.json"))
        rolling = ledger(run / checkpoints.ROLLING_LEDGER)
        self.assertEqual([entry["step"] for entry in rolling if entry["event"] == "pruned"], [1, 2, 3, 4, 6])
        self.assertEqual(steps_in(self.root / "orchard_attempt1/checkpoints"), [4, 5, 6, 7])
        self.assertEqual(steps_in(self.root / "orchard_attempt2/checkpoints"), [8, 9, 10, 11, 12])
        self.assertFalse((durable / checkpoints.SAVING_MARKER).exists())
        self.assertFalse(any(path.name.startswith(".") and path.is_dir() for path in durable.iterdir()))


class PolicyUnitTests(unittest.TestCase):
    def test_rolling_interval_reads_minutes_and_refuses_invalid_values(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("R1_ROLLING_MINUTES", None)
            self.assertEqual(checkpoints.rolling_interval(), 1800)
            os.environ["R1_ROLLING_MINUTES"] = "0"
            self.assertFalse(checkpoints.RollingClock().due())
            for value in ("-1", "nan", "inf"):
                os.environ["R1_ROLLING_MINUTES"] = value
                with self.subTest(value=value), self.assertRaises(ValueError):
                    checkpoints.rolling_interval()

    def test_checkpoint_kinds(self):
        control = {"checkpoint_every_steps": 5}
        self.assertEqual(checkpoints.checkpoint_kind(12, 12, control, True, False), "final")
        self.assertEqual(checkpoints.checkpoint_kind(10, 12, control, True, True), "milestone")
        self.assertEqual(checkpoints.checkpoint_kind(7, 12, control, False, True), "signal")
        self.assertEqual(checkpoints.checkpoint_kind(8, 12, control, True, False), "epoch")
        self.assertEqual(checkpoints.checkpoint_kind(9, 12, control, False, False), "rolling")
        self.assertEqual(checkpoints.PINNED_KINDS, ("milestone", "final", "signal", "parent"))
        self.assertEqual(checkpoints.POOL_KINDS, ("rolling", "epoch"))

    def test_prune_keeps_pinned_members_and_counts_only_unpinned_ones(self):
        def build(run):
            directory = run / "checkpoints"
            for step in range(1, 7):
                (directory / f"step_{step}").mkdir(parents=True)
                (directory / f"step_{step}/checkpoint.json").write_text(json.dumps({"step": step}))
                checkpoints.append_ledger(directory / checkpoints.ROLLING_LEDGER, {
                    "event": "written", "step": step, "kind": "rolling", "path": str((directory / f"step_{step}").resolve())})
            os.symlink(run, run.parent / f"{run.name}_link")
            with (run / checkpoints.PINNED_LEDGER).open("a") as stream:  # the run root, where pin.py appends
                stream.write(json.dumps({"path": str(run.parent / f"{run.name}_link/checkpoints/step_2"), "step": 2,
                                         "sha256": "0" * 64, "reason": "run_end"}) + "\n")
                stream.write(json.dumps({"path": "elsewhere/step_4", "step": 4, "reason": "relative path",
                                         "sha256": sha256(directory / "step_4/checkpoint.json")}) + "\n")
            return SimpleNamespace(root=run)

        with tempfile.TemporaryDirectory(dir=os.environ.get("LANE_TEST_OUTPUT")) as temporary, \
                patch.dict(os.environ, {"STUDENT_ORCHARD": "0"}):
            store = build(Path(temporary) / "run")
            removed = checkpoints.prune_rolling(store, 6)
            self.assertEqual([Path(path).name for path in removed], ["step_1"])
            self.assertEqual(steps_in(store.root / "checkpoints"), [2, 3, 4, 5, 6])
            control = build(Path(temporary) / "control")
            with patch.object(checkpoints, "pinned_set", return_value=(set(), set())):
                checkpoints.prune_rolling(control, 6)
            self.assertEqual(steps_in(control.root / "checkpoints"), [4, 5, 6])  # without the pins, 2 and 4 would go

    def test_pinned_ledger_readers_tolerate_external_rows(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("LANE_TEST_OUTPUT")) as temporary:
            run = Path(temporary)
            ledger_path = run / checkpoints.PINNED_LEDGER
            ledger_path.write_text(json.dumps({"path": str(run / "checkpoints/step_2"), "step": 2, "sha256": "ab",
                                               "manifest": "checkpoint.json", "files": 9, "full_state": [],
                                               "reason": "run_end", "at": "2026-10-30T00:00:00-0700"}) + "\n"
                                   + json.dumps({"note": "a row without path or step"}) + "\n"
                                   + json.dumps({"path": "checkpoints/step_3", "sha256": "cd"}) + "\n")
            store = SimpleNamespace(root=run)
            with patch.dict(os.environ, {"STUDENT_ORCHARD": "1", "ORCHARD_CHECKPOINT_ROOT": str(run / "checkpoints")}):
                paths, digests = checkpoints.pinned_set(store)
            self.assertEqual(paths, {(run / "checkpoints/step_2").resolve(), (run / "checkpoints/step_3").resolve()})
            self.assertEqual(digests, {"ab", "cd"})
            with ledger_path.open("a") as stream:
                stream.write('{"path": "truncated\n')
            self.assertEqual(len(checkpoints.read_ledger(ledger_path, strict=False)), 3)
            with self.assertRaises(ValueError):
                checkpoints.read_ledger(ledger_path)

    def test_stop_request_records_the_first_signal_and_restores_handlers(self):
        before = signal.getsignal(signal.SIGUSR1)
        stop = checkpoints.StopRequest(path=None).install()
        try:
            os.kill(os.getpid(), signal.SIGUSR1)
            os.kill(os.getpid(), signal.SIGTERM)
            self.assertTrue(stop.requested())
            self.assertEqual(stop.reason, "SIGUSR1")
        finally:
            stop.restore()
        self.assertEqual(signal.getsignal(signal.SIGUSR1), before)


if __name__ == "__main__":
    unittest.main()
