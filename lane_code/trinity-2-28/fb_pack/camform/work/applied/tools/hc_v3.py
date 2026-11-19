"""HC and HX on PDG v3: the head-call arms start from PDG v3's final export with the gated G3T connector active.

Both arms take PDG v3's stage-2 config unchanged (tools/pdg_v3.stage2_config: gated Spatial-MLLM connector at 1e-5,
the same G3T store, camera + point-depth heads with loss weights x0.1, Cambrian-P rates for LLM, merger, vision and
heads, segment loss, 32 frames, world 32, batch 256, one epoch, seed 17) and change only:
  full_ft.init           full_export of PDG v3's final full_weights.json (LLM, merger, vision);
  full_ft.init_modules   PDG v3's final geometry connector (gate included) and auxiliary heads;
  headcall               HC: the head-call sidecar, tool responses masked, scheduled sampling 0 -> 0.5 over steps
                         0-1,000 (seed 17); HX: the matched answer-only sidecar (same carriers and queried depth
                         points), no sampling.
Rows: HC trains RG2P2_X's 396,649 questions with HC_REPLACE's targets; HX trains RG2P2_X's rows. The 8-GPU smokes use
the same derivation from SMOKE_PDG_S2_V3G's config, with the smoke sampling 0 -> 0.5 over steps 0-20 and checkpoints
every 25 steps (no milestone_20, so the closure's carrier-only smoke publisher stays idle; publish_hc_v3 publishes
milestone_25 with its geometry connector).
"""
import copy
import hashlib
import json
from pathlib import Path

ARMS = ("HC", "HX")
SAMPLING = {"start_p": 0.0, "end_p": 0.5, "start_step": 0, "end_step": 1000}
SMOKE_SAMPLING = {"start_p": 0.0, "end_p": 0.5, "start_step": 0, "end_step": 20}
SMOKE_FIELDS = {"world_size": 8, "effective_batch_size": 64, "max_steps": 30, "checkpoint_every_steps": 25}
STAGE2_CAMERA = {"weight": 0.1, "weight_gravity": 0.05, "weight_scale": 0.02, "point_depth": 0.05}
STAGE2_RATES = {"geometry": 1e-5, "heads": 1e-4, "llm": 1e-5, "merger": 1e-5, "vision_blocks": 2e-6}
# The only config fields an arm may change relative to the PDG v3 stage-2 config it derives from.
ARM_PREFIXES = ("full_ft.init.", "full_ft.init_modules.geometry.", "full_ft.init_modules.heads.", "headcall.",
                "camera.g3t_prior.")
ARM_FIELDS = {"full_ft.init.kind", "full_ft.init.path", "full_ft.init.sha256", "headcall.arm", "headcall.sidecar.path",
              "headcall.sidecar.sha256", "headcall.scheduled_sampling", "seed",
              "camera.g3t_prior", "geometry.store.camera_manifest", "geometry.store.camera_manifest_sha256"}
_MISSING = object()


def flatten(value, prefix=""):
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


def check_stage2(config):
    """A PDG v3 stage-2 config: gated connector, the x0.1 head weights, full FT of every group at Cambrian-P's rates
    with the connector at 1e-5, init_modules for the stage-1 connector and heads."""
    from student_pilot import geometry_input
    if config.get("geometry", {}).get("injection") != geometry_input.GATED_SPATIAL_INJECTION:
        raise ValueError("HC/HX v3 derive from a PDG v3 config with the gated G3T connector")
    camera = config["camera"]
    weights = {"weight": camera["weight"], "weight_gravity": camera["weight_gravity"],
               "weight_scale": camera["weight_scale"], "point_depth": camera["point_depth"]["weight"]}
    if weights != STAGE2_CAMERA:
        raise ValueError(f"HC/HX v3 keep PDG v2/v3's stage-2 head weights {STAGE2_CAMERA}, found {weights}")
    block = config["full_ft"]
    if block.get("train") != {"llm": True, "merger": True, "vision_blocks": True}:
        raise ValueError("HC/HX v3 fully fine-tune the LLM, merger and vision blocks")
    if block.get("learning_rates") != STAGE2_RATES:
        raise ValueError(f"HC/HX v3 keep PDG v3 stage 2's rates {STAGE2_RATES}, found {block.get('learning_rates')}")
    if set(block.get("init_modules", {})) != {"geometry", "heads"}:
        raise ValueError("The PDG v3 stage-2 config loads stage-1 geometry and heads")
    if "headcall" in config:
        raise ValueError("The source config already has a headcall block")


def headcall_block(arm, seed, sidecar, sampling=SAMPLING):
    if arm not in ARMS:
        raise ValueError(f"arm must be one of {ARMS}")
    return {"arm": arm, "sidecar": {"path": sidecar["path"], "sha256": sidecar["sha256"]},
            "scheduled_sampling": {**sampling, "seed": seed} if arm == "HC" else None}


