"""Standalone, content-pinned T0 inference without the training data closure."""
import argparse
import hashlib
from pathlib import Path
import resource
import shutil
import time

import torch

from .p3_provenance import load, pinned, sha256, write

SCHEMA = 'mdg-t0-bundle-v1'
SMALL_LIMIT = 64 * 1024 * 1024


def _local(root, name):
    path = Path(name)
    if path.is_absolute() or '..' in path.parts or str(path) != name:
        raise ValueError('Bundle requires canonical relative paths')
    target = (root / path).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError('Bundle file escapes its root')
    return target


def _check(path, expected):
    if sha256(path) != expected:
        raise ValueError('SHA256 differs: ' + str(path))
    return path


def _native(native, receipt, manifest):
    if (native.get('frame_layout') != 'duplicate' or not native.get('frame_markers')
            or native.get('training_mode') != 'final' or not native.get('depth_enabled', True)
            or native.get('carrier_placement') != 'append_after_temporal_group_video_tokens_v1'):
        raise ValueError('MDG requires final C1_A, duplicate frames, markers and private depth')
    if receipt.get('schema') != 'c1-preparation-v1' or manifest.get('base_identity') != native['base_identity']:
        raise ValueError('Preparation/base identity differs')
    for key, default in (('training_mode', 'mixed'), ('depth_enabled', True),
                         ('frame_layout', 'spread'), ('skip_unsupervised_lm', None),
                         ('depth_fov_source', None), ('depth_init', None)):
        if receipt.get(key, default) != native.get(key, default):
            raise ValueError('Preparation/config differs: ' + key)
    if receipt.get('trace_program_version') != native.get('trace_program_version'):
        raise ValueError('Preparation/config differs: trace_program_version')
    if receipt.get('mdg') != native.get('mdg'):
        raise ValueError('Preparation/config differs: mdg')
    if {k: v['receipt'] for k, v in receipt.get('streams', {}).items()} != native.get('streams', {}):
        raise ValueError('Preparation/config stream identities differ')
    # Match prepared()'s final-mode overrides without opening its AWS data closure.
    return {**receipt, 'recipe': native['recipe'], 'carrier_placement': native['carrier_placement'],
            'align': native.get('align'), 'init_artifact': native.get('init_artifact'),
            'frame_markers': native.get('frame_markers', False),
            'camera': {**receipt['camera'], **native.get('camera_overrides', {})}}


def _artifact(value, native):
    from . import carrier_c1_run as c1
    if (value.get('schema') != 'carrier-c1-artifact-v1' or value.get('pose_backing') != 'lm_final_norm'
            or value.get('placement') != native['carrier_placement'] or value.get('training_mode') != 'final'
            or value.get('frame_layout', 'spread') != 'duplicate'
            or value.get('carrier_position_policy', 'native_v1') != 'native_v1'
            or value.get('depth_backing') != 'private_vit'):
        raise ValueError('Artifact placement/training mode/position policy/depth differs')
    if ('mdg' in value) != ('mdg' in native):
        raise ValueError('Artifact/config MDG architecture differs')
    if value.get('base_identity') != native['base_identity'] or value.get('config_sha256') != c1.identity(native):
        raise ValueError('MDG base artifact/config identity differs')


def _export_files(artifact_dir, artifact):
    from . import full_ft
    paths = {'artifact/artifact.json': sha256(artifact_dir / 'artifact.json')}
    for key, name in (('heads', 'heads.pt'), ('full_weights', 'full_weights/full_weights.json')):
        paths['artifact/' + name] = artifact[key]['sha256']
        _check(_local(artifact_dir, name), artifact[key]['sha256'])
    weights = load(artifact_dir / 'full_weights/full_weights.json')
    if weights.get('schema') != full_ft.EXPORT_SCHEMA or weights.get('dtype') != 'bfloat16':
        raise ValueError('Unsupported full-weights export')
    for item in [weights['index'], *weights['files']]:
        name = item['name']
        if Path(name).name != name:
            raise ValueError('Export requires flat file names')
        paths['artifact/full_weights/' + name] = item['sha256']
    return paths


