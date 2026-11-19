"""python -B -m derivgen: CPU-only commands, with no production defaults."""
import argparse
import os
import socket
import sys

from .common import ProvenanceError, encoded


def main():
    if socket.gethostname().split(".")[0] == "trinity":
        raise SystemExit("Agents and commands may not run on the head node")
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise SystemExit('Set CUDA_VISIBLE_DEVICES=""')
    if not sys.dont_write_bytecode:
        raise SystemExit("Run Python with -B or PYTHONDONTWRITEBYTECODE=1")
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        if os.environ.get(key) != "1": raise SystemExit("Set " + key + "=1")
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    run = sub.add_parser("generate")
    run.add_argument("--config", required=True)
    run.add_argument("--output", required=True)
    run.add_argument("--limit", type=int)
    run.add_argument("--infrastructure-only", action="store_true")
    run.add_argument("--parent-record")
    run.add_argument("--parent-record-sha256")
    run.add_argument("--input", action="append", help="Explicit configured input path; repeat in configured order")
    run.add_argument("--scene-registry", help="Explicit configured scene registry path")
    run.add_argument("--authority", help="Explicit configured physical authority path")
    native = sub.add_parser("prepare-native")
    native.add_argument("--config", required=True)
    native.add_argument("--output", required=True)
    replay = sub.add_parser("replay")
    replay.add_argument("--build", required=True)
    ground = sub.add_parser("generate-ground", help="SPEC v3.12 GT review rows")
    ground.add_argument("--config", required=True)
    ground.add_argument("--output", required=True)
    pack = sub.add_parser("pack-ground", help="Package v3.12.1 review rows with forced-response loss masks")
    pack.add_argument("--build", required=True)
    pack.add_argument("--output", required=True)
    args = p.parse_args()
    try:
        if args.command == "pack-ground":
            from .ground_v312_pack import pack
            print(encoded(pack(args.build, args.output)))
        elif args.command == "generate-ground":
            from .ground_v312_io import build
            result = build(args.config, args.output)
            print(encoded({"status": result["status"], "candidates": result["candidates"], "output": args.output}))
        elif args.command == "generate":
            from .pipeline import build
            from .common import read_json
            config = read_json(args.config)
            if args.input is not None and args.input != [p['path'] for p in config['inputs']]:
                raise ProvenanceError("--input paths must equal the pinned configuration")
            for flag, key in ((args.scene_registry, 'scene_registry'), (args.authority, 'authority')):
                if flag is not None and flag != config[key]['path']:
                    raise ProvenanceError("explicit path differs from pinned configuration: " + key)
            parent = {"path": args.parent_record, "sha256": args.parent_record_sha256} if args.parent_record and args.parent_record_sha256 else None
            result = build(args.config, args.output, args.infrastructure_only, args.limit, parent)
            print(encoded({"status": result["status"], "real_accepted": result["real_accepted"], "output": args.output}))
        elif args.command == "prepare-native":
            from .native import prepare_native
            entry = prepare_native(args.config, args.output)
            print(encoded({"gt": entry["gt"], "admission": "not granted"}))
        else:
            from .check_build import check_build
            print(encoded(check_build(args.build)))
    except ProvenanceError as exc:
        raise SystemExit("PROVENANCE FAILURE: " + str(exc)) from exc


if __name__ == "__main__": main()
