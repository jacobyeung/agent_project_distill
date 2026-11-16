"""Authenticate and localize an export. No model weights are allocated on a GPU."""
import argparse
from copy import deepcopy
from pathlib import Path
import shutil

from parity_kit.common import (META, PREP, REQUEST, TREE, checked, install, pin, read, sha, write)


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


def stage(source, heads, meta, out, *, request=REQUEST, tree=TREE):
    source, heads, meta, out = map(lambda p: Path(p).resolve(), (source, heads, meta, out))
    if out.exists() and any(out.iterdir()):
        raise ValueError('restore output must be empty')
    req = read(request)
    cfg_path = meta / PREP / 'config.json'
    receipt_path = meta / PREP / 'prepared/s1_receipt.json'
    data_path = meta / 'fsw/ap/8865619b/runs/469ddece/inputs/data_receipt.json'
    cfg = read(checked(cfg_path, req['config']['sha256']))
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
    full_path = checked(heads / 'full_weights/full_weights.json', artifact['full_weights']['sha256'])
    full = read(full_path)
    if full.get('schema') != 'full-ft-export-v1' or full.get('dtype') != 'bfloat16':
        raise ValueError('unsupported full-weights export')
    hp = checked(heads / 'heads.pt', artifact['heads']['sha256'])
    entries = full['files'] + [full['index']]
    names = [e['name'] for e in entries]
    if len(set(names)) != len(names) or any(Path(n).name != n for n in names):
        raise ValueError('invalid export file names')
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
    proof = prove_depth(hp, source / 'config.json', receipt, tree)
    # Only known processor/config formats are copied; weights remain symlinks.
    assets = sorted(p for p in source.iterdir() if p.is_file() and
                    p.name not in names and p.suffix in {'.json', '.jinja', '.txt', '.model'})
    required = {'config.json', 'tokenizer.json', 'tokenizer_config.json', 'preprocessor_config.json'}
    if not required <= {p.name for p in assets}:
        raise ValueError('processor assets missing')
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
    for p in assets:
        shutil.copyfile(p, out / 'base' / p.name)
    (out / 'heads.pt').symlink_to(hp)
    local_artifact = deepcopy(artifact)
    local_artifact['full_weights']['path'] = str(out / 'full_weights/full_weights.json')
    local_artifact['heads']['path'] = str(out / 'heads.pt')
    write(out / 'artifact.json', local_artifact)
    files = {p.name: sha(p) for p in assets}
    files.update({e['name']: e['sha256'] for e in entries})
    write(out / 'model.json', dict(schema='p3-model-input-v1', root=str(out / 'base'),
                                  base_identity=cfg['base_identity'], files=files))
    local_receipt = deepcopy(receipt)
    local_receipt['model'] = pin(out / 'model.json')
    local_receipt.pop('depth_init', None)
    write(out / 'receipt.json', local_receipt)
    record = dict(schema='parity-restore-v1', original=dict(artifact=pin(artifact_path),
                  config=pin(cfg_path), receipt=pin(receipt_path), data_receipt=pin(data_path),
                  full_weights=pin(full_path), heads=pin(hp)),
                  local={n: pin(out / n) for n in ('artifact.json', 'receipt.json', 'model.json')},
                  base_files=files, depth_overwrite=proof,
                  deviations=[
                      dict(field='artifact.full_weights.path, artifact.heads.path', reason='Local files replace AWS paths; content pins stay unchanged.'),
                      dict(field='receipt.model', reason='Base loads step-544 LM and ViT; load_export still checks and replaces every base tensor exactly.'),
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
    a = p.parse_args()
    stage(a.source, a.heads, a.meta, a.out, request=a.request, tree=a.tree)
    print(str(Path(a.out) / 'RESTORE.json'))


if __name__ == '__main__':
    main()
