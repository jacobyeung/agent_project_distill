"""Authenticate C1 exports and require an exact native tensor inventory."""
import json
from pathlib import Path
import shutil
import struct
from stage import sha, verified


def member(root, name):
    p = Path(name)
    if p.name != name or p.is_absolute():
        raise ValueError('Unsafe export member: '+str(name))
    return root / p


def headers(path):
    # Inspect names/dtypes/shapes without loading model tensors or importing torch.
    with Path(path).open('rb') as f:
        prefix = f.read(8)
        if len(prefix) != 8:
            raise ValueError('Invalid safetensors header')
        n = struct.unpack('<Q', prefix)[0]
        if not 2 <= n <= 16*1024*1024:
            raise ValueError('Safetensors header exceeds bound')
        raw = f.read(n)
    h = json.loads(raw)
    return {k: (v['dtype'], v['shape']) for k, v in h.items() if k != '__metadata__'}


def inventory(root, weight_map):
    result = {}
    errors = []
    for name in sorted(set(weight_map.values())):
        path = member(root, name)
        for key, value in headers(path).items():
            if key in result or weight_map.get(key) != name:
                errors.append(key)
            result[key] = value
    if set(result) != set(weight_map) or errors:
        raise ValueError('Tensor index differs: '+json.dumps(dict(
            missing=sorted(set(weight_map)-set(result)), extra=sorted(set(result)-set(weight_map)),
            misplaced_or_duplicate=sorted(errors))))
    return result


def native_inventory(base):
    index = base/'model.safetensors.index.json'
    if index.exists():
        return inventory(base, json.loads(index.read_text())['weight_map'])
    path = base/'model.safetensors'
    if not path.is_file():
        raise ValueError('Base requires native safetensors inventory')
    return headers(path)


def stage_export(spec, base, dest):
    artifact_path = verified(spec)
    if artifact_path.name != 'artifact.json':
        raise ValueError('C1 pin must name artifact.json')
    artifact = json.loads(artifact_path.read_text())
    if artifact.get('schema') != 'carrier-c1-artifact-v1':
        raise ValueError('Require carrier-c1-artifact-v1')
    manifest_path = artifact_path.parent/'full_weights'/'full_weights.json'
    if Path(artifact['full_weights']['path']).resolve() != manifest_path.resolve():
        raise ValueError('C1 full_weights pin must be inside its milestone')
    manifest_path = verified(artifact['full_weights'])
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('schema') != 'full-ft-export-v1' or manifest.get('dtype') != 'bfloat16':
        raise ValueError('Require BF16 full-ft-export-v1')
    source = manifest_path.parent
    index_pin = manifest['index']
    index = member(source, index_pin['name'])
    if index.name != 'model.safetensors.index.json' or sha(index) != index_pin['sha256']:
        raise ValueError('Export index hash differs')
    files = manifest['files']
    names = [r['name'] for r in files]
    if len(names) != len(set(names)) or not names:
        raise ValueError('Duplicate or empty shard list')
    for row in files:
        path = member(source, row['name'])
        if path.suffix != '.safetensors' or path.stat().st_size != row['bytes'] or sha(path) != row['sha256']:
            raise ValueError('Export shard hash/size differs: '+row['name'])
    weight_map = json.loads(index.read_text())['weight_map']
    if set(weight_map.values()) != set(names) or len(weight_map) != manifest['tensor_count']:
        raise ValueError('Export manifest/index disagree')
    actual, expected = inventory(source, weight_map), native_inventory(Path(base))
    # Accepted, recorded differences: the C1 export omits base's multi-token-prediction head (mtp.*, unused by
    # the trainer and by greedy/sampled decoding here), and exports base's FP32 GDN tensors (A_log, norms) in BF16.
    mismatch = dict(missing=sorted(n for n in set(expected)-set(actual) if not n.startswith('mtp.')),
        extra=sorted(set(actual)-set(expected)),
        dtype=[dict(name=n, export=actual[n][0], base=expected[n][0]) for n in sorted(actual.keys() & expected.keys())
               if actual[n][0] != 'BF16' or expected[n][0] not in ('BF16', 'F32')],
        shape=[dict(name=n, export=actual[n][1], base=expected[n][1]) for n in sorted(actual.keys() & expected.keys())
               if actual[n][1] != expected[n][1]])
    if any(mismatch.values()):
        raise ValueError('C1 tensors do not map 1:1 to native base: '+json.dumps(mismatch, sort_keys=True))
    for row in files:
        if len(headers(source/row['name'])) != row['tensors']:
            raise ValueError('Export shard tensor count differs: '+row['name'])
        target = dest/row['name']
        if not target.exists():
            shutil.copyfile(source/row['name'], target)
        if sha(target) != row['sha256']:
            raise ValueError('Staged C1 shard differs: '+row['name'])
    shutil.copyfile(index, dest/index.name)
    # Base was authenticated by stage.snapshot; no export config or heads are used.
    for p in Path(base).iterdir():
        if p.is_file() and p.suffix in ('.json', '.jinja', '.txt', '.model') and not p.name.endswith('.index.json'):
            shutil.copyfile(p, dest/p.name)
