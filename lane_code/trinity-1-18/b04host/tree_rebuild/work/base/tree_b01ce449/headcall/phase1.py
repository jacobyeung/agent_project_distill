"""The trainer's head code (student_pilot in this tree): the head API, carriers, the camera-hooked prefill, the gate's
thresholds and held-out scene list.

Phase 2 was built against phase 1's checkout (pd-build2-heads df6cf8c) and imported it from $PHASE1_TRAINER. On branch
headcall-fullft the headcall package lives in the trainer's own tree, so every import resolves to this tree's
student_pilot and the trainer commit pins both. provenance() records the tree's commit and the SHA-256 of every
student_pilot file phase 2 imports, so a gate report names the exact code it ran.
"""
import hashlib
import importlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMPORTED = ("student_pilot/head_api.py", "student_pilot/camera_targets.py", "student_pilot/camera_config.py",
            "student_pilot/gate_eval.py", "student_pilot/gate_driver.py", "student_pilot/auxiliary_losses.py",
            "student_pilot/camera_head.py", "student_pilot/batches.py", "student_pilot/ddp_training.py",
            "student_pilot/ddp_core.py", "student_pilot/diagnostic_data.py", "student_pilot/auxiliary_targets.py",
            "student_pilot/full_ft.py", "configs/gate_heldout_scenes_v1.json")
CARRIERS = 16


def trainer_root():
    return ROOT


def _module(name):
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    return importlib.import_module("student_pilot." + name)


def head_api():
    return _module("head_api")


def camera_targets():
    return _module("camera_targets")


def gate_eval():
    return _module("gate_eval")


def gate_driver():
    return _module("gate_driver")


def auxiliary_losses():
    return _module("auxiliary_losses")


def camera_heads(model):
    """The model's auxiliary heads when they include the camera head, else None."""
    unwrapped = auxiliary_losses().unwrap(model)
    heads = getattr(unwrapped, "auxiliary_heads", None)
    return heads if heads is not None and getattr(heads, "has_camera", False) else None


GEOMETRY_KEY = "geometry_features"


class GeometryContext(object):
    """Feeds one row's G3T features to the model's attached geometry input for exactly one vision forward, as the
    trainer's runner (supervised_logits) and the evaluator (generate_with_inputs) do: the features never reach the
    model as an input; the vision tower's forward hook consumes them. Entered once, around one forward, optionally
    wrapping another context (the trainer's autocast). A model with a geometry input refuses a forward without
    features, and a model without one refuses features, so no head-call forward can silently drop the geometry."""

    def __init__(self, model, features, inner=None):
        self.geometry = getattr(auxiliary_losses().unwrap(model), "geometry_input", None)
        if self.geometry is None and features is not None:
            raise ValueError("Geometry features supplied to a model without a geometry input")
        if self.geometry is not None and features is None:
            raise ValueError("A model with a geometry input needs the row's geometry features in every head-call "
                             "forward (prefill, session and matched forwards)")
        self.features, self.inner, self.calls = features, inner, None

    def __enter__(self):
        if self.inner is not None:
            self.inner.__enter__()
        if self.geometry is not None:
            self.calls = self.geometry.calls
            try:
                self.geometry.provide(self.features.to(next(self.geometry.parameters()).device))
            except BaseException:
                if self.inner is not None:
                    self.inner.__exit__(None, None, None)
                raise
        return self

    def __exit__(self, kind, value, traceback):
        try:
            if self.geometry is not None:
                pending = self.geometry._pending is not None
                self.geometry.clear()
                if kind is None and (pending or self.geometry.calls != self.calls + 1):
                    raise ValueError("Geometry features must be consumed by exactly one vision forward")
        finally:
            if self.inner is not None:
                self.inner.__exit__(kind, value, traceback)
        return False


def split_geometry(batch):
    """(batch without the geometry features, the features or None)."""
    return {k: v for k, v in batch.items() if k != GEOMETRY_KEY}, batch.get(GEOMETRY_KEY)


def session_forward(model, batch, forward_context=None):
    """HeadSession.from_forward over one carrier-bearing row, with the row's geometry features (if any) fed to the
    geometry input in that forward: the scheduled-sampling session forward and any context without prefill states."""
    batch, features = split_geometry(batch)
    return head_api().HeadSession.from_forward(model, batch, forward_context=GeometryContext(model, features,
                                                                                             forward_context))


