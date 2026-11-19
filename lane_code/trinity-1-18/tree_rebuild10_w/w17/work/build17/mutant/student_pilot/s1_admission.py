import argparse
from collections import Counter
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import sqlite3
import subprocess
import sys
import time
import uuid

from .p3_provenance import file_pin, load, pinned, sha256, write


class FrameAudit:
    def __init__(self, output, roots, *, sample_size=64, seed=17):
        if type(sample_size) is not int or sample_size < 1 or not roots:
            raise ValueError("Frame audit requires roots and a nonempty fixed hash sample")
        self.roots = [Path(root).resolve() for root in roots]
        if any(not root.is_dir() for root in self.roots):
            raise ValueError("Frame store root is not staged")
        self.output = Path(output)
        self.sample_size, self.seed = sample_size, seed
        self.rows = Counter()
        self.database = self.output / "frame_inventory.sqlite"
        self.connection = sqlite3.connect(self.database)
        self.connection.execute("CREATE TABLE frames (path TEXT PRIMARY KEY, logical TEXT NOT NULL, sha256 TEXT NOT NULL, sample_key TEXT NOT NULL)")
        self.connection.execute("CREATE TABLE refs (source TEXT NOT NULL, path TEXT NOT NULL, n INTEGER NOT NULL, PRIMARY KEY(source,path))")

    def counts(self, source):
        self.rows.setdefault(source, 0)

    def expect(self, source, rows, population):
        self.counts(source)

    def keep(self, row, source):
        from .orchard_paths import resolve_read
        if source.startswith("mdg/"):
            from .grounding_train import clip_row
            row = clip_row(row)
        inputs = row.get("student_input", {})
        frames = inputs.get("frames")
        if not isinstance(frames, list) or not frames:
            raise ValueError(f"Retained row lacks explicit native RGB pins: {source}")
        self.rows[source] += 1
        for pin in frames:
            if (not isinstance(pin, dict) or set(pin) != {"path", "sha256"}
                    or not isinstance(pin["sha256"], str) or not re.fullmatch("[0-9a-f]{64}", pin["sha256"])):
                raise ValueError("Frame requires an exact path/SHA256 pin")
            path = resolve_read(pin["path"]).resolve()
            if not any(path.is_relative_to(root) for root in self.roots) or not path.is_file():
                raise ValueError(f"Retained RGB is absent or outside its frame store: {path}")
            found = self.connection.execute("SELECT sha256 FROM frames WHERE path=?", (str(path),)).fetchone()
            if found is not None and found[0] != pin["sha256"]:
                raise ValueError("Retained rows give one physical frame conflicting hashes")
            key = hashlib.sha256(f"{self.seed}|{pin['path']}|{pin['sha256']}".encode()).hexdigest()
            self.connection.execute("INSERT OR IGNORE INTO frames VALUES (?,?,?,?)",
                                    (str(path), pin["path"], pin["sha256"], key))
            self.connection.execute("INSERT INTO refs VALUES (?,?,1) ON CONFLICT(source,path) DO UPDATE SET n=n+1",
                                    (source, str(path)))
        return True

    def finish(self):
        self.connection.commit()
        records = {}
        for source, rows in sorted(self.rows.items()):
            unique, references = self.connection.execute("SELECT count(*),coalesce(sum(n),0) FROM refs WHERE source=?",
                                                         (source,)).fetchone()
            sample = []
            query = ("SELECT f.path,f.logical,f.sha256 FROM frames f JOIN refs r ON f.path=r.path "
                     "WHERE r.source=? ORDER BY f.sample_key,f.logical LIMIT ?")
            for path, logical, expected in self.connection.execute(query, (source, self.sample_size)):
                actual = sha256(path)
                if actual != expected:
                    raise ValueError(f"Fixed RGB hash sample differs: {logical}")
                sample.append(dict(path=logical, resolved=path, sha256=actual))
            if rows and (not unique or not sample):
                raise ValueError("A retained source lacks its RGB audit")
            records[source] = dict(rows=rows, frame_references=references, unique_frames=unique, hash_sample=sample)
        return dict(schema="s1-frame-audit-v1", all_retained_frames_exist=True, fixed_hash_sample_verified=True,
                    roots=[str(root) for root in self.roots], sample_size_per_source=self.sample_size,
                    sample_seed=self.seed, sources=records, inventory=file_pin(self.database))

    def close(self):
        self.connection.close()


