"""Synchronous durable state handoff before optional project mirroring."""
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
import tarfile
from student_pilot.p3_provenance import file_pin, load, pinned, sha256, write


def plan(cfg):
    from student_pilot.checkpoint_space import plan as native_plan
    guard = cfg['checkpoint_disk_guard']
    expected = native_plan(cfg['recipe'], reserve_bytes=guard['reserve_bytes'])
    if guard != expected:
        raise ValueError('Persistence plan differs from checkpoint disk guard')
    return dict(full_states=guard['planned_full_states']+guard['extra_full_states'],
                exports=guard['planned_weight_exports'], reserve_bytes=guard['reserve_bytes'],
                primary='node-local then durable upload', project_required=False)


def upload(cfg, directory, kind, uploader=None, mirror=None):
    """Run only after all ranks finish the immutable native checkpoint/export."""
    spec = cfg.get('r2_persistence')
    if not spec:
        raise ValueError('Missing durable state persistence binding')
    plan(cfg)
    directory = Path(directory).resolve()
    output = Path(cfg['output']).resolve()
    if output not in directory.parents:
        raise ValueError('State is outside the node-local run')
    marker = directory/('complete.json' if kind == 'checkpoint' else 'artifact.json')
    value = load(marker)
    if kind == 'checkpoint':
        from student_pilot.carrier_c1_run import complete_states
        if marker not in complete_states(output, value['binding']):
            raise ValueError('Native state predicate refused')
        for name, pin in value['files'].items():
            if sha256(directory/name) != pin['sha256']:
                raise ValueError('State member digest differs')
    spool = output/'persist'
    spool.mkdir(exist_ok=True)
    name = sha256(marker)
    receipt = spool/(name+'.json')
    if receipt.exists():
        return load(receipt)
    claim = spool/(name+'.claim')
    with claim.open('x') as f:
        f.write(name)
    # A claimed interrupted upload never retries an ambiguous server session.
    archive = spool/(name+'.tar')
    entries = {str(p.relative_to(directory)): file_pin(p) for p in directory.rglob('*') if p.is_file()}
    archive_bound = sum((directory/name).stat().st_size+1024 for name in entries)+10240
    if shutil.disk_usage(spool).free < archive_bound+cfg['checkpoint_disk_guard']['reserve_bytes']:
        raise ValueError('Node-local archive reserve is insufficient')
    if any(p.is_symlink() for p in directory.rglob('*')):
        raise ValueError('State symlink refused')
    with tarfile.open(archive, 'w') as handle:
        for rel in sorted(entries):
            handle.add(directory/rel, arcname=rel, recursive=False)
    with tarfile.open(archive) as handle:
        if {m.name for m in handle.getmembers()} != set(entries):
            raise ValueError('Archive inventory differs')
        for m in handle.getmembers():
            h = hashlib.sha256()
            with handle.extractfile(m) as source:
                for block in iter(lambda: source.read(1024*1024), b''):
                    h.update(block)
            if h.hexdigest() != entries[m.name]['sha256'] or sha256(directory/m.name) != h.hexdigest():
                raise ValueError('Archive or source changed')
    if uploader is None:
        sessions = pinned(spec['sessions'])
        tool = pinned(spec['uploader'])
        module_spec = importlib.util.spec_from_file_location('durable_writer', tool)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        def uploader(path, key):
            if module.main(['split',str(sessions),key,str(path),'4','4']):
                raise ValueError('Durable upload failed')
            values = [json.loads(line) for line in Path(str(sessions)+'.receipts.jsonl').read_text().splitlines()]
            return [v for v in values if v['name'].startswith(key+'.part')]
    records = uploader(archive, name)
    if len(records) != 4 or any(not r.get('generation') or not r.get('sha256') for r in records):
        raise ValueError('Upload lacks all verified generations')
    cursor = 0
    with archive.open('rb') as source:
        for part in sorted(records, key=lambda r:r['offset']):
            if part['offset'] != cursor:
                raise ValueError('Upload ranges differ')
            h, remaining = hashlib.sha256(), part['bytes']
            while remaining:
                block=source.read(min(1024*1024,remaining))
                if not block:
                    raise ValueError('Upload range exceeds archive')
                h.update(block)
                remaining -= len(block)
            if h.hexdigest() != part['sha256']:
                raise ValueError('Upload range digest differs')
            cursor += part['bytes']
        if cursor != archive.stat().st_size:
            raise ValueError('Upload does not cover archive')
    result = dict(kind=kind, source=file_pin(marker), archive=file_pin(archive), parts=records,
                  durable=True, project_required=False)
    write(receipt, result)
    if mirror is not None:
        try:
            mirror(archive, result)
        except OSError:
            pass
    return result


def milestone(cfg, directory, kind, rank=0, distributed=True):
    if 'r2_identity' not in cfg:
        return
    result = [None]
    if rank == 0:
        try:
            upload(cfg, directory, kind)
        except Exception as error:
            result[0] = str(error)
    if distributed:
        import torch.distributed as dist
        dist.broadcast_object_list(result, src=0)
    if result[0]:
        raise ValueError('Durable persistence refused: '+result[0])
