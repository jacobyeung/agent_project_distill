"""Frozen point-depth source for tower scale; the own arm keeps its live heads."""
import copy
import hashlib
import math
from pathlib import Path
from types import SimpleNamespace
import weakref

import torch
from torch import nn

from .p3_provenance import digest, load, pinned, sha256

SCHEMA = 'tower-scale-donor-v1'
PREFIX = 'scale_donor.'
VISUAL = 'depth.model.visual.'
POINT = 'depth.auxiliary_heads.camera.point_depth.'
FEATURE_FILES = ('decoupled_v.py', 'decoupled_vc.py', 'p3_heads.py', 'point_depth_head.py',
                 'carrier_c1_data.py', 'scale_donor.py', 'tower_read.py',
                 '_tower_native.py', 'fixed_readout.py')


def tensor_pins(state):
    """Hash exact tensor bytes, with shape and dtype bound separately."""
    result = {}
    for name, tensor in sorted(state.items()):
        value = tensor.detach().cpu().contiguous()
        if not torch.isfinite(value).all():
            raise ValueError('Nonfinite donor tensor: ' + name)
        result[name] = dict(shape=list(value.shape), dtype=str(value.dtype),
                           sha256=hashlib.sha256(value.reshape(-1).view(torch.uint8).numpy().tobytes()).hexdigest())
    return result


def visual_identity(visual):
    return digest(tensor_pins(visual.state_dict()))


def feature_contract(depth):
    """Bind native patch processing, temporal layout, queries and head architecture."""
    root = Path(__file__).parent
    return dict(p3=copy.deepcopy(depth.config.p3), vision=depth.config.vision_config.to_dict(),
                point_depth=copy.deepcopy(depth.auxiliary_heads.camera.point_depth.settings),
                sources={name: sha256(root/name) for name in FEATURE_FILES})


def validate(settings):
    keys = {'schema', 'checkpoint', 'fov_source', 'visual_sha256', 'feature_contract_sha256'}
    if not isinstance(settings, dict) or set(settings) != keys or settings['schema'] != SCHEMA:
        raise ValueError('scale_donor requires the complete pinned tower-scale-donor-v1 configuration')
    if settings['fov_source'] not in ('V1', 'V2'):
        raise ValueError('scale_donor.fov_source must explicitly select V1 or V2')
    pin = settings['checkpoint']
    if not isinstance(pin, dict) or set(pin) != {'path', 'sha256'} or not Path(pin['path']).is_absolute():
        raise ValueError('scale_donor.checkpoint requires an absolute artifact path and SHA256')
    for value in (pin['sha256'], settings['visual_sha256'], settings['feature_contract_sha256']):
        if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError('scale_donor requires lowercase SHA256 pins')
    return copy.deepcopy(settings)


