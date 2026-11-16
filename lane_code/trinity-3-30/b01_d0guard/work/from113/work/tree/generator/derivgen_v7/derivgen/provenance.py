"""Configured imports, physical membership and scene registry admission."""
import importlib.util
import hashlib
import re
import sys
from pathlib import Path

from .common import ProvenanceError, Refusal, defer, digest, pinned, read_json, sha256, source_module

AUTH_SHA = "95ebc13b24b5fb8832b7ddc7f1c384bc808ddf6d77b013c132a8f5ef37ea3638"
MAP_SHA = "a88300f51dd3f35db3cf7e6daaa1d3f2ea9ee7d9fc6f3e959558163211756101"


def rung1_alias(canonical, source_alias=None):
    """Bind the division token to the admitted scene and its dataset prefix."""
    dataset, scene = canonical.split("/", 1)
    prefix = {"scannet": "d1", "scannetpp": "d2", "scannetppv2": "d2",
              "arkitscenes": "d3"}.get(dataset)
    # Synthetic and additional admitted datasets retain their authority prefix.
    if prefix is None and isinstance(source_alias, str):
        prefix = source_alias.split("/", 1)[0]
    if not scene or not isinstance(prefix, str) or not re.fullmatch(r"d[1-9][0-9]*", prefix):
        raise ProvenanceError("unknown rung-1 dataset prefix: " + canonical)
    return prefix + "/v" + hashlib.sha256(("rung1 scene " + canonical).encode()).hexdigest()[:12]


def exclusion_group(group):
    """Normalize only the documented external exclusion namespace spelling."""
    old = "scannetppv2/"
    return "scannetpp/" + group[len(old):] if group.startswith(old) else group


def adapters(config):
    root = Path(config["toolprog_root"]).resolve()
    pins = {str(Path(p["path"]).resolve()): p for p in config["dependencies"]}
    for name in ("programs.py", "tplib.py"):
        p = root / name
        if str(p) not in pins:
            raise ProvenanceError("unpinned adapter: " + str(p))
        pinned(pins[str(p)])
    pinned(config["spec"])
    # programs.py imports tplib by its public name. Bind that name before executing it;
    # its legacy sys.path insertion must never choose an unconfigured dependency.
    for name in ("tplib", "programs"):
        module = source_module(name, pins[str(root / (name + ".py"))])
        if Path(module.__file__).resolve() != root / (name + ".py"):
            raise ProvenanceError("adapter import escaped configured root")
    return sys.modules["programs"], sys.modules["tplib"]


def l1_api(config):
    """Reuse the pinned P1 v2 formatter; never import a model or torch runtime."""
    binding = config.get("l1")
    if not binding: return None
    path = pinned(binding["programs"])
    if path.name != "head_programs.py": raise ProvenanceError("L1 formatter path")
    receipt = read_json(pinned(binding["equivalence"]))
    if receipt.get("production_pass") is not True or receipt.get("eligible_default") != "cache":
        raise ProvenanceError("L1 cache equivalence receipt required")
    return source_module("derivgen_pinned_l1_programs", binding["programs"])


def validate_review_pool(config, record):
    """Authorize bounded review output without granting scale or training."""
    from .bindings import FAMILIES
    heads = sorted(set(FAMILIES) - {
        "room_size_estimation", "object_size_estimation", "absolute_size_object", "relative_size_object"})
    if (config.get("trace_form") != "canonical_v38" or config.get("readout_mode") != "gt"
            or config.get("source_schedule") != "review_type_coverage"
            or "canonical_preview_per_type" in config or "scale_approval" in config
            or config.get("additions") != {"max_candidates": 0}
            or sorted(config.get("required_review_types", [])) != heads
            or record.get("purpose") != "review_pool" or record.get("training_approval") is not False
            or not config.get("review_pool_authorization")):
        raise ProvenanceError("review pool needs bounded complete GT scope and explicit parent authorization")
    approval = read_json(pinned(config["review_pool_authorization"]))
    if (approval.get("schema") != "derivgen-review-pool-authorization-v1"
            or approval.get("issued_by") != "parent" or approval.get("scope") != "review_pool"
            or approval.get("review_only") is not True or approval.get("training_approval") is not False
            or approval.get("allow_above_pilot_ceiling") is not True
            or approval.get("source_row_ceiling") != 15000
            or approval.get("required_real_rows_per_type") != 25 or approval.get("head_types") != heads
            or not approval.get("user_instruction")):
        raise ProvenanceError("invalid review-only authorization")
    pinned(approval["user_instruction"])


