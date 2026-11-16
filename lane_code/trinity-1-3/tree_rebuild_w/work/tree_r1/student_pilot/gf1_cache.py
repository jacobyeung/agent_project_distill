"""GF-1 cached tower bank and shuffled-bank reads.

The connector computes area_pool(proj(norm(x))) per layer. Area weights are non-negative and sum to one
over every merger cell of an ROI inside the 1024 raster, and LayerNorm's affine part and the projection are
token-shared affine maps, so pool(W(g*n_hat+b)+c) = W(g*pool(n_hat)+b)+c with n_hat the per-token
normalised feature without learned parameters. A cache of pool(n_hat) per layer, LM anchor frame and merger
cell therefore keeps every connector parameter live. Rows without a cache (pose rows, whose dense frames are
augmented per row) run the tower online. A cache whose identity differs refuses; it never falls back.
"""
import argparse
import copy
import hashlib
import inspect
import json
import math
from pathlib import Path

import torch
from torch.nn import functional as F

SCHEMA = 'gf1-pooled-nhat-v1'
DONOR_SCHEMA = 'gf1-bank-donor-v1'
PLAN_SCHEMA = 'gf1-shuffled-bank-v1'
TENSOR_KEY = 'pool'
DTYPES = {'float32': torch.float32, 'bfloat16': torch.bfloat16}


def clip_key(dense):
    """Content key of a dense clip: digest of its (source ordinal, sha256) pairs, as r2_dense builds it."""
    from .p3_provenance import digest
    frames, ordinals = dense['frames'], dense['frame_indices']
    if len(frames) != len(ordinals) or any(not isinstance(f, dict) or not f.get('sha256') for f in frames):
        raise ValueError('GF1 cache key needs sha256-pinned dense frames')
    return digest([(i, f['sha256']) for i, f in zip(ordinals, frames)])


def pooled_nhat(bank, coords, grid, eps, chunk=8):
    """bank [layers, anchors, patches, channels] -> FP32 [layers, anchors, merger cells, channels]."""
    from .gf1 import area_pool
    layers, frames, patches, channels = bank.shape
    side = math.isqrt(patches)
    t, h, w = map(int, grid)
    if side * side != patches or frames != t or coords.shape != (t, 4):
        raise ValueError('GF1 cache bank, ROI and grid disagree')
    out = torch.empty(layers, t, (h // 2) * (w // 2), channels, dtype=torch.float32, device=bank.device)
    with torch.autocast(bank.device.type, enabled=False):
        for layer in range(layers):
            for start in range(0, t, chunk):
                stop = min(t, start + chunk)
                block = bank[layer, start:stop].float().reshape(stop - start, side, side, channels)
                normed = F.layer_norm(block, (channels,), eps=eps)
                out[layer, start:stop] = area_pool(normed, coords[start:stop], (stop - start, h, w)).reshape(
                    stop - start, -1, channels)
    return out


def code_version():
    from . import gf1
    parts = [SCHEMA, inspect.getsource(gf1.area_pool), inspect.getsource(pooled_nhat),
             inspect.getsource(gf1.Fusion.cached_bank)]
    return hashlib.sha256('\0'.join(parts).encode()).hexdigest()


def bank_dtype(geometry_online, device_type):
    """The dtype of the tower's layer bank: G3TEncoder autocasts on CUDA or with BF16 storage."""
    return 'bfloat16' if device_type == 'cuda' or geometry_online.get('encoder_dtype') == 'bf16' else 'float32'


def identity(geometry_online, *, device_type, eps, input_dim, compute_dtype, grid, dtype):
    """Fields a cache must share with the consuming model; the clip key and anchors are checked per row."""
    enc = geometry_online['encoder']
    gf1 = geometry_online['gf1']
    return dict(schema=SCHEMA, code_version=code_version(), layers=list(gf1['layers']),
                dense_frames=gf1['dense_frames'],
                tower=dict(weights_sha256=enc['weights']['sha256'], config_sha256=enc['config']['sha256'],
                           source_sha256=enc['source_sha256'], input=geometry_online['input'],
                           encoder_dtype=geometry_online.get('encoder_dtype', 'fp32')),
                bank_dtype=bank_dtype(geometry_online, device_type),
                norm=dict(kind='layer_norm_without_affine', eps=float(eps), input_dim=int(input_dim),
                          compute_dtype=compute_dtype),
                pool='gf1_area_pool_roi_1024_merge2', merger_grid=[int(v) for v in grid], dtype=dtype,
                augment='none')


def model_identity(model, grid, device_type):
    fusion = model.auxiliary_heads.gf1
    eps = {float(n.eps) for n in fusion.norms}
    dims = {int(n.normalized_shape[0]) for n in fusion.norms}
    dtypes = {str(p.weight.dtype).removeprefix('torch.') for p in fusion.projections}
    if len(eps) != 1 or len(dims) != 1 or len(dtypes) != 1:
        raise ValueError('GF1 cached bank needs one LayerNorm eps, width and projection dtype')
    return identity(model.geometry_online, device_type=device_type, eps=eps.pop(), input_dim=dims.pop(),
                    compute_dtype=dtypes.pop(), grid=grid, dtype=model.geometry_online['gf1']['cached_bank']['dtype'])


def _sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 22), b''):
            h.update(block)
    return h.hexdigest()


