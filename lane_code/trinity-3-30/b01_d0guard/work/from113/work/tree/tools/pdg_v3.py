"""PDG v3 (gated): the G3T connector's contribution is bounded by construction in both stages.

The connector keeps Spatial-MLLM's mlp_add layers and source init (RMSNorm ones; both Linears N(0, 0.02), biases 0,
seed 17) and adds to the merged video tokens as in the source. Its output is normalized by a LayerNorm without affine
parameters (Swin Transformer V2's res-post-norm, arXiv 2111.09883) and scaled by Flamingo's tanh gate (Alayrac et al.,
arXiv 2204.14198: a scalar alpha initialised at 0, trained with the new layers at 1e-4). The delta per token is
tanh(alpha) * LayerNorm(connector(x)), whose norm is exactly |tanh(alpha)| * 64 at width 4,096, so the frozen-VLM student
starts at the base model and the contribution can grow only as fast as Adam moves one scalar (about lr per step),
however the 335M connector weights move. Design: lanes/fullft_review/PDG_V3_DESIGN.md.

- Stage 1: the geometry block names the gated injection; the connector group (gate included) trains at Flamingo's 1e-4.
  The init reaches the trainer through full_ft.init_modules (exact names, shapes, dtypes and values).
- Stage 2: PDG_S2 v2 (head loss weights x0.1, connector at 1e-5) with the gated block and init_modules pinning the
  stage-1 export.
"""
import copy
import hashlib
import math
from pathlib import Path

import torch

from student_pilot import full_ft, geometry_input

STAGE1_RATE = 1e-4  # Flamingo's rate for its new layers and tanh gates
INIT_SEED = 17
GATED_FIELDS = {"geometry.injection", "geometry.projector.output_norm", "geometry.projector.gate"}
# The only config fields v3 may change, relative to the v2 configs it derives from.
STAGE1_FIELDS = {"learning_rate", "full_ft.learning_rates.geometry", "full_ft.init_modules.geometry.path",
                 "full_ft.init_modules.geometry.sha256"} | GATED_FIELDS
STAGE2_FIELDS = {"full_ft.init_modules.geometry.path", "full_ft.init_modules.geometry.sha256",
                 "full_ft.init_modules.heads.path", "full_ft.init_modules.heads.sha256"} | GATED_FIELDS
# The 8-GPU smoke fields (SMOKE_FT_A / SMOKE_PDG_S1 against FT_A / PDG_S1).
SMOKE_FIELDS = {"checkpoint_every_steps": 20, "effective_batch_size": 64, "max_steps": 30, "world_size": 8}
# PDG_S2 v2 head loss weights (PDG_HEADGRAD_FIX.md candidate A), kept in v3.
STAGE2_CAMERA = {"weight": 0.1, "weight_gravity": 0.05, "weight_scale": 0.02, "point_depth": 0.05}
_MISSING = object()


def flatten(value, prefix=""):
    """Dotted leaf paths of a nested config (an empty dict is a leaf)."""
    if isinstance(value, dict) and value:
        out = {}
        for key, item in value.items():
            out.update(flatten(item, f"{prefix}{key}."))
        return out
    return {prefix[:-1]: value}


def config_changes(old, new):
    left, right = flatten(old), flatten(new)
    return sorted(key for key in set(left) | set(right) if left.get(key, _MISSING) != right.get(key, _MISSING))


def sha_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def gated_block(block):
    """The gated geometry block of a Spatial-MLLM geometry block: same encoder, layer, store; gated injection."""
    if block["injection"] not in geometry_input.SPATIAL_INJECTIONS:
        raise ValueError("PDG v3 applies to the Spatial-MLLM connector")
    gated = copy.deepcopy(block)
    gated["injection"] = geometry_input.GATED_SPATIAL_INJECTION
    gated["projector"] = dict(geometry_input.SPATIAL_MLLM_GATED)
    return geometry_input.normalize(gated)


def gated_init_state(feature_dim, output_dim, seed=INIT_SEED):
    """Gated connector tensors: Spatial-MLLM's source init from a fixed seed (RMSNorm ones, both Linears N(0, 0.02),
    biases 0) and the tanh gate at 0."""
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        module = geometry_input.GatedSpatialMLLMConnector(feature_dim, output_dim)
    return {name: tensor.detach().to(torch.float32).contiguous() for name, tensor in module.state_dict().items()}


def write_init(path, feature_dim, output_dim, seed=INIT_SEED):
    """Write the gated init as safetensors (the published projector format) and return its sha256."""
    from safetensors.torch import save_file

    save_file(gated_init_state(feature_dim, output_dim, seed), str(path))
    return sha_file(path)


