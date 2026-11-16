import argparse
import base64
from copy import deepcopy
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import re
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import native_common as C
import orchard_launcher as L
import native_stage as S
import native_metrics as M

NATIVE = ("native_common.py", "native_stage.py", "native_job.py", "native_worker.py",
          "native_launcher.py", "kernels.py", "native_metrics.py", "native_local_check.py",
          "native_pin_graph.py", "native_cpu_replica.py")
CORE = ("orchard_launcher.py", "orchard_job.py", "orchard_stage.py", "orchard_results.py",
        "chain_save.py", "stdout_transfer.py", "native_bootstrap.py", "ORCHARD_ASSETS.json")
DIRECT_DIGEST = "555eb7395150722208b4d3652f53b10571e5d732fc780ba0a99c6a3085e93bc4"


def bootstrap_sources():
    root = Path(__file__).resolve().parent
    return {**{name: root.parent/name for name in CORE},
            **{"orchard_native/"+name: root/name for name in NATIVE}}


def seal(assets, contract, destination):
    if set(contract) != C.WORKER_FIELDS:
        raise ValueError("Native family worker contract is incomplete")
    direct = {str(C.LOGICAL_ROOT/name): C.sha(C.ROOT/name) for name in L.CORE}
    if L.canonical(direct) != DIRECT_DIGEST:
        raise ValueError("The accepted direct launcher differs; native sealing stops")
    for part in assets["small_objects"]:
        S.cloud_uri(part)
    sources = bootstrap_sources()
    code_pins = {**{str(C.LOGICAL_ROOT/name): C.sha(path) for name, path in sources.items()},
                 **contract["adapter_pins"]}
    entrypoint = assets.get("worker_entrypoint", {})
    if entrypoint.get("path") not in code_pins or code_pins[entrypoint["path"]] != entrypoint.get("sha256"):
        raise ValueError("The runtime worker entrypoint differs from its code pin")
    mask = contract["mask_cache"]
    if mask.get("path") == str(C.LOGICAL_ROOT/"orchard_native/MASK_CACHE_P6_BOUND.json"):
        source = Path(__file__).resolve().parent/"MASK_CACHE_P6_BOUND.json"
        if C.sha(source) != mask["sha256"]:
            raise ValueError("The mask receipt differs from its shipped code member")
        code_pins[mask["path"]] = mask["sha256"]
    value = dict(
        schema="evalx-orchard-native-family-v1", synthetic=False, modes=["pilot", "full"],
        partitions=["general", "advanced"], assets=assets, worker_contract=contract,
        bootstrap_pins={name: C.sha(path) for name, path in sources.items()},
        code_pins=code_pins,
        direct_launcher_digest=DIRECT_DIGEST,
        limits={mode: dict(gpu_seconds=2400 if mode == "pilot" else 21600,
                           stall_seconds=1200, poll_seconds=30,
                           return_bytes=256*1024**2, pool_bytes=1024**3)
                for mode in ("pilot", "full")})
    C.dump(destination, value)
    return C.pin(destination)


def render_batch(bundle, token):
    script = L.render_batch(bundle, token)
    changes = {
        "exec python3 -I -s -B": "exec /usr/bin/python3 -I -s -B",
        "('evalx_'+job": "('evalx_native_'+job",
        "root/'bootstrap/orchard_job.py'": "root/'bootstrap/orchard_native/native_job.py'"}
    for before, after in changes.items():
        if script.count(before) != 1:
            raise ValueError("Accepted batch template changed")
        script = script.replace(before, after)
    return script


def batch_files(config, family, review, order):
    sources = bootstrap_sources()
    if {name: C.sha(path) for name, path in sources.items()} != family["bootstrap_pins"]:
        raise ValueError("Native bootstrap changed after family admission")
    files = {"bootstrap/"+name: path.read_bytes() for name, path in sources.items()}
    files.update({
        "bootstrap/CONFIG.json": (json.dumps(config, indent=2, sort_keys=True)+"\n").encode(),
        "bootstrap/FAMILY.json": family["bytes"],
        "bootstrap/REVIEW.json": review,
        "bootstrap/ORDER.md": order})
    return files


