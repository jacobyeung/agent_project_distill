"""Explicit local transport and unavailable-object boundaries for the batch test."""
import json
from pathlib import Path

def install(H, S, NS, root, case, production, fixture, objects):
    events = []
    def record(role, verified, detail):
        events.append(dict(role=role, production_verifier=verified, detail=detail))
        H.dump(case/'VERIFIERS.json', events)
    original_copy, original_copied = S.copy_parts, NS.copied
    original_open, original_stat = Path.open, Path.stat
    original_verify = NS.verify_inventory
    original_unpack = H.unpack
    cache_file = case.parent/'ANCHOR_CACHE.json'
    def portable(path):
        path = Path(path)
        return str(case/'job_tmp/424242'/path.relative_to('/tmp')) if path.is_relative_to('/tmp') else str(path)
    def key(item): return item.get('name', item.get('path'))
    def copy(parts, destination, opener, expected_sha=None, **kwargs):
        rows = [objects.get(key(p)) for p in parts]
        if not all(rows):
            return original_copy(parts, destination, opener, expected_sha=expected_sha, **kwargs)
        if parts == [production['anchors']] and cache_file.exists():
            import os
            cache = json.loads(cache_file.read_text())
            os.link(cache['archive'], destination)
            record('anchors transport', False, 'reuse the production-verified success-case archive; copy verifier not repeated')
            return cache['copy']
        substituted = any(row['substituted'] for row in rows)
        actual = [dict(row, name=key(p), generation=p.get('generation')) for p,row in zip(parts,rows)] if substituted else parts
        expected = fixture['export']['sha256'] if len(parts)==4 else rows[0]['sha256']
        def local_open(p):
            if opener is not None:
                return opener(objects[key(p)]['production'])
            return original_open(Path(objects[key(p)]['path']), 'rb')
        result = original_copy(actual, destination, local_open,
                               expected_sha=expected if substituted else expected_sha, **kwargs)
        record([key(p) for p in parts], not substituted,
               'fixture bytes/SHA256 only; production verifier NOT exercised' if substituted else 'production size, SHA256, MD5 when present')
        if parts == [production['anchors']]:
            H.dump(case/'ANCHOR_COPY.json', result)
        return result
    S.copy_parts = copy
    def unpack(stager, archive, target, **kwargs):
        if Path(archive).name != 'a1.tar':
            return original_unpack(stager, archive, target, **kwargs)
        if cache_file.exists():
            cache = json.loads(cache_file.read_text())
            Path(target).parent.mkdir(parents=True, exist_ok=True)
            Path(target).symlink_to(cache['extraction'], target_is_directory=True)
            record('anchors unpack', False, 'reuse success-case extraction and measured inventory; unpack not repeated')
            return cache['inventory']
        inventory = original_unpack(stager, archive, target, **kwargs)
        original_verify(inventory, production['anchors']['members'])
        H.dump(cache_file, dict(archive=portable(archive), extraction=portable(target), inventory=inventory,
                               copy=json.loads((case/'ANCHOR_COPY.json').read_text())))
        record('anchors unpack', True, 'native H.unpack(strip=0) and NS.verify_inventory on the real tar')
        return inventory
    H.unpack = unpack
    # Pool-file transport retains the production record and maps only reads.
    def opened(path, mode='r', *args, **kwargs):
        row = objects.get(str(path))
        if row:
            assert mode in ('r','rb')
            path = Path(row['path'])
        return original_open(path, mode, *args, **kwargs)
    Path.open = opened
    fla = production['assets']['fla']
    def stat(path, *args, **kwargs):
        row = objects.get(str(path))
        if row:
            value = original_stat(Path(row['path']), *args, **kwargs)
            if str(path) == fla['path']:
                # Explicitly bypass the unavailable production FLA size gate.
                import os
                fields = list(value); fields[6] = fla['bytes']
                return os.stat_result(fields)
            return value
        return original_stat(path, *args, **kwargs)
    Path.stat = stat
    def copied(item, destination):
        row = objects.get(key(item))
        if row and row['substituted']:
            return copy([item], destination, None, expected_sha=item['sha256'])
        return original_copied(item, destination)
    NS.copied = copied
    def verify(actual, expected):
        model = NS.physical(root, production['assets']['model_manifest']['path'])
        if model.is_file() and expected == json.loads(model.read_text())['files']:
            record('base members', False, 'unavailable production base inventory NOT exercised')
            return
        original_verify(actual, expected)
        record('inventory', True, dict(members=len(expected),
               anchors=(expected==production['anchors']['members']), code=(expected==production['code']['members'])))
    NS.verify_inventory = verify
    extract = NS.extract_named
    def extract_fla(path, target, wanted):
        assert str(path)==fla['path']
        manifest = NS.physical(root, fixture['assets']['fla']['manifest']['path'])
        selected = {'ebe69df8/p/'+name:dict(destination='p/'+name,sha256=digest)
                    for name,digest in NS.manifest_files(manifest).items()}
        record('FLA size and selected members',False,'fixture only; production verifier NOT exercised')
        return extract(fixture['assets']['fla']['path'],target,selected)
    NS.extract_named = extract_fla
    runtime_spec = NS.runtime_spec
    def runtime(root, config, python):
        record('runtime spec/imports',False,'CPU fixture runtime, overlays and interpreter; production verifier NOT exercised')
        return runtime_spec(root, fixture, python)
    NS.runtime_spec = runtime
    return events