def check_init(path, sha256, settings, output_dim, resolve=None):
    """Load the init through the trainer's own init_modules path and prove that it is the source init with the gate at
    0, that the connector adds exactly zero, and that a nonzero gate gives the bounded delta norm."""
    if settings["injection"] != geometry_input.GATED_SPATIAL_INJECTION:
        raise ValueError("The PDG v3 init applies to the gated connector")
    module = geometry_input.GeometryInput(settings, output_dim)
    receipt = full_ft.load_init_modules({"init_modules": {"geometry": {"path": str(path), "sha256": sha256}}},
                                        geometry=module, resolve=resolve)
    projector = module.projector
    if receipt != {"geometry": {"sha256": sha256, "tensors": 6}}:
        raise ValueError(f"Unexpected init receipt {receipt}")
    if projector.gate.count_nonzero():
        raise ValueError("The connector gate is not zero")
    if (projector.fc1.bias.count_nonzero() or projector.fc2.bias.count_nonzero()
            or not torch.equal(projector.ln_q.weight, torch.ones_like(projector.ln_q.weight))):
        raise ValueError("The RMSNorm or a Linear bias differs from the source init")
    stds = {name: float(layer.weight.detach().std()) for name, layer in (("fc1", projector.fc1), ("fc2", projector.fc2))}
    for name, std in stds.items():
        if abs(std - geometry_input.SPATIAL_MLLM_INIT_STD) > 0.01 * geometry_input.SPATIAL_MLLM_INIT_STD:
            raise ValueError(f"{name} std {std} is not the source N(0, 0.02)")
    with torch.no_grad():
        generator = torch.Generator().manual_seed(0)
        features = torch.randn(4, geometry_input.token_width(module.settings), generator=generator)
        if projector(features).count_nonzero():
            raise ValueError("The gated connector returned a nonzero delta at gate 0")
        probe = copy.deepcopy(projector)
        probe.gate.fill_(0.01)
        norms = probe(features).norm(dim=-1)
        expected = math.tanh(0.01) * math.sqrt(output_dim)
        if not torch.allclose(norms, torch.full_like(norms, expected), rtol=1e-3):
            raise ValueError(f"Gated delta norms {norms.tolist()} differ from tanh(gate) * sqrt(width) = {expected}")
    return {"sha256": sha256, "tensors": 6, "fc1_std": stds["fc1"], "fc2_std": stds["fc2"], "gate": 0.0,
            "output_zero": True, "delta_norm_at_gate_0.01": float(norms.mean())}


def rebind_trainer_entries(recorded, trainer, sha_file, fingerprint):
    """Pre-stage clone across trainer trees: a source cache built under another installed trainer tree (a sibling of
    `trainer`) records that tree's large files by path. Rebind each such entry to the same relative file of `trainer`,
    refusing unless the bytes are identical, with this tree's file identity. Returns the rebound relative paths."""
    trainer = str(trainer).rstrip("/") + "/"
    parent = str(Path(trainer).parent).rstrip("/") + "/"
    rebound = []
    for key in sorted(recorded):
        target = str(recorded[key].get("target", key))
        if not target.startswith(parent) or target.startswith(trainer):
            continue
        entry = recorded.pop(key)
        relative = target[len(parent):].partition("/")[2]
        new = trainer + relative
        if not relative or sha_file(new) != entry["sha256"]:
            raise ValueError(f"{target} has no byte-identical counterpart in {trainer}")
        recorded[new] = {"target": new, "sha256": entry["sha256"], "stat": fingerprint(new)}
        rebound.append(relative)
    return rebound


def stage1_config(source, init_pin):
    """PDG_S1 v3 from a PDG_S1 (or SMOKE_PDG_S1) v2 config: gated connector block, connector rate 1e-4, gated init."""
    config = copy.deepcopy(source)
    block = config["full_ft"]
    if not full_ft.frozen_vlm(full_ft.normalize(block)) or "init_modules" in block:
        raise ValueError("Stage 1 v3 derives from a frozen-VLM config without init modules")
    if config["geometry"]["injection"] != geometry_input.SPATIAL_INJECTION:
        raise ValueError("Stage 1 v3 applies to the Spatial-MLLM connector")
    config["geometry"] = gated_block(config["geometry"])
    block["learning_rates"]["geometry"] = STAGE1_RATE
    block["init_modules"] = {"geometry": {"path": str(init_pin["path"]), "sha256": init_pin["sha256"]}}
    # Inert under full_ft; fullft_arm_configs sets it to the first group's rate (llm, else geometry).
    config["learning_rate"] = STAGE1_RATE
    full_ft.normalize(block)
    geometry_input.normalize(config["geometry"])
    extra = set(config_changes(source, config)) - STAGE1_FIELDS
    if extra:
        raise ValueError(f"Stage 1 v3 changed fields beyond its recipe: {sorted(extra)}")
    return config


def stage2_config(source, geometry_pin, heads_pin):
    """PDG_S2 v3 from the PDG_S2 v2 config: the gated connector block and init_modules pinning the v3 stage-1 export."""
    config = copy.deepcopy(source)
    camera = config["camera"]
    weights = {"weight": camera["weight"], "weight_gravity": camera["weight_gravity"],
               "weight_scale": camera["weight_scale"], "point_depth": camera["point_depth"]["weight"]}
    if weights != STAGE2_CAMERA:
        raise ValueError(f"Stage 2 v3 derives from the v2 head weights {STAGE2_CAMERA}, found {weights}")
    if set(config["full_ft"].get("init_modules", {})) != {"geometry", "heads"}:
        raise ValueError("Stage 2 v3 derives from a config that loads stage-1 geometry and heads")
    if config["geometry"]["injection"] != geometry_input.SPATIAL_INJECTION:
        raise ValueError("Stage 2 v3 derives from the v2 Spatial-MLLM connector config")
    config["geometry"] = gated_block(config["geometry"])
    config["full_ft"]["init_modules"] = {"geometry": {"path": str(geometry_pin["path"]), "sha256": geometry_pin["sha256"]},
                                         "heads": {"path": str(heads_pin["path"]), "sha256": heads_pin["sha256"]}}
    full_ft.normalize(config["full_ft"])
    extra = set(config_changes(source, config)) - STAGE2_FIELDS
    if extra:
        raise ValueError(f"Stage 2 v3 changed fields beyond its recipe: {sorted(extra)}")
    return config


def smoke_config(config):
    """The 8-GPU, 30-step smoke variant of a full config (the SMOKE_FT_A / SMOKE_PDG_S1 field values)."""
    smoke = copy.deepcopy(config)
    smoke.update(SMOKE_FIELDS)
    return smoke