class ScaleDonor(nn.Module):
    def __init__(self, depth, settings, source, source_pins):
        super().__init__()
        self.settings = validate(settings)
        if depth.config.p3.get('frame_count') != 32:
            raise ValueError('Scale donor requires the fixed 32-frame grid')
        visual = depth.model.visual
        if any(p.requires_grad for p in visual.parameters()):
            raise ValueError('Scale donor requires an already frozen private visual copy')
        if digest(feature_contract(depth)) != settings['feature_contract_sha256']:
            raise ValueError('Scale donor preprocessing/architecture pin differs')
        own_visual = {k.removeprefix(VISUAL): v for k, v in source.items() if k.startswith(VISUAL)}
        if (not own_visual or digest(tensor_pins(own_visual)) != settings['visual_sha256']
                or visual_identity(visual) != settings['visual_sha256']):
            raise ValueError('Scale donor shared visual pin differs from checkpoint or live copy')
        self.point_depth = copy.deepcopy(depth.auxiliary_heads.camera.point_depth)
        self.point_depth.load_state_dict({k.removeprefix(POINT): v for k, v in source.items()
                                          if k.startswith(POINT)}, strict=True)
        # PrefixCapture adds these queries to private pooled states. V1 must not
        # read the live queries, even though the visual weights are frozen.
        key = 'depth.auxiliary_heads.frame_queries'
        if key not in source or source[key].shape != depth.auxiliary_heads.frame_queries.shape:
            raise ValueError('MISSING donor checkpoint tensor: ' + key)
        self.frame_queries = nn.Parameter(source[key].detach().clone(), requires_grad=False)
        if settings['fov_source'] == 'V1':
            self.fov = copy.deepcopy(depth.fov)
            self.fov.load_state_dict({k.removeprefix('depth.fov.'): v for k, v in source.items()
                                     if k.startswith('depth.fov.')}, strict=True)
        self.config = copy.deepcopy(depth.config)
        self.gradient_checkpointing = False
        # A weak reference shares the frozen copy without registering or exporting it twice.
        self._visual_ref = weakref.ref(visual)
        self.source_pins = copy.deepcopy(source_pins)
        self.requires_grad_(False)
        self.train(False)
        self.initial_pins = tensor_pins(self.state_dict())

    @property
    def visual(self):
        visual = self._visual_ref()
        if visual is None:
            raise ValueError('Scale donor shared visual is unavailable')
        return visual

    def train(self, mode=True):
        super().train(False)
        self.visual.eval()
        return self

    def assert_frozen(self):
        if any(p.requires_grad for p in self.parameters()) or any(p.requires_grad for p in self.visual.parameters()):
            raise ValueError('Scale donor or shared visual was made trainable')
        if self.training or self.visual.training:
            raise ValueError('Scale donor and shared visual must stay in eval mode')

    @torch.no_grad()
    def forward(self, batch, tower_state=None):
        from .decoupled_v import features
        from .tower_read import GRID_UV, TowerState
        self.assert_frozen()
        # This isolated feature view uses only frozen donor queries and the shared
        # private ViT. It never reads the LM, live pose FoV or live depth queries.
        heads = SimpleNamespace(backing='decoupled_vc', camera=SimpleNamespace(point_depth=self.point_depth),
                                frame_queries=self.frame_queries)
        visual_owner = nn.Module()
        visual_owner.model = nn.Module()
        visual_owner.model.visual = self.visual
        view = SimpleNamespace(config=self.config, model=visual_owner.model, auxiliary_heads=heads,
                               named_modules=visual_owner.named_modules, training=False,
                               gradient_checkpointing=False)
        captured = features(view, batch, allow_short=True)
        if captured.states.shape[:2] != (1, 32):
            raise ValueError('Scale donor requires one clip with 32 anchor frames')
        if self.settings['fov_source'] == 'V1':
            fov = (1e-4 + (math.pi - 2e-4) * self.fov(captured.states.float()).sigmoid())[0]
        else:
            if not isinstance(tower_state, TowerState):
                raise ValueError('V2 requires the frozen G3T TowerState')
            tower_state.validate_batch(batch)
            fov = torch.as_tensor(tower_state.raw_pose9[tower_state.anchor_slots, 7:9].copy(),
                                  device=captured.states.device, dtype=torch.float32)
        if fov.shape != (32, 2) or not torch.isfinite(fov).all() or not ((fov > 0) & (fov < math.pi)).all():
            raise ValueError('Donor FoV requires finite vertical/horizontal radians')
        axis = torch.as_tensor(GRID_UV.copy(), device=captured.states.device)
        yy, xx = torch.meshgrid(axis, axis, indexing='ij')
        uv = torch.stack((xx, yy), -1).reshape(1, -1, 2).expand(32, -1, -1)
        latent = self.point_depth.encode(captured.grids[0], captured.vits[0], fov.float())
        return self.point_depth.query(latent, uv).reshape(32, 51, 51)

    def metadata(self, state=None, visual_state=None):
        self.assert_frozen()
        pins = tensor_pins(self.state_dict() if state is None else state)
        if pins != self.initial_pins:
            raise ValueError('Scale donor tensor changed since initialization')
        visual_sha = visual_identity(self.visual) if visual_state is None else digest(tensor_pins(visual_state))
        if visual_sha != self.settings['visual_sha256']:
            raise ValueError('Scale donor shared visual changed since initialization')
        from .tower_scale import RULE_SHA256, ESTIMATOR_SHA256
        from .tower_read import WEIGHTS_SHA256, CONFIG_SHA256, SOURCE_SHA256, NATIVE_INPUT
        fov = (dict(kind='checkpoint_private_fov', tensor_prefix='scale_donor.fov.')
               if self.settings['fov_source'] == 'V1' else
               dict(kind='frozen_g3t_intrinsics', weights_sha256=WEIGHTS_SHA256,
                    config_sha256=CONFIG_SHA256, source_sha256=SOURCE_SHA256,
                    preprocessing=NATIVE_INPUT, selection='raw_pose9[anchor_slots,7:9]'))
        return dict(schema=SCHEMA, settings=copy.deepcopy(self.settings), tensors=pins,
                    shared_visual_sha256=visual_sha, input_sha256=copy.deepcopy(self.source_pins),
                    fov_source=fov, scale_rule=dict(rule_sha256=RULE_SHA256,
                                                   estimator_sha256=ESTIMATOR_SHA256))