def validate_build(config, config_path, infrastructure, parent_record=None):
    for p in config["dependencies"]:
        pinned(p)
    pinned(config["spec"])
    if infrastructure:
        if not config.get("infrastructure_only"):
            raise ProvenanceError("fixture mode requires infrastructure_only config")
        return
    if config.get("infrastructure_only"):
        raise ProvenanceError("synthetic config cannot launch production")
    stage = config.get("generation_stage", "pilot")
    if stage not in ("pilot", "review_pool", "scale"):
        raise ProvenanceError("generation_stage must be pilot, review_pool or scale")
    if stage == "scale":
        if not config.get("scale_approval"): raise ProvenanceError("parent/user/Claude real-pilot review required before scale")
        approval = read_json(pinned(config["scale_approval"]))
        from .bindings import FAMILIES
        if (approval.get("issued_by") != "parent" or approval.get("user_reviewed") is not True
                or approval.get("parent_reviewed") is not True or approval.get("Claude_review_pass") is not True
                or approval.get("real_rows_reviewed", 0) < 1000
                or any(approval.get("real_samples_per_type", {}).get(t, 0) < 5 for t in FAMILIES)
                or not approval.get("arithmetic_measured") or not approval.get("grounding_measured")):
            raise ProvenanceError("incomplete real-pilot scale approval")
    if not config.get("inputs"):
        raise ProvenanceError("production needs explicit source inputs")
    if not config.get("l1"):
        raise ProvenanceError("production needs pinned L1 formatter and equivalence receipt")
    if not config.get("row_ready"):
        raise ProvenanceError("parent row-ready receipt is still required")
    ready = read_json(pinned(config["row_ready"]))
    if ready.get("schema") == "p1cb-rows-handoff-v1":
        source = ready.get("files", {}).get("r.jsonl.gz", {})
        if (ready.get("status") != "P1CB ROWS READY" or ready.get("consumer") != "derivgen"
                or ready.get("excluded_group_overlap") != 0
                or ready.get("counts", {}).get("question_rows") != 380649
                or not any(p["path"] == source.get("path") and p["sha256"] == source.get("sha256") for p in config["inputs"])):
            raise ProvenanceError("P1c-b row-ready handoff mismatch")
    elif (ready.get("issued_by") != "parent" or ready.get("status") != "ready"
          or ready.get("inputs") != config["inputs"]
          or ready.get("scene_registry_sha256") != config["scene_registry"]["sha256"]):
        raise ProvenanceError("parent row-ready receipt mismatch")
    if parent_record is None:
        raise ProvenanceError("parent record path and SHA must be supplied on the command line")
    record = read_json(pinned(parent_record))
    if (record.get("issued_by") != "parent" or record.get("clean") is not True
            or not re.fullmatch(r"[0-9a-f]{40}", record.get("commit", ""))
            or record.get("config_sha256") != sha256(config_path)
            or record.get("spec_sha256") != config["spec"]["sha256"]
            or record.get("dependencies_sha256") != digest(config["dependencies"])):
        raise ProvenanceError("clean parent commit/config/spec/dependency record required")
    closure = record.get("code_closure", [])
    actual = {str(p.resolve()) for p in Path(__file__).parent.glob("*.py")}
    if {p["path"] for p in closure} != actual:
        raise ProvenanceError("parent code closure must pin every package module")
    for p in closure:
        pinned(p)
    if stage == "review_pool":
        validate_review_pool(config, record)


