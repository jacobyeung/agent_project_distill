"""Run the phase-1 held-out accuracy gate on a PDG/HC/HX full-FT checkpoint or milestone export."""
import argparse
from collections import OrderedDict
import json
import os

from pathlib import Path
import torch

from headcall import gate_eval as ge
from headcall import phase1
from headcall.heads import Phase1Heads
from student_pilot import geometry_input as gi


GATE_ATTRS = {
    "alpha_cam": ("cam_token_connector", "alpha_cam"),
    "alpha_bypass": ("cam_head_bypass", "alpha_bypass"),
    "alpha_pose": ("head", "alpha_pose"),
    "alpha_grav": ("head", "alpha_grav"),
}


def parse_gate_overrides(spec):
    if not spec:
        return {}
    overrides = OrderedDict()
    for item in spec.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError("Invalid --gate-override item (expected name=float): " + item)
        name, val = item.split("=", 1)
        name = name.strip()
        if name not in GATE_ATTRS:
            raise ValueError("Unknown gate in --gate-override: %s (expected one of %s)" % (name, sorted(GATE_ATTRS)))
        overrides[name] = float(val)
    return overrides


def apply_gate_overrides(camera_module, overrides):
    applied = OrderedDict()
    with torch.no_grad():
        for name, val in overrides.items():
            sub_name, attr_name = GATE_ATTRS[name]
            sub = getattr(camera_module, sub_name, None)
            param = getattr(sub, attr_name, None) if sub is not None else None
            if param is None:
                raise ValueError("Checkpoint camera module has no %s.%s to override" % (sub_name, attr_name))
            param.fill_(float(val))
            applied[name] = float(param.detach().cpu().item())
    return applied


def read_gate_values(camera_module):
    values = OrderedDict()
    for name, (sub_name, attr_name) in GATE_ATTRS.items():
        sub = getattr(camera_module, sub_name, None)
        param = getattr(sub, attr_name, None) if sub is not None else None
        if param is not None:
            raw = float(param.detach().cpu().item())
            values[name] = OrderedDict([("raw", raw), ("tanh", float(torch.tanh(param.detach().cpu()).item()))])
    return values