def attach(model, settings, *, verify_assets=True):
    """Load after warm start; followers may reuse rank zero's asset verification.

    verify_assets=False is only for the trainer's synchronized, immutable staging
    path after rank zero has successfully attached with verification enabled.
    Tensor, visual and feature-contract checks remain mandatory on every rank.
    """
    settings = validate(settings)
    if hasattr(model.auxiliary_heads, 'scale_donor'):
        raise ValueError('Scale donor is already attached')
    artifact_path = pinned(settings['checkpoint'])
    artifact = load(artifact_path)
    if (artifact.get('schema') != 'carrier-c1-artifact-v1' or artifact.get('pose_backing') != 'lm_final_norm'
            or artifact.get('step') not in (400, 544)):
        raise ValueError('Scale donor checkpoint must be a C1 export artifact')
    from .r1_persisted import relocated
    heads_pin = artifact['heads']
    if not isinstance(heads_pin, dict) or set(heads_pin) != {'path', 'sha256'}:
        raise ValueError('Donor heads require an exact path/SHA256 pin')
    heads_path = pinned(heads_pin) if verify_assets else Path(relocated(heads_pin))
    if not heads_path.is_absolute() or not heads_path.is_file():
        raise ValueError('Missing donor heads: ' + str(heads_path))
    # Immutable local staging lets ranks share file-backed pages rather than
    # eagerly deserializing the entire source export into each process.
    state = torch.load(heads_path, map_location='cpu', weights_only=True, mmap=True)
    source_pins = {settings['checkpoint']['path']: settings['checkpoint']['sha256'],
                   artifact['heads']['path']: artifact['heads']['sha256']}
    donor = ScaleDonor(model.auxiliary_heads.depth, settings, state, source_pins)
    model.auxiliary_heads.scale_donor = donor
    return donor


def export_metadata(model, heads):
    donor = getattr(model.auxiliary_heads, 'scale_donor', None)
    if donor is None:
        return None
    state = {k.removeprefix(PREFIX): v for k, v in heads.items() if k.startswith(PREFIX)}
    visual = {k.removeprefix(VISUAL): v for k, v in heads.items() if k.startswith(VISUAL)}
    return donor.metadata(state, visual)


def verify_export(model, heads, metadata):
    """Verify against the pinned initialization, not self-reported export hashes."""
    expected = export_metadata(model, heads)
    if expected != metadata:
        raise ValueError('Scale donor export pins differ or donor binding is absent')
    if expected is None and any(k.startswith(PREFIX) for k in heads):
        raise ValueError('Scale donor tensors require an explicit reader binding')
    return expected
