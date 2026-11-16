import argparse
import json
import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

from .common import ARTIFACTS, REPO, configure_environment


def main():
    sys.dont_write_bytecode = True
    configure_environment()
    for key, path in {"CUDA_CACHE_PATH": REPO / ".cache/cuda", "TORCHINDUCTOR_CACHE_DIR": REPO / ".cache/torchinductor"}.items():
        path.mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(path)
    parser = argparse.ArgumentParser(description="Source-backed RGB infrastructure smoke; never a benchmark-improvement claim")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("cpu-check")
    check.add_argument("--manifest")
    check.add_argument("--output", default=str(ARTIFACTS / "checks" / ("cpu_ready_" + uuid4().hex[:12] + ".json")))
    candidate = commands.add_parser("inspect-smoke-candidate")
    candidate.add_argument("--qid", default="1506")
    candidate.add_argument("--output", default=str(ARTIFACTS / "checks/smoke_candidate.json"))
    prepare = commands.add_parser("prepare-smoke")
    prepare.add_argument("--qid", default="1506")
    prepare.add_argument("--answer-key")
    prepare.add_argument("--output", default=str(ARTIFACTS / "data/smoke.json"))
    smoke = commands.add_parser("smoke")
    smoke.add_argument("--manifest", default=str(ARTIFACTS / "data/smoke.json"))
    smoke.add_argument("--lease", required=True)
    smoke.add_argument("--output", default=str(ARTIFACTS / "runs" / (datetime.now(timezone.utc).strftime("smoke_%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])))
    smoke.add_argument("--learning-rate", type=float, default=1e-5)
    args = parser.parse_args()
    if args.command == "cpu-check":
        from .checks import cpu_check
        result = cpu_check(args.output, args.manifest)
        print(json.dumps({key: result[key] for key in ("status", "gpu_smoke_passed", "cuda_initialized", "checkpoint_tensor_shapes_verified", "versions")}, indent=2))
        print(json.dumps({"trainable_parameters": result["adapters"]["trainable_parameters"], "group_parameters": result["adapters"]["group_parameters"], "report": args.output}, indent=2))
    elif args.command == "inspect-smoke-candidate":
        from .admission import inspect_candidate
        print(json.dumps(inspect_candidate(args.qid, args.output), indent=2))
    elif args.command == "prepare-smoke":
        from .admission import prepare_smoke
        print(json.dumps(prepare_smoke(args.qid, args.answer_key, args.output), indent=2))
    elif args.command == "smoke":
        from .runner import run_smoke
        run_smoke(args.manifest, args.output, args.lease, args.learning_rate)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, FileNotFoundError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        sys.exit(2)
