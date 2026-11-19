"""Head backends: what answers a parsed call during decoding, scheduled sampling and the gate.

Every backend implements
  begin(context)         once per sample, after the prompt prefill
  depth(frame, point)    metres along the optical axis at the [0, 1000] grid point of the 1-based frame
  pose(frame)            PoseValue in the frame-1 gravity-aligned reference (see protocol)
and raises CallError for a call it cannot answer (the loop turns that into an error response, and the gate counts it
as a failure).

Backends here:
  OracleHeads     GT values: the row's recorded head calls first, then scene GT (Reference poses with the official
                  view, the first-hit depth raster of a first_hits_pack.Pack); nothing else
  NoisyHeads      a base backend's values with deterministic noise (scheduled-sampling and gate tests)
  ConstantHeads   fixed values, for loop tests
  ShuffledHeads   real head outputs recorded for other samples, permuted across samples (the shuffled control)
  RecordingHeads  a backend that records every value it answers into a HeadOutputPool (the shuffled arm's source)
  TinyStateHeads  a small learned head that reads the prefill hidden states, the shape of phase 1's heads
  Phase1Heads     phase 1's trained heads through student_pilot.head_api.HeadSession
"""
import hashlib
import math
import random

from .geometry import grid_to_raster, pose_from_gravity_rt
from .protocol import DEPTH_FRAMES, FRAME_ORIGIN, POSE_FRAMES, CallError, PoseValue, format_pose, validate


class HeadContext(object):
    """What a backend sees for one sample.

    input_ids       prompt token ids (1-D list)
    hidden_states   the prefill's hidden states (tuple of [1, T, H] tensors: embeddings, then each layer), or None
    video_token_id  id of the video placeholder token, to find each temporal group's tokens
    video_grid_thw  the processor's [t, h, w] grid of the video, or None
    key             a stable sample identity (seeds noisy backends, keys the shuffled pool)
    row             the dataset row; only oracle backends read it
    batch           the carrier-bearing prompt batch (Phase1Heads.from_model runs phase 1's session forward on it only
                    when no camera_states were captured)
    camera_states   the decode prefill's captured camera states (phase1.prefill), so the session needs no forward
    """

    def __init__(self, input_ids, hidden_states=None, video_token_id=None, video_grid_thw=None, key=None, row=None,
                 batch=None, camera_states=None):
        self.input_ids = list(input_ids)
        self.hidden_states = hidden_states
        self.video_token_id = video_token_id
        self.video_grid_thw = video_grid_thw
        self.key = key
        self.row = row
        self.batch = batch
        self.camera_states = camera_states

    def video_positions(self):
        if self.video_token_id is None:
            return []
        return [i for i, t in enumerate(self.input_ids) if t == self.video_token_id]

    @property
    def scene(self):
        row = self.row or {}
        return (row.get("dataset"), row.get("scene")) if row.get("scene") else None


class HeadBackend(object):
    needs_hidden_states = False
    addressing = "frame"

    def begin(self, context):
        self.context = context

    def depth(self, frame, point):
        raise NotImplementedError

    def pose(self, frame):
        raise NotImplementedError

    def answer(self, call):
        validate(call, addressing=self.addressing)
        if call.name == "depth":
            value = self.depth(call.frame, call.point)
            if not (isinstance(value, float) and math.isfinite(value) and value > 0):
                raise CallError("head", "the depth head returned no value")
            return value
        value = self.pose(call.frame)
        if not isinstance(value, PoseValue):
            raise CallError("head", "the pose head returned no value")
        try:
            format_pose(value)
        except ValueError as error:  # e.g. a field of view outside (0, 180): refused, never clamped
            raise CallError("head", "the pose head returned an unprintable value: %s" % error)
        return value


def value_of_record(record):
    """The GT value a converted row records for one call."""
    gt = record["gt"]
    if record["name"] == "depth":
        return float(gt["depth_m"])
    view = tuple(gt["view_deg"]) if gt.get("view_deg") else None
    return PoseValue(tuple(float(v) for v in gt["position_m"]), float(gt["heading_deg"]), float(gt["pitch_deg"]),
                     float(gt.get("roll_deg", 0.0)), view)


class ConstantHeads(HeadBackend):
    def __init__(self, depth=1.0, pose=PoseValue((0.0, 0.0, 0.0), 0.0, 0.0, 0.0, (60.0, 46.0))):
        self.value_depth, self.value_pose = float(depth), pose

    def depth(self, frame, point):
        return self.value_depth

    def pose(self, frame):
        return self.value_pose