def write_clip(encoder, row, root, *, grid, dtype, eps=1e-5, compute_dtype='float32'):
    """Run the frozen tower once on a dense clip and write pool(n_hat) at its LM anchors.

    One file per clip, named by the clip content key, plus a JSON identity record (the commit marker)
    holding the tensor's sha256. Rewriting an existing clip must reproduce it byte for byte.
    """
    from safetensors.torch import save
    from .g3t_online import features, native_square_518
    from .gf1 import dense_inputs
    from .pose_samples import load_frames
    settings = encoder.settings
    cfg = settings['gf1']
    if dtype not in DTYPES:
        raise ValueError('GF1 cache dtype must be float32 or bfloat16')
    dense, anchors = dense_inputs(row, cfg)
    key = clip_key(dense)
    if len(anchors) != int(grid[0]):
        raise ValueError('GF1 cache anchors must equal the temporal merger grid')
    device = next(encoder.parameters()).device
    images, coords = native_square_518(load_frames(dense), expected_frames=cfg['dense_frames'])
    mapping = torch.tensor(anchors, dtype=torch.long, device=device)
    with torch.no_grad():
        _, bank = features(encoder, images.to(device), coords.to(device))
        bank = bank.index_select(1, mapping)
        roi = coords.to(device).index_select(0, mapping)
        pooled = pooled_nhat(bank, roi, grid, eps)
        del bank
    pooled = pooled.to(DTYPES[dtype]).cpu().contiguous()
    payload = save({TENSOR_KEY: pooled})
    record = identity(settings, device_type=device.type, eps=eps, input_dim=pooled.shape[-1],
                      compute_dtype=compute_dtype, grid=grid, dtype=dtype)
    record.update(clip_key=key, anchor_slots=list(anchors), dense_frame_indices=list(dense['frame_indices']),
                  roi_1024=roi.cpu().tolist(), shape=list(pooled.shape),
                  tensor=dict(file=key + '.safetensors', sha256=hashlib.sha256(payload).hexdigest(),
                              bytes=len(payload)))
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    tensor_path, record_path = root / record['tensor']['file'], root / (key + '.json')
    if record_path.exists():
        if json.loads(record_path.read_text()) != record or _sha256(tensor_path) != record['tensor']['sha256']:
            raise ValueError('GF1 cache rewrite differs from the stored clip: ' + key)
        return record
    if tensor_path.exists():
        raise ValueError('GF1 cache tensor exists without its identity record: ' + str(tensor_path))
    with open(tensor_path, 'xb') as f:
        f.write(payload)
    with open(record_path, 'x') as f:
        json.dump(record, f, indent=1, sort_keys=True)
        f.write('\n')
    return record


class RowBank:
    """One row's GF-1 bank source: a cached pool(n_hat) tensor, or dense frames for an online tower pass."""
    def __init__(self, kind, mapping, record=None, tensor=None, images=None, coords=None, donor=None):
        if kind not in ('cached', 'dense'):
            raise ValueError('Unknown GF1 row bank kind')
        self.kind, self.mapping, self.record, self.tensor = kind, mapping, record, tensor
        self.images, self.coords, self.donor = images, coords, donor

    def to(self, device):
        for name in ('mapping', 'tensor', 'images', 'coords'):
            value = getattr(self, name)
            if value is not None:
                setattr(self, name, value.to(device))
        return self

    def key(self):
        source = self.record['tensor']['sha256'] if self.kind == 'cached' else id(self.images)
        return (self.kind, source, None if self.donor is None else self.donor['clip_key'])


