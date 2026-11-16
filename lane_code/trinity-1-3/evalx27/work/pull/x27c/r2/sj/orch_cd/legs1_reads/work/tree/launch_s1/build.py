import argparse
import copy
import importlib.util
import json
from pathlib import Path
import re
import shutil

from student_pilot import carrier_c1_run as run, g3t_online, rehearsal
from student_pilot.c1r_ref import REPOSITORY, REVISION
from student_pilot.p3_provenance import digest, file_pin, load, pinned, sha256, source_files, write
from student_pilot.s1_pool import implementation as pool_implementation
from student_pilot import source_seal
from student_pilot.source_seal import archive, inventory as tree_files


LOGICAL = Path("/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b")


def build(base, output, pool_receipt, bindings=None):
    base, output = Path(base), Path(output)
    tree = Path(__file__).resolve().parent.parent
    bindings = {} if bindings is None else copy.deepcopy(bindings)
    world = bindings.get("world_size", 4)
    if type(world) is not int or world not in (4, 8):
        raise ValueError("The single-node launch world must be four or eight")
    pool = load(pinned(pool_receipt))
    if (pool.get("schema") != "s1-pool-selection-v1" or pool.get("training_admission") is not False
            or pool.get("implementation") != pool_implementation() or pool.get("blockers")):
        raise ValueError("Expected a non-admitting source-selection receipt")
    sources = {str(path.relative_to(tree)): sha256(path)
               for path in source_files([tree / "student_pilot/carrier_c1_run.py"])}
    operations = {str(path.relative_to(tree)): sha256(path) for path in source_files([
        tree / "student_pilot/carrier_c1_routing.py", tree / "student_pilot/carrier_c1_canary.py"])}
    output.mkdir()
    for name in ("k", "o", "runs"):
        (output / name).mkdir()
    shutil.copytree(tree / "launch_s1/b", output / "b")
    shutil.copy2(tree / ("launch_s1/job.sh" if world == 4 else "launch_s1/job8.sh"), output / "job.sh")
    shutil.copy2(tree / "launch_s1/job8.sh", output / "job8.sh")
    for path in sorted((base / "k").glob("*.json")):
        if path.name not in ("0.json", "1.json", "4.json", "7.json"):
            shutil.copy2(path, output / "k" / path.name)
    kit_key = bindings.get("kit_key", digest(dict(sources=sources, pool=pool_receipt["sha256"]))[:8])
    run_key = bindings.get("run_key", digest(dict(kit=kit_key, operation="train"))[:8])
    if any(not isinstance(key, str) or not re.fullmatch("[0-9a-f]{8}", key) for key in (kit_key, run_key)):
        raise ValueError("Kit and run keys must be opaque eight-digit hexadecimal tokens")

    def put(name, value):
        path = output / "k" / name
        write(path, value)
        return dict(path=str(LOGICAL / "k" / name), sha256=sha256(path))

    def small_input(name, pin):
        source = pinned({key: pin[key] for key in ("path", "sha256")})
        if source.stat().st_size > 16_000_000:
            raise ValueError("Only small metadata belongs in a kit")
        destination = output / "k" / name
        with destination.open("xb") as target, source.open("rb") as stream:
            shutil.copyfileobj(stream, target)
        return dict(path=str(LOGICAL / "k" / name), sha256=sha256(destination))

    def local(name):
        return dict(file="k/"+name, sha256=sha256(output / "k" / name))

    files = tree_files(tree)
    tar_name = "t_"+digest(files)[:16]+".tar"
    archive(tree, output / "k" / tar_name, files)
    code = source_seal.create(tree, output / "k" / tar_name, sources, operations,
                              archive_path=LOGICAL / "k" / tar_name)
    if bindings.get("code_seal") and load(pinned(bindings["code_seal"])) != code:
        raise ValueError("External source seal does not describe this exact tree and archive")
    code_pin = put("7.json", code)
    for name, pin in bindings.get("small_inputs", {}).items():
        if not re.fullmatch(r"input_[a-z0-9_]+\.json", name):
            raise ValueError("Additional metadata must use the reserved input namespace")
        small_input(name, pin)
    inherited = load(base / "k/1.json")
    cfg = load(base / "k" / (inherited["1"]+".json"))
    original_streams = copy.deepcopy(cfg["streams"])
    model = load(tree / "configs/stageb_cp1rv_mdg_w4.json")
    placeholder = str(LOGICAL / "u/unbound")
    model = json.loads(json.dumps(model).replace("/PLACEHOLDER", placeholder))
    cfg.update(streams=model["streams"], mdg=model["mdg"], mix=model["mix"],
               world_size=world, reference_world_size=32, trace_program_version="3.14",
               ground_target_filter=True,
               preparation_output=str(LOGICAL / "f" / run_key), output=str(LOGICAL / "runs" / run_key),
               preparation=dict(path=str(LOGICAL / "f" / run_key / "receipt.json"), sha256="0"*64))
    cfg.update(copy.deepcopy(bindings.get("config", {})))
    if cfg.get("geometry_online"):
        raise ValueError("The queued main leg keeps GF1 and its connector candidate separate")
    if cfg.get("tool_mode_flag") is not None:
        raise ValueError("The main leg does not accept a tool-mode input flag")
    cfg.pop("geometry_online", None)
    cfg.pop("tool_mode_flag", None)
    cfg.update(code=code_pin, world_size=world, reference_world_size=32,
               trace_program_version="3.14", ground_target_filter=True)
    if world == 4:
        cfg["first_step_admission"] = "all_rank_native_v1"
    cfg["milestones"] = sorted({1, *cfg["milestones"]})
    cfg["remove_files"] = [{**small_input(f"remove_{number}.jsonl", pin),
                            **({"defects": pin["defects"]} if "defects" in pin else {})}
                           for number, pin in enumerate(pool["remove_files"])]
    for name, key in (("dev_scene_exclusions", "dev"), ("benchmark_scene_exclusions", "benchmark")):
        cfg[name] = small_input(name+".json", pool["scene_exclusions"][key])
    if world == 4:
        catalog = dict(bindings.get("input_catalog", {}))
        metadata = [("pool_manifest.json", pool["manifest"])]
        metadata.extend((f"pool_exclusion_{number}.tsv", pin)
                        for number, pin in enumerate(pool["exclusions"].values()))
        metadata.extend((f"pool_indices_{number}.json", entry["selection"])
                        for number, entry in enumerate(pool["sources"].values()) if entry.get("selection"))
        for name, pin in metadata:
            catalog[pin["sha256"]] = small_input(name, pin)["path"]
        for pin in [*cfg["remove_files"], cfg["dev_scene_exclusions"], cfg["benchmark_scene_exclusions"]]:
            catalog[pin["sha256"]] = pin["path"]
        cfg["s1_routing"] = dict(schema="s1-routing-inputs-v1",
            selection=small_input("pool_selection.json", pool_receipt), catalog=catalog,
            frame_map=small_input("frame_map.jsonl.gz", bindings["frame_map"]) if bindings.get("frame_map")
                      else dict(path=placeholder+"/frame_map.jsonl.gz", sha256="0"*64),
            frame_plan=small_input("frame_plan.json.gz", bindings["frame_plan"]) if bindings.get("frame_plan")
                       else dict(path=placeholder+"/frame_plan.json.gz", sha256="0"*64))
        if bindings.get("fps_authority"):
            cfg["s1_routing"]["fps_authority"] = small_input("frame_rates.json", bindings["fps_authority"])
        scene_reference = bindings.get("scene_reference")
        references = load(pinned(scene_reference))["withheld_training_rows"] if scene_reference else {}
        pose_reference = "pose_dbs (posedata2/work/cnt/c.json db rows by source index)"
        source_map = {
            "pose/0": [dict(source=pose_reference, index="0")],
            "pose/1": [dict(source=pose_reference, index="2")],
            "vqa": [dict(source=name) for name in
                    ("mix:vqa_x4", "mix:vqa_sel_v3", "mix:vqa_box_k3", "mix:vqa_box_k6", "mix:vsd_q_v4")],
            "pointing": [dict(source="mix:pointing_v2")],
            "mdg": [dict(source="mix:mdg_r7_119970"), dict(source="mix:mdg_r7_119971")],
            "routing": [dict(source="mix:routing_M"), dict(source="mix:routing_L")]+[
                dict(source="pool_s1:"+name) for name, entry in pool["sources"].items()
                if entry["status"] == "ELIGIBLE" and "pool_s1:"+name in references],
        }
        cfg["scene_coverage"] = dict(schema="s1-scene-coverage-v1",
            reference=small_input("scene_reference.json", scene_reference) if scene_reference else
                      dict(path=placeholder+"/scene_reference.json", sha256="0"*64),
            source_map=copy.deepcopy(bindings.get("scene_source_map", source_map)))
    routes = load(pinned(bindings["route_table"])) if bindings.get("route_table") else cfg["route_table"]
    route_pin = put("routes.json", routes)
    cfg["route_table"] = routes
    cfg["recipe"].update(wall_seconds=86400, stop_before_seconds=3600 if world == 4 else 900,
                         resume_every_seconds=7200,
                         export_at_stop=True)
    cfg["recipe"] = run.recipe_for(cfg)
    cfg["stall_guard"] = dict(startup_seconds=max(3600, cfg.get("schedule", {}).get("startup_seconds", 3600)),
                             idle_seconds=1200,
                             checkpoint_grace_seconds=600, poll_seconds=10)
    from student_pilot.checkpoint_space import plan
    cfg["checkpoint_disk_guard"] = plan(cfg["recipe"])
    proof_pins = {}
    for key in ("review", "staging", "archive"):
        if bindings.get(key):
            small_input(key+".json", bindings[key])
            proof_pins[key] = local(key+".json")
    if bindings.get("review"):
        cfg["admission"] = dict(path=str(LOGICAL / "k/review.json"), sha256=proof_pins["review"]["sha256"])
    if bindings.get("first_batch"):
        batch = load(pinned(bindings["first_batch"]))
        small_input("first_batch_report.json", batch["report"])
        batch["report"] = local("first_batch_report.json")
        put("first_batch.json", batch)
        proof_pins["first_batch"] = local("first_batch.json")
    config_key = digest(cfg)[:8]
    put(config_key+".json", cfg)
    secondary = copy.deepcopy(cfg)
    secondary.update(world_size=8, output=str(LOGICAL / "runs" / digest(dict(run=run_key, world=8))[:8]))
    secondary["recipe"] = run.recipe_for(secondary)
    secondary_pin = put("world8.json", secondary)
    put("1.json", {"0": config_key})
    auth = dict(allow_until_utc="2026-11-22T00:00:00Z", arm=["0"], modes=[], source_revision=code["commit"],
                new_gpus=0, other_running_and_pending_gpus=0, gpu_cap=8, resume="latest", review=None,
                milestone_gate=None, guard=None, kernel=None)
    auth.update(copy.deepcopy(bindings.get("authorization", {})))
    put("4.json", auth)
    cur = load(base / "k/0.json")
    cur.update(copy.deepcopy(bindings.get("deployment", {})))
    record = dict(schema="rung1-neutral-runtime-v1",
                  trees=dict(trainer=dict(commit=code["commit"], files=files, file_count=len(files))))
    record_pin = put("s1_record.json", record)
    cur.update(commit=code["commit"],
               trainer=dict(file=str(LOGICAL / "k" / tar_name), sha256=sha256(output / "k" / tar_name)),
               record=dict(file=record_pin["path"], sha256=record_pin["sha256"]))
    put("0.json", cur)
    candidates = []
    for stage in (1, 2):
        spec = load(tree / f"configs/gf1_stage{stage}.json")
        candidate = copy.deepcopy(cfg)
        candidate.update(world_size=4, steps=spec["steps"], milestones=spec["milestones"],
                         output=str(LOGICAL / "runs" / (run_key+str(stage))))
        fusion = dict(spec["gf1"], gf1_init="zero" if stage == 1 else "warm")
        candidate["geometry_online"] = g3t_online.normalize(dict(schema="gx-carrier-v1", mode="frozen",
            encoder=dict(repository=REPOSITORY, revision=REVISION, source_sha256=g3t_online.vendor_digest(),
                         weights=dict(path=placeholder+"/encoder.safetensors", sha256="0"*64),
                         config=dict(path=placeholder+"/encoder.json", sha256="0"*64)),
            input=g3t_online.INPUT, feature=g3t_online.FEATURE,
            connector=dict(out_init="zero", rms_cam="warm_start_carrier_median_rms_v1", rms_scale=1.),
            finetune=None, gf1=fusion))
        if stage == 2:
            candidate["init_artifact"] = dict(artifact=dict(path=placeholder+"/stage1/artifact.json", sha256="0"*64),
                                              lm="full", heads=["pose", "depth", "gf1"])
        candidate["recipe"] = run.recipe_for(candidate)
        candidate["checkpoint_disk_guard"] = plan(candidate["recipe"])
        candidate_pin = put(f"candidate_{stage}.json", candidate)
        candidates.append(dict(stage=stage, config=candidate_pin, world_size=4, status="BLOCKED",
                               allocation="separate-four-rank-allocation-not-the-eight-rank-queue-slot"))
    put("candidates.json", dict(main_world_size=world, main_gf1=False, candidates=candidates,
                               standby_world8=dict(config=secondary_pin, submitted=False, status="BLOCKED")))
    status = bindings.get("status", "BLOCKED")
    launch = dict(schema="s1-orchard-launch-v1", status=status,
                  production_authorized=status == "READY" and bindings.get("production_authorized") is True,
                  source_revision=code["commit"], source_seal=source_seal.binding(code, run.identity(cfg)),
                  config=local(config_key+".json"),
                  rehearsal_environment=rehearsal.ENVIRONMENT, kit_key=kit_key, run_key=run_key,
                  run_directory=f"/tmp/jjyeung/okit_8865619b/runs/{run_key}",
                  persistent_run_root=bindings.get("persistent_run_root", "/home/jjyeung/okit/r/0d67d2c5"),
                  route_table=route_pin, source_selection=pool_receipt, inherited_streams=original_streams,
                  slot=dict(partition="advanced" if world == 4 else "preempt", nodes=1, gpus=world,
                            cpus=48 if world == 4 else 96, memory_gb=800 if world == 4 else 1600,
                            wall_seconds=86400),
                  **proof_pins)
    if world == 4:
        launch["in_job_admission"] = dict(schema="s1-in-job-admission-v1",
            directory=str(Path(cfg["output"]) / "inputs"), frame_roots=bindings.get("frame_roots", []),
            parent_grounding_required=True, gpu_first_step_required=True)
    put("launch.json", launch)
    inventory = {str(path.relative_to(output)): sha256(path) for part in ("b", "k")
                 for path in sorted((output / part).rglob("*")) if path.is_file()}
    inventory.update({name: sha256(output / name) for name in ("job.sh", "job8.sh")})
    manifest = output / "SHA256SUMS.txt"
    manifest.write_text("".join(f"{value}  {key}\n" for key, value in sorted(inventory.items())))
    certificate = dict(status="UNREVIEWED", hits=None, manifest_sha256=sha256(manifest), external=[],
                       scope="integrity-manifest-only; independent-content-scan-not-supplied")
    if bindings.get("scan_certificate"):
        certificate = load(pinned(bindings["scan_certificate"]))
        if certificate.get("manifest_sha256") != sha256(manifest):
            raise ValueError("Independent scan certificate belongs to another sealed kit")
    write(output / "ANON_OK.json", certificate)
    if status not in ("BLOCKED", "PREPARATION_ONLY", "READY"):
        raise ValueError("Unknown launch disposition")
    if status != "BLOCKED":
        spec = importlib.util.spec_from_file_location("s1_packaged_gate", output / "b/g.py")
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
        gate.check(output, {}, "p" if status == "PREPARATION_ONLY" or world == 4 else "t")
        if certificate.get("status") != "CLEAN" or certificate.get("hits") != 0:
            raise ValueError("Executable kit needs its independently bound content scan")
    result = dict(schema="s1-launch-build-v1", status=status, submitted=False,
                  native_config_sha256=run.identity(cfg), source_committed=False,
                  source_authority="sha256-tree-and-config", source_seal=launch["source_seal"],
                  archive_local=file_pin(output / "k" / tar_name),
                  pool_selected_rows=pool["selected_rows"], metadata_inventory=file_pin(manifest),
                  local_kit=str(output), deployment_home=f"/home/jjyeung/okit/x/{kit_key}",
                  blockers=["unbound native source receipts and MDG assets", "in-job admission and first-step proof",
                            "off-scratch archive attestation", "independent admission and content scan",
                            "pre-staged Orchard inputs", "written launch authorization"] if status == "BLOCKED" else [])
    write(output / "BUILD.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-kit", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--pool-receipt", required=True)
    parser.add_argument("--bindings")
    args = parser.parse_args()
    result = build(args.base_kit, args.output, file_pin(args.pool_receipt),
                   load(args.bindings) if args.bindings else None)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
