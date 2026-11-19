#!/usr/bin/env python3
"""Head-call decode check of an HC/HX v3 smoke milestone on code-aws (1 GPU, inside the evaluator container with the
eval closure as /opt/anyhost_jobs).

1. Publish milestone_STEP with its gated G3T connector (tools/publish_hc_v3.py), admitted with the eval store, carriers
   inserted and head-call decoding.
2. Evaluator run: cpu-check and generate on ITEMS VSI items (default: the first item of each head-call type) with
   --geometry-store-* --carriers insert --headcall decode; per-item call records from headcalls/<qid>.json.
3. Forced-call probe: the same published model, heads and store; each item's decode starts with a scripted pose call
   and a scripted depth call, which the decode loop answers from the real heads (prefill with carriers and geometry),
   then decodes freely. This shows the call path end to end even when a 25-step model emits no call of its own.

usage: hc_v3_decode_check.py RUN_DIR STEP CELL FROZEN STORE_MANIFEST STORE_SHA256 RUNTIME_RECORD [--items q1,q2,...]
       hc_v3_decode_check.py --probe PREFLIGHT ITEMS_JSON OUT_JSON   (step 3, run by step 2's process)
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HEADCALL_TYPES = ("object_abs_distance", "object_rel_distance", "object_rel_direction_easy",
                  "object_rel_direction_medium", "object_rel_direction_hard")


def choose_items(rows, labels):
    chosen = {}
    for row, label in zip(rows, labels):
        kind = label["question_type"]
        if kind in HEADCALL_TYPES and kind not in chosen:
            chosen[kind] = row["qid"]
    order = {row["qid"]: index for index, row in enumerate(rows)}
    return sorted(chosen.values(), key=order.get)  # manifest order: the evaluator refuses any other


def check(args):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('tools/hc_v3_decode_check.py:check')
    sys.path.insert(0, os.environ["ANYHOST_JOBS"])
    import eval_ops_aws
    receipt = eval_ops_aws.stage()
    evaluator = eval_ops_aws.configure()
    os.environ["ANYHOST_NEUTRAL_RUNTIME"] = args.runtime  # this tree's record (evaluator, trainer)
    from student_pilot.common import sha256
    from student_pilot.orchard_eval.contracts import load_generation, load_json, load_jsonl, safe_id
    prepared = Path(receipt["cohorts"]["vsibench_answerable500"]["prepared"])
    run_dir = Path(args.run_dir).resolve()
    pub = run_dir / f"milestone_{args.step}_pubv3"
    env = {**os.environ, "TRAINER": str(evaluator), "PYTHONPATH": f"{evaluator}:{eval_ops_aws.ALIAS}"}
    cam_manifest, cam_sha256 = args.camera_manifest, args.camera_sha256
    if not (pub / "PUBLISHED.json").is_file():
        attempts = sorted(p for p in run_dir.glob("attempt-*") if (p / "adapters.json").is_file())
        if not attempts:
            raise SystemExit(f"No attempt-* with adapters.json under {run_dir}")
        pub_args = [eval_ops_aws.PYTHON, "-B", "-u", str(evaluator / "tools/publish_hc_v3.py"), str(attempts[-1]),
                    str(run_dir / "checkpoints"), args.frozen, str(pub), str(args.step), args.store_manifest,
                    args.store_sha256]
        if cam_manifest and cam_sha256:
            pub_args.extend([cam_manifest, cam_sha256])
        subprocess.run(pub_args, check=True, cwd=evaluator, env=env)
    published = json.loads((pub / "PUBLISHED.json").read_bytes())
    heads_meta = json.loads((pub / "auxiliary_heads.json").read_bytes()) if (pub / "auxiliary_heads.json").is_file() else {}
    if not cam_manifest and heads_meta.get("camera", {}).get("settings", {}).get("g3t_prior"):
        auto_cam = Path(args.store_manifest).resolve().parent / "camera_manifest.jsonl"
        if auto_cam.is_file():
            cam_manifest = str(auto_cam)
            cam_sha256 = sha256(auto_cam)
    adapter = pub / published["adapter_directory"]
    cell = eval_ops_aws.ROOT / "eval/cells" / args.cell
    if cell.exists():
        raise SystemExit(f"{cell} exists; name a new cell")
    cell.mkdir(parents=True)
    _, rows, _ = load_generation(prepared / "generation/manifest.json")
    scoring = load_json(prepared / "scoring/manifest.json")
    labels = load_jsonl(scoring["labels"]["path"])
    items = args.items.split(",") if args.items else choose_items(rows, labels)
    (cell / "items.json").write_text(json.dumps(items) + "\n")
    kinds = {row["qid"]: label["question_type"] for row, label in zip(rows, labels)}
    cli = [eval_ops_aws.PYTHON, "-B", "-u", "-m", "student_pilot.orchard_eval"]
    common = ["--manifest", str(prepared / "generation/manifest.json"), "--model", "qwen35", "--variant", "distilled",
              "--model-root", str(eval_ops_aws.ROOT / "models"), "--adapter", str(adapter),
              "--training-receipt", str(pub / "PUBLISHED.json"), "--artifact-root", str(eval_ops_aws.ROOT / "eval"),
              "--provisional-diagnostic", eval_ops_aws.LABEL, "--geometry-store-manifest", args.store_manifest,
              "--geometry-store-sha256", args.store_sha256,
              *(["--geometry-camera-manifest", cam_manifest, "--geometry-camera-sha256", cam_sha256]
                if cam_manifest and cam_sha256 else []),
              "--carriers", "insert", "--headcall", "decode",
              "--items-file", str(cell / "items.json"), "--allow-distilled-controls"]
    subprocess.run([*cli, "cpu-check", *common, "--output", str(cell / "preflight")], check=True, cwd=evaluator,
                   env={**os.environ, "CUDA_VISIBLE_DEVICES": ""})
    preflight = json.loads((cell / "preflight/preflight.json").read_bytes())
    assert preflight["status"] == "CPU_READY" and not preflight["failures"], preflight
    assert preflight["headcall"] == "decode" and preflight["carriers"] == "insert", preflight
    assert "geometry" in preflight["adapter"], "the published connector is not pinned"
    os.environ["AGENT_COORD_DIR"] = f"/project/community/jjyeung/distill/coord/aws128_eval_{os.environ['SLURM_JOB_ID']}_{args.cell}"
    from student_pilot.orchard_admission import allocation, issue
    from student_pilot.orchard_eval.sharding import shard_work_id
    from student_pilot.provisional import bind_lease
    assert len(allocation()["gpu_indices"]) == 1, "Expected 1 GPU allocation"
    request = {"work_id": shard_work_id(preflight["work_id"], 0, 1), "protocol_sha256": preflight["protocol_sha256"]}
    attempt = cell / f"lease-{os.environ['SLURM_JOB_ID']}-0-{time.time_ns()}"
    paths = issue(request, attempt, eval_ops_aws.LABEL)
    bound = attempt / "bound.json"
    lease = bind_lease(paths[0], bound, eval_ops_aws.LABEL, request["work_id"], request["protocol_sha256"])
    gpu_env = {**os.environ, "CUDA_VISIBLE_DEVICES": lease["gpu_uuid"]}
    subprocess.run([*cli, "generate", *common, "--allow-unpaired-adapter", "--preflight", str(cell / "preflight/preflight.json"),
                    "--coord-root", os.environ["AGENT_COORD_DIR"], "--lease", str(bound), "--output", str(cell / "run"),
                    "--shard-index", "0", "--shard-count", "1"], check=True, cwd=evaluator, env=gpu_env)
    generations = {r["qid"]: r for r in load_jsonl(cell / "run/generations.jsonl")}
    per_item = []
    for qid in items:
        record = load_json(cell / "run/headcalls" / f"{safe_id(qid)}.json")
        per_item.append({"qid": qid, "type": kinds[qid], "status": generations[qid]["status"],
                         "parsed_answer": generations[qid].get("parsed_answer"), "summary": record["summary"],
                         "calls": record["calls"][:6], "generation_head": generations[qid].get("raw_generation", "")[:400]})
    probe_out = cell / "forced_probe.json"
    subprocess.run([eval_ops_aws.PYTHON, "-B", "-u", str(evaluator / "tools/hc_v3_decode_check.py"), "--probe",
                    str(cell / "preflight/preflight.json"), str(cell / "items.json"), str(probe_out)],
                   check=True, cwd=evaluator, env=gpu_env)
    report = {"publication": str(pub), "cell": str(cell), "items": items, "preflight_status": preflight["status"],
              "carriers": preflight["carriers"], "headcall": preflight["headcall"],
              "geometry_pin": {k: preflight["adapter"]["geometry"][k] for k in ("store", "weights")},
              "evaluator_run": per_item, "natural_calls": sum(item["summary"].get("calls", 0) for item in per_item),
              "forced_probe": json.loads(probe_out.read_text())}
    out = run_dir / f"decode_check_{args.cell}.json"
    out.write_text(json.dumps(report, indent=1, sort_keys=True, default=str) + "\n")
    print(json.dumps({key: report[key] for key in ("items", "natural_calls")}, sort_keys=True), flush=True)
    print(json.dumps(report["forced_probe"]["summary"], sort_keys=True), flush=True)


class Forced(object):
    """The model with its first generated tokens scripted (a pose call, then a depth call after the first inserted
    response); afterwards the real logits decide. Attributes (heads, geometry input, camera hooks) resolve on the model."""

    def __init__(self, model, segments, prompt_length, close_id):
        self.model, self.segments, self.prompt_length, self.close = model, segments, prompt_length, close_id
        self.history = []

    def __getattr__(self, name):
        return getattr(self.__dict__["model"], name)

    def __call__(self, **kwargs):
        out = self.model(**kwargs)
        if kwargs.get("past_key_values") is None or len(self.history) == 0:
            self.history = kwargs["input_ids"][0].tolist()
        else:
            self.history.append(int(kwargs["input_ids"][0, 0]))
        generated = self.history[self.prompt_length:]
        index = generated.count(self.close)
        last = max([i for i, t in enumerate(generated) if t == self.close], default=-1)
        position = len(generated) - last - 1
        if index < len(self.segments) and position < len(self.segments[index]):
            forced = out.logits[:, -1:].clone().fill_(-1e4)
            forced[0, 0, self.segments[index][position]] = 0.0
            out.logits = forced
        return out


def probe(preflight_path, items_path, out_path):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('tools/hc_v3_decode_check.py:probe')
    import torch
    from transformers import AutoProcessor
    from headcall.decode import DecodeConfig, headcall_generate
    from headcall.heads import Phase1Heads
    from headcall.protocol import Call, render_call
    from student_pilot.orchard_eval import contracts as C
    from student_pilot.orchard_eval import generate as G
    from student_pilot.orchard_eval.frames import pack_input
    preflight = json.loads(Path(preflight_path).read_text())
    items = json.loads(Path(items_path).read_text())
    pin = preflight["adapter"]
    attached = {}
    model = G.load_local_model("qwen35", preflight, pin, attached=attached)
    processor = AutoProcessor.from_pretrained(preflight["model"]["snapshot"], local_files_only=True, trust_remote_code=False)
    processor.tokenizer.padding_side = "right"
    G.load_headcall_heads(model, pin["headcall"], processor.tokenizer)
    if attached.get("geometry") is None or attached.get("carriers") is None:
        raise SystemExit("the probe needs the published connector and carriers")
    store = C.feature_store(pin["geometry"])
    _, rows, config = C.load_generation(preflight["manifest"]["path"])
    by_qid = {row["qid"]: row for row in rows}
    tokenizer = processor.tokenizer
    encode = lambda text: tokenizer.encode(text, add_special_tokens=False)  # noqa: E731
    segments = [encode("<think>\n") + encode(render_call(Call("pose", 8, None))),
                encode("\n") + encode(render_call(Call("depth", 8, (500, 500))))]
    close_id = tokenizer.convert_tokens_to_ids("</tool_response>")
    eos = preflight["effective_generation_config"]["eos_token_id"]
    config_decode = DecodeConfig(list(eos) if isinstance(eos, (list, tuple)) else [eos], max_new_tokens=160, max_calls=8,
                                 max_call_tokens=128)
    results, geometry = [], attached["geometry"]
    for qid in items:
        batch, audit = pack_input(processor, by_qid[qid], "qwen35", config, "pinned", carriers="insert")
        features = store.tokens(audit["frame_hashes"], audit["video_grid_thw"][0])
        device_batch = {key: value.to("cuda:0") for key, value in batch.items()}
        device_batch["aux_camera_positions"] = torch.tensor([audit["carrier_positions"]], dtype=torch.long, device="cuda:0")
        device_batch["geometry_features"] = features
        if store.has_camera_sidecar:
            for key, value in store.camera_sidecar(audit["frame_hashes"], device="cuda:0").items():
                device_batch[key] = value
        calls_before = geometry.calls
        forced = Forced(model, segments, device_batch["input_ids"].shape[1], close_id)
        result = headcall_generate(forced, device_batch, tokenizer, Phase1Heads.from_model(model), config_decode, key=qid)
        results.append({"qid": qid, "geometry_vision_forwards": geometry.calls - calls_before,
                        "calls": [{"body": call.body, "response": call.response, "error_code": call.error_code}
                                  for call in result.calls],
                        "text": tokenizer.decode(result.tokens, skip_special_tokens=False)[:600],
                        "finish_reason": result.finish_reason})
    answered = sum(1 for item in results for call in item["calls"] if call["error_code"] is None)
    summary = {"items": len(results), "calls": sum(len(item["calls"]) for item in results), "answered_by_heads": answered,
               "geometry_forwards_per_item": sorted({item["geometry_vision_forwards"] for item in results})}
    Path(out_path).write_text(json.dumps({"summary": summary, "items": results}, indent=1, default=str) + "\n")
    print(json.dumps(summary), flush=True)


def main():
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('tools/hc_v3_decode_check.py:main')
    if len(sys.argv) > 1 and sys.argv[1] == "--probe":
        probe(*sys.argv[2:5])
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir")
    parser.add_argument("step", type=int)
    parser.add_argument("cell")
    parser.add_argument("frozen")
    parser.add_argument("store_manifest")
    parser.add_argument("store_sha256")
    parser.add_argument("runtime")
    parser.add_argument("--camera-manifest", default=None)
    parser.add_argument("--camera-sha256", default=None)
    parser.add_argument("--items")
    check(parser.parse_args())


if __name__ == "__main__":
    main()
