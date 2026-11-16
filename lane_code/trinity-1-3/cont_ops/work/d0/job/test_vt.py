"""Synthetic tests of vt.py: a valid new archive passes; extra, absent, altered, symlink, duplicate and e00-colliding members
and a wrong stream pin are refused; a new extra over an e00 member is refused."""
import copy, hashlib, io, json, subprocess, sys, tarfile, tempfile
from pathlib import Path
H = Path(__file__).resolve().parent; T = Path(tempfile.mkdtemp(dir=H / 'vt_test'))
AS = '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/'
sha = lambda b: hashlib.sha256(b).hexdigest()
fails = 0
def check(name, cond):
    global fails; fails += not cond; print('OK ' if cond else 'BAD', name)
def mktar(path, members, links=(), dirs=()):
    with tarfile.open(str(path), 'w') as t:
        for n, b in members:
            i = tarfile.TarInfo(n); i.size = len(b); t.addfile(i, io.BytesIO(b))
        for n in dirs:
            i = tarfile.TarInfo(n); i.type = tarfile.DIRTYPE; t.addfile(i)
        for n in links:
            i = tarfile.TarInfo(n); i.type = tarfile.SYMTYPE; i.linkname = '/etc/passwd'; t.addfile(i)
    return str(path)
e00 = mktar(T / 'e00', [(AS[1:] + 'ap/e84d901c/z/div.json', b'{"d":1}')])
fw = json.dumps(dict(index=dict(name='idx.json', sha256=sha(b'idx')), files=[dict(name='m1.safetensors', sha256=sha(b'w1'))])).encode()
D = 'ap/8865619b/runs/469ddece/m544/full_weights/'
good = [('ap/d0i1/m544/artifact.json', b'art'), (D + 'full_weights.json', fw), (D + 'idx.json', b'idx'), (D + 'm1.safetensors', b'w1')]
files = {'ap/d0i1/m544/artifact.json': sha(b'art'), D + 'full_weights.json': sha(fw)}
base = dict(small=dict(file=e00, sha256=sha(Path(e00).read_bytes())), a1rows=dict(dest=AS + 'ap/e84d901c/arm/r.sqlite', parts=['/x'], sha256='a'*64),
            extra=[], tars=[dict(parts=['/sealed.tar'], files={'ap/f2ad01ad/old.bin': 'b'*64})])
(T / 'sealed0.json').write_text(json.dumps(base)); S0 = sha((T / 'sealed0.json').read_bytes())
def run(name, members, links=(), entry_sha=None, extra=None, files_=None, dirs=()):
    k = T / name; (k / 'k').mkdir(parents=True)
    p = mktar(T / (name + '.tar'), members, links, dirs)
    cur = copy.deepcopy(base); e = dict(parts=[p], files=files_ or files)
    if entry_sha: e['sha256'] = entry_sha
    cur['tars'] = [dict(parts=['/sealed.tar'], files={'ap/f2ad01ad/old.bin': 'b'*64}), e]; cur['extra'] = extra or []
    (k / 'k/0.json').write_text(json.dumps(cur))
    r = subprocess.run([sys.executable, str(H / 'vt.py'), str(k), str(T / 'sealed0.json'), S0], stdout=subprocess.PIPE, text=True)
    return r.returncode, r.stdout.strip()
rc, out = run('good', good); check('valid archive passes: ' + out[:120], rc == 0 and '"PASS"' in out)
whole = sha(Path(T / 'good.tar').read_bytes())
rc, out = run('good_pin', good, entry_sha=whole); check('stream pin matches', rc == 0)
for name, args, needle in [
        ('extra_member', dict(members=good + [('ap/d0i1/evil.py', b'x')]), 'neither listed'),
        ('absent', dict(members=good[1:]), 'absent'),
        ('altered', dict(members=good[:3] + [(D + 'm1.safetensors', b'w2')]), 'differs'),
        ('symlink', dict(members=good, links=['ap/d0i1/link']), 'non-regular'),
        ('duplicate', dict(members=good + [good[0]]), 'duplicate'),
        ('e00_collision', dict(members=good + [('ap/e84d901c/z/div.json', b'{}')], files_={**files, 'ap/e84d901c/z/div.json': sha(b'{}')}), 'e00 member'),
        ('sealed_collision', dict(members=good + [('ap/f2ad01ad/old.bin', b'{}')], files_={**files, 'ap/f2ad01ad/old.bin': sha(b'{}')}), 'sealed placement'),
        ('manifest_shard_absent', dict(members=good[:3]), 'absent'),
        ('conflicting_pin', dict(members=good, files_={**files, D + 'm1.safetensors': sha(b'zz')}), 'different bytes'),
        ('dir_member', dict(members=good, dirs=['ap/8865619b/runs']), 'non-regular'),
        ('wrong_pin', dict(members=good, entry_sha='c'*64), 'stream differs'),
        ('extra_over_e00', dict(members=good, extra=[dict(dest='/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/e84d901c/z/div.json', parts=['/y'], sha256='d'*64)]), 'new extra')]:
    rc, out = run(name, **args); check(f'{name} refused: {out[:110]}', rc == 3 and needle in out)
print('FAILS', fails); sys.exit(1 if fails else 0)
