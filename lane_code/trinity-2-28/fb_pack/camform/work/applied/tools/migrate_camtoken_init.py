"""Migrate an existing PDG v3 milestone init or auxiliary_heads.pt to include G3T camera-token prior modules.

Copies or hardlinks full_weights/ and geometry/ unchanged, augments auxiliary_heads.pt with deterministic
seed-initialized GatedCameraTokenConnector(4096, 4096), GatedCameraHeadBypass(4096, 2048),
and zero-initialized head.alpha_pose / head.alpha_grav scalars, updates auxiliary_heads.json with
g3t_prior settings, and seals MILESTONE.json.
"""
import argparse
import copy
import hashlib
import io
import json
import os
import shutil
from collections import OrderedDict
from pathlib import Path

import torch

from student_pilot import camera_config, full_ft
from student_pilot.geometry_input import GatedCameraHeadBypass, GatedCameraTokenConnector


def file_pin(root, rel_path):
    abs_path = os.path.join(root, rel_path)
    digest = hashlib.sha256()
    size = 0
    with open(abs_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
            size += len(chunk)
    return OrderedDict([("bytes", size), ("sha256", digest.hexdigest())])


def _populate_camtoken_tensors(target, prefix, hidden_size, head_dim, cam_token_dim, seed):
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(int(seed))
        cam_conn = GatedCameraTokenConnector(cam_token_dim, hidden_size)
        cam_bypass = GatedCameraHeadBypass(cam_token_dim, head_dim)
    for k, v in cam_conn.state_dict().items():
        key = f"{prefix}cam_token_connector.{k}"
        if key not in target:
            target[key] = v.detach().to(torch.float32).cpu().contiguous()
    for k, v in cam_bypass.state_dict().items():
        key = f"{prefix}cam_head_bypass.{k}"
        if key not in target:
            target[key] = v.detach().to(torch.float32).cpu().contiguous()
    for name in ("alpha_pose", "alpha_grav"):
        key = f"{prefix}head.{name}"
        if key not in target:
            target[key] = torch.zeros(1, dtype=torch.float32)


def migrate_heads_checkpoint(state_or_path, hidden_size=4096, head_dim=2048, cam_token_dim=4096, seed=17):
    """Idempotently add G3T camera-token connector, head bypass, and pose/gravity gates to a heads state_dict."""
    if isinstance(state_or_path, (str, Path)):
        state = torch.load(state_or_path, map_location="cpu", weights_only=True)
    else:
        state = copy.deepcopy(state_or_path)
    if isinstance(state.get("camera"), dict):
        out = OrderedDict(state)
        sub = OrderedDict(out["camera"])
        _populate_camtoken_tensors(sub, "", hidden_size, head_dim, cam_token_dim, seed)
        out["camera"] = sub
        return out
    out = OrderedDict(state)
    prefix = "camera." if any(k.startswith("camera.") for k in out) else ""
    _populate_camtoken_tensors(out, prefix, hidden_size, head_dim, cam_token_dim, seed)
    return out


def check_heads_init(heads_pt_path, hidden_size=4096, head_dim=2048, cam_token_dim=4096):
    """Verify that a migrated heads checkpoint has zero-initialized camera gates and valid tensor shapes."""
    state = torch.load(heads_pt_path, map_location="cpu", weights_only=True)
    sub = state["camera"] if isinstance(state.get("camera"), dict) else state
    prefix = "camera." if any(k.startswith("camera.") for k in sub) else ""
    required_zero = (
        f"{prefix}cam_token_connector.alpha_cam",
        f"{prefix}cam_head_bypass.alpha_bypass",
        f"{prefix}head.alpha_pose",
        f"{prefix}head.alpha_grav",
    )
    for key in required_zero:
        if key not in sub:
            raise ValueError(f"Missing G3T camera prior gate tensor: {key}")
        if sub[key].count_nonzero():
            raise ValueError(f"G3T camera prior gate {key} is non-zero at init")
    if tuple(sub[f"{prefix}cam_token_connector.mlp.0.weight"].shape) != (hidden_size, cam_token_dim):
        raise ValueError("cam_token_connector.mlp.0.weight shape mismatch")
    if tuple(sub[f"{prefix}cam_token_connector.mlp.2.weight"].shape) != (hidden_size, hidden_size):
        raise ValueError("cam_token_connector.mlp.2.weight shape mismatch")
    if tuple(sub[f"{prefix}cam_head_bypass.fc.weight"].shape) != (head_dim, cam_token_dim):
        raise ValueError("cam_head_bypass.fc.weight shape mismatch")
    return True


def migrate_init(src_dir, dst_dir, seed=17, hardlink=True, hidden_size=4096, head_dim=2048, cam_token_dim=4096):
    src_dir = os.path.abspath(src_dir)
    dst_dir = os.path.abspath(dst_dir)
    if os.path.exists(dst_dir):
        raise ValueError("Destination already exists: " + dst_dir)
    src_milestone, _ = full_ft.read_milestone(src_dir)
    os.makedirs(dst_dir, exist_ok=True)

    for rel_path in sorted(src_milestone["files"]):
        if rel_path in ("auxiliary_heads.pt", "auxiliary_heads.json"):
            continue
        s_path = os.path.join(src_dir, rel_path)
        d_path = os.path.join(dst_dir, rel_path)
        os.makedirs(os.path.dirname(d_path), exist_ok=True)
        if hardlink:
            try:
                os.link(s_path, d_path)
            except OSError:
                shutil.copy2(s_path, d_path)
        else:
            shutil.copy2(s_path, d_path)

    with open(os.path.join(src_dir, "auxiliary_heads.json")) as handle:
        heads_meta = json.load(handle)
    new_state = migrate_heads_checkpoint(
        os.path.join(src_dir, "auxiliary_heads.pt"),
        hidden_size=hidden_size,
        head_dim=head_dim,
        cam_token_dim=cam_token_dim,
        seed=seed,
    )
    buf = io.BytesIO()
    torch.save(new_state, buf)
    pt_bytes = buf.getvalue()
    pt_path = os.path.join(dst_dir, "auxiliary_heads.pt")
    with open(pt_path, "wb") as handle:
        handle.write(pt_bytes)
    pt_sha256 = hashlib.sha256(pt_bytes).hexdigest()
    check_heads_init(pt_path, hidden_size=hidden_size, head_dim=head_dim, cam_token_dim=cam_token_dim)

    orig_cam = dict(heads_meta.get("camera") or {})
    cam_settings = dict(orig_cam.get("settings") or {})
    cam_settings["g3t_prior"] = dict(camera_config.G3T_PRIOR_DEFAULTS)
    cam_settings = camera_config.normalize(cam_settings)
    if isinstance(new_state.get("camera"), dict):
        cam_params = sum(int(v.numel()) for v in new_state["camera"].values())
    else:
        cam_params = sum(int(v.numel()) for k, v in new_state.items()
                         if k.startswith("camera.") or not any(name.startswith("camera.") for name in new_state))

    new_cam = OrderedDict(orig_cam)
    new_cam["settings"] = cam_settings
    new_cam.setdefault("inference_required", False)
    new_cam["parameters"] = cam_params
    new_cam["sha256"] = pt_sha256

    heads_meta = dict(heads_meta)
    heads_meta["camera"] = new_cam
    if isinstance(heads_meta.get("weights"), dict):
        weights_meta = OrderedDict(heads_meta["weights"])
        weights_meta["sha256"] = pt_sha256
        weights_meta["size_bytes"] = len(pt_bytes)
        heads_meta["weights"] = weights_meta
    heads_meta["camtoken_migration"] = OrderedDict([
        ("source_init", src_dir),
        ("seed", int(seed)),
        ("g3t_prior", cam_settings["g3t_prior"]),
    ])
    json_path = os.path.join(dst_dir, "auxiliary_heads.json")
    with open(json_path, "w") as handle:
        json.dump(heads_meta, handle, indent=2)
        handle.write("\n")

    files = OrderedDict()
    for rel_path in src_milestone["files"]:
        files[rel_path] = file_pin(dst_dir, rel_path)
    milestone = OrderedDict(src_milestone)
    milestone["files"] = files
    milestone_path = os.path.join(dst_dir, "MILESTONE.json")
    with open(milestone_path, "w") as handle:
        json.dump(milestone, handle, indent=2)
        handle.write("\n")

    full_ft.read_milestone(dst_dir)
    return {
        "dst_dir": dst_dir,
        "auxiliary_heads_pt_sha256": pt_sha256,
        "auxiliary_heads_json_sha256": files["auxiliary_heads.json"]["sha256"],
        "milestone_sha256": file_pin(dst_dir, "MILESTONE.json")["sha256"],
        "camera_parameters": cam_params,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src-init", required=True)
    parser.add_argument("--dst-init", required=True)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--copy", action="store_true", help="copy full_weights shards instead of hardlinking")
    args = parser.parse_args(argv)
    report = migrate_init(args.src_init, args.dst_init, seed=args.seed, hardlink=not args.copy)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
