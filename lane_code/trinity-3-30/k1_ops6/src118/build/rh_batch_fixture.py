"""Small CPU assets for the real batch staging controller; never an upload."""
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import shlex
import tarfile


def make(package, case, config, python, project=False):
    import job_support as H
    _, _, NS, _ = H.native()
    objects = case / 'objects'
    objects.mkdir()
    pins = {}
    def pin(path, name):
        result = dict(path=str(path), name='q8/fixture/' + name, generation='1',
                      bytes=path.stat().st_size, sha256=H.sha(path))
        pins[result['name']] = result
        return result
    def tar(name, files, modes=None):
        path = objects / (name + '.tar')
        inventory = {}
        with tarfile.open(path, 'w') as archive:
            for filename, raw in files.items():
                item = tarfile.TarInfo(filename)
                item.size, item.mode = len(raw), (modes or {}).get(filename, 0o644)
                archive.addfile(item, io.BytesIO(raw))
                inventory[filename] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        result = pin(path, name + '.tar')
        result['members'] = inventory
        return result
    c = deepcopy(config)
    a = c['assets']
    anchor = package / 'inputs/anchors.tar'
    if not anchor.is_file():
        anchor = Path('/scratch/jjyeung/k1/partB/k1_partB_anchors.tar')
    assert anchor.stat().st_size == c['anchors']['bytes']
    c['anchors'] = dict(c['anchors'], path=str(anchor))
    for index, filename in ((1, 'a.tar'), (3, 'model.tar')):
        original = a['small_objects'][index]
        path = package / 'inputs' / filename
        if not path.is_file() and index == 1:
            path = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/partb/meta/e10fbb95.tar')
        assert path.stat().st_size == original['bytes'] and H.sha(path) == original['sha256']
        a['small_objects'][index] = dict(original, path=str(path))
        pins[original['name']] = a['small_objects'][index]
    c['code'] = dict(c['code'], path=str(package / 'packet' / Path(c['code']['name']).name))
    assert H.sha(c['code']['path']) == c['code']['sha256']
    pins[c['code']['name']] = c['code']
    # Keep the real model metadata for prepared(); use a separate fixture model
    # manifest solely for the unavailable 19-GB base archive's staging inventory.
    model = dict(root='/scratch/jjyeung/rh_base', files={'base.txt': hashlib.sha256(b'base').hexdigest()})
    model_raw = json.dumps(model).encode()
    fla_files = {'fla/__init__.py': b'__version__="0.6.0"\n',
                 'triton/__init__.py': b'__version__="3.7.1"\n',
                 'triton/backends/nvidia/bin/ptxas': b'#!/bin/sh\nexit 1\n'}
    fla_manifest = ''.join(hashlib.sha256(raw).hexdigest()+'  '+name+'\n'
                           for name, raw in fla_files.items()).encode()
    a['closure'] = tar('closure', {'CPU_FIXTURE': b'No production overlays\n'})
    # Sidecar metadata under the export destination is staged before the base.
    export = tar('export_full', {'rh/model.json': model_raw, 'rh/fla.sha': fla_manifest,
                                'rh/aliases/sitecustomize.py': b'pass\n', 'rh/kit/a.py': b''})
    raw = Path(export['path']).read_bytes()
    parts = []
    for index in range(4):
        path = objects / ('full_part' + str(index))
        path.write_bytes(raw[len(raw)*index//4:len(raw)*(index+1)//4])
        parts.append(pin(path, path.name))
    c['export'] = dict(parts=parts, sha256=export['sha256'])
    logical = c['export_destination'] + '/rh'
    a['model_manifest'] = dict(path=logical+'/model.json', sha256=hashlib.sha256(model_raw).hexdigest())
    a['base'] = tar('base', {'a/b/c/base.txt': b'base'})
    a['base'].pop('members')
    launcher = ('#!/bin/sh\nexec ' + shlex.quote(str(python)) + ' -I -s -B ' +
                shlex.quote(str(package / 'rh_batch.py')) + ' --worker ' +
                shlex.quote(str(case / 'CONTEXT.json')) + ' "$@"\n').encode()
    runtime_files = {NS.RUNTIME+'/lib/python3.12/site-packages/'+name+'/__init__.py': b''
                     for name in ('scipy', 'torch', 'transformers', 'PIL')}
    runtime_files[NS.RUNTIME+'/bin/python'] = launcher
    a['runtime'] = tar('runtime', runtime_files, {NS.RUNTIME+'/bin/python': 0o755})
    a['numpy'] = tar('numpy', {'numpy/__init__.py': b''})
    a['trainer'] = dict(a['trainer'], path=str(package / 'payload/a845b1789.tar'))
    assert H.sha(a['trainer']['path']) == a['trainer']['sha256']
    fla = tar('fla', {'ebe69df8/p/'+name: raw for name, raw in fla_files.items()},
              {'ebe69df8/p/triton/backends/nvidia/bin/ptxas': 0o755})
    a['fla'] = dict(path=fla['path'], bytes=fla['bytes'],
                    manifest=dict(path=logical+'/fla.sha', sha256=hashlib.sha256(fla_manifest).hexdigest()))
    a['kit_import_root'] = logical+'/kit'
    a['aliases_root'] = logical+'/aliases'
    a['sitecustomize'] = dict(path=logical+'/aliases/sitecustomize.py', sha256=hashlib.sha256(b'pass\n').hexdigest())
    a['bwrap'] = pin(Path('/usr/bin/bwrap'), 'bwrap')
    a['gcloud_config'] = str(objects)
    c.update(pool=str(case / 'pool'), cloud=str(case / 'cloud'), pointer=str(case / 'pool/a.json'))
    if project:
        a['gcloud_config'] = '/project/community/jjyeung/gcloud'
        c.update(pool='/project/community/jjyeung/okh7/b7e31d84a90c62f5',
                 pointer='/project/community/jjyeung/okh7/b7e31d84a90c62f5/a.json')
    # Transport keys are always production names/paths. Fixture identities remain
    # separate and may never replace the embedded CONFIG or a.json.
    objects_by_production_key = {}
    for original, fixture in [(config['anchors'], c['anchors']), (config['code'], c['code'])] + [
            (config['assets']['small_objects'][i], a['small_objects'][i]) for i in (1, 3)] + [
            (config['assets'][role], a[role]) for role in ('base','runtime','numpy','closure','trainer','bwrap','fla')] + list(zip(config['export']['parts'], c['export']['parts'])):
        key = original.get('name', original.get('path'))
        objects_by_production_key[key] = dict(fixture, production=original,
            substituted=any(fixture.get(k) != original.get(k) for k in ('bytes','sha256','members')))
    return c, objects_by_production_key