class FullFTCheckpointHeads(object):
    def __init__(self, student, full_weights, heads_json, heads_pt, store_manifest=None, device="cuda:0",
                 geometry_dir=None, camera_manifest=None, gate_overrides=None, *, rgb_only=False):
        self.model, self.processor, self.load_report = ge.load_full_ft_checkpoint(
            student, full_weights, heads_json, heads_pt, device=device
        )
        if rgb_only:
            if any(v is not None for v in (store_manifest, geometry_dir, camera_manifest)):
                raise ValueError("RGB sessions cannot accept geometry inputs")
            camera_mod = getattr(self.model.auxiliary_heads, "camera", None)
            if getattr(camera_mod, "has_g3t_prior", False):
                raise ValueError("This attachment requires geometry")
            self.geometry = self.store = None
            if gate_overrides:
                self.load_report["gate_overrides"] = apply_gate_overrides(camera_mod, gate_overrides)
            self.load_report["input_mode"] = "rgb"
        else:
            if geometry_dir is None:
                candidate = Path(heads_json).resolve().parent / "geometry"
                if (candidate / gi.MANIFEST_NAME).is_file():
                    geometry_dir = str(candidate)
            if geometry_dir is None:
                raise ValueError("PDG/HC/HX gate evaluation requires a geometry projector directory (geometry/)")
            geom_dir = Path(geometry_dir).resolve()
            geom_manifest = json.loads((geom_dir / gi.MANIFEST_NAME).read_text())
            self.geometry = gi.load(self.model, geom_dir, geom_manifest["settings"], device=device)
            store_pin = {
                "manifest": str(Path(store_manifest).resolve()),
                "manifest_sha256": gi.file_sha256(Path(store_manifest).resolve()),
            }
            if camera_manifest:
                cam_path = Path(camera_manifest).resolve()
                store_pin["camera_manifest"] = str(cam_path)
                store_pin["camera_manifest_sha256"] = gi.file_sha256(cam_path)
            store_settings = {**geom_manifest["settings"], "store": store_pin}
            self.store = gi.FeatureStore(store_settings)
            camera_mod = getattr(self.model.auxiliary_heads, "camera", None)
            if getattr(camera_mod, "has_g3t_prior", False) and not self.store.has_camera_sidecar:
                raise ValueError("G3T prior checkpoint requires a geometry store with camera_manifest.jsonl")
            if gate_overrides:
                self.load_report["gate_overrides"] = apply_gate_overrides(camera_mod, gate_overrides)
            if camera_mod is not None:
                self.load_report["gate_values"] = read_gate_values(camera_mod)
            self.load_report["has_camera_sidecar"] = bool(self.store.has_camera_sidecar)
            self.load_report["geometry_dir"] = str(geom_dir)
        encode_prompt = phase1._module("diagnostic_data").encode_prompt
        context = torch.autocast("cuda", dtype=torch.bfloat16) if str(device).startswith("cuda") else None

        def session(ctx):
            batch = encode_prompt(self.processor, ctx.row)[0]
            frames = [f["sha256"] for f in ctx.row["student_input"]["frames"]]
            batch = {k: v.to(device) if hasattr(v, "to") else v for k, v in batch.items()}
            batch = phase1.insert_carriers(batch, self.processor.tokenizer)
            if self.store is not None:
                batch["geometry_features"] = self.store.tokens(frames, batch["video_grid_thw"][0])
            if self.store is not None and self.store.has_camera_sidecar:
                for k, v in self.store.camera_sidecar(frames, device=device).items():
                    batch[k] = v
            return phase1.session_forward(self.model, batch, forward_context=context)

        self.heads = Phase1Heads(session)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", required=True)
    parser.add_argument("--training-scenes", required=True)
    parser.add_argument("--heldout", default=None)
    parser.add_argument("--out", required=True)
    parser.add_argument("--student", required=True)
    parser.add_argument("--full-weights", default=None)
    parser.add_argument("--milestone", default=None)
    parser.add_argument("--heads-json", default=None)
    parser.add_argument("--heads-pt", default=None)
    parser.add_argument("--geometry-store-manifest", required=True)
    parser.add_argument("--geometry-camera-manifest", default=None)
    parser.add_argument("--gate-override", default=None,
                        help="Comma-separated gate overrides, e.g. alpha_pose=0,alpha_grav=0")
    parser.add_argument("--shuffled", action="store_true")
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args(argv)
    if os.path.exists(args.out):
        raise SystemExit("the gate report already exists: " + args.out)
    if bool(args.milestone) == bool(args.full_weights):
        parser.error("Provide exactly one of --milestone or --full-weights")
    if args.full_weights and not (args.heads_json and args.heads_pt):
        parser.error("--heads-json and --heads-pt are required with --full-weights")
    rows = ge.load_rows(args.rows)
    heldout = phase1.heldout_scenes(args.heldout)
    training = [tuple(s) for s in json.load(open(args.training_scenes))["scenes"]]
    ge.check_scenes(rows, heldout, training)
    milestone = None
    full_weights, heads_json, heads_pt = args.full_weights, args.heads_json, args.heads_pt
    if args.milestone:
        full_weights, heads_json, heads_pt, milestone = ge.milestone_paths(args.milestone)
    overrides = parse_gate_overrides(args.gate_override)
    backend = FullFTCheckpointHeads(
        args.student, full_weights, heads_json, heads_pt,
        args.geometry_store_manifest, device=args.device,
        camera_manifest=args.geometry_camera_manifest,
        gate_overrides=overrides,
    )
    heads = backend.heads
    checkpoint = {
        "student": args.student,
        "full_weights": full_weights,
        "heads_json": heads_json,
        "heads_pt": heads_pt,
        "milestone": milestone,
        "geometry_store_manifest": args.geometry_store_manifest,
        "geometry_camera_manifest": args.geometry_camera_manifest,
        "load_report": backend.load_report,
    }
    if args.shuffled:
        result = ge.evaluate_with_shuffled(rows, heads, heldout, training)
        passed = result["heads"]["passed"]
    else:
        result = ge.evaluate(rows, heads, heldout, training)
        passed = result["passed"]
    result = OrderedDict([
        ("phase1", phase1.provenance()),
        ("checkpoint", checkpoint),
        ("rows", os.path.abspath(args.rows)),
        ("report", result),
    ])
    with open(args.out, "w") as stream:
        json.dump(result, stream, indent=1, default=lambda v: v.tolist() if hasattr(v, "tolist") else str(v))
    print(json.dumps({"gate_passed": passed}))


if __name__ == "__main__":
    main()
