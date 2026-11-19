import argparse
import json
import os
from pathlib import Path
from launch_s1.b.q0 import ENVIRONMENT, attempt_id, enabled


def require_production():
    if enabled():
        raise ValueError(f"Production launch refuses {ENVIRONMENT}=1")


def authorize(root, mode, arm):
    if not enabled():
        raise ValueError("CPU authorization requires explicit rehearsal mode")
    from . import carrier_c1_run as trainer
    from .p3_provenance import load, pinned
    root = Path(root).resolve()
    auth = load(root / "k/authorization.json")
    cfg = load(pinned(auth["config"]))
    manifest = load(pinned(auth["model"]))
    if (not root.is_relative_to("/scratch") or mode not in auth["modes"] or arm != "0"
            or auth.get("schema") != "s1-cpu-authorization-v1" or auth.get("new_gpus") != 0
            or auth.get("world_size") != 4 or cfg.get("world_size") != 4
            or auth.get("config_sha256") != trainer.identity(cfg) or not fixture_manifest(manifest)
            or os.environ.get("CUDA_VISIBLE_DEVICES") != ""):
        raise ValueError("CPU authorization differs from the pinned tiny four-rank run")
    trainer.validate(cfg)
    trainer.authenticate(cfg)
    return auth, cfg


def fixture_manifest(manifest):
    if not manifest.get("rehearsal"):
        return False
    if not enabled():
        raise ValueError("Tiny rehearsal assets are forbidden in production")
    from .p3_provenance import sha256
    root = Path(manifest["root"])
    config = json.loads((root / "config.json").read_text())
    text, vision = config["text_config"], config["vision_config"]
    if (config["model_type"] != "qwen3_5" or text["hidden_size"] > 64
            or text["num_hidden_layers"] > 32 or vision["hidden_size"] > 64
            or vision["depth"] > 32):
        raise ValueError("Rehearsal requires a tiny native Qwen3.5 configuration")
    for name, expected in manifest["files"].items():
        path = root / name
        if Path(name).name != name or path.stat().st_size > 16_000_000 or sha256(path) != expected:
            raise ValueError("Rehearsal asset exceeds the tiny-model bound or differs from its pin")
    return True


def tower_architecture(settings):
    if not enabled():
        return None
    from .p3_provenance import load, pinned
    config = load(pinned(settings["encoder"]["config"]))
    architecture = config.get("rehearsal_architecture")
    if architecture is None:
        return None
    aggregator, head = architecture["aggregator"], architecture["head"]
    if (aggregator["embed_dim"] > 64 or aggregator["depth"] > 24
            or aggregator["img_size"] != 518 or aggregator["patch_size"] < 74
            or head["dim_in"] != 2 * aggregator["embed_dim"] or head["trunk_depth"] > 2):
        raise ValueError("Rehearsal requires a bounded native G3T architecture")
    return architecture


def feature_width(settings):
    architecture = tower_architecture(settings)
    return 2 * architecture["aggregator"]["embed_dim"] if architecture else 2048


def validate_tower_config(config):
    expected = dict(embed_dim=1024, enable_depth=True, enable_gravity_camera_heads=True,
                    enable_point=True, img_size=518, patch_size=14)
    if config == expected:
        return
    if not enabled() or set(config) != {"rehearsal_architecture"}:
        raise ValueError("GX encoder configuration differs")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", action="store_true", required=True)
    parser.parse_args()
    require_production()


if __name__ == "__main__":
    main()
