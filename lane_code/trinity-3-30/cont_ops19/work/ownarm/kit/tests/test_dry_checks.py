"""Offline synthetic archives exercise the actual embedded Python 3.6 checks."""
import copy
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile

import pytest

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT))
import build_ownread as B

BUILD = KIT.parent/'out/pkg/r400'
PY36 = '/usr/bin/python3'


def tarraw(files):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode='w') as t:
        for name, data in sorted(files.items()):
            m = tarfile.TarInfo(name); m.size = len(data)
            t.addfile(m, io.BytesIO(data))
    return out.getvalue()


@pytest.fixture(scope='module')
def source():
    d = B.unpack((BUILD/'1.tgz').read_bytes())
    return d, B.unpack(d['0.tgz'])


def fixture(root, source, operator_change=None):
    """Use real code/items with synthetic, consistently resealed data/policy pins."""
    root.mkdir(parents=True, exist_ok=True)
    d, payload = map(dict, source)
    cfg = json.loads(payload['9.json'])
    logical = cfg['logical'] + '/d'
    policy = dict(vnice=logical+'/q/vnice.sh', terminator=logical+'/q/terminator.sh')
    q = {'q/vnice.sh': b'#!/bin/sh\nexit 0\n', 'q/terminator.sh': b'#!/bin/sh\nexit 1\n',
         'q/policy.json': B.jbytes(dict(policy, authorized=True)),
         'q/env.json': B.jbytes(dict(versions={'fixture': True}))}
    assets_name = 'orchard_h10/vendor/ORCHARD_ASSETS.json'
    assets = json.loads(payload[assets_name])
    for name in ('vnice', 'terminator'):
        assets[name+'_sha256'] = B.sha(q['q/'+name+'.sh'])
    payload[assets_name] = B.jbytes(assets)
    cfg['payload_pins'][assets_name] = dict(bytes=len(payload[assets_name]), sha256=B.sha(payload[assets_name]))
    prep = {name: B.jbytes(dict(fixture=name)) for name in B.PREP_NAMES}
    cfg['export_binding']['preparation_sha256'] = {k: B.sha(v) for k, v in prep.items()}
    payload['9.json'] = B.jbytes(cfg)
    operator = d['a/6.py']
    if operator_change:
        old, new = operator_change
        assert old in operator
        operator = operator.replace(old, new)
    d, _, pub, cfg, _ = B.seal(d, payload, B.bundle_of(d['BATCH.sh']), cfg['token'], operator)
    package = root/'package'
    for name, raw in d.items(): B.put(package/name, raw)
    binding = cfg['export_binding']
    members = {'artifact': 'artifact.json', 'heads': 'heads.pt', 'full_weights': 'full_weights/full_weights.json'}
    export_files = {binding['member_directory']+'/'+name: B.jbytes(dict(fixture=key)) for key, name in members.items()}
    pin = dict(binding, schema='h1-export-pins-v1', preparation={})
    pin['archive_sha256'] = re.search(r"^REVIEWED_ARCHIVE_SHA256 = '([^']+)'", d['a/4.py'].decode(), re.M)[1]
    files = {'policy': dict(path=logical+'/q/policy.json', bytes=len(q['q/policy.json']), sha256=B.sha(q['q/policy.json']))}
    for key, name in members.items():
        data = export_files[binding['member_directory']+'/'+name]
        pin[key] = dict(bytes=len(data), sha256=B.sha(data))
        files[key] = dict(pin[key], path=logical+'/'+binding['member_directory']+'/'+name)
    for name, data in prep.items():
        pin['preparation'][name] = dict(path='prep/'+name+'.json', source_path='/fixture/'+name,
                                       bytes=len(data), sha256=B.sha(data))
    destination = 'sj/'+str(Path(logical).relative_to('/scratch/jjyeung'))
    archives = []
    for name, contents, digest in [('export', export_files, pin['archive_sha256']),
                                  ('policy', q, '05dc8f79'+'0'*56),
                                  ('prep', {pin['preparation'][k]['path']: v for k, v in prep.items()}, None)]:
        raw = tarraw(contents)
        path = package/'a/6' if name == 'prep' else root/(name+'.tar')
        path.write_bytes(raw)
        archives.append(dict(destination=destination, sha256=digest or B.sha(raw),
                             parts=[dict(path=str(path), bytes=len(raw), sha256=B.sha(raw))]))
    export_raw = B.jbytes(pin); (package/'a/export.json').write_bytes(export_raw)
    inputs = dict(archives=archives, files=files, policy=policy, policy_receipt='policy', types=cfg['order'],
                  python=logical+'/python', frames_root=logical+'/frames', sam_source=logical+'/sam',
                  export_pin=dict(path='a/export.json', bytes=len(export_raw), sha256=B.sha(export_raw)))
    base = copy.deepcopy(inputs); base['archives'] = base['archives'][:-1]
    (package/'a/0.json').write_bytes(B.jbytes(base))
    manifest = json.loads((package/'PACKAGE.json').read_text())
    manifest['files']['a/0.json'] = B.sha((package/'a/0.json').read_bytes())
    (package/'PACKAGE.json').write_bytes(B.jbytes(manifest))
    (package/'a/1.json').write_bytes(B.jbytes(inputs))
    (package/'2.json').write_bytes(B.jbytes(dict(argv=['--job-name=a15_cot_ap'+pub['token']])))
    return package, inputs


