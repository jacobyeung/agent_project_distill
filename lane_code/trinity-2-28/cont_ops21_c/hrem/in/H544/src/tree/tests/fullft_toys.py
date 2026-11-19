"""Tiny native Qwen3.5 / Qwen3-VL bases and a CPU/gloo harness that runs ddp_training.train with full_ft."""
import json
import os
import signal
from contextlib import ExitStack, nullcontext
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import torch
import torch.distributed as dist

from student_pilot import ddp_checkpoints as checkpoints
from student_pilot import ddp_core, ddp_training, fsdp_training, full_ft, storage
from student_pilot.common import canonical_bytes, load_json
from tests import test_ddp_models
from tests.test_ddp_checkpoints import SyntheticPreemption, storage_patches
from tests.test_geometry_training import LABEL, ROWS, student_row


def tiny_base(student="qwen35", dtype=torch.bfloat16, seed=17):
    """The same tiny architecture as test_ddp_models' fixture, without PEFT: the plain base a full-FT run loads."""
    from transformers import Qwen3VLConfig, Qwen3_5Config
    from student_pilot.students import model_class

    torch.manual_seed(seed)
    text = {"vocab_size": 64, "hidden_size": 16, "intermediate_size": 32, "num_hidden_layers": 2,
            "num_attention_heads": 2, "num_key_value_heads": 1, "head_dim": 8, "use_cache": False,
            "pad_token_id": 0, "rope_parameters": {"rope_type": "default", "rope_theta": 10000.0,
                                                    "mrope_section": [1, 1, 2], "partial_rotary_factor": 1.0}}
    vision = {"depth": 1, "hidden_size": 16, "intermediate_size": 32, "num_heads": 2, "out_hidden_size": 16,
              "num_position_embeddings": 16, "patch_size": 2, "temporal_patch_size": 2, "spatial_merge_size": 2,
              "deepstack_visual_indexes": [0] if student == "onethinker" else []}
    if student == "qwen35":
        text.update(layer_types=["linear_attention", "full_attention"], linear_key_head_dim=4,
                    linear_value_head_dim=4, linear_num_key_heads=2, linear_num_value_heads=4)
    cls = Qwen3VLConfig if student == "onethinker" else Qwen3_5Config
    config = cls(text_config=text, vision_config=vision, image_token_id=60, video_token_id=61,
                 vision_start_token_id=62, vision_end_token_id=63)
    for item in (config, config.text_config, config.vision_config):
        item._attn_implementation = "sdpa"
    config.use_cache = False
    model = model_class(student)(config).to(dtype)
    model.requires_grad_(False)
    return model


def source_rows():
    return test_ddp_models.NativeMultimodalBatchTests.fixture("qwen35")[3]


def bf16_batch(batch):
    return {key: value.to(torch.bfloat16) if value.is_floating_point() else value for key, value in batch.items()}


def local_trainables(model):
    """Each rank's trainable tensors (local FSDP shards for base groups) by clean name."""
    return {full_ft.clean_name(name): parameter.detach().clone() for name, parameter in model.named_parameters()
            if parameter.requires_grad}


OUTPUTS = {"partial": "interrupted", "resume": "interrupted", "signal": "signalled", "signal_resume": "signalled",
           "tampered_resume": "tampered"}
RESUME_FROM = {"resume": "interrupted/checkpoints", "signal_resume": "signalled/checkpoints",
               "tampered_resume": "tampered_checkpoint"}