class Admission:
    def __init__(self, config, infrastructure=False):
        self.config, self.infrastructure = config, infrastructure
        from .goal_exclusions import RESTI_EXCLUSIONS, goal_tokens
        config.setdefault("goal_benchmark_exclusions", dict(RESTI_EXCLUSIONS))
        self.goal_tokens = goal_tokens(config)
        if not infrastructure and (config["authority"]["sha256"] != AUTH_SHA
                                   or config["scene_map"]["sha256"] != MAP_SHA):
            raise ProvenanceError("authority pins differ from dispatch")
        self.authority = read_json(pinned(config["authority"]))
        sm = read_json(pinned(config["scene_map"]))
        self.canonical = dict(self.authority["alias_to_canonical"])
        self.physical = dict(self.authority["alias_to_physical_group"])
        if (sm["alias_to_canonical"] != self.canonical
                or sm["alias_to_physical_group"] != self.physical):
            raise ProvenanceError("authority/scene-map disagreement")
        self.excluded = set(self.authority["excluded_canonical_groups"])
        if config.get("external_exclusions"):
            external = {exclusion_group(g) for g in read_json(pinned(config["external_exclusions"]))}
            if external != self.excluded:
                raise ProvenanceError("explicit physical exclusions disagree with P1c-b authority")
        self.blocked_alias = set(self.authority["group_ids"]) | set(sm.get("excluded_aliases", []))
        self.excluded |= {self.physical[a] for a in self.blocked_alias if a in self.physical}
        membership = read_json(pinned(config["membership"]))
        if (membership.get("reviewed") is not True
                or membership.get("authority_sha256") != config["authority"]["sha256"]):
            raise ProvenanceError("reviewed parent physical membership required")
        self.excluded |= set(membership["heldout_physical_groups"]) | set(membership["benchmark_physical_groups"])
        self.allowed = set(membership["train_physical_groups"])
        if self.allowed & self.excluded:
            raise ProvenanceError("training/exclusion physical overlap")
        if config.get("identity_additions"):
            additions = read_json(pinned(config["identity_additions"]))
            if additions.get("reviewed") is not True or additions.get("issued_by") != "parent":
                raise ProvenanceError("unreviewed identity additions")
            for a, entry in additions["aliases"].items():
                if a in self.canonical or not entry.get("evidence_sha256"):
                    raise ProvenanceError("identity addition collision/missing evidence")
                self.canonical[a], self.physical[a] = entry["canonical"], entry["physical_group"]
        registry = read_json(pinned(config["scene_registry"]))
        if registry.get("schema") != "derivgen-scenes-v1":
            raise ProvenanceError("scene registry schema")
        self.scenes = registry["scenes"]

    def identity(self, row):
        from .goal_exclusions import scene_tokens
        scene = row.get("scene", "")
        candidates = [scene, str(row.get("dataset", "")) + "/" + scene]
        if self.goal_tokens.intersection(scene_tokens(*candidates)):
            raise Refusal("goal_benchmark_scene", scene)
        aliases = [a for a in candidates if a in self.canonical]
        if not aliases:
            raise Refusal("unknown_alias", scene)
        if len({(self.canonical[a], self.physical[a]) for a in aliases}) != 1:
            raise ProvenanceError("ambiguous source alias")
        a = aliases[0]
        if self.goal_tokens.intersection((self.canonical[a], *aliases,
                                         rung1_alias(self.canonical[a], a))):
            raise Refusal("goal_benchmark_scene", self.canonical[a])
        physical = self.physical[a]
        if a in self.blocked_alias or physical in self.excluded:
            raise Refusal("excluded_physical_group", physical)
        if physical not in self.allowed:
            raise Refusal("outside_reviewed_training_membership", physical)
        return a, self.canonical[a], physical

    def entry(self, row):
        a, canonical, physical = self.identity(row)
        e = self.scenes.get(a)
        if e is None:
            defer("missing_scene_registry", a)
        if (e.get("canonical"), e.get("physical_group")) != (canonical, physical):
            raise ProvenanceError("registry identity mismatch: " + a)
        if bool(e.get("infrastructure_only")) != self.infrastructure:
            raise Refusal("infrastructure_scene_in_production")
        if e.get("coordinates") != "raw_z_up_opencv_c2w_m":
            raise ProvenanceError("unverified coordinate convention")
        geometry = e.get("geometry", {})
        if geometry.get("kind") != "native_gt":
            if not self.config.get("authorized_teacher"):
                raise Refusal("unauthorized_pseudo_geometry")
            teacher = read_json(pinned(self.config["authorized_teacher"]))
            if (teacher.get("issued_by") != "parent" or not teacher.get("authorized")
                    or teacher.get("fit_scope") not in ("full_video", "dense_video")
                    or teacher.get("selected_after_fit") is not True
                    or teacher.get("gt_sha256") != e["gt"]["sha256"]
                    or not teacher.get("dense_frame_indices")
                    or len(teacher["dense_frame_indices"]) <= 32
                    or not teacher.get("dense_accuracy") or not teacher.get("selected32_accuracy")):
                raise Refusal("teacher_dense_fit_evidence_missing")
        indices = e.get("frame_indices")
        if (not isinstance(indices, list) or len(indices) != 32
                or any(type(i) is not int or i < 0 for i in indices)
                or any(a >= b for a, b in zip(indices, indices[1:]))):
            raise ProvenanceError("registry requires 32 ordered source frames")
        si = row.get("student_input", row)
        ri = si.get("frame_indices")
        pending = row.get("frames_pending") or {}
        if ri is None:
            ri = pending.get("i")
        if ri is None:
            defer("missing_row_frame_indices")
        if ri != indices or (pending.get("i") is not None and pending["i"] != ri):
            raise Refusal("row_frame_alignment")
        if pending and (pending.get("s") != row.get("scene") or pending.get("d") != row.get("dataset")):
            raise Refusal("pending_identity_mismatch")
        return a, e