def prepare(family_path, review_path, order_path, artifact_path, transport_path,
            mode, partition, token, destination, pilot_receipt=None, pilot_archive=None,
            projection_scenario=None):
    if mode == "full" and projection_scenario not in M.SCENARIOS:
        raise ValueError("Full preparation requires an explicit projection scenario")
    if mode != "full" and projection_scenario is not None:
        raise ValueError("Only a full packet takes a projection scenario")
    L.valid_token(token)
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Native submission destination already exists")
    family, review = C.load(family_path), C.load(review_path)
    artifact, transport = C.load(artifact_path), C.load(transport_path)
    step, artifact_sha = artifact["step"], C.sha(artifact_path)
    logical = C.LOGICAL_ROOT/"orchard_native/submissions"/token
    config = dict(
        schema=C.SCHEMA, synthetic=False, build_only=False, token=token,
        mode=mode, partition=partition, step=step, gpus=1,
        logical_run=str(C.LOGICAL_ROOT/"runs"/token),
        assets=deepcopy(family["assets"]), limits=deepcopy(family["limits"][mode]),
        worker=dict(deepcopy(family["worker_contract"]),
                    artifact=dict(path="/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/"
                                  "jyeung/ap/8865619b/runs/469ddece/m"+str(step)+"/artifact.json",
                                  sha256=artifact_sha)),
        family=dict(path=str(logical/"FAMILY.json"), sha256=C.sha(family_path)),
        review=dict(path=str(logical/"REVIEW.json"), sha256=C.sha(review_path)),
        transport=transport)
    if mode == "full":
        if pilot_receipt is None or pilot_archive is None:
            raise ValueError("A full packet requires its passed pilot receipt and archive")
        config["full_projection"] = M.from_return(
            pilot_receipt, pilot_archive, config["family"]["sha256"], config["worker"]["artifact"],
            projection_scenario)
        if config["full_projection"]["report"]["artifact"] != config["worker"]["artifact"]:
            raise ValueError("The full packet artifact differs from its passed pilot")
    elif pilot_receipt is not None or pilot_archive is not None:
        raise ValueError("Pilot packets do not take full-return projection evidence")
    config["authorization"] = dict(
        issuer="ORCH", site="orchard", mode=mode, token=token, partition=partition,
        step=step, gpus=1, family_sha256=config["family"]["sha256"], artifact_sha256=artifact_sha,
        orch_order=dict(path=str(logical/"ORDER.md"), sha256=C.sha(order_path)))
    if mode == "full":
        config["authorization"]["projection_scenario"] = projection_scenario
    config["plan_sha256"] = C.plan(config)
    C.admit(config, family, review)
    C.validate_order(Path(order_path).read_text(), config)
    frozen = dict(family, bytes=Path(family_path).read_bytes())
    files = batch_files(config, frozen, Path(review_path).read_bytes(), Path(order_path).read_bytes())
    script = render_batch(L.tar_bytes(files), token)
    destination.mkdir(mode=0o700)
    for name, data in (("CONFIG.json", files["bootstrap/CONFIG.json"]),
                       ("FAMILY.json", files["bootstrap/FAMILY.json"]),
                       ("REVIEW.json", files["bootstrap/REVIEW.json"]),
                       ("ORDER.md", files["bootstrap/ORDER.md"]), ("BATCH.sh", script.encode())):
        with (destination/name).open("xb") as stream:
            stream.write(data)
    C.dump(destination/"PACKET.json", dict(
        schema="evalx-orchard-native-packet-v1", synthetic=False, config=C.pin(destination/"CONFIG.json"),
        batch=C.pin(destination/"BATCH.sh"), mode=mode, partition=partition,
        plan_sha256=config["plan_sha256"], submitted=False))
    return config


def validate_batch(script, config, family, review, order):
    match = re.search(r"^raw=base64\.b64decode\('([A-Za-z0-9+/=]+)',validate=True\)$", script, re.M)
    if not match:
        raise ValueError("Native batch has no embedded package")
    bundle = base64.b64decode(match[1], validate=True)
    if render_batch(bundle, config["token"]) != script:
        raise ValueError("Native batch differs from its admitted template")
    files, total = {}, 0
    with tarfile.open(fileobj=io.BytesIO(bundle)) as archive:
        for entry in archive:
            total += entry.size
            if (not entry.isfile() or entry.name in files or len(files) >= 64
                    or entry.size < 0 or total > 32*1024**2):
                raise ValueError("Native bootstrap inventory differs")
            S.S.relative(entry.name)
            files[entry.name] = archive.extractfile(entry).read()
    if files != batch_files(config, family, review, order):
        raise ValueError("Native batch evidence differs from its packet")


def submit_argv(config):
    C.validate_config(config, launch=False)
    return ["/usr/local/bin/sbatch", "--parsable", "--account=mt01",
            "--partition="+config["partition"], "--nodes=1", "--ntasks=1", "--gres=gpu:1",
            "--cpus-per-task=16", "--mem=200G",
            "--time="+("01:30:00" if config["mode"] == "pilot" else "07:00:00"),
            "--signal=B:USR1@300", "--no-requeue", "--output=/dev/null", "--error=/dev/null",
            "--chdir=/tmp", "--job-name=a15_cot_ap"+config["token"]]


