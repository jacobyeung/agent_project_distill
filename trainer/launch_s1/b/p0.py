import argparse
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


METADATA = ("a", "d", "g", "i", "r8", "w", "v", "x", "sg", "ab", "b3900003", "kitx", "s", "z", "f2")
TRAINING = ("s1_admission", "trace_version", "s1_route_policy", "row_removals", "s1_exclusions",
            "pose_source_guard", "students", "c1_pose_mix", "ground_target_filter", "stageb_mdg",
            "source_seal", "camera_targets", "ground_tokens", "c1r_align", "gf1", "trained_groups",
            "checkpoint_space")


def main(root, mode, metadata_only=False):
    root = Path(root).resolve()
    sys.path.insert(0, str(root / "b"))
    from q0 import enabled
    from v import write
    job = os.environ.get("SLURM_JOB_ID", "")
    if not job.isdecimal():
        raise ValueError("Preflight requires the actual numeric allocation identity")
    phase = "metadata" if metadata_only else "runtime"
    report = dict(schema="s1-production-import-preflight-v1", status="FAIL", phase=phase, mode=mode,
                  job_id=job, cwd=os.getcwd(), executable=sys.executable, python=sys.version,
                  environment={key: os.environ.get(key) for key in
                               ("PYTHONPATH", "PYTHONNOUSERSITE", "PYTHONDONTWRITEBYTECODE", "TRAINER",
                                "ANYHOST_JOBS", "PILOT_VENV", "TK_STAGE_ROOT", "C1_EXPECT_FLA")},
                  trainer_initially_visible=importlib.util.find_spec("student_pilot") is not None,
                  training_executed=False, persistent_marker_written=False)
    started = time.monotonic()
    try:
        if enabled():
            raise ValueError("Production preflight refuses CPU rehearsal mode")
        if report["trainer_initially_visible"]:
            raise ValueError("Trainer is visible before source authentication")
        for name in METADATA:
            importlib.import_module(name)
        import i
        import w
        i.authorize(root, "p", "0")
        report["worker_command"] = i.main(str(root), "p", "0", preflight=True)
        if not metadata_only:
            current = json.loads((root / "k/0.json").read_text())
            closure = Path(os.environ["ANYHOST_JOBS"])
            expected = [str(root / "b"), str(closure), str(closure / "site_alias")]
            if "np" in current:
                expected.insert(0, str(Path(os.environ["TK_STAGE_ROOT"]) / "np226"))
            if mode in ("t", "u"):
                expected.insert(0, str(Path(current["fla"]["file"]).parent / "p"))
                if os.environ.get("C1_EXPECT_FLA") != "1":
                    raise ValueError("Training preflight requires the production FLA overlay")
            if os.environ.get("PYTHONPATH", "").split(os.pathsep) != expected:
                raise ValueError("Production Python path differs from its staged layout")
            w.main(str(root), "p", "0", preflight=True)
            for name in TRAINING:
                importlib.import_module("student_pilot."+name)
            for name in ("torch.distributed.run", "torch.distributed.fsdp",
                         "transformers.models.qwen3_5.modeling_qwen3_5"):
                importlib.import_module(name)
            if mode in ("t", "u"):
                for name, version in (("fla", "0.6.0"), ("triton", "3.7.1")):
                    module = importlib.import_module(name)
                    if getattr(module, "__version__", None) != version:
                        raise ValueError("Training dependency version differs: "+name)
                    if name == "fla" and not Path(module.__file__).resolve().is_relative_to(Path(expected[0]).resolve()):
                        raise ValueError("Training dependency resolves outside the pinned overlay: "+name)
            trainer = Path(os.environ["TRAINER"]).resolve()
            for name, module in list(sys.modules.items()):
                if name == "student_pilot" or name.startswith("student_pilot."):
                    path = getattr(module, "__file__", None)
                    if path is None or not Path(path).resolve().is_relative_to(trainer):
                        raise ValueError("Trainer module resolves outside the authenticated tree: "+name)
            report["trainer"] = str(trainer)
        report["status"] = "PASS"
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        report["seconds"] = time.monotonic()-started
        report["sys_path"] = list(sys.path)
        report["module_origins"] = {name: getattr(module, "__file__", None)
                                    for name, module in sorted(sys.modules.items())}
        destination = root / "o" / f"{job}.preflight.{phase}.{mode}.json"
        write(destination, report)
        print(json.dumps({key: report.get(key) for key in ("status", "phase", "mode", "seconds", "error")},
                         sort_keys=True), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    parser.add_argument("mode", choices=("p", "t", "u"))
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()
    main(args.root, args.mode, args.metadata_only)