def audit_frames(receipt, roots, output, *, sample_size=64):
    from .s1_exclusions import selection
    audit = FrameAudit(output, roots, sample_size=sample_size)
    try:
        for name, value in receipt["streams"].items():
            selection(name, value, audit)
        return audit.finish()
    finally:
        audit.close()


def verify_frames(report):
    from .orchard_paths import resolve_read
    path = pinned(report["inventory"])
    connection = sqlite3.connect(path.as_uri()+"?mode=ro", uri=True)
    try:
        for actual, logical in connection.execute("SELECT path,logical FROM frames"):
            if resolve_read(logical).resolve() != Path(actual) or not Path(actual).is_file():
                raise ValueError("A retained RGB frame moved or disappeared after admission")
    finally:
        connection.close()
    for source in report["sources"].values():
        for sample in source["hash_sample"]:
            if sha256(resolve_read(sample["path"])) != sample["sha256"]:
                raise ValueError("The fixed RGB hash sample changed after admission")


def local_pins(value, root):
    if isinstance(value, dict):
        if set(value) == {"path", "sha256"} and Path(value["path"]).resolve().is_relative_to(root):
            yield value
        else:
            for item in value.values():
                yield from local_pins(item, root)
    elif isinstance(value, list):
        for item in value:
            yield from local_pins(item, root)


