"""GF-1: frozen dense G3T bank, aligned residuals, and explicit training stages."""
from contextlib import contextmanager, ExitStack
import copy
import math
import weakref

import torch
from torch import nn
from torch.utils.checkpoint import checkpoint

DEFAULT = dict(layers=[11, 17, 23], top_k=0, hidden=1024, injection='pre_lm',
               stage=1, learning_rate=1e-4, dense_frames=64, checkpointing=True, gf1_init='warm')


def normalize(value):
    if not isinstance(value, dict) or set(value) - set(DEFAULT):
        raise ValueError('Unknown GF1 setting')
    cfg = copy.deepcopy(DEFAULT | value)
    if cfg['gf1_init'] not in ('warm', 'zero'):
        raise ValueError('GF1 init must be warm or explicit zero')
    if cfg['stage'] == 2:
        if 'learning_rate' in value:
            raise ValueError('Stage 2 GF1 uses the actual LM rate; remove learning_rate')
        cfg.pop('learning_rate')
    layers = cfg['layers']
    if (not isinstance(layers, list) or not layers or layers != sorted(set(layers))
            or any(type(x) is not int or not 0 <= x <= 23 for x in layers)):
        raise ValueError('GF1 layers must be unique increasing zero-based aggregator indices')
    if cfg['top_k'] not in (0, 2) or (cfg['top_k'] == 2 and len(layers) < 2):
        raise ValueError('GF1 router selects exactly two layers, or sum uses top_k=0')
    if cfg['injection'] not in ('pre_lm', 'lm_012') or cfg['stage'] not in (1, 2):
        raise ValueError('Invalid GF1 injection or stage')
    if cfg['injection'] == 'lm_012' and len(layers) != 3:
        raise ValueError('LM 0/1/2 ablation requires three bank layers')
    if (type(cfg['hidden']) is not int or cfg['hidden'] < 1
            or type(cfg['dense_frames']) is not int or cfg['dense_frames'] < 1
            or type(cfg['checkpointing']) is not bool
            or (cfg['stage'] == 1 and (type(cfg['learning_rate']) not in (int, float)
                or not math.isfinite(cfg['learning_rate']) or cfg['learning_rate'] <= 0))):
        raise ValueError('Invalid GF1 dimensions or learning rate')
    return cfg