class RowBanks:
    """Per-row entries (None means: run the tower online on aux_g3t_images for that row)."""
    def __init__(self, entries):
        self.entries = list(entries)

    def to(self, device):
        for entry in self.entries:
            if entry is not None:
                entry.to(device)
        return self

    def key(self):
        return tuple(None if e is None else e.key() for e in self.entries)


def load_cached(settings, key, anchors):
    """Return the clip's cached entry, None when the clip has no record, and refuse any mismatch."""
    from safetensors.torch import load
    root = Path(settings['root'])
    if not root.is_dir():
        raise ValueError('GF1 cached_bank root is missing: ' + str(root))
    record_path = root / (key + '.json')
    if not record_path.exists():
        return None
    record = json.loads(record_path.read_text())
    if (record.get('schema') != SCHEMA or record.get('clip_key') != key or record.get('anchor_slots') != list(anchors)
            or record.get('dtype') != settings['dtype'] or record.get('augment') != 'none'
            or record.get('tensor', {}).get('file') != key + '.safetensors'):
        raise ValueError('GF1 cached bank identity differs from the row: ' + key)
    payload = (root / record['tensor']['file']).read_bytes()
    if hashlib.sha256(payload).hexdigest() != record['tensor']['sha256']:
        raise ValueError('GF1 cached bank tensor sha256 differs: ' + key)
    tensor = load(payload)[TENSOR_KEY]
    if tensor.dtype != DTYPES[settings['dtype']] or list(tensor.shape) != record['shape']:
        raise ValueError('GF1 cached bank tensor dtype or shape differs: ' + key)
    return RowBank('cached', torch.tensor(list(anchors), dtype=torch.long), record=record, tensor=tensor)


def _check_anchors(anchors, n):
    if (not isinstance(anchors, list) or not anchors or anchors[0] != 0 or anchors != sorted(set(anchors))
            or any(type(a) is not int for a in anchors) or anchors[-1] >= n):
        raise ValueError('GF1 bank donor anchors must be ordered dense slots starting at 0')


def row_bank(row, cfg, dense, indices, is_pose):
    """Encoder side: (geometry, LM arrays) for a cached or donor row, or None for the online path; plus audit."""
    from .g3t_online import native_square_518
    from .gf1 import ClipCache
    from .pose_samples import load_frames
    inputs = row['student_input']
    own = clip_key(dense)
    donor = inputs.get('geometry_bank_donor')
    settings = cfg.get('cached_bank')
    lm = lambda: load_frames(dict(frames=[dense['frames'][i] for i in indices]))
    if donor is not None:
        if is_pose:
            raise ValueError('GF1 shuffled bank is a read option; pose rows keep their own augmented clip')
        if (not isinstance(donor, dict) or donor.get('schema') != DONOR_SCHEMA
                or set(donor) != {'schema', 'clip_key', 'geometry_dense', 'anchor_slots', 'permutation_sha256'}):
            raise ValueError('Invalid GF1 bank donor')
        other, anchors = donor['geometry_dense'], donor['anchor_slots']
        if len(other.get('frames', [])) != cfg['dense_frames'] or other.get('frame_indices') != sorted(set(other['frame_indices'])):
            raise ValueError('GF1 bank donor needs the configured ordered dense frames')
        _check_anchors(anchors, cfg['dense_frames'])
        if len(anchors) != len(indices):
            raise ValueError('GF1 bank donor anchor count differs from the row')
        key = clip_key(other)
        if key != donor['clip_key'] or key == own:
            raise ValueError('GF1 bank donor key differs from its frames or names the row\'s own clip')
        entry = load_cached(settings, key, anchors) if settings else None
        if entry is None:
            images, coords = native_square_518(load_frames(other), expected_frames=cfg['dense_frames'])
            entry = RowBank('dense', torch.tensor(anchors, dtype=torch.long), images=images, coords=coords)
        entry.donor = dict(clip_key=key, own_clip_key=own, permutation_sha256=donor['permutation_sha256'])
        geometry = dict(aux_gf1_cache=ClipCache(), aux_gf1_lm_indices=torch.tensor([indices], dtype=torch.long),
                        aux_gf1_rowbanks=RowBanks([entry]))
        return (geometry, lm()), dict(source='shuffled_' + entry.kind, clip_key=own, donor_clip_key=key,
                                      permutation_sha256=donor['permutation_sha256'])
    if is_pose:
        return None, dict(source='online', reason='pose_row_augmented', clip_key=own)
    entry = load_cached(settings, own, indices)
    if entry is None:
        raise ValueError('GF1 cached_bank has no record for clip ' + own + '; write the cache for every non-pose clip first')
    geometry = dict(aux_gf1_cache=ClipCache(), aux_gf1_lm_indices=torch.tensor([indices], dtype=torch.long),
                    aux_gf1_rowbanks=RowBanks([entry]))
    return (geometry, lm()), dict(source='cached', clip_key=own, tensor_sha256=entry.record['tensor']['sha256'])


