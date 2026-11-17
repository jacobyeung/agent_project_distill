"""Repin only the terminator in the existing, authenticated H1-0 package.

Run from K with: bash cpu.sh -m orchard_h10.repin_terminator
The script requires the original package and a fresh backup/proof destination.
"""
import copy
import hashlib
import json
from pathlib import Path
import runpy
import sys
import tarfile

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from orchard_h10.build import K, T, batch
from orchard_h10.common import canonical, opaque, sha, template, write

OLD = b'cbb91ba7455d15007bd3affeb358dc5693f3845949ee0abacf892a4402748b94'
NEW = b'19727987d5517c0e2549e1205e55f4bcc87f34dafe66c96bdf90233305942e5d'
EXPECTED = '4847ad12194edae7f3d573baef4bff8120db89b4495e7e54bcf474d5caf90676'
ASSET = 'orchard_h10/vendor/ORCHARD_ASSETS.json'
TOKEN = 'b01ec87a6f29b'


def members(path):
    with tarfile.open(path) as archive:
        entries = archive.getmembers()
        assert all(e.isfile() for e in entries)
        assert len({e.name for e in entries}) == len(entries)
        return {e.name: archive.extractfile(e).read() for e in entries}


def render(destination, payload, cfg):
    template(T)
    import orchard_launcher as L
    assert (T/'orchard_launcher.py').read_bytes() == payload['orchard_h10/vendor/orchard_launcher.py']
    destination.mkdir(parents=True, exist_ok=False)
    token = cfg['token']
    plan=canonical(cfg)
    payload['9.json']=json.dumps(cfg,sort_keys=True).encode()
    raw=L.tar_bytes(payload)
    if len(raw)>8*1024**2:raise ValueError('Code archive exceeds local allowance')
    (destination/'0.tgz').write_bytes(raw)
    public=dict(token=token,payload_sha256=sha(destination/'0.tgz'),payload_bytes=len(raw),plan_sha256=plan)
    boot=("import sys,json,hashlib,tarfile\nfrom pathlib import Path\n"
          "r=Path(sys.argv[1]);c=json.loads((r/'0.json').read_text())\n"
          "a=Path('/project/community/jjyeung')/c['token']/'0.tgz'\n"
          "assert hashlib.sha256(a.read_bytes()).hexdigest()==c['payload_sha256']\n"
          "with tarfile.open(a) as t:\n"
          " for e in t:\n"
          "  if not e.name.startswith('orchard_h10/'):continue\n"
          "  if not e.isfile() or '..' in Path(e.name).parts:raise ValueError('Unsafe input')\n"
          "  p=r/'p'/e.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.extractfile(e).read())\n"
          "sys.path.insert(0,str(r/'p'))\nfrom orchard_h10.job import main\nmain(r)\n").encode()
    bundle=L.tar_bytes({'0.py':boot,'0.json':json.dumps(public).encode()})
    (destination/'BATCH.sh').write_text(batch(bundle,token))
    write(destination/'CONFIG.json',public)
    (destination/'SUBMIT.cmd').write_text('#!/bin/bash\nset -euo pipefail\ncd "$(dirname "$0")"\n'
        'exec /usr/bin/python3 -I -s -B 3.py submit --gpus "${A_N:?Set 1 to 4}" --time "${A_T:?Set HH:MM:SS}" "$@"\n')
    helper="""import hashlib,json,tarfile
from pathlib import Path
p=Path(__file__).resolve().parent
c=json.loads((p/'0.json').read_text())
assert hashlib.sha256((p/'0.tgz').read_bytes()).hexdigest()==c['payload_sha256']
with tarfile.open(p/'0.tgz') as t:
    exec(compile(t.extractfile('8.py').read(),__file__,'exec'))
"""
    opaque([helper]);(destination/'3.py').write_text(helper)
    write(destination/'INPUTS.example.json',dict(schema=1,archives=[],files={},python=None,
        policy=dict(vnice=None,terminator=None),resume=None,
        note='Fill and pin on Orchard; do not submit this unresolved example.'))
    (destination/'0.json').write_text(json.dumps(public,sort_keys=True)+'\n')
    write(destination/'PACKAGE.json',dict(token=token,files={n:sha(destination/n) for n in
          ('0.tgz','BATCH.sh','CONFIG.json','3.py','0.json')}))
    for path in destination.iterdir():
        if path.is_file() and path.name!='0.tgz':opaque([path.name,path.read_text()])
    return public


