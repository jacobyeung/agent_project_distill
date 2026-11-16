"""Stage the own job with the native transfer, namespace and runtime guards."""
import json
import os
from pathlib import Path
import sys
import time
import subprocess

import job_support as H

def stage(root, config):
    root = Path(root)
    S, R, NS, J = H.native()
    assets = config['assets']
    for name in ('archives', 'sj', 'fsw', 'm/ap', 'project', 'cache', 'temp', 'home'):
        (root / name).mkdir(parents=True, exist_ok=True)
    records = {}
    def resolved(item):
        if not str(item.get('generation', '')).isdigit():
            raise ValueError('Cloud object requires a pinned generation')
        uri = 'gs://cmu-gpucloud-jjyeung/' + item['name']
        result = subprocess.run(['/usr/bin/gcloud', 'storage', 'objects', 'describe', uri + '#' + str(item['generation']), '--format=json'],
                                env=S.cloud_environment(assets['gcloud_config']), check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        value = json.loads(result.stdout)
        if int(value['size']) != item['bytes'] or str(value['generation']) != str(item['generation']):
            raise ValueError('Cloud metadata differs from its pin')
        if item.get('crc32c') and value.get('crc32c_hash', value.get('crc32c')) != item['crc32c']:
            raise ValueError('Cloud CRC32C differs from its pin')
        return item
    def part(role, item, destination, *, cloud=False, strip=0, overlay=False, links=False):
        if cloud:
            item = resolved(item)
        archive = root / 'archives' / (role + '.tar')
        opener = (lambda p: NS.cloud(p, root, dict(assets, cloud_prefix=p['name'].rsplit('/', 1)[0]))) if cloud else lambda p: Path(p['path']).open('rb')
        records[role] = S.copy_parts([item], archive, opener, expected_sha=item['sha256'])
        inventory = H.unpack(S, archive, destination, strip=strip, overlay=overlay, links=links)
        if 'members' in item:
            NS.verify_inventory(inventory, item['members'])
        H.dump(root / 'a01.json', records)
        return archive, inventory
    # The four ordered parts form one authenticated export archive.
    export = config['export']
    archive = root / 'archives/a0.tar'
    records['export'] = S.copy_parts(export['parts'], archive,
        lambda p: NS.cloud(p, root, dict(assets, cloud_prefix=p['name'].rsplit('/', 1)[0])),
        expected_sha=export['sha256'])
    H.unpack(S, archive, NS.physical(root, config['export_destination']))
    part('a1', config['anchors'], NS.physical(root, '/scratch/jjyeung/k1_frames'), cloud=True)
    part('a2', assets['small_objects'][1], root, cloud=True, overlay=True)
    # The source bundle supplies the model JSON and the C8r import overlays.
    part('a3', config['code'], root, cloud=True, overlay=True)
    part('a30', assets['small_objects'][3], root, cloud=True, overlay=True)
    model = json.loads(NS.physical(root, assets['model_manifest']['path']).read_text())
    assert H.sha(NS.physical(root, assets['model_manifest']['path'])) == assets['model_manifest']['sha256']
    _, inventory = part('a4', assets['base'], NS.physical(root, model['root']), strip=3)
    NS.verify_inventory({k:v['sha256'] for k,v in inventory.items()}, model['files'])
    # Keep the native runtime and overlay identities, including executable links.
    for role in ('runtime', 'numpy', 'closure', 'trainer'):
        item = assets[role]
        target = (root / 'project/c7d31ddd/venvs' if role == 'runtime' else
                  NS.physical(root, assets['tree_root']) if role == 'trainer' else root / role)
        target.mkdir(parents=True, exist_ok=True)
        if role == 'runtime':
            archive = root / 'archives/a5.tar'
            records[role] = NS.copied(item, archive)
            saved = S.RUNTIME_ABSOLUTE_LINKS
            try:
                S.RUNTIME_ABSOLUTE_LINKS = NS.runtime_links(archive)
                H.unpack(S, archive, target, links=True)
            finally:
                S.RUNTIME_ABSOLUTE_LINKS = saved
            present = [p for p in (target / NS.RUNTIME / 'bin/python', target / 'venvs' / NS.RUNTIME / 'bin/python') if p.is_file()]
            assert len(present) == 1
            python = present[0]
        else:
            archive, inventory = part(role, item, target, overlay=role == 'trainer')
            if role == 'trainer':
                NS.verify_inventory({k:v['sha256'] for k,v in inventory.items()}, assets['tree_sources'])
                link = NS.physical(root, assets['trainer_logical_archive'])
                link.parent.mkdir(parents=True, exist_ok=True)
                os.link(archive, link)
    records['bwrap'] = NS.copied(assets['bwrap'], root / 'bwrap')
    (root / 'bwrap').chmod(0o700)
    manifest = NS.physical(root, assets['fla']['manifest']['path'])
    assert H.sha(manifest) == assets['fla']['manifest']['sha256']
    wanted = {'ebe69df8/p/' + name: dict(destination='p/' + name, sha256=digest)
              for name, digest in NS.manifest_files(manifest).items()}
    assert Path(assets['fla']['path']).stat().st_size == assets['fla']['bytes']
    records['fla'] = NS.extract_named(assets['fla']['path'], root / 'fla', wanted)
    # The authenticated map preserves the materialized kc kit at its exact path.
    runtime = NS.runtime_spec(root, config, python)
    worker = root / 'phase_worker.py'
    runtime['entrypoints'] = {worker.name: dict(path=str(worker), sha256=H.sha(worker))}
    H.dump(root / 'a02.json', runtime)
    H.dump(root / 'a01.json', records)
    S.room(root)
    return runtime

def environment(root):
    _, _, _, J = H.native()
    env = J.environment(root)
    env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               TRITON_CACHE_DIR=str(Path(root) / 'cache/a'), TORCH_HOME=str(Path(root) / 'cache/b'))
    return env

def namespace(root, config):
    _, _, NS, _ = H.native()
    argv = NS.namespace(root, config)
    parent = str(Path(config['logical_run']).parent)
    physical_parent = str(NS.physical(root, parent))
    argv += ['--bind', physical_parent, physical_parent, '--bind', physical_parent, parent]
    # Native namespace mounts the staged project read-only. Permit only this
    # packet's opaque return pool and the existing credential directory.
    pool_root = str(Path(config['pointer']).parent)
    NS.physical(root, pool_root).mkdir(parents=True, exist_ok=True)
    NS.physical(root, config['assets']['gcloud_config']).mkdir(parents=True, exist_ok=True)
    argv += ['--bind', pool_root, pool_root, '--bind',
             config['assets']['gcloud_config'], config['assets']['gcloud_config']]
    return argv