class OracleHeads(HeadBackend):
    """GT answers. Recorded calls (row['head_calls']) answer exactly; other calls read scene GT: poses from
    `reference` (geometry.Reference with intrinsics), depth from `pack` (first_hits_pack.Pack: the first-hit surface
    depth at the grid point's raster pixel, at frames 2, 4, ..., 32). A pixel without a valid first hit raises
    CallError('no_surface'); a call with no GT source raises CallError('no_gt'). Nothing is approximated."""

    def __init__(self, reference=None, pack=None, raster_hw=(240, 320)):
        self.reference, self.pack, self.raster_hw = reference, pack, raster_hw

    def begin(self, context):
        HeadBackend.begin(self, context)
        self.recorded = {}
        for record in (context.row or {}).get("head_calls", []):
            point = tuple(record["point"]) if record.get("point") is not None else None
            self.recorded[(record["name"], record["frame"], point)] = value_of_record(record)

    def depth(self, frame, point):
        value = self.recorded.get(("depth", frame, tuple(point)))
        if value is not None:
            return float(value)
        if self.pack is not None:
            row, column = grid_to_raster(point, self.raster_hw)
            value = float(self.pack.depth_frame(frame)[row, column])
            face = int(self.pack.arrays["face_even"][DEPTH_FRAMES.index(frame)][row, column])
            if face >= 0 and math.isfinite(value) and 0.05 <= value <= 25.0:
                return value
            raise CallError("no_surface", "no first-hit surface at that point")
        raise CallError("no_gt", "no GT depth at that point")

    def pose(self, frame):
        value = self.recorded.get(("pose", frame, None))
        if value is not None:
            return value
        if self.reference is None:
            raise CallError("no_gt", "no GT pose for that frame")
        return self.reference.pose(frame)


class NoisyHeads(HeadBackend):
    """Wraps a backend and perturbs its values: log-normal depth noise; Gaussian position, heading, pitch, roll and
    view noise. Frame 1 stays the origin (position 0, heading 0): only its pitch and roll are perturbed. The noise is
    a pure function of (seed, sample key, call), so a replayed batch sees identical values."""

    def __init__(self, base, depth_log_sigma=0.04, position_sigma_m=0.04, heading_sigma_deg=2.5,
                 pitch_sigma_deg=2.0, roll_sigma_deg=1.0, view_sigma_deg=1.0, seed=17):
        self.base, self.seed = base, seed
        self.depth_log_sigma, self.position_sigma_m = float(depth_log_sigma), float(position_sigma_m)
        self.heading_sigma_deg, self.pitch_sigma_deg = float(heading_sigma_deg), float(pitch_sigma_deg)
        self.roll_sigma_deg, self.view_sigma_deg = float(roll_sigma_deg), float(view_sigma_deg)

    @property
    def needs_hidden_states(self):
        return self.base.needs_hidden_states

    def begin(self, context):
        HeadBackend.begin(self, context)
        self.base.begin(context)

    def _rng(self, *parts):
        text = "|".join(str(p) for p in (self.seed, self.context.key) + parts)
        return random.Random(int(hashlib.sha256(text.encode()).hexdigest()[:16], 16))

    def depth(self, frame, point):
        value = self.base.depth(frame, point)
        return float(value * math.exp(self._rng("depth", frame, tuple(point)).gauss(0.0, self.depth_log_sigma)))

    def pose(self, frame):
        value = self.base.pose(frame)
        rng = self._rng("pose", frame)
        pitch = max(-89.0, min(89.0, value.pitch_deg + rng.gauss(0.0, self.pitch_sigma_deg)))
        roll = value.roll_deg + rng.gauss(0.0, self.roll_sigma_deg)
        if frame == FRAME_ORIGIN:
            return PoseValue(value.position, value.heading_deg, pitch, roll, value.view_deg)
        position = tuple(v + rng.gauss(0.0, self.position_sigma_m) for v in value.position)
        view = None if value.view_deg is None else tuple(
            min(170.0, max(10.0, v + rng.gauss(0.0, self.view_sigma_deg))) for v in value.view_deg)
        return PoseValue(position, value.heading_deg + rng.gauss(0.0, self.heading_sigma_deg), pitch, roll, view)