def make_bundle(out, *, config, receipt, model_manifest, base_dir, artifact_dir):
    out, base_dir, artifact_dir = Path(out), Path(base_dir), Path(artifact_dir).resolve()
    native, raw, manifest = load(config), load(receipt), load(model_manifest)
    _check(receipt, native['preparation']['sha256'])
    _check(model_manifest, raw['model']['sha256'])
    _native(native, raw, manifest)
    _artifact(load(artifact_dir / 'artifact.json'), native)
    sources = {'config.json': Path(config), 'receipt.json': Path(receipt), 'model.json': Path(model_manifest)}
    for name, expected in manifest['files'].items():
        if Path(name).name != name:
            raise ValueError('Base manifest requires flat file names')
        if name.endswith('.safetensors') or name.endswith('.bin'):
            continue
        sources['base/' + name] = _check(_local(base_dir, name), expected)
    files = _export_files(artifact_dir, load(artifact_dir / 'artifact.json'))
    for name, source in sources.items():
        if source.stat().st_size > SMALL_LIMIT:
            raise ValueError('Bundle copies only small files')
        files[name] = sha256(source)
    for name, expected in files.items():
        if name.startswith('artifact/'):
            _check(_local(artifact_dir, name.removeprefix('artifact/')), expected)
    out.mkdir(parents=True, exist_ok=False)
    for name, source in sources.items():
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with source.open('rb') as src, target.open('xb') as dst:
            shutil.copyfileobj(src, dst)
        _check(target, files[name])
    write(out / 'BUNDLE.json', dict(schema=SCHEMA, artifact_dir=str(artifact_dir), files=files))
    return out / 'BUNDLE.json'


def _bundle(value):
    path = pinned(value) if isinstance(value, dict) else Path(value)
    path = path / 'BUNDLE.json' if path.is_dir() else path
    bundle_sha = sha256(path)
    bundle = load(path)
    root = path.resolve().parent
    artifact_dir = Path(bundle['artifact_dir'])
    if bundle.get('schema') != SCHEMA or not artifact_dir.is_absolute():
        raise ValueError('Unsupported MDG bundle')
    files = bundle['files']
    for name, expected in files.items():
        target = (_local(artifact_dir, name.removeprefix('artifact/')) if name.startswith('artifact/')
                  else _local(root, name))
        _check(target, expected)
    native, raw, manifest = (load(root / name) for name in ('config.json', 'receipt.json', 'model.json'))
    _check(root / 'receipt.json', native['preparation']['sha256'])
    _check(root / 'model.json', raw['model']['sha256'])
    receipt = _native(native, raw, manifest)
    artifact = load(artifact_dir / 'artifact.json')
    _artifact(artifact, native)
    required = {'config.json', 'receipt.json', 'model.json'} | set(_export_files(artifact_dir, artifact))
    required.update('base/' + name for name in manifest['files']
                    if not name.endswith(('.safetensors', '.bin')))
    if set(files) != required:
        raise ValueError('Bundle file coverage differs')
    for name, expected in manifest['files'].items():
        if 'base/' + name in files and files['base/' + name] != expected:
            raise ValueError('Bundle base manifest pin differs')
    return root, artifact_dir, native, receipt, manifest, artifact, bundle_sha


def _empty_base(base_dir):
    from transformers import Qwen3_5Config, Qwen3_5ForConditionalGeneration
    from transformers.initialization import no_init_weights
    config = Qwen3_5Config.from_pretrained(base_dir, local_files_only=True)
    for item in (config, config.text_config, config.vision_config):
        item._attn_implementation = 'sdpa'
    config.dtype = config.text_config.dtype = config.vision_config.dtype = torch.bfloat16
    previous = torch.get_default_dtype()
    try:
        torch.set_default_dtype(torch.bfloat16)
        with no_init_weights(), torch.device('cpu'):
            return Qwen3_5ForConditionalGeneration(config)
    finally:
        torch.set_default_dtype(previous)


