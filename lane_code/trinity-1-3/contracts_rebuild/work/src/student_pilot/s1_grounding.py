from pathlib import Path
import re

from .candidate_policy import NAME
from .ground_sources import NativeMDG
from .ground_v3 import GroundV3
from .p3_provenance import file_pin, load, pinned
from .scene_state import FrameMap, SceneState


DEFAULT_WEIGHT_SHA256 = "e78463c537c6172720c818c162c35d3a956143850db19fb251b66dd3004207b4"


def default_policy():
    root = Path(__file__).with_name("assets")
    version = load(root / "s1_version.json")["ground_candidate_policy"]
    weights = file_pin(root / version["weights"])
    if version["name"] != NAME or weights["sha256"] != version["sha256"] or weights["sha256"] != DEFAULT_WEIGHT_SHA256:
        raise ValueError("Default candidate policy differs from the version manifest")
    return dict(name=NAME, weights=weights)


def candidate_names(question, options, cache_phrases=None):
    from trace_format.contracts import new_contracts
    if new_contracts():
        from .phrases import candidate_phrases
        return candidate_phrases(question, options, cache_phrases)
    from trace_format.category_vocab import vocabulary, normalized
    text = normalized(" ".join([question, *options]))
    return tuple(sorted(name for name in vocabulary()
                        if re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", text)))


def build_backend(row, batch, artifact_pin, audit_dir, settings=None):
    from trace_format.contracts import contract_epoch, new_contracts
    settings = settings or {}
    with contract_epoch(settings.get('contract_epoch', new_contracts())):
        return _build_backend(row, batch, artifact_pin, audit_dir, settings)


def _build_backend(row, batch, artifact_pin, audit_dir, settings=None):
    settings = settings or {}
    allowed = {"ground_candidate_policy", "geometry_manifest", "depth_source", "allow_own_fallback", "contract_epoch"}
    if set(settings) - allowed:
        raise ValueError("Unknown LEG-S1 grounding setting")
    frames = FrameMap(tuple(batch["frame_indices"]))
    typ = row.get("question_type") or row.get("routing", {}).get("question_type")
    if not typ:
        raise ValueError("Grounding requires the input question type")
    inputs = row["student_input"]
    names = candidate_names(inputs["question"], inputs.get("options") or [],
                            batch.get("cache_phrases", row.get("candidate_phrases")))
    geometry = None
    if settings.get("geometry_manifest"):
        manifest = load(pinned(settings["geometry_manifest"]))
        if manifest.get("schema") != "s1-predicted-geometry-v1":
            raise ValueError("Invalid predicted-geometry manifest")
        entry = manifest["videos"].get(batch["video_sha256"])
        if entry is not None:
            from .ground_profiles import load_geometry
            geometry = load_geometry(pinned(entry), frames, settings.get("depth_source", "tower_scaled"))
    allow_fallback = settings.get("allow_own_fallback", True)
    if type(allow_fallback) is not bool:
        raise ValueError("allow_own_fallback must be boolean")
    if geometry is None and not allow_fallback:
        raise ValueError("Configured predicted geometry is unavailable")
    identity = geometry.identity if geometry is not None else "same_checkpoint_own:" + artifact_pin["sha256"]
    scene = SceneState(batch["video_sha256"], frames, identity)
    source = NativeMDG(frames, artifact_pin["sha256"], names=names)
    backend = GroundV3(scene, geometry, source, mask_source="mdg", audit_dir=audit_dir,
        geometry_profile=geometry.contract.profile if geometry is not None else "legacy_v3122",
        ground_candidate_policy=settings.get("ground_candidate_policy", default_policy()), question_type=typ)
    backend.allow_own_geometry_fallback = allow_fallback
    backend.geometry_source = "configured_predicted" if geometry is not None else "same_checkpoint_own"
    return backend