@pytest.mark.parametrize('script', ['o_pullfill.sh', 'o_pullfill_resume.sh'])
@pytest.mark.parametrize('bad_pin', [None, 'member_bytes', 'export_sha', 'prep_sha', 'base_slot'])
def test_fill_dry_checks_fail_closed(tmp_path, source, script, bad_pin):
    package, inputs = fixture(tmp_path, source)
    if bad_pin == 'member_bytes': inputs['files']['heads']['bytes'] += 1
    if bad_pin == 'export_sha': inputs['export_pin']['sha256'] = '0'*64
    if bad_pin == 'prep_sha': inputs['archives'][-1]['sha256'] = '0'*64
    if bad_pin == 'base_slot': inputs['archives'][1]['sha256'] = '1'*64
    (package/'a/1.json').write_bytes(B.jbytes(inputs))
    e = package/'a/e'; e.mkdir()
    text = (BUILD/script).read_text()
    body = text.split("<<'SHELLCODE'\n", 1)[1].split('\nSHELLCODE\n', 1)[0]
    body = body[body.index('PREP='):]
    # Exercise the real post-fill checks and receipts. The preceding 3.py check
    # is covered separately; this fixture supplies its submission descriptor.
    command = 'CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00'
    assert body.count(command) == 1
    body = body.replace(command, 'true # submission descriptor supplied by fixture')
    result = subprocess.run(['bash', '-c', 'set -euo pipefail\n'+body],
                            env=dict(os.environ, P=str(package), E=str(e)), capture_output=True, text=True)
    resolution = json.loads((e/'dryres.json').read_text())
    assert resolution['passed'] == (bad_pin in (None, 'export_sha'))
    if bad_pin in (None, 'export_sha'):
        report = json.loads((e/'drypackage.json').read_text())
        assert report['passed'] == (bad_pin is None), report
        assert report['5.export_pins_load_validate']['ok'] == (bad_pin is None)
    assert (result.returncode == 0) == (bad_pin is None), result.stderr
    assert (e/'10.json').exists() == (bad_pin is None)
    assert (package/'a/1.txt').exists() == (bad_pin is None)


@pytest.mark.parametrize('change, failed', [
    ((b"'single_worker':False", b"'single_worker':True"), '6.worker_config_0'),
    ((b"ARMS=['tower','own']", b"ARMS=['tower']"), '6.descriptor'),
    ((b'EXPECTED=900', b'EXPECTED=636'), '6.descriptor'),
    ((b'types=[0,1,2]', b'types=[2,1,0]'), '6.types_order'),
])
def test_operator_contract(tmp_path, source, change, failed):
    package, _ = fixture(tmp_path, source, change)
    result = subprocess.run([PY36, '-I', '-s', '-B', str(KIT/'dry_own.py'), str(package), str(tmp_path/'dry')],
                            capture_output=True, text=True)
    report = json.loads(result.stdout)
    assert result.returncode == 1 and failed in report['failed'], (result.stderr, report)


def test_embedded_sources_and_local_trees(source):
    assert (KIT/'dryres2.py').read_bytes() == (KIT.parent/'dryres2.py').read_bytes()
    for name in ('o_pullfill.sh', 'o_pullfill_resume.sh'):
        text = (BUILD/name).read_text()
        assert text.count((KIT/'dryres2.py').read_text()) == 1
        assert text.count((KIT/'dry_own.py').read_text()) == 1
        assert text.index('dryres.json') < text.index('3.py check') < text.index('drypackage.json') < text.index("v=dict(passed=True")
    for name, contents in zip(('package', 'src'), source):
        tree = BUILD/name
        assert tree.is_dir() and KIT.parent in tree.resolve().parents
        assert all((tree/n).read_bytes() == raw for n, raw in contents.items())