def _valid_mapping(mapping, grid, n):
    return (mapping.dtype == torch.long and mapping.ndim == 1 and len(mapping) == int(grid[0])
            and int(mapping[0]) == 0 and len(mapping) == len(torch.unique(mapping)) and not (mapping < 0).any()
            and not (mapping >= n).any() and bool(torch.all(mapping[1:] > mapping[:-1])))


def rowbank_features(model, batch):
    """Model side of gf1.geometry_features when a batch carries per-row bank entries."""
    import math as _math
    from .g3t_online import features
    from .gf1 import ClipCache, CACHED_MARK, _version
    encoder = model.auxiliary_heads.geometry_encoder
    cfg = model.geometry_online['gf1']
    banks = batch['aux_gf1_rowbanks']
    rows = batch['input_ids'].shape[0]
    n = cfg['dense_frames']
    if not isinstance(banks, RowBanks) or len(banks.entries) != rows:
        raise ValueError('GF1 row banks must name one entry per row')
    online = [i for i, e in enumerate(banks.entries) if e is None]
    maps, grids = batch.get('aux_gf1_lm_indices'), batch['video_grid_thw']
    if maps is None or len(maps) != rows or grids.shape != (rows, 3):
        raise ValueError('GF1 dense clip batch shape differs')
    images = coords = None
    if online:
        if 'aux_g3t_images' not in batch or 'aux_g3t_coords' not in batch:
            raise ValueError('GF1 requires dense RGB, valid ROI and explicit nested LM indices')
        images, coords = batch['aux_g3t_images'], batch['aux_g3t_coords']
        if images.ndim != 5 or images.shape[:2] != (rows, n) or coords.shape != (*images.shape[:2], 4):
            raise ValueError('GF1 dense clip batch shape differs')
    device = next(encoder.parameters()).device
    for entry in banks.entries:
        if entry is None:
            continue
        if entry.donor is not None and model.training:
            raise ValueError('GF1 shuffled-bank donors are a read-time option only')
        if entry.kind == 'cached' and 'cached_bank' not in cfg:
            raise ValueError('GF1 cached bank supplied while the cached_bank switch is off')
    cache = batch.setdefault('aux_gf1_cache', ClipCache())
    if not isinstance(cache, ClipCache):
        raise ValueError('GF1 cache must be owned by the encoded row')
    sources = batch.get('aux_camera_rope_sources')
    key = ('rowbanks', banks.key(), _version(batch['pixel_values_videos']), id(encoder),
           _version(next(encoder.parameters())), str(device), None if images is None else _version(images),
           None if coords is None else _version(coords), str(maps.tolist()), str(grids.tolist()),
           None if sources is None else str(sources.tolist()), model.gx_zero_feature)
    if cache.key == key and cache.value is not None:
        model.gx_metrics = dict(feature_finite=True, dense_frames=n, tower_forwards=0, tower_cache_hit=True)
        return cache.value
    shared = batch.get('aux_gf1_shared')
    clips, forwards, cached, donors = [], 0, 0, 0
    for r, (entry, mapping, grid) in enumerate(zip(banks.entries, maps, grids)):
        mapping = mapping.to(device)
        if not _valid_mapping(mapping, grid, n):
            raise ValueError('GF1 LM frames must be an ordered nested subset of dense frames')
        if entry is None or entry.kind == 'dense':
            if entry is None and shared is not None:
                if rows != 1 or shared.encoder is not encoder or shared.layers != cfg['layers']:
                    raise ValueError('GF1 shared tower features have a different owner or layer bank')
                bank, roi, slots = shared.bank.to(device), coords[r].to(device), mapping
            else:
                image, roi = (images[r], coords[r]) if entry is None else (entry.images, entry.coords)
                slots = mapping if entry is None else entry.mapping.to(device)
                if image.shape[0] != n or not _valid_mapping(slots, grid, n):
                    raise ValueError('GF1 bank donor frames or anchors differ from the configured dense clip')
                with torch.no_grad():
                    _, bank = features(encoder, image.to(device), roi.to(device))
                forwards += 1
            donors += entry is not None
            bank = bank.index_select(1, slots)
            side = _math.isqrt(bank.shape[2])
            if side ** 2 != bank.shape[2]:
                raise ValueError('GF1 tower patch grid is not square')
            bank = bank.reshape(bank.shape[0], len(slots), side, side, bank.shape[-1])
            clips.append((torch.zeros_like(bank) if model.gx_zero_feature else bank,
                          roi.to(device).index_select(0, slots), grid))
            continue
        record = entry.record
        expected = model_identity(model, grid.tolist(), device.type)
        for field, value in expected.items():
            if record.get(field) != value:
                raise ValueError(f'GF1 cached bank identity differs in {field}: refusing the cache')
        if entry.donor is None and record['anchor_slots'] != mapping.tolist():
            raise ValueError('GF1 cached bank anchors differ from the row\'s nested LM indices')
        if record['anchor_slots'] != entry.mapping.tolist():
            raise ValueError('GF1 cached bank anchors differ from its entry')
        pooled = entry.tensor.to(device)
        pooled = pooled.reshape(pooled.shape[0], -1, pooled.shape[-1])
        clips.append((torch.zeros_like(pooled) if model.gx_zero_feature else pooled, CACHED_MARK, grid))
        cached += 1
        donors += entry.donor is not None
    model.gx_metrics = dict(feature_finite=True, dense_frames=n, tower_forwards=forwards, cached_rows=cached,
                            donor_rows=donors, shared_head_tower=shared is not None)
    cache.key, cache.value = key, (None, clips)
    return cache.value


