import json
from pathlib import Path
from uuid import uuid4

from .io import dump_json, json_hash, local_output, sha256, utc
from .provenance import verify_export_receipt


def fingerprint(settings):
    ignored = {"created_at", "configuration_fingerprint", "resume", "go_file", "run_host", "threads", "workers", "out"}
    return json_hash({key: value for key, value in settings.items() if key not in ignored})


def prepare_stage(path, settings, resume=False):
    root = local_output(path).resolve()
    digest = fingerprint(settings)
    if root.exists():
        if not resume:
            raise FileExistsError("An existing stage requires explicit --resume")
        previous = json.loads((root / "config.json").read_text())
        if previous.get("configuration_fingerprint") != digest or fingerprint(previous) != digest:
            raise ValueError("Resume configuration differs from the producing stage")
        return root
    root.mkdir(parents=True, exist_ok=False)
    dump_json(root / "config.json", {**settings, "created_at": utc(), "configuration_fingerprint": digest})
    return root


def preserve_files(root, paths, label):
    root = local_output(root).resolve()
    present = [Path(path) for path in paths if Path(path).exists()]
    if not present:
        return None
    destination = root / "preserved" / f"{label}_{uuid4().hex}"
    destination.mkdir(parents=True)
    for path in present:
        relative = path.resolve().relative_to(root)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        path.rename(target)
    return destination


def scene_files(root, scene):
    root = Path(root)
    return [root / f"scannet__{scene}.npz", root / "dense" / f"scannet__{scene}.npz",
            *[root / name / f"{scene}.json" for name in ("receipts", "consensus", "native_metrics", "native_recipes")]]


def resume_scene(root, scene, native_root=None, entry=None):
    root = Path(root)
    try:
        receipt = verify_export_receipt(root, scene, complete=False)
        if entry is not None:
            if receipt.get("frame_indices") != entry["dense_indices"]:
                raise ValueError("Resumed frame ordinals differ")
            hashes = receipt.get("decoded_frame_sha256")
            if not hashes or len(hashes) != len(entry["dense_indices"]):
                raise ValueError("Resumed scene has no decoded-frame proof")
            if entry.get("decoded_sha256") is not None and hashes != entry["decoded_sha256"]:
                raise ValueError("Resumed decoded frame identities differ")
            if entry.get("decoded_registry"):
                registry = json.loads(Path(entry["decoded_registry"]).read_text())
                if hashes != registry["decoded_sha256"] or registry["dense_indices"] != entry["dense_indices"]:
                    raise ValueError("Resumed scene differs from the shared decoded-frame proof")
        if receipt.get("native_depth"):
            from .contract import load_export
            from .native import verified_native
            if native_root is None:
                raise ValueError("Native storage is required to resume this scene")
            frames = load_export(root / f"scannet__{scene}.npz")["anchor_frame_indices"]
            verified_native(native_root, receipt["native_depth"], frames)
        return receipt
    except (FileNotFoundError, ValueError, KeyError, AssertionError, json.JSONDecodeError) as exc:
        preserved = preserve_files(root, scene_files(root, scene), scene)
        dump_json(root / "resume_checks" / f"{scene}_{uuid4().hex}.json",
                  {"checked_at": utc(), "scene": scene, "action": "recompute_unverified",
                   "reason": str(exc), "preserved": str(preserved) if preserved else None})
        return None


def finish_summary(root, summary):
    root = Path(root)
    path = root / "summary.json"
    if path.exists():
        old = json.loads(path.read_text())
        if (old.get("status") == "complete" and old.get("receipts") == summary["receipts"]
                and old.get("configuration_sha256") == sha256(root / "config.json")):
            return
        preserve_files(root, [path], "summary")
    dump_json(path, {**summary, "configuration_sha256": sha256(root / "config.json")})
