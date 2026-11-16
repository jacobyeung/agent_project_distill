"""Manifest-authenticated hard links for native D0 model packets."""
import hashlib
import json
import os
from pathlib import Path
import trinity_read as T


def checked(path, pin):
    path = Path(path)
    if (path.resolve() != path or not path.is_file() or
            ('bytes' in pin and path.stat().st_size != pin['bytes']) or T.sha(path) != pin['sha256']):
        raise ValueError('Linked model size/hash/path differs: '+str(path))
    return path


def plan(root, config):
    models = config['spec']['models']; base = models['base']; export = models['cp1m200']
    if base['kind'] != 'snapshot' or export['kind'] != 'c1_export':
        raise ValueError('--link-models requires a staged snapshot and c1_export')
    base_dir = T.physical(root, base['path'])
    manifest = checked(T.physical(root, base['manifest']['path']), base['manifest'])
    rows = []
    for pin in T.load(manifest)['files']:
        rel = Path(pin['path'])
        if rel.is_absolute() or '..' in rel.parts or not rel.parts: raise ValueError('Unsafe base member')
        rows.append(dict(source=str(base_dir/rel), target='base/'+str(rel), **{k:pin[k] for k in ('bytes','sha256')}))
    artifact = checked(T.physical(root, export['path']), export)
    weight_pin = T.load(artifact)['full_weights']
    weights = checked(T.physical(root, weight_pin['path']), weight_pin)
    if weights != artifact.parent/'full_weights/full_weights.json': raise ValueError('Export manifest outside milestone')
    full = T.load(weights)
    for pin in full['files']+[full['index']]:
        name = pin['name']
        if Path(name).name != name or name in ('.', '..'): raise ValueError('Unsafe export member')
        path = weights.parent/name
        rows.append(dict(source=str(path), target='cp1m200/'+name,
                         bytes=pin.get('bytes', path.stat().st_size), sha256=pin['sha256']))
    for row in list(rows):
        p = Path(row['target'])
        if (p.parent == Path('base') and p.suffix in ('.json','.jinja','.txt','.model')
                and not p.name.endswith('.index.json')):
            rows.append(dict(row, target='cp1m200/'+p.name))
    if not rows or len({r['target'] for r in rows}) != len(rows): raise ValueError('Empty/duplicate model inventory')
    for row in rows:
        if not T.inside(Path(row['source']), root): raise ValueError('Model source outside root')
        checked(row['source'], row)
    return rows


def link_files(root, destination, rows):
    destination = Path(destination)
    if destination.exists(): raise ValueError('Model destination exists')
    # Check the device before creating any links. Never fall back to copies.
    for row in rows:
        source = checked(row['source'], row)
        if not T.inside(source, root): raise ValueError('Model source outside root')
        if source.stat().st_dev != destination.parent.stat().st_dev:
            raise ValueError('Hard links require the same filesystem')
    destination.mkdir()
    for row in rows:
        target = destination/row['target']; target.parent.mkdir(parents=True, exist_ok=True)
        os.link(row['source'], str(target))
    verify(destination, rows)


def verify(destination, rows):
    for row in rows:
        source = checked(row['source'], row); target = checked(Path(destination)/row['target'], row)
        a, b = source.stat(), target.stat()
        if (a.st_dev, a.st_ino) != (b.st_dev, b.st_ino): raise ValueError('Model is not the staged hard link')


def prepare(root, config, destination):
    rows = plan(root, config)
    link_files(root, destination, rows)
    for name in ('base', 'cp1m200'):
        spec = config['spec']['models'][name]
        identity = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
        T.dump(destination/(name+'.json'), dict(identity=identity, models_linked=True))
    return rows


def readonly(root, destination, rows):
    mounts = {str(destination): str(destination)}
    for row in rows:
        source = Path(row['source']); mounts[str(source.parent)] = str(source.parent)
        for logical, physical in ((T.SJ, root/'sj'), (T.FSW, root/'fsw'), (T.AP, root/'m/ap')):
            if T.inside(source, physical):
                mounts[str(logical/source.parent.relative_to(physical))] = str(source.parent)
                break
    args = []
    for target, source in sorted(mounts.items()): args += ['--ro-bind', source, target]
    return args


def create(root, config, packet, family):
    destination = packet/'direct'/family/'models'
    rows = prepare(root, config, destination)
    argv = readonly(root, destination, rows)
    for row in rows: row['target'] = str(destination/row['target'])
    receipt = dict(models_linked=True, destination=str(destination), files=rows,
                   bwrap_args=argv, before_verified=True, after_verified=False)
    T.dump(packet/'MODELS_LINKED.json', receipt)
    return receipt


def finish(packet, root, receipt):
    try:
        verify(Path(receipt['destination']), receipt['files'])
        receipt['after_verified'] = True
    except Exception as error:
        receipt['after_verified'] = False; receipt['error'] = str(error)
        raise
    finally:
        T.dump(packet/'MODELS_LINKED.json', receipt)
