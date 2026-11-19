"""Authenticate and localize an export. No model weights are allocated on a GPU."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

from parity_kit.common import (LANE, META, PREP, REQUEST, TREE, checked, install, pin, read, write)

BASE_ASSETS = LANE / 'work/n13/obj/base/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a'
MODEL_MANIFEST_TAR = LANE / 'work/n13/obj/model_8005668fc14ce5ee.tar'


def original_assets(archive, base_assets, model_pin, base_identity):
    """Authenticate the archived manifest before trusting any asset pin."""
    with tarfile.open(archive) as tar:
        members = [m for m in tar if m.isfile()]
        if len(members) != 1 or Path(members[0].name).name != 'model.json':
            raise ValueError('expected one model.json in model manifest tar')
        raw = tar.extractfile(members[0]).read()
        if hashlib.sha256(raw).hexdigest() != model_pin['sha256']:
            raise ValueError('sha256 mismatch: original model manifest')
        member = members[0].name
    model = json.loads(raw)
    if model.get('schema') != 'p3-model-input-v1' or model.get('base_identity') != base_identity:
        raise ValueError('original model identity differs')
    assets = {}
    for name, digest in model['files'].items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or str(path) != name:
            raise ValueError('invalid original model file name')
        if name.endswith(('.safetensors', '.bin', '.pt', '.pth', '.safetensors.index.json', '.bin.index.json')):
            continue
        checked(Path(base_assets) / name, digest)
        assets[name] = digest
    if not {'config.json', 'tokenizer.json', 'tokenizer_config.json', 'preprocessor_config.json'} <= assets.keys():
        raise ValueError('original processor assets missing')
    return model, assets, member


def depth_shapes(config, receipt, tree=TREE):
    """Construct the actual private branch on meta, including its private vision copy."""
    install(tree)
    import torch
    from transformers import Qwen3_5Config, Qwen3_5ForConditionalGeneration
    from student_pilot.carrier_c1 import PrivateDepth
    cfg = Qwen3_5Config.from_dict(read(config))
    with torch.device('meta'):
        base = Qwen3_5ForConditionalGeneration(cfg)
        branch = PrivateDepth(cfg, base.model.visual, receipt['depth'])
    return {'depth.' + k: tuple(v.shape) for k, v in branch.state_dict().items()}


def prove_depth(heads, config, receipt, tree=TREE):
    import torch
    state = torch.load(heads, map_location='cpu', mmap=True, weights_only=True)
    expected = depth_shapes(config, receipt, tree)
    missing = sorted(set(expected) - set(state))
    wrong = sorted(k for k in expected if k in state and tuple(state[k].shape) != expected[k])
    if not expected or missing or wrong:
        raise ValueError(f'depth overwrite unproven: missing={missing}, shapes={wrong}')
    return dict(heads_keys=sorted(state), depth_keys=sorted(expected),
                depth_shapes={k: list(v) for k, v in expected.items()},
                covers='All PrivateDepth state, including every load_depth_stage1 target.',
                final_load='carrier_c1_run.load_artifact loads auxiliary_heads strictly')


def stage(source, heads, meta, out, *, request=REQUEST, tree=TREE,
          base_assets=BASE_ASSETS, model_manifest_tar=MODEL_MANIFEST_TAR,
          export_pins=None, data_root=None):
    source, heads, meta, out = map(lambda p: Path(p).resolve(), (source, heads, meta, out))
    if out.exists() and any(out.iterdir()):
        raise ValueError('restore output must be empty')
    req = read(request)
    cfg_path = meta / PREP / 'config.json'
    receipt_path = meta / PREP / 'prepared/s1_receipt.json'
    data_path = meta / 'fsw/ap/8865619b/runs/469ddece/inputs/data_receipt.json'
    if export_pins is not None:
        prep = export_pins['preparation']
        cfg_path, receipt_path, data_path = [Path(data_root)/prep[n]['path']
                                            for n in ('config', 'receipt', 'data_receipt')]
        for name, path in zip(('config', 'receipt', 'data_receipt'),
                              (cfg_path, receipt_path, data_path)):
            checked(path, prep[name]['sha256'])
            if path.stat().st_size != prep[name]['bytes']:
                raise ValueError('Preparation size differs: ' + name)
        req = dict(config=dict(path=prep['config']['source_path'], sha256=prep['config']['sha256']),
                   data_receipt=prep['data_receipt'], artifact=export_pins['artifact'])
    cfg = read(checked(cfg_path, req['config']['sha256']))
    if export_pins is not None and cfg.get('preparation') != dict(
            path=prep['receipt']['source_path'], sha256=prep['receipt']['sha256']):
        raise ValueError('Preparation receipt pin differs')
    receipt = read(checked(receipt_path, cfg['preparation']['sha256']))
    data = read(checked(data_path, req['data_receipt']['sha256']))
    artifact_path = checked(heads / 'artifact.json', req['artifact']['sha256'])
    artifact = read(artifact_path)
    if (data.get('status') != 'PREPARED' or data.get('schema') != 's1-in-job-data-v1'
            or data.get('config') != req['config'] or data.get('preparation') != cfg['preparation']
            or data.get('real_frames_verified') is not True or data.get('rehearsal') is not False
            or data.get('synthetic', False) is not False):
        raise ValueError('data receipt binding differs')
    if (receipt.get('config_sha256') != artifact.get('config_sha256')
            or artifact.get('base_identity') != cfg.get('base_identity')
            or receipt.get('frame_layout') != cfg.get('frame_layout')
            or artifact.get('frame_layout') != cfg.get('frame_layout')
            or cfg.get('frame_layout') != 'duplicate' or artifact.get('geometry_online')):
        raise ValueError('export architecture or identity differs')
    base_assets = Path(base_assets).resolve()
    original_model, assets, member = original_assets(
        model_manifest_tar, base_assets, receipt['model'], cfg['base_identity'])
    full_path = checked(heads / 'full_weights/full_weights.json', artifact['full_weights']['sha256'])
    full = read(full_path)
    if full.get('schema') != 'full-ft-export-v1' or full.get('dtype') != 'bfloat16':
        raise ValueError('unsupported full-weights export')
    hp = checked(heads / 'heads.pt', artifact['heads']['sha256'])
    entries = full['files'] + [full['index']]
    names = [e['name'] for e in entries]
    if len(set(names)) != len(names) or any(Path(n).name != n for n in names):
        raise ValueError('invalid export file names')
    if set(names) & assets.keys():
        raise ValueError('export weights overlap original assets')
    for e in entries:
        p = checked(source / e['name'], e['sha256'])
        if 'bytes' in e and p.stat().st_size != e['bytes']:
            raise ValueError('export size differs: ' + e['name'])
    index = read(source / full['index']['name'])
    if (set(index['weight_map'].values()) != {e['name'] for e in full['files']}
            or len(index['weight_map']) != full['tensor_count']):
        raise ValueError('index membership differs')
    from parity_kit.run_parity import configure_output
    configure_output(out)
    proof = prove_depth(hp, base_assets / 'config.json', receipt, tree)
    (out / 'full_weights').mkdir(parents=True, exist_ok=True)
    (out / 'base').mkdir()
    shutil.copyfile(full_path, out / 'full_weights/full_weights.json')
    for e in entries:
        src = source / e['name']
        if e is full['index']:
            shutil.copyfile(src, out / 'full_weights' / e['name'])
        else:
            (out / 'full_weights' / e['name']).symlink_to(src)
        (out / 'base' / e['name']).symlink_to(src)
    for name, digest in assets.items():
        dest = out / 'base' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(base_assets / name, dest)
        checked(dest, digest)
    (out / 'heads.pt').symlink_to(hp)
    local_artifact = deepcopy(artifact)
    local_artifact['full_weights']['path'] = str(out / 'full_weights/full_weights.json')
    local_artifact['heads']['path'] = str(out / 'heads.pt')
    write(out / 'artifact.json', local_artifact)
    files = dict(assets)
    files.update({e['name']: e['sha256'] for e in entries})
    write(out / 'model.json', dict(schema='p3-model-input-v1', root=str(out / 'base'),
                                  base_identity=cfg['base_identity'], files=files))
    local_receipt = deepcopy(receipt)
    local_receipt['model'] = pin(out / 'model.json')
    local_receipt.pop('depth_init', None)
    write(out / 'receipt.json', local_receipt)
    record = dict(schema='parity-restore-v1', original=dict(artifact=pin(artifact_path),
                  config=pin(cfg_path), receipt=pin(receipt_path), data_receipt=pin(data_path),
                  full_weights=pin(full_path), heads=pin(hp), model=receipt['model'],
                  model_manifest_tar=pin(model_manifest_tar), model_manifest_member=member,
                  base_files=original_model['files']),
                  local={n: pin(out / n) for n in ('artifact.json', 'receipt.json', 'model.json')},
                  base_files=files, depth_overwrite=proof,
                  base_file_pins=dict(original_assets=assets,
                                      step544_weights={e['name']: e['sha256'] for e in entries}),
                  deviations=[
                      dict(field='artifact.full_weights.path, artifact.heads.path', reason='Local files replace AWS paths; content pins stay unchanged.'),
                      dict(field='receipt.model', reason='Base loads the pinned export LM and ViT; load_export still checks and replaces every base tensor exactly.'),
                      dict(field='receipt.depth_init', reason='Removed because strictly restored heads cover every private-depth tensor; see depth_overwrite.'),
                      dict(field='init_artifact', reason='Omitted during evaluation, as in read_runtime.load_model.'),
                      dict(field='admission', reason='Pinned mirrored metadata replaces AWS path and Git authentication. Training databases are not opened.'),
                      dict(field='device', reason='CPU diagnostic is allowed; the Orchard loader required CUDA.')])
    write(out / 'RESTORE.json', record)
    return record


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'heads', 'out'):
        p.add_argument('--' + name, required=True)
    p.add_argument('--meta', default=str(META))
    p.add_argument('--request', default=str(REQUEST))
    p.add_argument('--tree', default=str(TREE))
    p.add_argument('--base-assets', default=str(BASE_ASSETS))
    p.add_argument('--model-manifest-tar', default=str(MODEL_MANIFEST_TAR))
    a = p.parse_args()
    stage(a.source, a.heads, a.meta, a.out, request=a.request, tree=a.tree,
          base_assets=a.base_assets, model_manifest_tar=a.model_manifest_tar)
    print(str(Path(a.out) / 'RESTORE.json'))


if __name__ == '__main__':
    main()
