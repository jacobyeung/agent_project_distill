import argparse
import json
from pathlib import Path

from . import provisional_data as data
from .common import configure_environment, load_json
from .provisional import LABELS, bind_lease, request_identity, require_mode, write_artifact
from .students import STUDENTS


def main(argv=None):
    parser = argparse.ArgumentParser(description="Explicitly labeled diagnostic, provisional candidate-pool training; never clean admission")
    commands = parser.add_subparsers(dest="command", required=True)
    protocol = commands.add_parser("prepare-protocol")
    protocol.add_argument("--candidate-index", "--manifest", dest="candidate_index", required=True)
    protocol.add_argument("--holdout-fraction", "--heldout-fraction", type=float, default=0.1)
    protocol.add_argument("--student", choices=tuple(STUDENTS), default="onethinker")
    protocol.add_argument("--training-config")
    protocol.add_argument("--inherit-division", help="a published division.json whose scene sides this division must keep")
    protocol.add_argument("--init-adapter")
    protocol.add_argument("--init-adapter-weights-sha256")
    protocol.add_argument("--init-adapter-published-sha256")
    protocol.add_argument("--init-adapter-run-name")
    for name in ("prepare-training", "prepare-heldout"):
        item = commands.add_parser(name)
        item.add_argument("--protocol", required=True)
    seal = commands.add_parser("seal-source", help="validate a frozen training manifest completely once and write its source receipt")
    seal.add_argument("--manifest", required=True)
    for name in ("train", "train-ddp", "evaluate", "lease-request", "lease-request-ddp"):
        item = commands.add_parser(name)
        item.add_argument("--manifest", required=True)
        item.add_argument("--protocol", required=True)
        item.add_argument("--student", choices=tuple(STUDENTS), default="onethinker")
        if name == "lease-request":
            item.add_argument("--mode", choices=("train", "evaluate"), required=True)
            item.add_argument("--variant", choices=("original", "adapter"))
        elif name == "lease-request-ddp":
            item.add_argument("--world-size", type=int, choices=range(2, 65), required=True)
        else:
            item.add_argument("--lease", required=True)
            item.add_argument("--stage-frames", action="store_true")
        if name == "train-ddp":
            item.add_argument("--training-config")
            item.add_argument("--parallel", choices=("ddp", "fsdp"), default="ddp")
            item.add_argument("--resume-from")
            item.add_argument("--init-adapter", help="relocated source for the already frozen parent; never applied on resume")
        if name == "evaluate":
            item.add_argument("--variant", choices=("original", "adapter"), required=True)
            item.add_argument("--training-run")
    lease = commands.add_parser("bind-lease")
    lease.add_argument("--lease", required=True)
    lease.add_argument("--request", required=True)
    leases = commands.add_parser("bind-lease-ddp")
    leases.add_argument("--leases", "--lease", nargs="+", required=True)
    leases.add_argument("--request", required=True)
    leases.add_argument("--node-rank", type=int)
    leases.add_argument("--nnodes", type=int, default=1)
    merge = commands.add_parser("merge-lease-ddp")
    merge.add_argument("--partials", nargs="+", required=True)
    merge.add_argument("--request", required=True)
    publish = commands.add_parser("finalize")
    publish.add_argument("--training-run", required=True)
    publish.add_argument("--evaluation-run")
    publish.add_argument("--publish-root", required=True)
    again = commands.add_parser("republish")
    again.add_argument("--publication", required=True)
    again.add_argument("--publish-root")
    again.add_argument("--dry-run", action="store_true")
    score = commands.add_parser("score")
    score.add_argument("--original-run", "--run", dest="run", required=True)
    compare = commands.add_parser("compare")
    compare.add_argument("--original-score", required=True)
    compare.add_argument("--adapter-score", required=True)
    for name, item in commands.choices.items():
        item.add_argument("--provisional-diagnostic", choices=LABELS, required=True)
        item.add_argument("--scratch-root", required=name in ("train", "train-ddp", "evaluate", "finalize"))
        if name != "finalize":
            item.add_argument("--output", required=name != "republish")
    args = parser.parse_args(argv)
    label = args.provisional_diagnostic
    if args.command == "prepare-training" and args.scratch_root:
        configure_environment(Path(args.scratch_root) / "provisional_cpu_runtime")
    if args.command == "prepare-protocol":
        initialization = {name: getattr(args, name) for name in ("init_adapter", "init_adapter_weights_sha256",
                          "init_adapter_published_sha256", "init_adapter_run_name") if getattr(args, name) is not None}
        result = data.prepare_protocol(args.candidate_index, args.output, label, args.student, args.holdout_fraction,
                                       args.scratch_root, training_config=args.training_config,
                                       inherit_division=args.inherit_division, **initialization)
    elif args.command == "prepare-training":
        result = data.prepare_training(args.protocol, args.output, label, args.scratch_root)
    elif args.command == "seal-source":
        result = data.seal_source(args.manifest, args.output, label, args.scratch_root)
    elif args.command == "prepare-heldout":
        result = data.prepare_heldout(args.protocol, args.output, label, args.scratch_root)
    elif args.command == "lease-request":
        data.load_protocol(args.protocol, label, student=args.student)
        loader = data.load_training if args.mode == "train" else data.load_heldout
        loader(args.manifest, label)
        result = request_identity(args.mode, args.student, args.manifest, args.protocol, label, args.variant)
        write_artifact(args.output, result, label, args.scratch_root)
    elif args.command == "lease-request-ddp":
        from .ddp_admission import request_identity as ddp_request
        data.load_protocol(args.protocol, label, student=args.student)
        data.load_training(args.manifest, label)
        result = ddp_request(args.manifest, args.protocol, label, args.student, args.world_size)
        write_artifact(args.output, result, label, args.scratch_root)
    elif args.command == "bind-lease":
        request = require_mode(load_json(args.request), label)
        result = bind_lease(args.lease, args.output, label, request["work_id"], request["protocol_sha256"])
    elif args.command == "bind-lease-ddp":
        from .ddp_admission import bind_leases
        result = bind_leases(args.leases, args.request, args.output, label, args.scratch_root,
                             node_rank=args.node_rank, nnodes=args.nnodes)
    elif args.command == "merge-lease-ddp":
        from .ddp_admission import merge_leases
        result = merge_leases(args.partials, args.request, args.output, label, args.scratch_root)
    elif args.command == "train-ddp":
        from .ddp_training import train
        result = train(args.manifest, args.protocol, args.output, args.lease, args.student,
                       args.scratch_root, args.stage_frames, label, args.training_config, parallel=args.parallel,
                       resume_from=args.resume_from, **({"init_adapter": args.init_adapter} if args.init_adapter is not None else {}))
    elif args.command == "train":
        from .diagnostic import train
        result = train(args.manifest, args.protocol, args.output, args.lease, args.student,
                       args.scratch_root, args.stage_frames, provisional_diagnostic=label)
    elif args.command == "evaluate":
        from .diagnostic import evaluate
        result = evaluate(args.manifest, args.protocol, args.output, args.lease, args.variant, args.training_run,
                          student=args.student, scratch_root=args.scratch_root, stage_frames=args.stage_frames,
                          provisional_diagnostic=label)
    elif args.command == "finalize":
        from .storage import finalize
        result = finalize(args.training_run, args.publish_root, args.scratch_root, args.evaluation_run, provisional_diagnostic=label)
    elif args.command == "republish":
        from .republish import republish
        result = republish(args.publication, args.publish_root, label, args.dry_run, args.output)
    elif args.command == "score":
        result = data.score_run(args.run, args.output, label, args.scratch_root)
    else:
        result = data.compare_scores(args.original_score, args.adapter_score, args.output, label, args.scratch_root)
    print(json.dumps(result, sort_keys=True, indent=2))
    if args.command == "train-ddp":
        from .camera_gate import exit_status
        return exit_status(result)
    return 0
