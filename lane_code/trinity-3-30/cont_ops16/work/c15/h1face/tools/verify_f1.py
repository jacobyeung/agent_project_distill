"""Capture FIX6 baselines and verify F1 CLI fixtures without external operations."""
import argparse
import base64
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tarfile
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tests'), str(ROOT/'kit/launcher')]
import offline_guard
import orchard_launcher as L

PLAN = '9fc9d1f6cbe29421d87abe0a8f47c85c934900205adc21b7ccd21a6824423a54'
INTEGRITY = {'launcher_pins', 'launcher_review', 'launcher_review_pin'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')


def payload(path):
    script = (path/'BATCH.sh').read_text()
    raw = base64.b64decode(re.search(r"raw=base64.b64decode\('([^']+)'", script).group(1))
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        return archive.extractfile('bootstrap/payload.tar.gz').read()


def cli(destination, token, families):
    argv = ['launcher', 'prepare', '--run', '673bc60f', '--namespace', '8865619b',
            '--step', '200', '--families'] + families + ['--types', 'direct',
            '--token', token, '--destination', str(destination)]
    with patch.object(sys, 'argv', argv), redirect_stdout(io.StringIO()) as output:
        L.main()
    config = load(destination/'CONFIG.json')
    L.validate_request(config)
    L.validate_payload(payload(destination), config)
    L.validate_batch((destination/'BATCH.sh').read_text(), config)
    print(output.getvalue().strip())
    return config


def guard(event, values):
    if event in ('os.remove', 'os.rmdir'):
        raise RuntimeError('Deletion forbidden')
    paths = []
    if event == 'open' and not isinstance(values[0], int):
        if values[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            paths = values[:1]
    elif event in ('os.mkdir', 'os.chmod'):
        paths = values[:1]
    elif event in ('os.rename', 'os.link', 'os.symlink'):
        paths = values[:2]
    for value in paths:
        path = Path(value).resolve()
        relative = path.relative_to(ROOT/'evidence')
        if not relative.parts[0].startswith('test_f1_'):
            raise RuntimeError('Write outside F1 fixtures: '+str(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('baseline', 'verify'))
    args = parser.parse_args()
    sys.addaudithook(guard)
    root = ROOT/'evidence/test_f1_baseline'
    original_open = Path.open
    def opened(path, mode='r', *a, **kw):
        if path == ROOT/'LEDGER.jsonl':
            path = root/'LEDGER.jsonl'
        return original_open(path, mode, *a, **kw)
    with patch.object(Path, 'open', opened):
        if args.mode == 'baseline':
            root.mkdir()
            cases = [('plan', 'a8102c3207b'), ('twins', 'a'+uuid.uuid4().hex[:10]),
                     ('all', 'a'+uuid.uuid4().hex[:10])]
            report = dict(cases=[], python=sys.version,
                          launcher_sha256=sha((ROOT/'kit/launcher/orchard_launcher.py').read_bytes()))
            for name, token in cases:
                config = cli(root/name, token, ['main', 'a7'])
                report['cases'].append(dict(name=name, token=token, plan_sha256=config['plan_sha256']))
            assert report['cases'][0]['plan_sha256'] == PLAN
            report['reader_pins'] = {str(p.relative_to(ROOT)):sha(p.read_bytes())
                                     for p in (ROOT/'kit/reader').rglob('*')
                                     if p.is_file() and '__pycache__' not in p.parts}
            dump(root/'BASELINE.json', report)
            print('FIX6_BASELINE '+json.dumps(report, sort_keys=True))
            return
        baseline = load(root/'BASELINE.json')
        assert baseline['launcher_sha256'] == sha((ROOT/'evidence/FIXF1_BEFORE_orchard_launcher.py.txt').read_bytes())
        report = dict(fixtures=[], population={}, reader_files=len(baseline['reader_pins']))
        for name, digest in baseline['reader_pins'].items():
            assert sha((ROOT/name).read_bytes()) == digest, name
        inventory = load(ROOT/'kit/reader/e193_items.json')['families']
        for family in ('away', 'forward'):
            rows = [dict(question_type=t) for t in inventory[family]['items'].values()]
            direct = L.F.population(rows, dict(types='direct'))
            full = L.F.population(rows, {})
            assert direct == full and direct['items'] == 150 and not direct['excluded']
            report['population'][family] = dict(direct=direct, unfiltered=full)
        for case in baseline['cases']:
            name, token = case['name'], case['token']
            dest = ROOT/('evidence/test_f1_'+name)
            families = {'plan':['main','a7'], 'twins':['away','forward'],
                        'all':['main','a7','away','forward']}[name]
            cfg = cli(dest, token, families)
            old = load(root/name/'CONFIG.json')
            assert payload(dest) == payload(root/name)
            assert cfg['payload_pins'] == old['payload_pins']
            assert cfg['payload_sha256'] == old['payload_sha256']
            differences = sorted(k for k in cfg if cfg[k] != old[k])
            if name == 'plan':
                assert cfg['plan_sha256'] == old['plan_sha256'] == PLAN
                assert set(differences) == INTEGRITY
            else:
                assert set(differences) == INTEGRITY | {'families','spec','plan_sha256'}
                spec_changes = {k for k in cfg['spec'] if cfg['spec'][k] != old['spec'][k]}
                assert spec_changes == {'families','population'}
            assert {k for k in cfg['launcher_pins'] if cfg['launcher_pins'][k] != old['launcher_pins'][k]} == {'orchard_launcher.py'}
            report['fixtures'].append(dict(destination=str(dest), token=token, families=families,
                plan_sha256=cfg['plan_sha256'], payload_sha256=cfg['payload_sha256'],
                payload_members=len(cfg['payload_pins']), config_differences=differences,
                validate_request='PASS', validate_payload='PASS', validate_batch='PASS',
                payload_bytes_equal=True, payload_pins_equal=True))
        audit = ROOT/'evidence/test_f1_audit'
        audit.mkdir()
        dump(audit/'AUDIT.json', report)
        print('F1_AUDIT '+json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
