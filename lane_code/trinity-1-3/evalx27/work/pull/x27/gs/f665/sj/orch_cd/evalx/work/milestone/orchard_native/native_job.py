import argparse
import csv
import json
import os
from pathlib import Path
import pwd
import signal
import stat
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import native_common as C
import native_stage as S
import native_metrics as M
import orchard_job as J
import orchard_results as R
import chain_save as A


def progress(paths):
    total = 0
    for root in paths:
        for directory, _, names in os.walk(root, followlinks=False):
            for name in names:
                path = Path(directory)/name
                try:
                    value = path.lstat()
                except FileNotFoundError:
                    continue
                if stat.S_ISREG(value.st_mode):
                    total += value.st_size
    return total


def card(require_empty=False):
    query = subprocess.run(
        ["/usr/bin/nvidia-smi", "--query-gpu=index,uuid,name,memory.used,utilization.gpu",
         "--format=csv,noheader,nounits"], check=True, capture_output=True, text=True, timeout=30)
    processes = subprocess.run(
        ["/usr/bin/nvidia-smi", "--query-compute-apps=gpu_uuid,pid,used_memory",
         "--format=csv,noheader,nounits"], check=True, capture_output=True, text=True, timeout=30)
    own = subprocess.run(
        ["/usr/bin/pgrep", "-fu", os.environ["USER"],
         "[/]evalx/work/milestone|[/]bootstrap/orchard_native"],
        capture_output=True, text=True, timeout=30)
    visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    rows = [[item.strip() for item in row] for row in csv.reader(query.stdout.splitlines()) if row]
    assigned = rows if len(rows) == 1 else [row for row in rows if visible in row[:2]]
    if len(assigned) != 1 or assigned[0][2] != "NVIDIA H100 80GB HBM3":
        raise ValueError("The assigned card is not one authenticated H100 80GB HBM3")
    selected = assigned[0]
    if not visible or "," in visible or (visible.startswith("GPU-") and visible != selected[1]):
        raise ValueError("CUDA visibility differs from the single assigned GPU")
    if require_empty and (float(selected[3]) > 32 or float(selected[4]) != 0
                          or selected[1] in processes.stdout):
        raise ValueError("The assigned GPU is not empty at the fresh check")
    return dict(utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), job=os.environ["SLURM_JOB_ID"],
                hostname=os.uname().nodename, gpu_type=selected[2], gpu_uuid=selected[1],
                slurm_job_gpus=os.environ.get("SLURM_JOB_GPUS"), cuda_visible_devices=visible,
                nvidia_smi=query.stdout, compute_processes=processes.stdout,
                pgrep=own.stdout, pgrep_returncode=own.returncode)


def context(root, config):
    job = os.environ.get("SLURM_JOB_ID", "")
    if (not job.isdigit() or not os.uname().nodename.startswith("orchard-")
            or os.environ.get("SLURM_JOB_PARTITION") != config["partition"]
            or Path(root).resolve() != Path("/tmp")/("evalx_native_"+job+"_"+config["token"])):
        raise ValueError("Native job requires its assigned partition and private Orchard root")
    if pwd.getpwuid(os.getuid()).pw_name != "jjyeung":
        raise ValueError("The native allocation belongs to a different user")
    os.environ.update(PATH="/usr/local/bin:/usr/bin:/bin", USER="jjyeung")


def early_admission(root, config):
    bootstrap = Path(root)/"bootstrap"
    evidence = {}
    for field, filename in (("family", "FAMILY.json"), ("review", "REVIEW.json")):
        record = config[field]
        path = C.checked(dict(path=str(bootstrap/filename), sha256=record["sha256"]))
        evidence[field] = C.load(path)
    order = C.checked(dict(path=str(bootstrap/"ORDER.md"),
                           sha256=config["authorization"]["orch_order"]["sha256"]))
    C.admit(config, evidence["family"], evidence["review"])
    C.validate_order(order.read_text(), config)
    for name, digest in evidence["family"]["bootstrap_pins"].items():
        S.S.relative(name)
        C.checked(dict(path=str(bootstrap/name), sha256=digest))
    return evidence


