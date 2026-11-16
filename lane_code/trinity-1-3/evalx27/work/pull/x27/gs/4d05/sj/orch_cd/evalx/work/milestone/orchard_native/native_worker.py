import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kernels as K
import native_common as C
import native_metrics as M


def modules(worker):
    for path, expected in worker["adapter_pins"].items():
        C.checked(dict(path=path, sha256=expected))
    native = C.ROOT/"native/out2"
    sys.path.insert(0, str(native))
    import nomdg
    import geometry
    return nomdg, geometry


def cohort(N, worker):
    tasks, captures = N.tasks_and_captures(worker["inputs"])
    chosen = [t for t in tasks if N.family(t["question_type"]) in N.FAMILIES]
    keys = ["devrows:"+t["id"] for t in chosen]
    if len(captures) != 152 or len(keys) != 636 or keys != worker["expected_keys"]:
        raise ValueError("The native job differs from the registered 152-capture/636-item cohort")
    names = sorted({task["native"] for task in chosen})
    if (names != worker["geometry_captures"] or len(names) != M.GEOMETRY_CAPTURES
            or Counter(N.family(task["question_type"]) for task in chosen) != Counter(M.FAMILY_COUNTS)):
        raise ValueError("The native geometry or family counts differ from the bound 636-item cohort")
    selection = K.select_pilot(
        [dict(key="devrows:"+t["id"], native=t["native"], family=N.family(t["question_type"]))
         for t in chosen], N.FAMILIES, item_keys=worker["pilot_selection"]["item_keys"])
    if selection != worker["pilot_selection"]:
        raise ValueError("The pilot selection differs from its sealed metadata")
    return chosen, captures, selection


def geometry_args(config, dest):
    worker = config["worker"]
    return SimpleNamespace(
        device="cuda:0", raw_tower=str(C.checked(worker["raw_tower"])),
        config=str(C.checked(worker["config"])), export=str(C.checked(worker["artifact"])),
        sha256=worker["artifact"]["sha256"], step=config["step"],
        frames_root=worker["frames_root"], dest=str(dest),
        data_receipt=str(C.checked(worker["data_receipt"])))


def request(N, config, selection, out):
    from routed import source_pins
    N.install_tree()
    from student_pilot.s1_grounding import default_policy
    worker = config["worker"]
    cfg = N.load(C.checked(worker["config"]))
    tree = source_pins()
    value = dict(schema="evalx-unscored-native-pilot-v1", arm="paired", scope="pilot",
                 step=config["step"], dry=False, parent_standin=False,
                 artifact=worker["artifact"], config=worker["config"],
                 data_receipt=worker["data_receipt"], mask_source="by_type",
                 grounding=dict(geometry_manifest=None, depth_source="tower_scaled",
                                allow_own_fallback=False),
                 mask_cache=worker["mask_cache"], fusion_policy=N.FUSION,
                 candidate_policy=default_policy(), route_table=cfg["route_table"],
                 tree_sources=tree, adapter_sources=N.adapter_sources(),
                 runtime_tree=N.tree_identity(N.TREE, tree),
                 max_new_tokens=16384, thinking=True, decoding="greedy",
                 decode_budget=dict(N.Q.DECODE_BUDGET), candidate_universe_policy=N.Q.UNIVERSE,
                 geometry_refusal_policy=N.GR.POLICY,
                 layout="duplicate", prompt_flag=None, frames_root=worker["frames_root"],
                 output=str(out), inputs=worker["inputs"], keys=selection["item_keys"],
                 training_decision_allowed=False)
    return value


def geometry_subset(G, required, allowed=None):
    captures = G.captures()
    by_name = {c["native"]: c for c in captures}
    allowed = set(by_name) if allowed is None else set(allowed)
    if not set(required) <= allowed <= set(by_name) or len(required) > 5:
        raise ValueError("Pilot geometry capture identity differs")
    names = set(required)
    for capture in captures:
        if len(names) >= 5:
            break
        if capture["native"] in allowed:
            names.add(capture["native"])
    if len(names) != 5:
        raise ValueError("The pilot needs five supported geometry captures")
    return [c for c in captures if c["native"] in names]


def geometry_cohort(G, required):
    captures = G.captures()
    if (len(required) != M.GEOMETRY_CAPTURES or len(set(required)) != M.GEOMETRY_CAPTURES
            or len({row["native"] for row in captures}) != len(captures)):
        raise ValueError("Full geometry requires 84 distinct bound captures")
    selected = [capture for capture in captures if capture["native"] in set(required)]
    if {capture["native"] for capture in selected} != set(required):
        raise ValueError("A bound full-geometry capture is absent")
    return selected