# Shuffled-bank read: the no-information baseline for geometry use.

def _order(keys, seed, tag):
    return sorted(keys, key=lambda k: hashlib.sha256(f'{seed}|{tag}|{k}'.encode()).hexdigest())


def shuffled_bank_plan(units, seed, require_same_grid=False):
    """Fixed derangement over clips. units: [{clip_key, dataset, grid}]. Pairs prefer the same dataset and
    grid; leftovers relax the dataset first when grids must match (cached reads), else the grid first."""
    if type(seed) is not int:
        raise ValueError('Shuffled-bank seed must be an integer')
    info = {}
    for unit in units:
        key, value = unit['clip_key'], (unit['dataset'], tuple(int(v) for v in unit['grid']))
        if info.setdefault(key, value) != value:
            raise ValueError('One clip has two datasets or grids')
    if len(info) < 2:
        raise ValueError('A shuffled-bank read needs at least two clips')
    donor = {}
    def cycles(groups, tag):
        left = []
        for name in sorted(groups):
            members = groups[name]
            if len(members) < 2:
                left += members
                continue
            order = _order(members, seed, f'{tag}|{name}')
            donor.update({order[i]: order[(i + 1) % len(order)] for i in range(len(order))})
        return left
    def group(keys, by):
        groups = {}
        for k in keys:
            groups.setdefault(repr(by(k)), []).append(k)
        return groups
    left = cycles(group(sorted(info), lambda k: info[k]), 'dataset_grid')
    second = (lambda k: info[k][1]) if require_same_grid else (lambda k: info[k][0])
    left = cycles(group(left, second), 'grid' if require_same_grid else 'dataset')
    if not require_same_grid:
        left = cycles({'all': left} if left else {}, 'all')
    for k in _order(left, seed, 'insert'):
        candidates = [a for a in sorted(donor) if not require_same_grid or
                      info[a][1] == info[k][1] == info[donor[a]][1]]
        if not candidates:
            raise ValueError('No shuffled-bank partner shares this clip\'s merger grid: ' + k)
        a = min(candidates, key=lambda a: (info[a][0] != info[k][0], info[a][1] != info[k][1], a))
        donor[k], donor[a] = donor[a], k
    if set(donor) != set(info) or any(k == v for k, v in donor.items()) or sorted(donor.values()) != sorted(info):
        raise AssertionError('Shuffled-bank plan is not a derangement')
    pairs = [dict(clip_key=k, donor_clip_key=v, dataset=info[k][0], donor_dataset=info[v][0],
                  grid=list(info[k][1]), donor_grid=list(info[v][1])) for k, v in sorted(donor.items())]
    permutation = hashlib.sha256(json.dumps([[p['clip_key'], p['donor_clip_key']] for p in pairs]).encode()).hexdigest()
    counts = dict(clips=len(pairs), same_dataset_same_grid=0, same_dataset_other_grid=0,
                  other_dataset_same_grid=0, other_dataset_other_grid=0)
    for p in pairs:
        same_dataset, same_grid = p['dataset'] == p['donor_dataset'], p['grid'] == p['donor_grid']
        counts[('same' if same_dataset else 'other') + '_dataset_' + ('same' if same_grid else 'other') + '_grid'] += 1
    return dict(schema=PLAN_SCHEMA, seed=seed, require_same_grid=require_same_grid, counts=counts,
                permutation_sha256=permutation, pairs=pairs)