def controls(root, config):
    bootstrap = Path(root)/"bootstrap"
    records = [(config["family"], "FAMILY.json"), (config["review"], "REVIEW.json"),
               (config["authorization"]["orch_order"], "ORDER.md")]
    for pin, name in records:
        target = S.physical(root, pin["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write((bootstrap/name).read_bytes())


def environment(root):
    value = J.environment(root)
    value.update(TRITON_CACHE_DIR=str(Path(root)/"cache/triton"),
                 TORCH_HOME=str(Path(root)/"cache/torch"), MKL_NUM_THREADS="1",
                 SLURM_JOB_PARTITION=os.environ["SLURM_JOB_PARTITION"])
    return value


def wait(process, paths, limits):
    previous = progress(paths)
    started = last_change = time.monotonic()
    while process.poll() is None:
        time.sleep(limits["poll_seconds"])
        now = time.monotonic()
        value = progress(paths)
        if value != previous:
            previous, last_change = value, now
        if now-last_change > limits["stall_seconds"]:
            raise RuntimeError("Stall guard: no phase/model/result/cache growth for 1200 seconds")
        if now-started > limits["gpu_seconds"]:
            raise RuntimeError("Native GPU phase exceeded its sealed wall-time allowance")
    if process.returncode:
        raise RuntimeError("Native worker exited with code "+str(process.returncode))
    return time.monotonic()-started


def terminal(root, config):
    run = S.physical(root, config["logical_run"])
    if config["mode"] == "pilot":
        report = C.load(run/"native/PILOT_REPORT.json")
        parity = C.load(C.checked(report["parity"], lambda p: S.physical(root, p)))
        if (report.get("synthetic") is not False or report.get("training_decision_allowed") is not False
                or report.get("full_read_authorized") is not False
                or report.get("family_sha256") != config["family"]["sha256"]
                or report.get("plan_sha256") != config["plan_sha256"]
                or report.get("artifact") != config["worker"]["artifact"]
                or report.get("selection") != config["worker"]["pilot_selection"]
                or len(report.get("items", [])) != 10 or not parity.get("pass")
                or (run/"native/R1.json").exists() or (run/"native/probe/COMPLETE.json").exists()):
            raise ValueError("Pilot evidence is incomplete, scored or foreign")
        M.project(report)
        receipts = ["native/PILOT_REPORT.json", "native/probe/GPU_PARITY.json",
                    "native/probe/items.jsonl", "native/geometry/GEOMETRY_MANIFEST.json"]
    else:
        report = C.load(run/"native/paired/IN_JOB_ADMISSION.json")
        if (report.get("synthetic") is not False or report.get("artifact") != config["worker"]["artifact"]
                or report.get("geometry_captures") != M.GEOMETRY_CAPTURES
                or report.get("geometry_capture_ids") != config["worker"]["geometry_captures"]):
            raise ValueError("Full native admission is incomplete or foreign")
        C.checked(report["bundle"], lambda p: S.physical(root, p))
        receipts = ["native/R1.json", "native/R1.json.pin.json",
                    "native/paired/IN_JOB_ADMISSION.json",
                    "native/paired/results/COMPLETE.json", "native/paired/results/GPU_PARITY.json"]
    return {name: C.sha(run/name) for name in receipts}


def run(root, config):
    root = Path(root)
    source = S.physical(root, config["logical_run"])
    process, code, failure = None, 1, None
    evidence = {}

    def interrupted(number, frame):
        raise RuntimeError("Orchard allocation signal "+str(number))

    for number in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1):
        signal.signal(number, interrupted)
    try:
        context(root, config)
        early_admission(root, config)
        evidence["storage"] = J.storage_proof(root, job=os.environ["SLURM_JOB_ID"])
        local = environment(root)
        os.environ.update({key: local[key] for key in ("HOME", "TMPDIR", "XDG_CACHE_HOME")})
        evidence["initial_card"] = card(require_empty=True)
        controls(root, config)
        evidence["staging"] = S.stage(root, config)
        C.validate_config(config, resolve=lambda p: S.physical(root, p))
        source.mkdir(parents=True)
        metadata = source/"metadata"
        metadata.mkdir()
        C.dump(metadata/"CONFIG.json", config)
        C.dump(metadata/"NATIVE_RUNTIME.json", evidence["staging"]["runtime_spec"])
        for name in ("FAMILY.json", "REVIEW.json", "ORDER.md"):
            with (metadata/name).open("xb") as stream:
                stream.write((root/"bootstrap"/name).read_bytes())
        proof = J.storage_proof(source, job=os.environ["SLURM_JOB_ID"])
        if proof["source"] != evidence["storage"]["source"]:
            raise ValueError("Native output is not on the proven job-local disk")
        evidence["launch_card"] = card(require_empty=True)
        vnice = C.checked(config["assets"]["vnice"], lambda p: S.physical(root, p))
        runtime = evidence["staging"]["runtime_spec"]
        command = S.namespace(root, config)+[
            "/bin/bash", str(vnice), runtime["python"]["path"], "-I", "-s", "-B",
            str(root/"bootstrap/native_bootstrap.py"), "--spec", str(metadata/"NATIVE_RUNTIME.json"),
            "--", config["assets"]["worker_entrypoint"]["path"],
            "--config", str(Path(config["logical_run"])/"metadata/CONFIG.json")]
        with (root/"worker.log").open("xb") as log:
            process = subprocess.Popen(command, env=environment(root), cwd=root,
                                       stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            evidence["gpu_phase_seconds"] = wait(process, [source, root/"cache"], config["limits"])
            code = process.returncode
        process = None
        receipts = terminal(root, config)
        C.dump(source/"COMPLETE.json", dict(
            schema="evalx-orchard-native-complete-v1", synthetic=False, mode=config["mode"],
            plan_sha256=config["plan_sha256"], artifact=config["worker"]["artifact"],
            family=config["family"], step=config["step"], training_decision_allowed=False,
            receipts=receipts))
    except BaseException as error:
        for number in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1):
            signal.signal(number, signal.SIG_IGN)
        failure, code = str(error), code or 1
        if isinstance(error, J.StorageRefusal):
            evidence["storage_refusal"] = error.evidence
        J.stop(process)
    finally:
        source.mkdir(parents=True, exist_ok=True)
        (source/"metadata").mkdir(exist_ok=True)
        (source/"logs").mkdir(exist_ok=True)
        try:
            evidence["final_card"] = card()
        except Exception as error:
            evidence["final_card_error"] = str(error)
            failure, code = failure or "Final GPU evidence unavailable", code or 1
        if failure:
            A.atomic_json(source/"FAILED.json", dict(error=failure, returncode=code))
        A.atomic_json(source/"metadata/ORCHARD_NATIVE.json", evidence)
        for name in ("STAGING.json",):
            if (root/name).is_file():
                (source/"metadata"/name).write_bytes((root/name).read_bytes())
        for name in ("worker.log", "staging.log"):
            path = root/name
            if path.is_file():
                with path.open("rb") as stream:
                    stream.seek(max(0, path.stat().st_size-2*1024**2))
                    (source/"logs"/name).write_bytes(stream.read(2*1024**2))
        try:
            result = R.publish(source, R.AUTHORIZED_POOL, config["token"], config["plan_sha256"], code)
            code = code if result["status"] == "COMPLETE" else code or 1
        except Exception as error:
            A.atomic_json(root/"RETURN_INCOMPLETE.json", dict(error=str(error), returncode=code or 1))
            code = code or 1
    return code


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = C.load(args.config)
    C.validate_config(config, launch=False)
    raise SystemExit(run(args.root, config))


if __name__ == "__main__":
    main()