def submit_command(config):
    command = L.submit_command(config["token"])
    before = "argv="+repr(L.submit_argv(None, config["token"]))+"\n"
    if command[-1].count(before) != 1:
        raise ValueError("The accepted submission wrapper changed")
    command[-1] = command[-1].replace(before, "argv="+repr(submit_argv(config))+"\n")
    command[0] = "/usr/bin/python3"
    return command


def submit(destination):
    destination = Path(destination)
    config = C.load(destination/"CONFIG.json")
    family = C.load(destination/"FAMILY.json")
    review = C.load(destination/"REVIEW.json")
    order = (destination/"ORDER.md").read_bytes()
    C.admit(config, family, review)
    C.validate_order(order.decode(), config)
    for field, name in (("family", "FAMILY.json"), ("review", "REVIEW.json")):
        if C.sha(destination/name) != config[field]["sha256"]:
            raise ValueError("Native admission bytes differ")
    if C.sha(destination/"ORDER.md") != config["authorization"]["orch_order"]["sha256"]:
        raise ValueError("Native launch order changed")
    frozen = dict(family, bytes=(destination/"FAMILY.json").read_bytes())
    script = (destination/"BATCH.sh").read_text()
    validate_batch(script, config, frozen, (destination/"REVIEW.json").read_bytes(), order)
    if (destination/"SUBMIT_INTENT.json").exists():
        raise ValueError("A native submission intent exists; reconcile it without retry")
    import native_local_check as I
    I.admit(destination, config, family,
            batch_files(config, frozen, (destination/"REVIEW.json").read_bytes(), order))
    queue = L.remote(["env", "TZ=UTC", "squeue", "-h", "-u", "jjyeung", "-p",
                      config["partition"], "-o", "%i|%j|%u|%T|%b"], text=True)
    C.dump(destination/"QUEUE_CHECK.json", dict(returncode=queue.returncode,
        stdout=queue.stdout, stderr=queue.stderr, checked_utc=datetime.now(timezone.utc).isoformat()))
    if queue.returncode:
        raise RuntimeError("Native queue observation failed; no retry")
    lines = [line for line in queue.stdout.splitlines() if line.strip()]
    if config["partition"] == "general":
        L.queue_admission(queue.stdout, "jjyeung")
    elif any(line.split("|")[0] == "169097" or "|a15_cot_ap" in line for line in lines):
        raise ValueError("The production or project allocation still holds the advanced slot")
    with L.NOTICES.open("rb") as stream:
        stream.seek(max(0, L.NOTICES.stat().st_size-32768))
        notice = stream.read(32768)
    with (destination/"MAIN_NOTICES.txt").open("xb") as stream:
        stream.write(notice)
    message = (datetime.now(timezone.utc).isoformat()+" evalx native "+config["mode"]+
               " token="+config["token"]+" partition="+config["partition"]+
               " gpus=1; separate ORCH order and scoped admission verified\n")
    with L.NOTICES.open("a") as stream:
        stream.write(message)
        stream.flush()
    C.dump(destination/"SUBMIT_INTENT.json", dict(
        token=config["token"], plan_sha256=config["plan_sha256"],
        utc=datetime.now(timezone.utc).isoformat(), argv=submit_argv(config)))
    result = L.remote(submit_command(config), input=script, text=True)
    value = dict(token=config["token"], plan_sha256=config["plan_sha256"],
                 returncode=result.returncode, stdout=result.stdout, stderr=result.stderr,
                 status="SUBMISSION_UNCERTAIN", job=None)
    if result.returncode == 0 and re.fullmatch(r"\d+(;[A-Za-z0-9_-]+)?\n?", result.stdout):
        value.update(status="SUBMITTED", job=int(result.stdout.split(";")[0].strip()))
    C.dump(destination/"SUBMISSION.json", value)
    return value


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    for name in ("family", "review", "order", "artifact", "transport", "token", "destination"):
        prepare_parser.add_argument("--"+name, required=True)
    prepare_parser.add_argument("--mode", choices=("pilot", "full"), required=True)
    prepare_parser.add_argument("--partition", choices=("general", "advanced"), required=True)
    prepare_parser.add_argument("--pilot-receipt")
    prepare_parser.add_argument("--pilot-archive")
    prepare_parser.add_argument("--projection-scenario", choices=M.SCENARIOS)
    for name in ("submit", "fetch"):
        sub.add_parser(name).add_argument("--destination", required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        value = prepare(args.family, args.review, args.order, args.artifact, args.transport,
                        args.mode, args.partition, args.token, args.destination,
                        args.pilot_receipt, args.pilot_archive, args.projection_scenario)
    elif args.command == "submit":
        value = submit(args.destination)
    else:
        value = L.fetch(args.destination)
    print(json.dumps(value, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
