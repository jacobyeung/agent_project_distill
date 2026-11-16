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
         for t in chosen], N.FAMILIES)
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
    report = M.PilotReport(native/"PILOT_REPORT.json", config, torch.cuda)
    started = time.monotonic()
    context = K.function(parts["restore"], vars(N))(args, bound)
    torch.cuda.synchronize()
    load_seconds = time.monotonic()-started
    report.checkpoint("loaded", load_seconds=load_seconds)
    started = time.monotonic()
    context.update(K.function(parts["parity"], {**vars(N), **context})(args, bound))
    torch.cuda.synchronize()
    parity_seconds = time.monotonic()-started
    report.checkpoint("parity_passed", parity_seconds=parity_seconds,
                      parity=N.pin(output/"GPU_PARITY.json"), parity_pass=True)
    geometry_times = []
    selected = geometry_subset(G, selection["captures"], worker["geometry_captures"])
    measured_geometry = set()

    def timed_captures():
        for capture in selected:
            torch.cuda.synchronize()
            start = time.monotonic()
            yield capture
            torch.cuda.synchronize()
            paths = set(geometry.glob("*.npz"))
            fresh = paths-measured_geometry
            if len(fresh) != 1:
                raise ValueError("Each geometry capture must produce one new measured cache")
            geometry_times.append(dict(native=capture["native"], group=capture["group"],
                                       seconds=time.monotonic()-start,
                                       return_size=M.measure(fresh, Path(config["logical_run"]))))
            measured_geometry.update(fresh)
            report.checkpoint("geometry_capture", geometry=geometry_times)

    geometry = native/"geometry"
    K.function(parts["geometry"], vars(G))(
        geometry_args(config, geometry), context["model"], context["processor"],
        context["info"], timed_captures())
    bound["grounding"]["geometry_manifest"] = N.pin(geometry/"GEOMETRY_MANIFEST.json")
    manifest = N.load(C.checked(bound["grounding"]["geometry_manifest"]))
    G.validate_manifest(manifest, bound["artifact"])
    masks = N.P.Masks(bound["mask_cache"])
    selected_tasks = [t for t in chosen if "devrows:"+t["id"] in selection["item_keys"]]
    bound["mask_operand_refusals"] = N.operand_refusals(selected_tasks, context["refs"], masks)
    bound["perceptions"] = {
        t["id"]: N.item_perception(t, captures[t["native"]], bound, manifest, masks.receipt)
        for t in selected_tasks}
    bound["binding"] = N.digest(bound)
    C.dump(output/"request.json", bound)
    context.update(g=manifest, masks=masks)
    run_pair = K.function(parts["pair"], {**vars(N), **context})
    timings = []
    for key in bound["keys"]:
        torch.cuda.synchronize()
        start = time.monotonic()
        pair = run_pair(args, bound, key)
        torch.cuda.synchronize()
        row = dict(key=key, family=N.family(pair[0]["question_type"]),
                   seconds=time.monotonic()-start, native_seconds=pair[0]["seconds"],
                   capped=pair[0]["capped"], no_answer=pair[0]["no_answer"],
                   call_errors=pair[0]["call_errors"],
                   return_size=M.pair_size(pair, output/"grounding"/N.digest(key),
                                           Path(config["logical_run"])))
        timings.append(row)
        report.checkpoint("item", items=timings)
        print(json.dumps(dict(event="pilot_pair", **row)), flush=True)
    if len(timings) != 10 or (output/"COMPLETE.json").exists():
        raise ValueError("The pilot must contain ten pairs and no completed R1 cell")
    fixed = [output/name for name in ("LOAD_RECEIPT.json", "PARITY_DECODE.json",
                                      "GPU_PARITY.json", "request.json")]
    fixed.append(geometry/"GEOMETRY_MANIFEST.json")
    report.checkpoint("complete", complete=True,
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
    report = N.admit_bundle(N.load(output), config["step"], worker["artifact"]["sha256"])
    C.dump(native/"paired/IN_JOB_ADMISSION.json", dict(
        schema="evalx-native-in-job-admission-v1", synthetic=False,
        artifact=worker["artifact"], bundle=N.pin(output),
        native_admission_source=N.pin(N.__file__), report=report,
        geometry_seconds=geometry_seconds, geometry_captures=M.GEOMETRY_CAPTURES,
        geometry_capture_ids=worker["geometry_captures"],
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