def prepare_full_geometry(config, N, G, destination):
    import torch
    parts = K.load_parts(dict(nomdg=Path(N.__file__), geometry=Path(G.__file__)),
                         config["worker"]["kernel_source_pins"])
    selected = geometry_cohort(G, config["worker"]["geometry_captures"])
    args = geometry_args(config, destination)
    torch.cuda.synchronize()
    started = time.monotonic()
    context = K.function(parts["geometry_restore"], vars(G))(args)
    K.function(parts["geometry"], vars(G))(
        args, context["model"], context["processor"], context["info"], selected)
    torch.cuda.synchronize()
    return time.monotonic()-started


def pilot(config, N, G):
    import torch
    worker = config["worker"]
    chosen, captures, selection = cohort(N, worker)
    native = Path(config["logical_run"])/"native"
    output = native/"probe"
    parts = K.load_parts(
        dict(nomdg=Path(N.__file__), geometry=Path(G.__file__)),
        worker["kernel_source_pins"])
    args = SimpleNamespace(device="cuda:0", dest=str(output), first_minute=False)
    bound = request(N, config, selection, output)
    torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    context = K.function(parts["restore"], vars(N))(args, bound)
    torch.cuda.synchronize()
    load_seconds = time.monotonic()-started
    print(json.dumps(dict(event="pilot_loaded", load_seconds=load_seconds,
                          peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                          peak_reserved_bytes=torch.cuda.max_memory_reserved())), flush=True)
    started = time.monotonic()
    try:
        context.update(K.function(parts["parity"], {**vars(N), **context})(args, bound))
    finally:
        torch.cuda.synchronize()
        report = M.PilotReport(output/"PILOT_REPORT.json", config, torch.cuda)
        report.checkpoint("loaded", load_seconds=load_seconds)
        parity_path = output/"GPU_PARITY.json"
        passed = parity_path.is_file() and C.load(parity_path).get("pass") is True
        report.checkpoint("parity_passed" if passed else "parity_failed",
                          parity_seconds=time.monotonic()-started, parity_pass=passed,
                          parity=N.pin(parity_path) if parity_path.is_file() else None)
    geometry_times = []
    selected = geometry_cohort(G, worker["geometry_captures"])
    candidates = [dict(key="devrows:"+task["id"], native=task["native"],
                       family=N.family(task["question_type"])) for task in chosen]
    report.checkpoint("geometry_starting", registered_selection=selection,
                      full_item_candidates=candidates, geometry_refusal_policy=N.GR.POLICY)

    def capture_done(record):
        counts = Counter(N.family(task["question_type"]) for task in chosen
                         if task["native"] == record["native"] and record["status"] == "REFUSED")
        paths = [C.checked(record["output"])] if record["output"] is not None else []
        value = dict(record, refused_items_by_arm={arm:dict(counts) for arm in N.GR.ARMS},
                     return_size=M.measure(paths, Path(config["logical_run"])))
        geometry_times.append(value)
        report.checkpoint("geometry_capture", geometry=geometry_times)
        print(json.dumps(dict(event="geometry_capture_outcome", native=record["native"],
            status=record["status"], error=record["error"], seconds=record["seconds"],
            refused_items_by_arm=value["refused_items_by_arm"], **record["diagnostics"]),
            sort_keys=True), flush=True)

    geometry = native/"geometry"
    geometry_options = geometry_args(config, geometry)
    geometry_options.capture_callback = capture_done
    geometry_started = time.monotonic()
    K.function(parts["geometry"], vars(G))(
        geometry_options, context["model"], context["processor"], context["info"], selected)
    geometry_seconds = time.monotonic()-geometry_started
    bound["grounding"]["geometry_manifest"] = N.pin(geometry/"GEOMETRY_MANIFEST.json")
    manifest = N.load(C.checked(bound["grounding"]["geometry_manifest"]))
    G.validate_manifest(manifest, bound["artifact"], worker["geometry_captures"])
    masks = N.P.Masks(bound["mask_cache"])
    registered_selection = selection
    selection = K.select_geometry_pilot(candidates, registered_selection, geometry_times)
    bound["keys"] = selection["item_keys"]
    bound["geometry_refusals"] = N.GR.item_refusals(chosen, manifest)
    selected_tasks = [t for t in chosen if "devrows:"+t["id"] in selection["item_keys"]]
    refused_tasks = [t for t in chosen if t["id"] in bound["geometry_refusals"]]
    served_tasks = [t for t in chosen if t["id"] not in bound["geometry_refusals"]]
    bound["mask_operand_refusals"] = N.operand_refusals(
        [task for task in selected_tasks if task["id"] not in bound["geometry_refusals"]], context["refs"], masks)
    bound["candidate_universe_admission"] = N.universe_admission(served_tasks, context["refs"], masks)
    for key, value in bound["candidate_universe_admission"].items():
        print(json.dumps(dict(event="runtime_universe_bind", key=key, **value), sort_keys=True), flush=True)
    bound["query_journal"] = N.Q.journal_policy([
        dict(key="devrows:"+t["id"], family=N.family(t["question_type"])) for t in selected_tasks])
    bound["perceptions"] = {
        t["id"]: N.item_perception(t, captures[t["native"]], bound, manifest, masks.receipt)
        for t in selected_tasks+refused_tasks}
    bound["binding"] = N.digest(bound)
    C.dump(output/"request.json", bound)
    refused_rows = [row for task in refused_tasks for row in N.geometry_refusal_pair(task, bound)]
    refused_counts = Counter(N.family(task["question_type"]) for task in refused_tasks)
    refused_captures = sum(record["status"] == "REFUSED" for record in geometry_times)
    near_boundary = [record["native"] for record in geometry_times
                     if -.07 < record["diagnostics"]["tower_reference_margin"] < 0]
    required = ("d3/41069053", "d3/41098149", "d3/41254810")
    if not set(required) <= {record["native"] for record in geometry_times} or not near_boundary:
        raise ValueError("The complete geometry audit lacks its named or near-boundary captures")
    report.checkpoint("geometry_complete", selection=selection, geometry_seconds=geometry_seconds,
        request_binding=bound["binding"], geometry_manifest=bound["grounding"]["geometry_manifest"],
        pilot_status=selection["status"], geometry_refused_items=dict(refused_counts),
        geometry_refusal_records=refused_rows,
        geometry_scores=N.geometry_score_report(refused_rows, chosen, bound),
        refusal_return_size=M.refusal_size(refused_rows),
        geometry_audit_captures=dict(required=list(required), near_boundary=near_boundary),
        geometry_cpu_comparison=dict(predicted_refused_captures=12, predicted_refused_distance_items=21,
            predicted_head_capture_range=[6, 13], observed_refused_captures=refused_captures,
            observed_refused_items=len(refused_tasks), within_capture_range=6 <= refused_captures <= 13))
    if selection["status"] != "READY":
        report.checkpoint("insufficient_passing_coverage", complete=False,
                          full_projection_refusal="The passed-capture cohort cannot supply the registered ten pairs.")
        return report.value
    context.update(g=manifest, masks=masks)
    run_pair = K.function(parts["pair"], {**vars(N), **context})
    timings, unit_rows, sample_rows = [], [], []
    for key in bound["keys"]:
        torch.cuda.synchronize()
        start = time.monotonic()
        pair = run_pair(args, bound, key)
        torch.cuda.synchronize()
        refusal = pair[0].get("geometry_refusal")
        decoded = pair[0].get("decode", {})
        digested = pair if refusal else [
            dict(item, decode=N.Q.journal_decode(item["decode"], False)) for item in pair]
        row = dict(key=key, family=N.family(pair[0]["question_type"]),
                   seconds=time.monotonic()-start, native_seconds=pair[0]["seconds"],
                   capped=pair[0]["capped"], no_answer=pair[0]["no_answer"] and not refusal,
                   geometry_refusal=refusal, decode_executed=not bool(refusal),
                   call_errors=pair[0]["call_errors"],
                   finish="geometry_refusal" if refusal else decoded["finish"],
                   generated_tokens=0 if refusal else decoded["generated_tokens"],
                   decode_budget=decoded.get("decode_budget", {}),
                   question_unit=pair[0]["question_unit"],
                   **N.Q.call_audit(decoded),
                   return_size=M.pair_size(pair, output/"grounding"/N.digest(key),
                                           Path(config["logical_run"]), digested))
        unit_rows.extend(dict({name: item[name] for name in
                          ("key", "arm", "question_type", "stratum", "scores", "question_unit")},
                          geometry_refusal=item.get("geometry_refusal"))
                         for item in pair)
        sample_rows.extend(pair)
        timings.append(row)
        report.checkpoint("item", items=timings)
        print(json.dumps(dict(event="pilot_pair", **row)), flush=True)
    if len(timings) != 10 or (output/"COMPLETE.json").exists():
        raise ValueError("The pilot must contain ten pairs and no completed R1 cell")
    fixed = [output/name for name in ("LOAD_RECEIPT.json", "PARITY_DECODE.json",
                                      "GPU_PARITY.json", "request.json")]
    fixed.append(geometry/"GEOMETRY_MANIFEST.json")
    sample_bundle = dict(schema="legs1-r1-nomdg-v1",
        arms={arm:[row for row in sample_rows if row["arm"] == arm] for arm in N.GR.ARMS},
        expected_keys=selection["item_keys"], artifact_sha256=bound["artifact"]["sha256"],
        binding=bound["binding"],
        perception_by_key={"devrows:"+key:N.digest(value) for key,value in bound["perceptions"].items()})
    report.checkpoint("complete", complete=True,
                      decode_budget=bound["decode_budget"], query_journal_retain_per_type=3,
                      unit_scores=N.Q.unit_report(unit_rows),
                      sample_scope="Ten pairs; exactly one bound geometry refusal when any capture refuses. No full-cohort score is inferred.",
                      sample_r1=N.rules(sample_bundle, step=config["step"]),
                      geometry_scores=N.geometry_score_report(
                          [row for row in sample_rows if not row.get("geometry_refusal")]+refused_rows, chosen, bound),
                      fixed_return_size=M.measure(fixed, Path(config["logical_run"])))
    report.checkpoint("complete", full_projection=M.project(report.value))
    return report.value