def frame_grid(row):
    """Video grid [32, H, W] of a row's LM frames under the trainer's pixel budget (header read only)."""
    from PIL import Image
    from .grounding_targets import grid_for
    from .r2_frames import verify_frame
    with Image.open(verify_frame(row['student_input']['frames'][0])) as image:
        gh, gw = grid_for(image.size)
    return [len(row['student_input']['frames']), 2 * gh, 2 * gw]


def _dataset(row):
    value = row.get('dataset') or row['student_input'].get('dataset') or str(row.get('scene', '')).split('/')[0]
    if not value:
        raise ValueError('Shuffled-bank pairing needs each row\'s dataset')
    return value


def shuffle_rows(rows, settings, seed, grids=None, require_same_grid=False):
    """Attach a donor clip's dense frames to every row; returns (rows, plan). grids: clip_key -> video grid."""
    from .gf1 import dense_inputs
    dense_of, anchors_of, units = {}, {}, []
    keyed = []
    for row in rows:
        dense, anchors = dense_inputs(row, settings)
        key = clip_key(dense)
        content = (list(dense['frame_indices']), [f['sha256'] for f in dense['frames']], dense.get('timestamps'))
        first = dense_of.setdefault(key, dense)
        if (anchors_of.setdefault(key, anchors) != anchors
                or (list(first['frame_indices']), [f['sha256'] for f in first['frames']], first.get('timestamps')) != content):
            raise ValueError('Rows of one dense clip disagree on its frames, timestamps or LM anchors')
        grid = grids[key] if grids is not None else frame_grid(row)
        units.append(dict(clip_key=key, dataset=_dataset(row), grid=grid))
        keyed.append(key)
    plan = shuffled_bank_plan(units, seed, require_same_grid)
    donors = {p['clip_key']: p['donor_clip_key'] for p in plan['pairs']}
    result = []
    for row, key in zip(rows, keyed):
        row = copy.deepcopy(row)
        other = donors[key]
        row['student_input']['geometry_bank_donor'] = dict(
            schema=DONOR_SCHEMA, clip_key=other, geometry_dense=copy.deepcopy(dense_of[other]),
            anchor_slots=list(anchors_of[other]), permutation_sha256=plan['permutation_sha256'])
        result.append(row)
    return result, plan


def main():
    """Write the cache for every distinct clip of a rows JSONL (non-pose rows only)."""
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('--run-config', required=True, help='C1 run config JSON with geometry_online.gf1')
    parser.add_argument('--rows', required=True)
    parser.add_argument('--root', required=True)
    parser.add_argument('--dtype', choices=sorted(DTYPES), required=True)
    parser.add_argument('--device', default='cuda:0')
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    from . import g3t_online
    from .gf1 import dense_inputs
    from .pose_samples import CATEGORY
    geometry = g3t_online.normalize(json.loads(Path(args.run_config).read_text())['geometry_online'])
    if 'gf1' not in geometry:
        raise ValueError('The run config has no GF1 block')
    import os
    os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
    # Deterministic kernels where available; write_clip refuses a rewrite that differs byte for byte.
    torch.use_deterministic_algorithms(True, warn_only=True)
    encoder = g3t_online.G3TEncoder(geometry)
    encoder.load_pinned(geometry['encoder']['weights']['path'])
    encoder.to(args.device).eval()
    seen, written = set(), []
    with open(args.rows) as handle:
        for line in handle:
            row = json.loads(line)
            if row.get('category') == CATEGORY and 'pose_sample' in row:
                continue
            dense, _ = dense_inputs(row, geometry['gf1'])
            key = clip_key(dense)
            if key in seen:
                continue
            seen.add(key)
            record = write_clip(encoder, row, args.root, grid=frame_grid(row), dtype=args.dtype)
            written.append(dict(clip_key=key, sha256=record['tensor']['sha256'], bytes=record['tensor']['bytes']))
            print(json.dumps(written[-1]), flush=True)
            if args.limit and len(written) >= args.limit:
                break
    print(json.dumps(dict(clips=len(written), bytes=sum(w['bytes'] for w in written))))


if __name__ == '__main__':
    main()