def load_runtime(cfg, device):
    if not cfg.get('bundle'):
        from .grounding_train import load_runtime as native_runtime
        return native_runtime(cfg, device)
    from . import carrier_c1_run as c1, full_ft, carrier_c1_routing as routing
    from .camera_targets import carrier_id
    root, artifact_dir, native, receipt, manifest, artifact, bundle_sha = _bundle(cfg['bundle'])
    from .trace_version import resolve
    resolve(artifact,cfg)
    if native.get('trace_program_version') is not None:resolve(artifact,native)
    if cfg.get('c1_config'):
        value = cfg['c1_config']
        external = load(pinned(value) if isinstance(value, dict) else value)
        if external != native:
            raise ValueError('Configured C1 config differs from bundle')
    if cfg.get('base_artifact'):
        value = cfg['base_artifact']
        expected = value['sha256'] if isinstance(value, dict) else sha256(value)
        if expected != sha256(artifact_dir / 'artifact.json'):
            raise ValueError('Configured base artifact differs from bundle')
    if receipt.get('align'):
        raise ValueError('Standalone T0 does not support a teacher-alignment architecture')
    processor = c1.processor_for_receipt({**manifest, 'root': str(root / 'base')}, receipt)
    base = _empty_base(root / 'base')
    model = c1.CarrierC1(base, receipt['camera'], receipt['depth'], carrier_id(processor.tokenizer),
        receipt['carrier_placement'], receipt['training_mode'], receipt['depth_enabled'], receipt['recipe'],
        receipt.get('skip_unsupervised_lm'), receipt.get('frame_layout', 'spread'),
        receipt.get('depth_fov_source', 'private'))
    # Routing does not resize: the native base reserves rows for the added tokens.
    routing.init_routing_embeddings(model, processor._routing_tokens)
    from . import ground_tokens
    if ground_tokens.enabled(receipt):
        ground_tokens.bind(model, processor)
        from .mdg_features import bind_processor
        bind_processor(model, processor)
    for _, parameter in full_ft.base_parameters(model):
        parameter.data = parameter.data.to(torch.bfloat16)
    report = full_ft.load_export(model, artifact_dir / 'full_weights')
    if 'mdg' in artifact:
        from .stageb_mdg import attach_export
        attach_export(model, artifact['mdg'])
    heads = torch.load(artifact_dir / 'heads.pt', map_location='cpu', weights_only=True)
    model.auxiliary_heads.load_state_dict(heads, strict=True)
    from .trace_version import bind, resolve
    if native.get('trace_program_version') is not None:resolve(artifact,native)
    bind(model,artifact,cfg)
    model.to(device).eval().requires_grad_(False)
    skipped = {'base_shards': 'Every base parameter is replaced by the exact-coverage export.',
               'base_weight_init': 'The export supplies parameters; constructor buffers remain native.'}
    for key in ('init_artifact', 'depth_init'):
        if receipt.get(key):
            skipped[key] = 'The final export replaces these warm-start weights in full.'
    model.mdg_runtime_report = dict(schema=SCHEMA, bundle_sha256=bundle_sha, **report,
        head_tensors=len(heads), state_tensors=len(model.state_dict()),
        buffer_tensors=len(list(model.named_buffers())), skipped=skipped)
    return model, processor, native


def tensor_digest(model):
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        value = value.detach().cpu().contiguous()
        digest.update((name + '\0' + str(value.dtype) + '\0' + str(tuple(value.shape)) + '\0').encode())
        raw = value.reshape(-1).view(torch.uint8).numpy()
        for offset in range(0, raw.size, 1024 * 1024):
            digest.update(memoryview(raw[offset:offset + 1024 * 1024]))
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    check = sub.add_parser('check')
    check.add_argument('--bundle', required=True)
    check.add_argument('--device', default='cpu')
    check.add_argument('--out', required=True)
    args = parser.parse_args()
    started = time.perf_counter()
    model, _, _ = load_runtime({'bundle': args.bundle}, torch.device(args.device))
    seconds = time.perf_counter() - started
    from . import full_ft
    groups = {}
    for name, parameter in model.named_parameters():
        group = ('pose' if name.startswith('auxiliary_heads.pose.') else
                 'private_depth' if name.startswith('auxiliary_heads.depth.') else full_ft.group_of(name))
        groups[group] = groups.get(group, 0) + parameter.numel()
    write(args.out, dict(**model.mdg_runtime_report, group_parameters=groups,
        state_sha256=tensor_digest(model), load_seconds=seconds,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024))


if __name__ == '__main__':
    main()
