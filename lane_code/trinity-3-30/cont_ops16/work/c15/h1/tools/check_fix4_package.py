"""Verify deterministic local artifacts and retained identity without Git or deletion."""
import base64, hashlib, io, json, os, subprocess, sys, tarfile
from pathlib import Path

H = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(H / 'tools'))
import derive_kit_h1 as dk
load = lambda n: json.loads((H / n).read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
out = H / 'evidence/fix4'
ids = load('ids.json'); before = load('evidence/fix4_before/hashes.json')
assert ids == load('evidence/fix4_before/ids.json')
for name in ('ids.json', 'TOKENS_H1.json', 'tests/RERUN_CHAIN.sh', 'runtime/jb.sh',
             'payload/jb.sh', 'payload/7.json', 'payload/4.json', 'payload/over.json'):
    assert sha(H / name) == before[name], name
subprocess.run([sys.executable, '-B', 'tools/make_deriver.py'], cwd=H, check=True)
assert sha(H / 'tools/derive_kit_h1.py') == sha(H / 'payload/d.py')
# Rebuild the trainer from its pinned local tree and exact archive metadata.
archive = out / 'trainer_rebuilt.tar'
with tarfile.open(archive, 'x') as tf:
    for p in sorted((H / 'build/tree').rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts: continue
        name = str(p.relative_to(H / 'build/tree'))
        m = tarfile.TarInfo(name); m.size = p.stat().st_size
        m.mode = 0o755 if os.access(p, os.X_OK) else 0o644
        tf.addfile(m, io.BytesIO(p.read_bytes()))
assert sha(archive) == ids['trainer']['sha256']
over = load('build/over_fx.json')
derived = []
for i in range(2):
    p = out / ('fixture_' + str(i))
    r = dk.derive('/scratch/jjyeung/orch_n30/review_h1pkt/work/d0/kitfull', p, over)
    assert r['config_identity'] == ids['identity']
    assert r['manifest_sha256'] == ids['fixture_manifest']
    assert (p / 'SHA256SUMS.txt').read_bytes() == (H / 'build/fx/SHA256SUMS.txt').read_bytes()
    derived.append(r)
assert derived[0] == derived[1]
# Two complete transport builds must have exactly the same bytes.
digests = []
for _ in range(2):
    subprocess.run([sys.executable, '-B', 'tools/make_orchard.py'], cwd=H, check=True)
    up = load('UPLOAD.json')
    digests.append({n: sha(H / n) for n in ('UPLOAD.json', 'orch_h1.sh', 'payload/sums.txt')})
    assert sha(H / 'build' / up['archive']) == up['sha256']
assert digests[0] == digests[1]
with tarfile.open(H / 'build' / up['archive']) as tf:
    names = []
    for m in tf:
        names.append(m.name)
        assert m.isfile() and m.mode == 0o600
        assert (m.uid, m.gid, m.uname, m.gname, m.mtime) == (0, 0, '', '', 0)
        assert tf.extractfile(m).read() == (H / 'payload' / m.name).read_bytes()
    assert names == sorted(names)
script = (H / 'orch_h1.sh').read_text()
encoded = script.split("<<'B64'\n", 1)[1].split('\nB64\n', 1)[0]
assert hashlib.sha256(base64.b64decode(encoded)).hexdigest() == up['sha256']
assert "echo 'target exists'" in script
subprocess.run(['sha256sum', '-c', 'sums.txt'], cwd=H / 'payload', check=True, stdout=subprocess.DEVNULL)
result = dict(status='PASS', trainer_rebuild=ids['trainer']['sha256'],
              fixture_manifest=ids['fixture_manifest'], identity=ids['identity'], contract=ids['contract'],
              ids_unchanged=True, wrapper_unchanged=True, chain_runner_unchanged=True,
              repeated_upload=up['sha256'], upload_metadata='PASS', embedded_transport='PASS', sums='PASS')
(out / 'package.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