def full(config, N, G):
    worker = config["worker"]
    cohort(N, worker)
    native = Path(config["logical_run"])/"native"
    geometry = native/"geometry"
    geometry_seconds = prepare_full_geometry(config, N, G, geometry)
    paired = native/"paired"
    args = SimpleNamespace(
        arm="paired", scope="r1", parent_standin=False, step=config["step"],
        config=str(C.checked(worker["config"])), dest=str(paired),
        export=str(C.checked(worker["artifact"])), sha256=worker["artifact"]["sha256"],
        dry=False, data_receipt=str(C.checked(worker["data_receipt"])),
        geometry=str(geometry/"GEOMETRY_MANIFEST.json"),
        mask_cache=str(C.checked(worker["mask_cache"])), frames_root=worker["frames_root"],
        camera_cohort=str(C.checked(worker["inputs"]["camera_cohort"])),
        device="cuda:0", first_minute=False)
    N.bind(args)
    bound = N.validate_request(N.load(paired/"request.json"), live=True)
    N.run(args, bound)
    output = native/"R1.json"
    N.merge(SimpleNamespace(paired=str(paired), output=str(output)))
    bundle = N.load(output)
    report = N.admit_bundle(bundle, config["step"], worker["artifact"]["sha256"])
    report["unit_scores"] = bundle["unit_scores"]
    comparison = N.GR.compare_refusals(
        config["full_projection"]["report"]["geometry"],
        N.load(geometry/"GEOMETRY_MANIFEST.json")["records"])
    report["geometry_refusal_comparison"] = comparison
    print(json.dumps(dict(event="full_geometry_refusal_comparison", **comparison), sort_keys=True), flush=True)
    C.dump(native/"paired/IN_JOB_ADMISSION.json", dict(
        schema="evalx-native-in-job-admission-v1", synthetic=False,
        artifact=worker["artifact"], bundle=N.pin(output),
        native_admission_source=N.pin(N.__file__), report=report,
        geometry_seconds=geometry_seconds, geometry_captures=M.GEOMETRY_CAPTURES,
        geometry_capture_ids=worker["geometry_captures"],
        geometry_refusal_comparison=comparison,
        geometry_phase_includes_model_restore=True,
        local_frame_reverification_required_for_original_reader=True))
    return report


def run(config):
    C.validate_config(config)
    if (not os.environ.get("SLURM_JOB_ID", "").isdigit()
            or not os.uname().nodename.startswith("orchard-")
            or len(os.environ.get("CUDA_VISIBLE_DEVICES", "").split(",")) != 1
            or not os.environ.get("CUDA_VISIBLE_DEVICES")):
        raise ValueError("Native restoration requires its assigned Orchard allocation")
    N, G = modules(config["worker"])
    return {"pilot": pilot, "full": full}[config["mode"]](config, N, G)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    run(C.load(args.config))


if __name__ == "__main__":
    main()