class HeadOutputPool(object):
    """Real head outputs, keyed by the sample (and scene) that produced them: the shuffled control's only source."""

    def __init__(self):
        self.entries = {}

    @staticmethod
    def stratum(name, frame):
        return (name, "origin" if name == "pose" and frame == FRAME_ORIGIN else "anchor")

    def add(self, key, scene, name, frame, value):
        self.entries.setdefault(self.stratum(name, frame), []).append((key, scene, value))

    def candidates(self, key, scene, name, frame):
        return [value for k, s, value in self.entries.get(self.stratum(name, frame), [])
                if k != key and (scene is None or s != scene)]

    def __len__(self):
        return sum(len(v) for v in self.entries.values())

    @classmethod
    def from_rows(cls, rows, base):
        """Pool of `base`'s answers to every recorded call of every row (calls it refuses are left out)."""
        pool = cls()
        from .protocol import Call
        for row in rows:
            context = HeadContext([], key=row.get("qid"), row=row)
            base.begin(context)
            for record in row.get("head_calls") or []:
                call = Call(record["name"], record["frame"], tuple(record["point"]) if record.get("point") else None)
                try:
                    value = base.answer(call)
                except CallError:
                    continue
                pool.add(context.key, context.scene, call.name, call.frame, value)
        return pool


class RecordingHeads(HeadBackend):
    """A backend that records every value it answers into `pool` (the head arm of the shuffled ablation)."""

    def __init__(self, base, pool):
        self.base, self.pool = base, pool
        self.addressing = getattr(base, "addressing", "frame")

    @property
    def needs_hidden_states(self):
        return self.base.needs_hidden_states

    @property
    def needs_carriers(self):
        return bool(getattr(self.base, "needs_carriers", False))

    def begin(self, context):
        HeadBackend.begin(self, context)
        self.base.begin(context)

    def depth(self, frame, point):
        value = self.base.depth(frame, point)
        self.pool.add(self.context.key, self.context.scene, "depth", frame, value)
        return value

    def pose(self, frame):
        value = self.base.pose(frame)
        self.pool.add(self.context.key, self.context.scene, "pose", frame, value)
        return value


class ShuffledHeads(HeadBackend):
    """The shuffled control: each call gets a real head output that the heads produced for another sample (another
    scene when the samples carry scenes), of the same kind (depth, origin pose, or anchor-frame pose). The choice is a
    pure function of (seed, sample key, call). Values are never invented: an empty stratum raises CallError."""

    def __init__(self, pool, seed=31):
        self.pool, self.seed = pool, seed

    def _choose(self, name, frame, point=None):
        candidates = self.pool.candidates(self.context.key, self.context.scene, name, frame)
        if not candidates:
            raise CallError("no_shuffle_pool", "no head output of another sample to shuffle in")
        text = "|".join(str(p) for p in (self.seed, self.context.key, name, frame, point))
        return candidates[int(hashlib.sha256(text.encode()).hexdigest()[:16], 16) % len(candidates)]

    def depth(self, frame, point):
        return float(self._choose("depth", frame, tuple(point)))

    def pose(self, frame):
        return self._choose("pose", frame)


class Phase1Heads(HeadBackend):
    """Phase 1's trained heads (student_pilot.head_api.HeadSession, branch pd-build2-heads): pose answers frames 1, 2,
    4, ..., 32 in the frame-1 gravity reference with the view of info['fov_hw_rad'], depth answers frames 2, 4, ..., 32.

    `session_factory(context)` returns the sample's HeadSession. from_model builds it from the decode prefill's
    captured camera states (phase1.prefill: one forward with training's carrier embeddings and capture hooks); only a
    context without them (scheduled sampling outside a decode, the gate) runs HeadSession.from_forward on the
    carrier-bearing batch. A head that raises answers with CallError('head'); no other value is ever substituted."""

    needs_carriers = True

    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.session = None

    @classmethod
    def from_session(cls, session):
        return cls(lambda context: session)

    @classmethod
    def from_model(cls, model, forward_context=None):
        from .phase1 import session_forward, session_from_states

        def factory(context):
            if getattr(context, "camera_states", None) is not None:
                return session_from_states(model, context.camera_states)
            if context.batch is None or "aux_camera_positions" not in context.batch:
                raise ValueError("Phase1Heads needs the carrier-bearing prompt batch (camera_targets.insert_carriers)")
            return session_forward(model, context.batch, forward_context=forward_context)
        return cls(factory)

    def begin(self, context):
        HeadBackend.begin(self, context)
        self.session = self.session_factory(context)

    def depth(self, frame, point):
        if frame not in DEPTH_FRAMES:
            raise CallError("frame", "depth frame %r has no head output; valid frames are 2, 4, ..., 32" % (frame,))
        try:
            return float(self.session.depth(int(frame), [int(point[0]), int(point[1])]))
        except ValueError as error:
            raise CallError("head", str(error))

    def pose(self, frame):
        if frame not in POSE_FRAMES:
            raise CallError("frame", "pose frame %r has no head output; valid frames are 1, 2, 4, ..., 32" % (frame,))
        try:
            rot, trans, info = self.session.pose(int(frame))
        except ValueError as error:
            raise CallError("head", str(error))
        return pose_from_gravity_rt(rot, trans, info.get("fov_hw_rad"))