def full_training_worker(rank, port, root, phase, interrupt_step=1):
    """One rank of ddp_training.train on the tiny base (CPU/gloo): reference, partial (stops after interrupt_step's
    checkpoint) or resume (from that checkpoint); signal (rank 1 receives SIGUSR1 after optimizer step interrupt_step,
    and the trainer's own graceful stop saves and pins that step) or signal_resume (from the signal checkpoint)."""
    from student_pilot import ddp_admission, provisional_data
    from student_pilot.common import binding

    torch.set_num_threads(1)
    root = Path(root)
    protocol = load_json(root / "protocol.json")
    settings = protocol["training"]
    model = tiny_base()
    source = source_rows()
    rows = [student_row(index) for index in range(ROWS)]
    audits = {}
    for row in rows:
        batch = source[int(row["qid"]) % len(source)]
        target = int((batch["labels"] != -100).sum())
        sequence = batch["labels"].numel()
        audits[row["qid"]] = {"qid": row["qid"], "assistant_tokens_including_eos": target, "prompt_tokens": sequence - target,
                              "sequence_tokens": sequence, "visual_tokens": 16, "video_grid_thw": [[16, 2, 2]]}
    manifest = {"protocol": binding(root / "protocol.json"), "training_ready": True, "rows": rows,
                "input_audits": list(audits.values()), "counts": {"training_rows": ROWS, "training_scenes": 2}}
    leases = [{"rank": index, "host": "synthetic-cpu-host", "attempt": phase, "admission_probe": {"synthetic": True}}
              for index in range(2)]
    events = {"losses": [], "restored": False}
    original_to, original_zeros, original_group = torch.Tensor.to, torch.zeros, dist.new_group
    original_full_save, original_full_restore = checkpoints.save_full_checkpoint, checkpoints.restore_full_checkpoint
    original_save = checkpoints.save_checkpoint
    original_full_wrap, original_wrap = full_ft.wrap_full_model, fsdp_training.wrap_model
    original_agree = checkpoints.agree
    steps_seen = [0]

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

    def stop_after(result, state):
        if phase == "partial" and state["realized"]["optimizer_steps"] == interrupt_step:
            raise SyntheticPreemption
        return result

    def full_save(store, header, trainables, optimizer, state, *args, **kwargs):
        return stop_after(original_full_save(store, header, trainables, optimizer, state, *args, **kwargs), state)

    def save(*args, **kwargs):
        return stop_after(original_save(*args, **kwargs), args[4])

    def agree(rank_, stop, rolling=None):
        if rolling is not None:  # the per-step decision, after optimizer step steps_seen
            steps_seen[0] += 1
            if phase == "signal" and rank == 1 and steps_seen[0] == interrupt_step:
                os.kill(os.getpid(), signal.SIGUSR1)
        return original_agree(rank_, stop, rolling)

    def full_restore(*args, **kwargs):
        events["restored"] = True
        return original_full_restore(*args, **kwargs)

    def full_wrap(model, replicated, process_group, device, **kwargs):
        return original_full_wrap(model, replicated, process_group, torch.device("cpu"), **kwargs)

    def wrap(model, parameters, process_group, device, **kwargs):
        return original_wrap(model, parameters, process_group, torch.device("cpu"), mixed_precision=True, **kwargs)

    output = root / OUTPUTS.get(phase, phase)
    resume = root / RESUME_FROM[phase] / f"step_{interrupt_step}" if phase in RESUME_FROM else None
    with ExitStack() as stack:
        stack.enter_context(patch.dict(os.environ, {"MASTER_ADDR": "127.0.0.1", "MASTER_PORT": str(port), "RANK": str(rank),
                                                    "WORLD_SIZE": "2", "R1_ROLLING_MINUTES": os.environ.get(
                                                        "FULLFT_TEST_ROLLING_MINUTES", "0")}))
        storage_patches(stack, root)
        stack.enter_context(patch.object(storage, "PUBLISH_HOME", root / "published"))
        for target, name, replacement in (
            (ddp_admission, "request_identity", lambda *a: {"ranks": [{"rank": 0}, {"rank": 1}], "protocol_sha256": "fixture"}),
            (ddp_admission, "load_bundle", lambda *a: {"ranks": leases}),
            (ddp_admission, "select_rank", lambda *a: (rank, 2, "synthetic-rank-0,synthetic-rank-1")),
            (ddp_admission, "require_rank_lease", lambda *a, **k: leases[rank]),
            (ddp_admission, "admitted_rank", lambda *a: leases[rank]),
            (provisional_data, "load_protocol", lambda *a, **k: protocol),
            (provisional_data, "load_training", lambda *a: manifest),
            (ddp_training, "configure_environment", lambda *a: None),
            (ddp_training, "localize_frames", lambda values, store, path, *a: (store.write("input_manifest.json", {
                "source_manifest": binding(path), "rows": values}), values)[1]),
            (checkpoints, "localize_resume_frames", lambda values, store, path, *a: values),
            (ddp_training, "memory_probe", lambda *a, **k: {"rank": rank, "trials": [{"microbatch": 4, "fits": True,
                                                                                     "seconds": 1.0}]}),
            (checkpoints, "save_full_checkpoint", full_save), (checkpoints, "restore_full_checkpoint", full_restore),
            (checkpoints, "save_checkpoint", save), (checkpoints, "agree", agree),
            (full_ft, "wrap_full_model", full_wrap), (fsdp_training, "wrap_model", wrap),
            (torch.Tensor, "to", cpu_to), (torch, "zeros", cpu_zeros),
            (torch, "autocast", lambda *a, **k: nullcontext()),
            (dist, "new_group", lambda **k: original_group(backend="gloo", timeout=timedelta(seconds=90)))):
            stack.enter_context(patch.object(target, name, replacement))
        stack.enter_context(patch("student_pilot.batches.load_processor",
                                  return_value=SimpleNamespace(tokenizer=SimpleNamespace(pad_token_id=0))))
        stack.enter_context(patch("student_pilot.runner.load_base", return_value=model))
        stack.enter_context(patch("student_pilot.diagnostic_data.encode_training", side_effect=lambda processor, row:
            (source[int(row["qid"]) % len(source)], audits[row["qid"]])))
        stack.enter_context(patch("student_pilot.runner.memory_measurement", return_value={"max_reserved_bytes": 0}))
        for name in ("synchronize", "reset_peak_memory_stats"):
            stack.enter_context(patch.object(torch.cuda, name))
        try:
            outcome = ddp_training.train(root / "manifest.json", root / "protocol.json", output, root / f"{phase}_lease.json",
                                         scratch_root=root, stage_frames=True, provisional_diagnostic=LABEL,
                                         resume_from=resume, parallel=settings.get("parallel", "ddp"))
        except SyntheticPreemption:
            assert phase == "partial"
            outcome = {"preempted": True}
        else:
            if rank == 0 and outcome.get("status") != "STOPPED_ON_SIGNAL":
                outcome["publication"] = storage.finalize(output, root / "published" / phase, root, provisional_diagnostic=LABEL)
    geometry = getattr(model, "geometry_input", None)
    torch.save({"trainables": local_trainables(model), "restored": events["restored"],
                "geometry": None if geometry is None else {name: value.detach().clone()
                                                           for name, value in geometry.projector.state_dict().items()},
                "outcome": json.loads(canonical_bytes(outcome))}, root / f"{phase}_rank{rank}.pt")
    assert not torch.cuda.is_initialized()
