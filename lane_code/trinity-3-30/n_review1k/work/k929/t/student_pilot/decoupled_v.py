"""Stage 1 on frozen base vision features, using the P3 native head contract."""
import copy
import hashlib
import math
from pathlib import Path
from types import SimpleNamespace

import torch
from torch import nn
from torch.nn import functional as F

from .p3_heads import P3Heads, PrefixCapture
from .readout_geometry import depth_readout, geometry_diagnostics
from .p3_provenance import digest, file_pin, load, pinned, sha256, write

ANCHORS = list(range(2, 33, 2))
RECIPE = dict(steps=1600, global_batch=64, world_size=8, warmup_ratio=.03,
              learning_rate=1e-4, weight_decay=.01, milestones=[200, 400, 800, 1600], seed=17)


def head_settings(camera, base_identity, encoder_sha, all_frames=False):
    from .camera_config import normalize
    if type(all_frames) is not bool:
        raise ValueError('all_frames must be boolean')
    if camera.get('g3t_prior') or camera.get('max_groups', 16) not in ((16, 32) if all_frames else (16,)):
        raise ValueError('Decoupled training requires fresh heads and 16 fused anchors')
    # P3's camera schema predates trainer-only freeze/max_groups/prior fields.
    camera = {k: v for k, v in camera.items() if k not in ('freeze_modules', 'max_groups', 'g3t_prior', 'row_routing')}
    camera = normalize({**camera, 'feature_layers': None})
    return dict(schema='p3-model-v1', feature_backing='decoupled_v', start='base',
                camera=camera, anchors=list(range(1, 33)) if all_frames else ANCHORS,
                temporal_grouping='fused_pairs_all_frames' if all_frames else 'fused_pairs_second_anchor',
                translation_convention='metric', depth_convention='optical_axis_metric',
                base_identity=base_identity, feature_encoder_sha256=encoder_sha, head_loss_weight=0.)


def tensor_identity(state):
    return digest({k: {'shape': list(v.shape), 'dtype': str(v.dtype),
                       'sha256': hashlib.sha256(memoryview(v.contiguous().view(torch.uint8).numpy())).hexdigest()}
                   for k, v in state.items()})


def base_manifest(root, base_identity):
    """CPU preparation measures native assets once; only vision tensors are materialized."""
    from safetensors import safe_open
    from .students import get_student
    root = Path(root).resolve()
    spec = get_student('qwen35')
    if root.name != spec['snapshot'].name or sha256(root/'config.json') != spec['config_sha256']:
        raise ValueError('Stage 1 must start from the original base snapshot')
    files = {p.name: sha256(p) for p in sorted(root.iterdir()) if p.is_file()}
    vision = {}
    for name in files:
        if name.endswith('.safetensors'):
            with safe_open(root/name, framework='pt', device='cpu') as h:
                for k in h.keys():
                    if k.startswith('model.visual.'):
                        if k in vision:
                            raise ValueError('Duplicate vision tensor')
                        vision[k] = h.get_tensor(k)
    if not vision:
        raise ValueError('Base snapshot has no native vision tensors')
    return dict(schema='p3-model-input-v1', infrastructure_only=False, kind='base',
                root=str(root), base_identity=base_identity, files=files,
                feature_encoder_sha256=tensor_identity(vision))


class VisionOnly(nn.Module):
    """Native vision module under its native name; no decoder is constructed."""
    def __init__(self, config, visual):
        super().__init__()
        self.config = config
        self.model = nn.Module()
        self.model.visual = visual.requires_grad_(False).eval()
        # HF dtype='auto' loads BF16 parameters but keeps native FP32 rotary buffers.
        # Casting the entire module would round those buffers and change features.
        for parameter in self.model.visual.parameters():
            parameter.data = parameter.data.to(dtype=torch.bfloat16)
        self.auxiliary_heads = P3Heads(config).float()
        if hasattr(self.auxiliary_heads, 'frame_queries'):
            # Trainer loss capacity is not part of P3's serialized camera schema.
            self.auxiliary_heads.camera.settings['max_groups'] = 32

    def train(self, mode=True):
        super().train(mode)
        self.model.visual.eval()
        return self

    def forward(self, batch, targets):
        capture = features(self, batch, allow_short=True)
        n = capture.states.shape[1]
        slots = len(self.config.p3['anchors'])
        states = F.pad(capture.states, (0, 0, 0, slots-n))
        positions = torch.arange(slots, device=states.device)[None]
        positions = torch.where(positions < n, positions, -1)
        targets = {**targets, 'aux_camera_positions': positions}
        loss = self.auxiliary_heads.camera.loss(states, targets, visual_grids=capture.grids,
                                                 vit_grids=capture.vits,
                                                 frame_queries=getattr(self.auxiliary_heads, 'frame_queries', None))
        # Carrier embedding tokens are retained for exact P3 state-dict compatibility.
        return loss + self.auxiliary_heads.camera.tokens.sum()*0.