def prefill(model, batch, forward_context=None, **forward_kwargs):
    """The decode prefill: one forward over a single carrier-bearing prompt (use_cache=True, logits_to_keep=1) with
    the trainer's camera hooks, registered as training registers them (auxiliary_losses.camera_hooks): the carrier
    embeddings become the learned c_first / c_rest camera tokens, and the decoder-layer, ViT-block and final-norm
    states the heads read are captured (auxiliary_losses.camera_head_inputs, which training and
    capture_camera_states share). Returns (output, camera_states): camera_states is {'carrier_states',
    'visual_grid', 'vit_grids'} for HeadSession, or None for a model without camera heads (plain forward). No second
    forward runs: Phase1Heads builds its session from these states. A geometry-input model reads the row's
    'geometry_features' from the batch through GeometryContext (one vision forward), never as a model input."""
    import torch

    batch, features = split_geometry(batch)
    feed = {k: v for k, v in batch.items() if not k.startswith("aux_") and k != "labels"}
    kwargs = dict(use_cache=True, logits_to_keep=1)
    kwargs.update(forward_kwargs)
    context = GeometryContext(model, features, forward_context)
    heads = camera_heads(model)
    if heads is None:
        with context:
            return model(**feed, **kwargs), None
    aux = auxiliary_losses()
    unwrapped = aux.unwrap(model)
    positions = batch.get("aux_camera_positions")
    if positions is None or tuple(positions.shape) != (1, CARRIERS) or bool((positions < 0).any()):
        raise ValueError("a camera-head model decodes from a prompt with the 16 carriers (insert_carriers)")
    need_depth = heads.camera.point_depth is not None
    captured, vit_captured, states = {}, {}, {}

    def hook(module, args, output):
        if states:
            return
        layer_states, grids, vit = aux.camera_head_inputs(heads, unwrapped, batch, output, captured, vit_captured,
                                                          need_depth)
        states["carrier_states"] = heads.camera.carrier_states(output, positions, layer_states)[0].float()
        states["visual_grid"] = grids[0].float() if grids is not None else None
        states["vit_grids"] = [grid.float() for grid in vit[0]] if vit is not None else None
        for key in ("aux_g3t_cam_tokens", "aux_g3t_pose_9d", "aux_g3t_gravity_up", "aux_g3t_step_scale"):
            if key in batch:
                states[key] = batch[key]
    handles = aux.camera_hooks(unwrapped, heads, batch, captured, vit_captured)
    handles.add(aux.final_norm(unwrapped).register_forward_hook(hook))
    try:
        with torch.no_grad(), context:
            output = model(**feed, **kwargs)
    finally:
        handles.remove()
    if "carrier_states" not in states:
        raise ValueError("the final language norm did not run in the prefill")
    return output, states


def session_from_states(model, states):
    """A HeadSession from a prefill's captured camera states (no forward)."""
    heads = camera_heads(model)
    if heads is None:
        raise ValueError("the model has no camera heads")
    return head_api().HeadSession(
        heads.camera,
        states["carrier_states"],
        states["visual_grid"],
        states["vit_grids"],
        g3t_cam_tokens=states.get("aux_g3t_cam_tokens"),
        g3t_pose_9d=states.get("aux_g3t_pose_9d"),
        g3t_gravity_up=states.get("aux_g3t_gravity_up"),
        g3t_step_scale=states.get("aux_g3t_step_scale"),
    )


def gate_thresholds():
    """The agreed gate (student_pilot.gate_eval.GATE): medians for pose and absolute depth error, means for AbsRel
    and delta < 1.25, and the decision-agreement floor."""
    return dict(gate_eval().GATE)


def heldout_scenes(path=None):
    """The 38 held-out scenes as (dataset token, scene token) pairs."""
    path = path or os.path.join(ROOT, "configs", "gate_heldout_scenes_v1.json")
    data = json.load(open(path))
    if data.get("schema") != "gate_heldout_scenes_v1":
        raise ValueError("not the held-out scene list: " + path)
    return [tuple(item) for item in data["scenes"]]


def commit():
    """The tree's HEAD commit, read from the git files (no git command)."""
    gitdir = os.path.join(ROOT, ".git")
    if os.path.isfile(gitdir):
        gitdir = open(gitdir).read().split("gitdir:", 1)[1].strip()
    head = open(os.path.join(gitdir, "HEAD")).read().strip()
    if not head.startswith("ref: "):
        return head
    ref = head[5:]
    common = gitdir
    if os.path.exists(os.path.join(gitdir, "commondir")):
        common = os.path.normpath(os.path.join(gitdir, open(os.path.join(gitdir, "commondir")).read().strip()))
    for base in (gitdir, common):
        path = os.path.join(base, ref)
        if os.path.exists(path):
            return open(path).read().strip()
    for line in open(os.path.join(common, "packed-refs")):
        if line.strip().endswith(" " + ref):
            return line.split()[0]
    raise ValueError("cannot resolve the tree's HEAD")


def provenance():
    files = {}
    for name in IMPORTED:
        path = os.path.join(ROOT, name)
        files[name] = hashlib.sha256(open(path, "rb").read()).hexdigest() if os.path.exists(path) else None
    try:
        head = commit()
    except (OSError, ValueError, IndexError):
        head = None  # an exported tree without git files (e.g. an AWS closure); the file hashes still pin the code
    return {"trainer": ROOT, "commit": head, "files_sha256": files}


def insert_carriers(batch, tokenizer):
    """camera_targets.insert_carriers: one <|fim_middle|> carrier after each of the 16 temporal groups' video-token
    runs, with 'aux_camera_positions' [1, 16]. Training prompts and decode prefills both go through it, so the heads
    read the positions they were trained on."""
    return camera_targets().insert_carriers(batch, tokenizer)


def carrier_token_id(tokenizer):
    return camera_targets().carrier_id(tokenizer)


def check_carriers(input_ids, tokenizer):
    """Raise unless the prompt holds exactly 16 carriers, each directly after a video-token run."""
    carrier = carrier_token_id(tokenizer)
    video = tokenizer.convert_tokens_to_ids(camera_targets().VIDEO_TOKEN)
    ids = [int(t) for t in input_ids]
    where = [i for i, t in enumerate(ids) if t == carrier]
    if len(where) != CARRIERS or any(i == 0 or ids[i - 1] != video for i in where):
        raise ValueError("the prompt needs the 16 camera carriers, one after each temporal group's video tokens "
                         "(found %d)" % len(where))
    return where