def admit(config_pin, output, roots, *, threads=16, memory_gib=256, sample_size=64, max_seconds=86400,
          rank_limit=None, attempt=None, prepare_only=False):
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise ValueError("The admission command requires CUDA_VISIBLE_DEVICES to be empty")
    if type(threads) is not int or not 1 <= threads <= 16 or not 8 <= memory_gib <= 512:
        raise ValueError("Admission resources are outside the CPU-only bounds")
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    limit = int(memory_gib * (1 << 30))
    resource.setrlimit(resource.RLIMIT_AS, (min(value for value in (soft, hard, limit) if value > 0), hard))
    import torch
    torch.set_num_threads(threads)
    torch.set_num_interop_threads(1)
    from . import carrier_c1_data as data, carrier_c1_run as run, rehearsal
    from .first_batch_progress import PhaseJournal, publish
    from .s1_exclusions import Exclusions
    started = time.monotonic()
    output = Path(output)
    attempt = attempt or uuid.uuid4().hex
    if not re.fullmatch("[0-9a-f]{32}", attempt):
        raise ValueError("Invalid admission attempt identity")
    attempt_dir = output / ("attempt_"+attempt)
    attempt_dir.mkdir()
    cfg = load(pinned(config_pin))
    world = cfg.get("world_size")
    if (type(world) is not int or world not in (4, 8) or cfg.get("ground_target_filter") is not True
            or not cfg.get("dev_scene_exclusions") or not cfg.get("benchmark_scene_exclusions")
            or not cfg.get("remove_files") or cfg.get("tool_mode_flag") is not None):
        raise ValueError("Admission requires the four- or eight-rank unflagged mix and all source filter bindings")
    has_mdg = "mdg" in cfg
    presence = {} if has_mdg else dict(mdg="absent")
    if set(cfg.get("streams", {})) != {"pose", "vqa", "pointing", "routing"} | ({"mdg"} if has_mdg else set()):
        raise ValueError("Admission requires every mixed stream")
    run.validate(cfg)
    revision = run.authenticate(cfg)
    if not revision.startswith("sha256:"):
        raise ValueError("LEG-S1 admission requires its archived tree seal")
    before = dict(cfg["streams"])
    request = dict(schema="s1-admission-request-v1", config=config_pin, source_revision=revision,
                   frame_roots=[str(Path(root).resolve()) for root in roots], sample_size=sample_size,
                   cpu_threads=threads, frame_root_map=os.environ.get("STUDENT_FRAME_ROOT_MAP"),
                   rehearsal=rehearsal.enabled(), **presence)
    if (output / "request.json").exists():
        if load(output / "request.json") != request:
            raise ValueError("Admission resume belongs to another input, source or CPU configuration")
    else:
        publish(output / "request.json", request)
    phases = PhaseJournal(output, request)

    def prepare_phase(directory):
        from .mdg_parent import bind as bind_parent_grounding
        parent_grounding = bind_parent_grounding(cfg, directory)
        point = load(pinned(before["pointing"]))
        scene_filter = Exclusions(cfg["dev_scene_exclusions"], cfg["benchmark_scene_exclusions"])
        rebuilt = data.build_stream(before["pointing"], point["division"], directory / "pointing", "pointing",
                                    training_mode=cfg["training_mode"], geometry_online=cfg.get("geometry_online"),
                                    remove_files=cfg["remove_files"], ground_target_filter=True,
                                    source_receipt=True, scene_filter=scene_filter)
        vqa = load(pinned(before["vqa"]))
        rebuilt_vqa = data.build_stream(before["vqa"], vqa["division"], directory / "vqa", "vqa",
                                       training_mode=cfg["training_mode"], geometry_online=cfg.get("geometry_online"),
                                       remove_files=cfg["remove_files"], source_receipt=True,
                                       scene_filter=Exclusions(cfg["dev_scene_exclusions"],
                                                               cfg["benchmark_scene_exclusions"]))
        selected = {**cfg, "streams": {**before, "pointing": file_pin(directory / "pointing/receipt.json"),
                                       "vqa": file_pin(directory / "vqa/receipt.json")},
                    "preparation_output": str(directory / "prepared")}
        if has_mdg:
            selected["mdg"] = {**cfg["mdg"], "confusers": parent_grounding["confusers"]}
        routing_outputs = []
        if cfg.get("s1_routing"):
            from .mdg_parent import model_pin
            from .s1_routing import build as build_routing
            routed = build_routing(cfg, directory / "routing", point["division"], model_pin(cfg))
            selected["streams"]["routing"] = file_pin(directory / "routing/receipt.json")
            routing_outputs = [selected["streams"]["routing"], routed["database"], routed["materialization"],
                               *local_pins(load(pinned(routed["materialization"])), directory)]
            if cfg.get('r1_training'):
                from .r1_routing import compose_native
                composed = compose_native(cfg, selected['streams']['routing'], directory/'composed')
                selected['streams']['routing'] = file_pin(directory/'composed/receipt.json')
                routing_outputs.extend([selected['streams']['routing'], composed['database'], composed['source_membership']])
        selected.pop("preparation", None)
        selected.pop("admission", None)
        selected["recipe"] = run.recipe_for(selected)
        if selected.get('r1_training',{}).get('handover_receipt'):
            from .r1_handover import bind_target
            selected = bind_target(selected,directory/'handover.json')
        receipt = run.prepare(selected)
        preparation = directory / "prepared/receipt.json"
        if not has_mdg:
            receipt = {**receipt, "stream_status": presence, "native_preparation": file_pin(preparation)}
            preparation = directory / "prepared/s1_receipt.json"
            write(preparation, receipt)
        selected["preparation"] = file_pin(preparation)
        write(directory / "config.json", selected)
        return dict(config=file_pin(directory / "config.json"), pointing=selected["streams"]["pointing"],
                    vqa=selected["streams"]["vqa"],
                    parent_grounding=file_pin(directory / "parent_grounding.json"),
                    **(dict(routing=selected["streams"]["routing"],
                            routing_materialization=routed["materialization"]) if routing_outputs else {}),
                    outputs=[file_pin(directory / "config.json"), selected["preparation"],
                             selected["streams"]["pointing"], rebuilt["database"],
                             selected["streams"]["vqa"], rebuilt_vqa["database"],
                             *([parent_grounding["confusers"]] if has_mdg else []),
                             file_pin(directory / "parent_grounding.json"),
                             *routing_outputs, *local_pins(receipt, directory)], **presence)

    prepared, prep_reused = phases.run("prepare", prepare_phase)
    cfg = load(pinned(prepared["config"]))
    rebuilt = load(pinned(prepared["pointing"]))
    rebuilt_vqa = load(pinned(prepared["vqa"]))
    parent_grounding = load(pinned(prepared["parent_grounding"]))
    receipt, _ = run.prepared(cfg)
    if "source_seal" not in receipt:
        raise ValueError("Preparation lacks its tree/configuration seal")

    def frame_phase(directory):
        frames = audit_frames(receipt, roots, directory, sample_size=sample_size)
        frames.update(presence)
        write(directory / "frames.json", frames)
        return dict(report=file_pin(directory / "frames.json"),
                    outputs=[file_pin(directory / "frames.json"), frames["inventory"]], **presence)

    frame_result, frames_reused = phases.run("frames", frame_phase)
    frames = load(pinned(frame_result["report"]))
    if frames_reused:
        verify_frames(frames)
    mdg_fields, grounding_fields = presence, {}
    if has_mdg:
        mdg = load(pinned(receipt["streams"]["mdg"]["index"]))
        if not isinstance(mdg.get("target_filter"), dict):
            raise ValueError("MDG admission lacks mask-source accounting")
        mdg_fields = dict(mdg_targets=mdg["target_filter"])
        grounding_fields = dict(rebuilt_confusers=parent_grounding["confusers"],
                                changed_confuser_classes=parent_grounding["changed_confuser_classes"])
    data_receipt = dict(schema="s1-in-job-data-v1", status="PREPARED", production_authorized=False,
        gpu_first_step_pending=True, input_config=config_pin, config=prepared["config"],
        source_revision=revision, source_seal=receipt["source_seal"], preparation=cfg["preparation"],
        input_streams=before, world_size=world,
        source_counts={key: value["count"] for key, value in receipt["streams"].items()},
        scene_exclusions=receipt["scene_filter_report"], pointing_scene_exclusions=rebuilt["source_scene_exclusions"],
        vqa_scene_exclusions=rebuilt_vqa["source_scene_exclusions"], vqa_removals=rebuilt_vqa["removals"],
        pointing_targets=rebuilt["target_filter"], frames=frame_result["report"], **mdg_fields,
        parent_grounding=prepared["parent_grounding"],
        **(dict(routing_materialization=prepared["routing_materialization"]) if "routing" in prepared else {}),
        **grounding_fields,
        real_frames_verified=not rehearsal.enabled(), rehearsal=rehearsal.enabled(),
        phase_resources=dict(prepare=prepared["resources"], frames=frame_result["resources"]))
    if (output / "data_receipt.json").exists():
        if load(output / "data_receipt.json") != data_receipt:
            raise ValueError("Prepared data receipt changed across admission attempts")
    else:
        publish(output / "data_receipt.json", data_receipt)
    if prepare_only:
        return data_receipt
    report = attempt_dir / "first_batch_report.json"
    batch_started = time.perf_counter()
    run.first_batch_check(cfg, list(range(world)), report, steps=1, device="cpu",
                          progress_dir=output / "first_batch_progress", rank_limit=rank_limit)
    batch_seconds = time.perf_counter()-batch_started
    native = load(report)
    expected = {(rank, stream) for rank in range(world) for stream in cfg["recipe"]["mix"]}
    observed = {(row["rank"], row["stream"]) for row in native["records"] if row.get("finite") is True}
    if not expected <= observed:
        if native["status"] != "PARTIAL" or rank_limit is None:
            raise ValueError("First batch lacks a finite rank/stream pair")
        write(attempt_dir / "partial.json", dict(status="PARTIAL", production_authorized=False,
              report=file_pin(report), completed_ranks=native["completed_ranks"],
              preparation=prepared["resources"], frames=frame_result["resources"], **presence))
        raise SystemExit(75)
    if (output / "receipt.json").exists():
        existing = load(output / "receipt.json")
        first = load(pinned(existing["first_batch"]))
        original = load(pinned(first["report"]))
        if (existing.get("config") != prepared["config"] or existing.get("source_seal") != receipt["source_seal"]
                or native["resources"]["model_loads"] != 0 or original["records"] != native["records"]):
            raise ValueError("Completed CPU admission does not match its resumed rank proofs")
        write(attempt_dir / "verified.json", dict(status="PASS", production_authorized=False,
              receipt=file_pin(output / "receipt.json"), current_report=file_pin(report), **presence))
        return existing
    first = dict(schema="s1-first-batch-binding-v1", config_sha256=run.identity(cfg), source_revision=revision,
                 preparation=cfg["preparation"], streams=cfg["streams"], source_seal=receipt["source_seal"],
                 real_rgb_verified=not rehearsal.enabled(), native_full_forward=True, report=file_pin(report), **presence)
    write(attempt_dir / "first_batch.json", first)
    from .row_removals import Removals
    lists = [{key: value for key, value in row.items()
              if key in ("file", "source_listed", "listed", "retained_by_filter")}
             for row in Removals(cfg["remove_files"]).report()]
    result = dict(schema="s1-orchard-admission-v1", status="PASS", production_authorized=False,
                  independent_review=False, input_config=config_pin, config=prepared["config"],
                  source_revision=revision, source_seal=receipt["source_seal"], preparation=cfg["preparation"],
                  input_streams=before, source_counts={key: value["count"] for key, value in receipt["streams"].items()},
                  scene_exclusions=receipt["scene_filter_report"],
                  pointing_scene_exclusions=rebuilt["source_scene_exclusions"],
                  vqa_scene_exclusions=rebuilt_vqa["source_scene_exclusions"], vqa_removals=rebuilt_vqa["removals"],
                  pointing_targets=rebuilt["target_filter"], **mdg_fields,
                  removal_list_readiness=lists, frames=frame_result["report"],
                  first_batch=file_pin(attempt_dir / "first_batch.json"), rehearsal=rehearsal.enabled(),
                  phase_resources=dict(prepare=prepared["resources"], frames=frame_result["resources"]),
                  reused_phases=dict(prepare=prep_reused, frames=frames_reused),
                  first_batch_resources=native["resources"], rank_resources=native["rank_resources"],
                  resources=dict(cpu_threads=threads, ranks_checked=world, concurrent_model_copies=1, device="cpu",
                                 memory_limit_gib=memory_gib, peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                                 first_batch_seconds=batch_seconds, wall_limit_seconds=max_seconds,
                                 elapsed_seconds=time.monotonic()-started))
    publish(output / "receipt.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--frame-root", action="append", required=True)
    parser.add_argument("--threads", type=int, default=16)
    parser.add_argument("--memory-gib", type=int, default=256)
    parser.add_argument("--sample-size", type=int, default=64)
    parser.add_argument("--max-seconds", type=int, default=86400)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--rank-limit", type=int)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--attempt")
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if not any(output.is_relative_to(root) and output != root for root in (Path("/scratch"), Path("/tmp/jjyeung"))):
        raise ValueError("Admission writes must stay in owned node-local scratch")
    if args.worker:
        admit(file_pin(args.config), output, args.frame_root, threads=args.threads,
              memory_gib=args.memory_gib, sample_size=args.sample_size, max_seconds=args.max_seconds,
              rank_limit=args.rank_limit, attempt=args.attempt, prepare_only=args.prepare_only)
        return
    if (not 1 <= args.threads <= 16 or not 8 <= args.memory_gib <= 512 or not 1 <= args.max_seconds <= 86400
            or args.sample_size < 1 or (args.rank_limit is not None and not 1 <= args.rank_limit <= 8)):
        raise ValueError("Invalid admission resource or sampling bound")
    if args.resume:
        if not output.is_dir():
            raise ValueError("Admission resume directory is absent")
    else:
        output.mkdir()
    lock = (output / "admission.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    environment = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "PYTHONDONTWRITEBYTECODE": "1",
                   "OMP_NUM_THREADS": str(args.threads), "MKL_NUM_THREADS": str(args.threads),
                   "OPENBLAS_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"}
    attempt = uuid.uuid4().hex
    command = [sys.executable, "-B", "-m", "student_pilot.s1_admission", *sys.argv[1:],
               "--worker", "--attempt", attempt]
    started = time.monotonic()
    log_path = output / ("admission_"+attempt+".log")
    with log_path.open("x") as log:
        child = subprocess.Popen(command, env=environment, stdout=log, stderr=subprocess.STDOUT,
                                 start_new_session=True)

        def stop_child(sig):
            if child.poll() is None:
                os.killpg(child.pid, sig)
            try:
                child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()

        def interrupted(sig, frame):
            stop_child(sig)
            raise InterruptedError(sig)

        handlers = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGINT, signal.SIGTERM)}
        try:
            code = child.wait(timeout=args.max_seconds)
        except subprocess.TimeoutExpired:
            stop_child(signal.SIGTERM)
            code = 124
        except InterruptedError as error:
            code = 128+int(error.args[0])
        finally:
            for sig, handler in handlers.items():
                signal.signal(sig, handler)
    if code:
        write(output / ("attempt_result_"+attempt+".json"), dict(schema="s1-orchard-admission-attempt-v1",
              status="PARTIAL" if code == 75 else "FAIL",
              production_authorized=False, returncode=code, seconds=time.monotonic()-started,
              max_seconds=args.max_seconds, log=file_pin(log_path)))
        raise SystemExit(code)
    final = output / ("data_receipt.json" if args.prepare_only else "receipt.json")
    result = load(final)
    status = "PREPARED" if args.prepare_only else "PASS"
    if result.get("status") != status or result.get("production_authorized") is not False:
        raise ValueError("Admission worker lacks its completed CPU-only receipt")
    write(output / ("attempt_result_"+attempt+".json"), dict(schema="s1-orchard-admission-attempt-v1", status=status,
          production_authorized=False, returncode=code, seconds=time.monotonic()-started,
          max_seconds=args.max_seconds, log=file_pin(log_path), receipt=file_pin(final)))
    print(json.dumps(dict(status=status, receipt=file_pin(final), production_authorized=False)))


if __name__ == "__main__":
    main()