_TORCH_CLASSES = {}


def _torch_heads():
    if "TinyStateHeads" in _TORCH_CLASSES:
        return _TORCH_CLASSES["TinyStateHeads"]
    import torch
    from torch import nn

    class TinyStateHeads(nn.Module, HeadBackend):
        """Toy point-depth and pose heads over the prefill's final hidden states.

        A depth query (frame embedding + Fourier features of the grid point) and a pose query (frame embedding)
        cross-attend over every prompt token's state, so a head answer depends on the frames' tokens rather than
        on a pooled vector. Depth is softplus(.) + 0.05 m; pose is (x, y, z, heading/90, pitch/90)."""

        needs_hidden_states = True

        def __init__(self, hidden_size, dim=32, heads=2, frequencies=8, layer=-1):
            nn.Module.__init__(self)
            self.layer, self.frequencies = layer, frequencies
            self.frame = nn.Embedding(32, dim)
            self.point = nn.Linear(4 * frequencies, dim)
            self.pose_query = nn.Parameter(torch.zeros(dim))
            self.key = nn.Linear(hidden_size, dim)
            self.value = nn.Linear(hidden_size, dim)
            self.attend = nn.MultiheadAttention(dim, heads, batch_first=True)
            self.depth_out = nn.Sequential(nn.Linear(dim, dim), nn.GELU(), nn.Linear(dim, 1))
            self.pose_out = nn.Sequential(nn.Linear(dim, dim), nn.GELU(), nn.Linear(dim, 5))

        def states(self, context):
            return context.hidden_states[self.layer][0].float()  # [T, H]

        def fourier(self, points):
            scaled = points.float() / 1000.0
            bands = (2.0 ** torch.arange(self.frequencies, dtype=torch.float32)) * math.pi
            angles = scaled[..., None] * bands  # [Q, 2, F]
            return torch.cat((angles.sin(), angles.cos()), dim=-1).flatten(1)

        def read(self, states, queries):
            keys, values = self.key(states)[None], self.value(states)[None]
            out, _ = self.attend(queries[None], keys, values)
            return out[0]

        def depth_tensor(self, states, frames, points):
            """frames [Q] 1-based, points [Q, 2] grid -> metres [Q]."""
            queries = self.frame(frames - 1) + self.point(self.fourier(points))
            return nn.functional.softplus(self.depth_out(self.read(states, queries))[:, 0]) + 0.05

        def pose_tensor(self, states, frames):
            queries = self.frame(frames - 1) + self.pose_query
            return self.pose_out(self.read(states, queries))

        def depth(self, frame, point):
            with torch.no_grad():
                value = self.depth_tensor(self.states(self.context), torch.tensor([frame]), torch.tensor([point]))
            return float(value[0])

        def pose(self, frame):
            with torch.no_grad():
                v = self.pose_tensor(self.states(self.context), torch.tensor([frame]))[0].tolist()
            return PoseValue((v[0], v[1], v[2]), 90.0 * v[3], max(-89.0, min(89.0, 90.0 * v[4])))

        def loss(self, states, targets):
            """Head loss on a row's queried points: L1 on log depth plus L1 on the scaled pose (masked)."""
            total = states.new_zeros(())
            if targets["depth_mask"].any():
                m = targets["depth_mask"]
                pred = self.depth_tensor(states, targets["depth_frame"][m], targets["depth_point"][m])
                total = total + (pred.log() - targets["depth_m"][m].log()).abs().mean()
            if targets["pose_mask"].any():
                m = targets["pose_mask"]
                pred = self.pose_tensor(states, targets["pose_frame"][m])
                target = targets["pose"][m][:, :5].clone()  # x, y, z, heading, pitch (the toy head's outputs)
                target[:, 3:] = target[:, 3:] / 90.0
                total = total + (pred - target).abs().mean()
            return total

    _TORCH_CLASSES["TinyStateHeads"] = TinyStateHeads
    return TinyStateHeads


def TinyStateHeads(*args, **kwargs):
    return _torch_heads()(*args, **kwargs)