def main():
    package = K/'orchard_h10/package'
    backup = K/'orchard_h10/package_cbb91ba7'
    proof = K/'tmp/t10/repin'
    assert not backup.exists(), 'Refuse to overwrite the original backup'
    assert not proof.exists(), 'Require a fresh proof directory'
    assert sha(package/'0.tgz') == EXPECTED
    original = {p.name: p.read_bytes() for p in package.iterdir() if p.is_file()}
    assert len(original) == 8
    old = members(package/'0.tgz')
    cfg = json.loads(old['9.json'])
    assert cfg['token'] == TOKEN
    assert old['9.json'] == json.dumps(cfg, sort_keys=True).encode()
    payload = {n: raw for n, raw in old.items() if n != '9.json'}
    for n, raw in payload.items():
        assert cfg['payload_pins'][n] == dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
    selftest = proof/'selftest'
    render(selftest, dict(payload), copy.deepcopy(cfg))
    assert sha(selftest/'0.tgz') == EXPECTED
    assert (selftest/'PACKAGE.json').read_bytes() == original['PACKAGE.json']
    assert all((selftest/n).read_bytes() == raw for n, raw in original.items())
    print('No-replacement self-test: all eight files reproduce byte-for-byte', flush=True)
    assert payload[ASSET].count(OLD) == 1
    payload[ASSET] = payload[ASSET].replace(OLD, NEW, 1)
    updated = copy.deepcopy(cfg)
    updated['payload_pins'][ASSET] = dict(sha256=hashlib.sha256(payload[ASSET]).hexdigest(), bytes=len(payload[ASSET]))
    staged = proof/'new'
    public = render(staged, dict(payload), updated)
    new = members(staged/'0.tgz')
    assert new.keys() == old.keys()
    changed = [n for n in old if old[n] != new[n]]
    assert set(changed) == {ASSET, '9.json'}
    restored = copy.deepcopy(json.loads(new['9.json']))
    restored['payload_pins'][ASSET] = cfg['payload_pins'][ASSET]
    assert restored == cfg
    assert public['plan_sha256'] == canonical(updated)
    backup.mkdir()
    for n, raw in original.items():
        (backup/n).write_bytes(raw)
    for p in staged.iterdir():
        (package/p.name).write_bytes(p.read_bytes())
    mapping = K/'orchard_h10/TOKENS.json'
    tokens = json.loads(mapping.read_text())
    tokens[TOKEN] = dict(package=str(package.relative_to(K)), meaning='step-544 own dev-S1; registered modes; five ordered types')
    expected_tokens = json.dumps(tokens, sort_keys=True, indent=2, allow_nan=False)+'\n'
    tokens_changed = mapping.read_text() != expected_tokens
    if tokens_changed:
        write(mapping, tokens)
    # Execute 3.py exactly as a loader, without invoking its command-line action.
    helpers = runpy.run_path(str(package/'3.py'), run_name='repin_check')
    loaded = helpers['load_helpers'](package)
    from orchard_h10.job import verify_config
    verify_config(loaded)
    assert loaded['plan_sha256'] == public['plan_sha256']
    for p in package.iterdir():
        if p.name != '0.tgz':
            opaque([p.name, p.read_text()])
    record = dict(old=dict(sha256=EXPECTED, bytes=len(original['0.tgz']),
                          plan_sha256=json.loads(original['0.json'])['plan_sha256'],
                          package_sha256=hashlib.sha256(original['PACKAGE.json']).hexdigest()),
                  new=dict(sha256=sha(package/'0.tgz'), bytes=(package/'0.tgz').stat().st_size,
                           plan_sha256=public['plan_sha256'], package_sha256=sha(package/'PACKAGE.json')),
                  members=len(old), unchanged_payload_members=len(old)-2, changed_members=changed,
                  changed_public_files=[n for n, raw in original.items() if (package/n).read_bytes() != raw],
                  tokens_changed=tokens_changed, old_files=json.loads(original['PACKAGE.json'])['files'],
                  new_files=json.loads((package/'PACKAGE.json').read_text())['files'],
                  no_replacement_selftest='all eight files byte-identical',
                  helpers_and_config='passed', public_opacity='passed')
    write(proof/'verification.json', record)
    print(json.dumps(record, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
