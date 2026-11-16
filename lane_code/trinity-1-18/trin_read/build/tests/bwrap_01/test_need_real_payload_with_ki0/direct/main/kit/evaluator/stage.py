"""Authenticate snapshots and full-weight archives into one node-local directory."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def verified(pin):
    p=Path(pin['path'])
    if sha(p)!=pin['sha256']:raise ValueError('Artifact hash differs')
    return p


def extract(archive,dest):
    with tarfile.open(archive) as tf:
        members=tf.getmembers()
        for m in members:
            p=Path(m.name)
            if p.is_absolute() or '..' in p.parts or not (m.isfile() or m.isdir()):
                raise ValueError('Unsafe archive member')
        tf.extractall(dest,members=members,filter='data')


def snapshot(spec,dest):
    manifest=json.loads(verified(spec['manifest']).read_text())
    files=manifest['files']
    if not files:raise ValueError('Empty snapshot inventory')
    for row in files:
        rel=Path(row['path'])
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe snapshot member')
        src=Path(spec['path'])/rel
        if src.is_symlink():src=src.resolve(strict=True)
        if sha(src)!=row['sha256']:raise ValueError('Snapshot member hash differs')
        if row.get('bytes') is not None and src.stat().st_size!=row['bytes']:raise ValueError('Snapshot size differs')
        target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():shutil.copyfile(src,target)
        if sha(target)!=row['sha256']:raise ValueError('Staged snapshot differs')


def prepare(spec,base,dest):
    dest=Path(dest)
    receipt=dest.parent/(dest.name+'.json')
    identity=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest()
    if receipt.exists():
        if json.loads(receipt.read_text())['identity']!=identity:raise ValueError('Model cache binding differs')
        return dest
    dest.mkdir(parents=True,exist_ok=True)
    if spec['kind']=='snapshot':
        snapshot(spec,dest)
    elif spec['kind']=='archive':
        unpack=dest/'a'
        unpack.mkdir(exist_ok=True)
        extract(verified(spec),unpack)
        # Only the authenticated local archive is searched; never a shared tree.
        candidates=[p.parent for p in unpack.rglob('*.safetensors')]
        candidates+= [p.parent for p in unpack.rglob('pytorch_model*.bin')]
        candidates=sorted(set(candidates))
        if len(candidates)!=1:raise ValueError('Require one native full_weights directory')
        weights=candidates[0]
        for p in weights.iterdir():
            if p.is_file():shutil.copyfile(p,dest/p.name)
        # Missing model metadata and tokenizer come from the authenticated base snapshot.
        for p in Path(base).iterdir():
            if (p.is_file() and p.suffix in ('.json','.jinja','.txt','.model')
                    and not p.name.endswith('.index.json') and not (dest/p.name).exists()):
                shutil.copyfile(p,dest/p.name)
    elif spec['kind']=='c1_export':
        from c1_export import stage_export
        if base is None:raise ValueError('C1 export requires a manifest-pinned staged base')
        stage_export(spec,base,dest)
    else:
        raise ValueError('Only native snapshots and full-weight archives are accepted')
    cfg=json.loads((dest/'config.json').read_text())
    if cfg.get('model_type')!='qwen3_5' or not (dest/'tokenizer_config.json').exists():
        raise ValueError('Require native Qwen3.5 model config and tokenizer')
    if not list(dest.glob('*.safetensors')) and not list(dest.glob('pytorch_model*.bin')):
        raise ValueError('No native full weights')
    index=dest/'model.safetensors.index.json'
    if index.exists():
        for member in set(json.loads(index.read_text())['weight_map'].values()):
            p=Path(member)
            if p.name!=member or not (dest/p).is_file():raise ValueError('Incomplete native weight shards')
    receipt.write_text(json.dumps(dict(identity=identity))+'\n')
    return dest