def features(model, batch, allow_short=False):
    """P3's exact finish implementation after a vision-only native forward."""
    grid = batch['video_grid_thw']
    if grid.shape != (1, 3):
        raise ValueError('Use one video per microbatch; accumulate row means')
    n = int(grid[0, 0])
    anchors = model.config.p3['anchors']
    from trace_format.readout_config import load as readout_config
    frame_count=model.config.p3.get('frame_count',readout_config()['frame_count'])
    groups=frame_count//2
    all_frames = anchors == list(range(1, frame_count+1))
    if anchors != ANCHORS and not (all_frames and hasattr(model.auxiliary_heads, 'frame_queries')
            and model.config.p3['temporal_grouping'] == 'fused_pairs_all_frames'):
        raise ValueError('The supplied supervision cannot train all-frame queries')
    single_slot = model.config.p3.get('frame_layout', 'spread') in ('duplicate', 'paired')
    allowed = tuple(range(1, frame_count+1)) if allow_short else (frame_count,)
    if n not in (allowed if single_slot else (tuple(range(groups//4,groups+1,groups//4)) if allow_short else (groups,))):
        raise ValueError('Unexpected temporal groups')
    view = model
    if n != groups or single_slot:
        # Only finish's length assertion changes. Hooks, raster ordering, pooling and dtype do not.
        cfg = copy.copy(model.config)
        cfg.p3 = {**cfg.p3, 'anchors': anchors[:n * (2 if all_frames and not single_slot else 1)]}
        view = SimpleNamespace(config=cfg, auxiliary_heads=model.auxiliary_heads,
                               named_modules=model.named_modules)
    if model.config.p3['feature_backing'] == 'decoupled_vc':
        from .decoupled_vc import capture_features
        return capture_features(model, view, batch)
    with torch.no_grad(), PrefixCapture(view, batch) as capture:
        visual = model.model.visual
        visual(batch['pixel_values_videos'].to(dtype=next(visual.parameters()).dtype), grid_thw=grid)
    capture.finish()
    return capture


def load_vision(manifest, settings):
    from safetensors import safe_open
    from transformers import Qwen3_5Config
    from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5VisionModel
    root = Path(manifest['root'])
    if manifest.get('kind') != 'base' or settings.get('start') != 'base' or settings.get('feature_backing') not in ('decoupled_v', 'decoupled_vc'):
        raise ValueError('Stage 1 requires base vision provenance')
    if manifest['base_identity'] != settings['base_identity'] or manifest['feature_encoder_sha256'] != settings['feature_encoder_sha256']:
        raise ValueError('Model and head provenance differ')
    for name, sha in manifest['files'].items():
        if Path(name).name != name:
            raise ValueError('Invalid base asset name')
        if not name.endswith('.safetensors') and sha256(root/name) != sha:
            raise ValueError('Base configuration or processor assets changed')
    config = Qwen3_5Config.from_dict(load(root/'config.json'))
    config.p3 = settings
    config.vision_config._attn_implementation = 'sdpa'
    state = {}
    for name in manifest['files']:
        if name.endswith('.safetensors'):
            with safe_open(root/name, framework='pt', device='cpu') as h:
                for k in h.keys():
                    if k.startswith('model.visual.'):
                        state[k] = h.get_tensor(k)
    if tensor_identity(state) != settings['feature_encoder_sha256']:
        raise ValueError('Frozen encoder differs from the base pin')
    # Native rotary buffers are nonpersistent; a meta construction would leave them unmaterialized.
    visual = Qwen3_5VisionModel(config.vision_config)
    visual.load_state_dict({k[len('model.visual.'):]: v for k, v in state.items()}, strict=True, assign=True)
    if settings['feature_backing'] == 'decoupled_vc':
        from .decoupled_vc import VisionCopy
        return VisionCopy(config, visual)
    return VisionOnly(config, visual)


def target_tensors(record, device='cpu', all_frames=False):
    d = record['point_depth']
    values = dict(aux_camera_target=record['camera'], aux_camera_mask=record['camera_mask'],
                  aux_camera_scale=record['trajectory_scale'], aux_gravity_target=record['gravity'],
                  aux_gravity_mask=record['gravity_mask'], aux_point_depth_uv=d['uv'],
                  aux_point_depth_gt=d['depth'], aux_point_depth_mask=d['mask'])
    tensors = {k: torch.tensor(v, dtype=torch.bool if k.endswith('mask') else torch.float32,
                              device=device).unsqueeze(0) for k, v in values.items()}
    slots = len(record['camera'])
    if slots not in ((16, 32) if all_frames else (16,)):
        raise ValueError('Camera target slots differ from the selected head contract')
    if all_frames:
        for key in ('aux_camera_target', 'aux_camera_mask', 'aux_point_depth_uv',
                    'aux_point_depth_gt', 'aux_point_depth_mask'):
            value = tensors[key]
            if value.shape[1] == 16:
                expanded = value.new_zeros((1, 32, *value.shape[2:]))
                expanded[:, 1::2] = value
                tensors[key] = expanded
            elif value.shape[1] != 32:
                raise ValueError('All-frame targets require 16 or 32 slots')
    return tensors


def learning_rate(step, recipe=RECIPE):
    warm = math.ceil(recipe['steps']*recipe['warmup_ratio'])
    if step <= warm:
        return recipe['learning_rate']*step/warm
    return recipe['learning_rate']*.5*(1+math.cos(math.pi*(step-warm)/(recipe['steps']-warm)))


def export_heads(model, directory, step, provenance):
    from safetensors.torch import save_file
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    weights = directory/'heads.safetensors'
    save_file({k: v.detach().float().cpu().contiguous() for k, v in model.auxiliary_heads.state_dict().items()}, str(weights))
    artifact = {**model.config.p3, 'schema': 'p3-head-artifact-v1', 'step': step,
                'dimensions': {'vision': model.config.vision_config.hidden_size,
                               'language': model.config.text_config.hidden_size},
                'weights': file_pin(weights), 'provenance': provenance,
                'feature_dtype': 'bfloat16', 'head_dtype': 'float32'}
    if model.config.p3['feature_backing'] == 'decoupled_vc':
        encoder = directory/'encoder.safetensors'
        # FP32 masters are the canonical saved copy; consumers cast for BF16 compute.
        state = {k: v.detach().cpu().contiguous() for k, v in model.model.visual.state_dict().items()}
        save_file(state, str(encoder))
        artifact['encoder_copy'] = dict(weights=file_pin(encoder), tensor_sha256=tensor_identity(state),
                                       parameter_dtype='float32', compute_dtype='bfloat16',
                                       key_prefix='')
    write(directory/'heads.json', artifact)
    return file_pin(directory/'heads.json')


def load_heads(model, artifact_pin):
    """Same strict keys and state loading as P3Model.load_heads."""
    from safetensors.torch import load_file
    artifact = load(pinned(artifact_pin))
    keys = ('feature_backing', 'camera', 'anchors', 'translation_convention', 'base_identity',
            'start', 'temporal_grouping', 'feature_encoder_sha256', 'depth_convention')
    if artifact.get('schema') != 'p3-head-artifact-v1' or any(artifact.get(k) != model.config.p3.get(k) for k in keys):
        raise ValueError('Head artifact provenance differs')
    if artifact['dimensions'] != {'vision': model.config.vision_config.hidden_size,
                                   'language': model.config.text_config.hidden_size}:
        raise ValueError('Head dimensions differ')
    heads = load_file(str(pinned(artifact['weights'])))
    if artifact['feature_backing'] == 'decoupled_vc':
        saved = artifact['encoder_copy']
        if (saved['parameter_dtype'], saved['compute_dtype'], saved['key_prefix']) != ('float32', 'bfloat16', ''):
            raise ValueError('Unsupported private encoder precision or keys')
        state = load_file(str(pinned(saved['weights'])))
        if tensor_identity(state) != saved['tensor_sha256']:
            raise ValueError('Private encoder tensor identity differs')
        model.model.visual.load_state_dict(state, strict=True)
    model.auxiliary_heads.load_state_dict(heads, strict=True)
    return artifact


def readout(model, batch, uv):
    """Score raw head outputs and report P3 tool validation separately."""
    model.eval()
    capture = features(model, batch)
    with torch.no_grad():
        pose, gravity, scale = model.auxiliary_heads.camera.predict_all(capture.states, **capture.pose_inputs())
        anchors = model.config.p3['anchors']
        depth_anchors = ANCHORS if len(uv) == 16 else anchors
        depth = depth_readout(capture, pose, uv, depth_anchors)
        raw_pose = pose[-1][0].double().cpu().tolist()
        diagnostics = geometry_diagnostics(capture, raw_pose)
    return dict(raw_pose=raw_pose,
                gravity_up=gravity[-1][0].double().cpu().tolist(),
                trajectory_step_m=float(scale[-1][0].exp()), point_depth=depth, **diagnostics)