def arm_config(stage2, arm, sidecar, init, smoke=False):
    """The HC or HX config from PDG v3's stage-2 config (SMOKE_PDG_S2_V3G's for a smoke) and the export pins
    init = {"full_weights": pin, "geometry": pin, "heads": pin}."""
    from headcall import rows as R
    from student_pilot import camera_config, full_ft, geometry_input
    check_stage2(stage2)
    config = copy.deepcopy(stage2)
    seed = config["seed"]
    config["full_ft"]["init"] = {"kind": "full_export", "path": init["full_weights"]["path"],
                                 "sha256": init["full_weights"]["sha256"]}
    config["full_ft"]["init_modules"] = {name: {"path": init[name]["path"], "sha256": init[name]["sha256"]}
                                         for name in ("geometry", "heads")}
    if init.get("g3t_prior") is not None:
        config["camera"]["g3t_prior"] = copy.deepcopy(init["g3t_prior"])
    if init.get("camera_store") is not None:
        config["geometry"]["store"]["camera_manifest"] = init["camera_store"]["path"]
        config["geometry"]["store"]["camera_manifest_sha256"] = init["camera_store"]["sha256"]
        geometry_input.normalize(config["geometry"])
    config["headcall"] = headcall_block(arm, seed, sidecar, SMOKE_SAMPLING if smoke else SAMPLING)
    if smoke:
        if any(stage2.get(key) != value for key, value in SMOKE_FIELDS.items() if key != "checkpoint_every_steps"):
            raise ValueError("A smoke derives from the smoke stage-2 config (world 8, batch 64, 30 steps)")
        config["checkpoint_every_steps"] = SMOKE_FIELDS["checkpoint_every_steps"]
    full_ft.normalize(config["full_ft"])
    R.check_camera(camera_config.normalize(config["camera"]))
    extra = [key for key in config_changes(stage2, config)
             if key not in ARM_FIELDS and not key.startswith(ARM_PREFIXES)
             and not (smoke and key == "checkpoint_every_steps")]
    if extra:
        raise ValueError(f"HC/HX v3 changed fields beyond the recipe: {extra}")
    from tools.fullft_arm_configs import validated
    return validated(json.loads(json.dumps(config)))


def pair(stage2, sidecars, init, smoke=False):
    """HC and HX configs; they differ only in the headcall block."""
    configs = {arm: arm_config(stage2, arm, sidecars[arm], init, smoke=smoke) for arm in ARMS}
    diff = config_changes(configs["HC"], configs["HX"])
    if any(not key.startswith("headcall.") for key in diff):
        raise ValueError(f"HC and HX differ beyond the headcall block: {diff}")
    return configs


def milestone_pins(directory):
    """Pins of a milestone export (MILESTONE.json; the smoke stand-in): full weights, heads and geometry connector,
    each verified against MILESTONE.json's file table (full_ft.read_milestone checks every file)."""
    from student_pilot import full_ft, geometry_input
    directory = Path(directory)
    manifest, pins = full_ft.read_milestone(directory)
    name = f"geometry/{geometry_input.WEIGHTS_NAME}"
    if name not in manifest["files"] or pins.get("heads") is None:
        raise ValueError(f"{directory} lacks the geometry connector or the heads")
    out = {"source": {"kind": "milestone", "path": str(directory.resolve()), "step": manifest["step"],
                      "identity": manifest.get("identity")},
           "full_weights": pins["full_weights"], "heads": pins["heads"],
           "geometry": {"path": str((directory / name).resolve()), "sha256": manifest["files"][name]["sha256"]}}
    heads_json = directory / "auxiliary_heads.json"
    if heads_json.is_file():
        heads_meta = json.loads(heads_json.read_text())
        g3t_prior = heads_meta.get("camera", {}).get("settings", {}).get("g3t_prior")
        if g3t_prior is not None:
            out["g3t_prior"] = g3t_prior
    return out


def publication_pins(publication, steps=None):
    """Pins of a final training publication (PUBLISHED.json, status TRAINED, every optimizer step when `steps` is
    given): the adapter directory's full_weights.json, auxiliary_heads.pt and geometry/geometry_projector.safetensors,
    each hashed and checked against the publication's SHA256_MANIFEST.json."""
    from student_pilot import geometry_input
    publication = Path(publication)
    receipt = json.loads((publication / "PUBLISHED.json").read_text())
    result = json.loads((publication / "training_result.json").read_text())
    if receipt.get("status") != "TRAINED" or result.get("status") != "TRAINED":
        raise ValueError(f"{publication} is not a TRAINED publication")
    realized = int(result.get("realized", {}).get("optimizer_steps", 0))
    if steps is not None and realized != steps:
        raise ValueError(f"{publication} trained {realized} optimizer steps, not {steps}")
    census = json.loads((publication / "SHA256_MANIFEST.json").read_text())["files"]
    names = {"full_weights": f"{receipt['adapter_directory']}/full_weights/full_weights.json",
             "heads": "auxiliary_heads.pt", "geometry": f"geometry/{geometry_input.WEIGHTS_NAME}"}
    out = {"source": {"kind": "publication", "path": str(publication.resolve()), "step": realized}}
    for key, name in names.items():
        path = publication / name
        digest = sha_file(path)
        if name not in census or census[name]["sha256"] != digest:
            raise ValueError(f"{name} differs from the publication's SHA256_MANIFEST.json")
        out[key] = {"path": str(path.resolve()), "sha256": digest}
    if receipt["adapter"].get("full_weights_manifest_sha256") != out["full_weights"]["sha256"]:
        raise ValueError("The publication's full_weights.json differs from its receipt")
    if receipt["adapter"].get("geometry_weights_sha256") != out["geometry"]["sha256"]:
        raise ValueError("The publication's geometry connector differs from its receipt")
    heads_json = publication / "auxiliary_heads.json"
    if heads_json.is_file():
        heads_meta = json.loads(heads_json.read_text())
        g3t_prior = heads_meta.get("camera", {}).get("settings", {}).get("g3t_prior")
        if g3t_prior is not None:
            out["g3t_prior"] = g3t_prior
    return out


def run_publication(run_root, steps):
    """The newest TRAINED publication of a run (attempt-*/publication) with all `steps` optimizer steps."""
    found = sorted(Path(run_root).glob("attempt-*/publication/PUBLISHED.json"), key=lambda p: p.stat().st_mtime)
    if not found:
        raise ValueError(f"{run_root} has no publication yet")
    return publication_pins(found[-1].parent, steps=steps)