def area_pool(features, coords, grid, merge=2):
    """Integrate constant square G3T patch cells over the unpadded Qwen grid.

    features: [frames, patch rows, patch columns, channels]; coords: xyxy in
    the 1024-pixel padded source. Flatten output in temporal/row/column order.
    Projection precedes pooling; no register or camera token enters the grid.
    """
    t, h, w = map(int, grid)
    if (features.ndim != 4 or len(features) != t or h <= 0 or w <= 0
            or h % merge or w % merge or coords.shape != (t, 4)
            or not torch.isfinite(coords).all() or (coords[:, :2] < 0).any()
            or (coords[:, 2:] > 1024).any() or (coords[:, 2:] <= coords[:, :2]).any()):
        raise ValueError('GF1 invalid grid, frame count or ROI')
    def weights(start, end, source, target):
        edges = torch.linspace(0, 1024, source + 1, device=features.device)
        bounds = torch.linspace(0, 1, target + 1, device=features.device) * (end-start) + start
        return (torch.minimum(bounds[1:, None], edges[None, 1:]) -
                torch.maximum(bounds[:-1, None], edges[None, :-1])).clamp_min(0) / ((end-start)/target)
    pooled = []
    with torch.autocast(features.device.type, enabled=False):
        for block, (x1, y1, x2, y2) in zip(features, coords.float()):
            y = weights(y1, y2, block.shape[0], h//merge)
            x = weights(x1, x2, block.shape[1], w//merge)
            pooled.append(torch.einsum('ai,ijd,bj->abd', y, block.float(), x))
    return torch.stack(pooled).flatten(0, 2)


class Fusion(nn.Module):
    def __init__(self, output_dim, settings, input_dim=2048):
        super().__init__()
        self.settings = settings = normalize(settings)
        self.norms = nn.ModuleList([nn.LayerNorm(input_dim) for _ in settings['layers']])
        self.projections = nn.ModuleList([nn.Linear(input_dim, settings['hidden']) for _ in settings['layers']])
        self.router = nn.Linear(output_dim, len(settings['layers'])) if settings['top_k'] else None
        count = 3 if settings['injection'] == 'lm_012' else 1
        self.outputs = nn.ModuleList([nn.Linear(settings['hidden'], output_dim, bias=False) for _ in range(count)])
        for output in self.outputs:
            nn.init.zeros_(output.weight)

    def pooled_bank(self, bank, coords, grid):
        if bank.shape[0] != len(self.norms) or bank.ndim != 5 or not torch.isfinite(bank).all():
            raise ValueError('GF1 bank must be finite [layers, frames, h, w, channels]')
        return torch.stack([area_pool(proj(norm(layer.to(proj.weight.dtype))), coords, grid)
                            for norm, proj, layer in zip(self.norms, self.projections, bank)])

    def forward(self, visual, *clips):
        banks = []
        for i in range(0, len(clips), 3):
            banks.append(self.pooled_bank(*clips[i:i+3]))
        pooled = torch.cat(banks, dim=1)
        if pooled.shape[1] != visual.shape[0]:
            raise ValueError('GF1 bank does not match the video placeholders')
        if self.router is not None:
            scores = self.router(visual.to(self.router.weight.dtype))
            values, indices = scores.topk(2, dim=-1)
            weights = torch.zeros_like(scores).scatter(-1, indices, values.softmax(-1))
            pooled = pooled * weights.T.unsqueeze(-1)
        if self.settings['injection'] == 'pre_lm':
            return (self.outputs[0](pooled.sum(0).to(self.outputs[0].weight.dtype)),)
        return tuple(output(layer.to(output.weight.dtype)) for output, layer in zip(self.outputs, pooled))

    @contextmanager
    def inject(self, model, clips, batch, metrics):
        video_grid = batch['video_grid_thw']
        pending = True
        deltas = None
        def visual_hook(module, args, kwargs, output):
            nonlocal pending, deltas
            grid = kwargs.get('grid_thw', args[1] if len(args) > 1 else None)
            if grid is not video_grid:
                return output
            if not pending:
                raise ValueError('GF1 video features consumed twice')
            pending = False
            visual = output.pooler_output if hasattr(output, 'pooler_output') else output[1]
            inputs = tuple(tensor for clip in clips for tensor in clip)
            if self.settings['checkpointing'] and torch.is_grad_enabled():
                deltas = checkpoint(self, visual, *inputs, use_reentrant=False)
            else:
                deltas = self(visual, *inputs)
            deltas = tuple(d.to(visual.dtype) for d in deltas)
            with torch.no_grad():
                metrics['patch_delta_ratio'] = float(sum(d.float().square().mean().sqrt() for d in deltas) /
                                                    visual.float().square().mean().sqrt().clamp_min(1e-12))
            if self.settings['injection'] == 'pre_lm':
                merged = visual + deltas[0]
                if hasattr(output, 'pooler_output'):
                    output.pooler_output = merged
                    return output
                return (output[0], merged, *output[2:])
            return output
        def language_hook(module, args, kwargs):
            if deltas is None:
                raise ValueError('GF1 LM ran before the visual merger')
            mask = batch['input_ids'] == model.config.video_token_id
            embedded = kwargs.get('inputs_embeds')
            if embedded is not None and embedded.shape[:2] != mask.shape:
                # Native cached decode carries geometry in its prefix state already.
                return args, kwargs
            return args, {**kwargs, 'gf1_residuals': deltas, 'gf1_mask': mask}
        with ExitStack() as stack:
            handle = model.model.visual.register_forward_hook(visual_hook, with_kwargs=True)
            stack.callback(handle.remove)
            if self.settings['injection'] == 'lm_012':
                handle = model.model.language_model.register_forward_pre_hook(language_hook, with_kwargs=True)
                stack.callback(handle.remove)
            yield
            if pending:
                raise ValueError('GF1 video features were not consumed')


def install_decoder_hooks(model):
    """Permanent hooks use per-call kwargs retained by checkpoint recomputation."""
    layers = model.model.language_model.layers
    if len(layers) < 3:
        raise ValueError('GF1 lm_012 needs three LM layers')
    for index, layer in enumerate(layers):
        def hook(module, args, kwargs, index=index):
            kwargs = dict(kwargs)
            residuals = kwargs.pop('gf1_residuals', None)
            mask = kwargs.pop('gf1_mask', None)
            if residuals is None or index >= 3:
                return args, kwargs
            hidden = args[0] if args else kwargs['hidden_states']
            if hidden.shape[:2] != mask.shape:
                raise ValueError('GF1 decode mask shape differs')
            update = torch.zeros_like(hidden).masked_scatter(mask[..., None], residuals[index].to(hidden.dtype))
            if args:
                return (hidden + update, *args[1:]), kwargs
            return args, {**kwargs, 'hidden_states': hidden + update}
        layer.register_forward_pre_hook(hook, with_kwargs=True)


def configure_trainables(model):
    cfg = model.geometry_online['gf1']
    if cfg['stage'] == 1:
        model.requires_grad_(False)
        model.auxiliary_heads.gf1.requires_grad_(True)
    # GXC's loaded CAM path stays frozen in Stage 1 so GF1 is the only difference.
    model.auxiliary_heads.geometry_encoder.requires_grad_(False).eval()


def parameter_groups(model, recipe, inherited=(), pose_lr_scale=1., lm_lr_scale=1.):
    from .carrier_c1 import parameter_groups as legacy
    cfg = model.geometry_online['gf1']
    params = list(model.auxiliary_heads.gf1.parameters())
    ids = {id(p) for p in params}
    # Legacy grouping remains authoritative for the LM, own heads and camera path.
    groups = legacy(model, recipe, inherited, pose_lr_scale, lm_lr_scale, _gf1=False)
    for group in groups:
        group['params'] = [p for p in group['params'] if id(p) not in ids]
    lr = cfg['learning_rate'] if cfg['stage'] == 1 else recipe['lm_learning_rate'] * lm_lr_scale
    return [g for g in groups if g['params']] + [dict(params=params, name='gf1', lr=lr, initial_lr=lr)]


class ClipCache:
    """Row-owned frozen features shared by prefix readout and the supervised forward."""
    def __init__(self):self.key=None;self.value=None
    def to(self,device):return self
    def clear(self):self.key=None;self.value=None


def _version(tensor):
    try:return tensor._version
    except RuntimeError:return None


def geometry_features(model, batch):
    from .g3t_online import features
    encoder = model.auxiliary_heads.geometry_encoder
    required = ('aux_g3t_images', 'aux_g3t_coords', 'aux_gf1_lm_indices')
    if any(k not in batch for k in required):
        raise ValueError('GF1 requires dense RGB, valid ROI and explicit nested LM indices')
    images, coords, maps = (batch[k] for k in required)
    rows = batch['input_ids'].shape[0]
    if (images.ndim != 5 or images.shape[:2] != (rows, model.geometry_online['gf1']['dense_frames'])
            or coords.shape != (*images.shape[:2], 4) or len(maps) != rows
            or batch['video_grid_thw'].shape != (rows, 3)):
        raise ValueError('GF1 dense clip batch shape differs')
    cache = batch.setdefault('aux_gf1_cache', ClipCache())
    if not isinstance(cache, ClipCache):
        raise ValueError('GF1 cache must be owned by the encoded row')
    sources = batch.get('aux_camera_rope_sources')
    key = (_version(batch['pixel_values_videos']), id(encoder), _version(next(encoder.parameters())), str(images.device), _version(images),
           _version(coords), str(maps.dtype), str(maps.tolist()), str(batch['video_grid_thw'].tolist()),
           None if sources is None else str(sources.tolist()), model.gx_zero_feature)
    if cache.key == key and cache.value is not None:
        model.gx_metrics = dict(feature_finite=True, dense_frames=images.shape[1], tower_forwards=0, tower_cache_hit=True)
        return cache.value
    # Reuse the donor's exact student-unpatchify camera path under no_grad.
    with torch.no_grad():
        cameras = model.geometry_features(batch, _camera_only=True)
    clips = []
    for image, roi, mapping, grid in zip(images, coords, maps, batch['video_grid_thw']):
        if (mapping.dtype != torch.long or mapping.ndim != 1 or len(mapping) != int(grid[0])
                or int(mapping[0]) != 0 or len(mapping) != len(torch.unique(mapping)) or (mapping < 0).any()
                or (mapping >= len(image)).any() or not torch.all(mapping[1:] > mapping[:-1])):
            raise ValueError('GF1 LM frames must be an ordered nested subset of dense frames')
        device = next(encoder.parameters()).device
        shared = batch.get('aux_gf1_shared')
        if shared is not None:
            if rows != 1 or shared.encoder is not encoder or shared.layers != model.geometry_online['gf1']['layers']:
                raise ValueError('GF1 shared tower features have a different owner or layer bank')
            cam, bank = shared.cameras.to(device), shared.bank.to(device)
        else:
            with torch.no_grad():
                cam, bank = features(encoder, image.to(device), roi.to(device))
        mapping = mapping.to(device)
        bank = bank.index_select(1, mapping)
        patch_side = math.isqrt(bank.shape[2])
        if patch_side ** 2 != bank.shape[2]:
            raise ValueError('GF1 tower patch grid is not square')
        bank = bank.reshape(bank.shape[0], len(mapping), patch_side, patch_side, bank.shape[-1])
        clips.append((torch.zeros_like(bank) if model.gx_zero_feature else bank,
                      roi.to(device).index_select(0, mapping), grid))
    model.gx_metrics = dict(feature_finite=True, dense_frames=images.shape[1], tower_forwards=(rows if cameras is not None else 0) + (0 if batch.get('aux_gf1_shared') is not None else rows),
                            shared_head_tower=batch.get('aux_gf1_shared') is not None)
    cache.key, cache.value = key, (cameras, clips)
    return cache.value


def dense_inputs(row, cfg):
    """Require a supplied dense sample; never substitute duplicated sparse frames."""
    sparse = row['student_input']
    dense = sparse.get('geometry_dense')
    if not isinstance(dense, dict) or len(dense.get('frames', [])) != cfg['dense_frames']:
        raise ValueError('GF1 row needs student_input.geometry_dense with the configured dense frames')
    keys = dense.get('frame_indices', [])
    if len(keys) != len(set(keys)) or keys != sorted(keys) or len(keys) != cfg['dense_frames']:
        raise ValueError('GF1 dense frame IDs must be unique and ordered')
    indices = []
    for frame, key, timestamp in zip(sparse['frames'], sparse['frame_indices'], sparse['timestamps'], strict=True):
        if key not in keys:
            raise ValueError('GF1 LM frame is absent from the dense clip')
        slot = keys.index(key)
        if frame != dense['frames'][slot] or timestamp != dense['timestamps'][slot]:
            raise ValueError('GF1 nested RGB path or timestamp differs')
        indices.append(slot)
    if not indices or indices[0] != 0 or indices != sorted(set(indices)):
        raise ValueError('GF1 nested frame order differs')
    return dense, indices


def check_camera_context(model, artifact):
    """A nonzero inherited GXC path must keep its reconstruction context at step zero."""
    output = model.auxiliary_heads.pose.cam_token_connector.mlp[2]
    if not torch.count_nonzero(output.weight).item() and not torch.count_nonzero(output.bias).item():
        return
    donor = artifact.get('geometry_online') or {}
    live = model.geometry_online
    if any(donor.get(k) != live.get(k) for k in ('encoder', 'encoder_dtype', 'input', 'feature')):
        raise ValueError('GF1 would change the nonzero GXC camera context at step zero')



class SharedHeadFeatures:
    """Normal no-grad tensors, safe to save for connector backward after inference."""
    def __init__(self, encoder, layers, cameras, bank):
        self._encoder=weakref.ref(encoder)
        self.layers,self.cameras,self.bank=list(layers),cameras,bank
    @property
    def encoder(self):return self._encoder()
    def to(self,device):
        self.cameras=self.cameras.to(device);self.bank=self.bank.to(device)
        return self


def share_head_tower(model, tower):
    """Validate sharing without replacing the routed tower's FP32 modules."""
    from . import tower_read as T
    geometry=model.geometry_online;encoder=model.auxiliary_heads.geometry_encoder
    if (geometry['encoder']['weights']['sha256'] != T.WEIGHTS_SHA256
            or geometry['encoder']['config']['sha256'] != T.CONFIG_SHA256
            or geometry['encoder']['source_sha256'] != T.SOURCE_SHA256):
        raise ValueError('GF1 and routed head tower pins differ')
    if tower.dense_frames != geometry['gf1']['dense_frames'] or tower.device != next(encoder.parameters()).device:
        raise ValueError('GF1 and routed head tower device or dense frame count differs')
    # The routed tower owns its precision. Only its detached bank is shared.


def bind_head_features(model,batch,blocks,start,inputs,coords,slots,local,global_):
    """Publish the head tower's one reconstruction to the visual-token connector."""
    from .g3t_online import pose9, disagreement
    layers=model.geometry_online['gf1']['layers'];encoder=model.auxiliary_heads.geometry_encoder
    # tower_read uses inference_mode; clone into ordinary tensors before an LM
    # connector can save these constants for its backward pass.
    with torch.inference_mode(False), torch.no_grad():
        bank=torch.stack([blocks[i][0,:,start:] for i in layers]).clone()
        cam=blocks[23][0,:,0].float().clone()
        local=torch.as_tensor(local,device=cam.device).clone()
        global_=torch.as_tensor(global_,device=cam.device).clone()
        roi=torch.as_tensor(coords,device=cam.device).clone()
        pose,_=pose9(local,global_,roi)
        cameras=torch.cat([cam,pose.float(),disagreement(local).float()],-1)
        batch.update(aux_g3t_images=inputs.clone()[None],aux_g3t_coords=roi[None],
                     aux_gf1_lm_indices=torch.as_tensor(slots,device=cam.device,dtype=torch.long).clone()[None],
                     aux_gf1_cache=ClipCache(),
                     aux_gf1_shared=SharedHeadFeatures(encoder,layers,cameras,bank))


def harm_guard(ratio, loss0=None, loss1=None, *, device='cpu', distributed=False):
    """Agree on harm before any rank enters backward or another update."""
    bad_ratio = not math.isfinite(ratio) or ratio > .5
    bad_loss = loss0 is not None and (not math.isfinite(loss0) or not math.isfinite(loss1) or loss1 > 1.02 * loss0)
    flags = torch.tensor([bad_ratio, bad_loss], dtype=torch.int32, device=device)
    if distributed:
        import torch.distributed as dist
        dist.all_reduce(flags, op=dist.ReduceOp.MAX)
    if flags[0].item():
        raise ValueError('GF1 harm stop: patch_delta_ratio exceeds 0.5 or is nonfinite')
    if flags[1].item():
        raise ValueError('GF1 harm stop: step-1 loss exceeds 1.02 times step-0 loss or is nonfinite')


def screen_loss(model, batch, targets, stream):
    """Evaluate the same encoded row before and after the first update."""
    modes = [(module, module.training) for module in model.modules()]
    try:
        model.eval()
        with torch.no_grad():
            result = model(batch, targets, stream=stream)
        return float(result['loss']), result.get('metrics', {}).get('gx', {}).get('patch_delta_ratio', 0.)
    finally:
        for module, training in modes:
            module.training = training
