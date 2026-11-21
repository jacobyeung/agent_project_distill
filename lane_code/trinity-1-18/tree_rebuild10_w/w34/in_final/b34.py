"""fix17: build kit w34 = W/w33n/n_go (929ab213) + fix16 DIFF.patch; rebuild the k/j.json shell capsule, reseal with
support.reseal, verify with the tree's launch_r1.build.verify, run the build checks.
Usage: b34.py <out kit dir> <in dir> <expected DIFF sha256>. Writes <out>/../BUILD34.json, j_old.sh, j_new.sh."""
import sys, json, shutil, hashlib, subprocess, tempfile, py_compile, base64, re
from pathlib import Path
W = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w'); OLD = W/'w33n/n_go'
NEW = Path(sys.argv[1]); IN = Path(sys.argv[2]); DSHA = sys.argv[3]; OUT = NEW.parent
sys.path[:0] = [str(W/'w24z11b/work/build24m4x2')]
from support import J, reseal
OLDSEAL = '929ab2139b6dd408972e7b5bcffcf00588f70cecb006f6f9c0da44c55825dc57'
out = dict(python=sys.version.split()[0], new=str(NEW))
assert J.seal(OLD) == OLDSEAL and J.load(OLD/'BUILD.json')['kit_sha256'] == OLDSEAL
out['old_seal_929ab213_checked'] = True
P = IN/'DIFF.patch'; out['diff_sha256'] = J.sha(P); assert out['diff_sha256'] == DSHA, 'DIFF sha differs'
hdr = {}
for line in P.read_text().splitlines():
    m = re.match(r'#\s+(\S+(?: decoded)?)(?: \(.*\))? ([0-9a-f]{64}) -> ([0-9a-f]{64})$', line)
    if m: hdr[m.group(1)] = (m.group(2), m.group(3))
out['diff_header'] = hdr
assert not NEW.exists(), str(NEW) + ' exists'
shutil.copytree(OLD, NEW, copy_function=shutil.copy2)
# split the DIFF into file sections
sec, cur = {}, None
for line in P.read_text().splitlines(keepends=True):
    if line.startswith('--- a/'): cur = line[6:].split()[0]; sec[cur] = [line]; continue
    if cur: sec[cur].append(line)
out['diff_sections'] = sorted(sec)
def capsule(raw):
    # the kit's raw-payload capsule: json.dumps(dict(encoding, payload, sha256), sort_keys=True) + newline
    return (json.dumps(dict(encoding='base64', payload=base64.b64encode(raw).decode(), sha256=hashlib.sha256(raw).hexdigest()), sort_keys=True) + '\n').encode()
oldj = json.loads((OLD/'k/j.json').read_text()); old_sh = base64.b64decode(oldj['payload'], validate=True)
assert oldj['encoding'] == 'base64' and hashlib.sha256(old_sh).hexdigest() == oldj['sha256']
out['j_capsule_writer_reproduces_929ab213_bytes'] = capsule(old_sh) == (OLD/'k/j.json').read_bytes(); assert out['j_capsule_writer_reproduces_929ab213_bytes']
(OUT/'j_old.sh').write_bytes(old_sh)
pr = {}
with tempfile.TemporaryDirectory() as t:
    t = Path(t); (t/'j.sh').write_bytes(old_sh)
    jp = ''.join(sec['k/j.json:decoded']).replace('--- a/k/j.json:decoded', '--- a/j.sh', 1).replace('+++ b/k/j.json:decoded', '+++ b/j.sh', 1)
    (t/'j.patch').write_text(jp)
    r = subprocess.run(['patch', '-p1', '-F0', '--no-backup-if-mismatch', '-d', str(t), '-i', str(t/'j.patch')], capture_output=True, text=True)
    pr['k/j.json:decoded'] = (r.returncode, r.stdout.strip()); assert r.returncode == 0
    new_sh = (t/'j.sh').read_bytes()
    for name in ('b/a.py', 'b/pf.py'):
        (t/'c.patch').write_text(''.join(sec[name]))
        r = subprocess.run(['patch', '-p1', '-F0', '--no-backup-if-mismatch', '-d', str(NEW), '-i', str(t/'c.patch')], capture_output=True, text=True)
        pr[name] = (r.returncode, r.stdout.strip()); assert r.returncode == 0
out['patch_runs'] = pr
out['patch_offset_or_fuzz'] = any(('offset' in v[1] or 'fuzz' in v[1]) for v in pr.values())
(OUT/'j_new.sh').write_bytes(new_sh)
mode = (OLD/'k/j.json').stat().st_mode & 0o777
(NEW/'k/j.json').write_bytes(capsule(new_sh)); (NEW/'k/j.json').chmod(mode)
chk = json.loads((NEW/'k/j.json').read_text()); assert hashlib.sha256(base64.b64decode(chk['payload'], validate=True)).hexdigest() == chk['sha256'] == hashlib.sha256(new_sh).hexdigest()
out['j_method'] = 'raw capsule writer (reproduces 929ab213 k/j.json byte for byte from its decoded payload); hash computed, not edited'
out['j_decoded_sha256'] = hashlib.sha256(new_sh).hexdigest(); out['j_json_sha256'] = J.sha(NEW/'k/j.json')
out['j_bash_n_rc'] = subprocess.run(['bash', '-n', str(OUT/'j_new.sh')]).returncode
out['j_old_bash_n_rc'] = subprocess.run(['bash', '-n', str(OUT/'j_old.sh')]).returncode
seal = reseal(NEW); out['seal'] = seal
sys.path.insert(0, str(W/'w30f1/tree'))
from launch_r1.build import verify
out['verify_kit_tree_equals_seal'] = verify(NEW) == seal
out['zseal_equals'] = J.seal(NEW) == seal
def inv(k): return {str(p.relative_to(k)): (J.sha(p), oct(p.stat().st_mode & 0o777)) for p in sorted(k.rglob('*')) if p.is_file()}
a, b = inv(OLD), inv(NEW)
out['members_added'] = sorted(set(b) - set(a)); out['members_removed'] = sorted(set(a) - set(b))
out['changed_vs_929ab213'] = {n: dict(old=a.get(n, [None])[0], new=b[n][0], mode_old=a.get(n, [None, None])[1], mode_new=b[n][1]) for n in b if a.get(n) != b[n]}
T = 'k/t_e047002134f979bd.tar'
want = {T: '5f2d77c4', 'k/c.json': '76de3706', 'k/n.json': '4b8b9533', 'k/p.json': '77525f28', 'k/y.json': '9ce25396'}
out['pins'] = {n: b[n][0] for n in want}
out['pins_unchanged_and_expected'] = {n: a[n] == b[n] and b[n][0].startswith(p) for n, p in want.items()}
# against fix16's stated bytes
cand = IN/'cand'
out['equal_fix16'] = {'k/j.json': b['k/j.json'][0] == J.sha(cand/'k/j.json') == hdr['k/j.json'][1],
                      'k/j.json decoded': out['j_decoded_sha256'] == hashlib.sha256((cand/'j.sh').read_bytes()).hexdigest() == hdr['k/j.json decoded'][1],
                      'b/a.py': b['b/a.py'][0] == J.sha(cand/'b/a.py') == hdr['b/a.py'][1],
                      'b/pf.py': b['b/pf.py'][0] == J.sha(cand/'b/pf.py') == hdr['b/pf.py'][1],
                      'old members': all(a[n][0] == hdr[n][0] for n in ('k/j.json', 'b/a.py', 'b/pf.py')),
                      'SHA256SUMS.txt == fix16 expected': (NEW/'SHA256SUMS.txt').read_bytes() == (cand/'SHA256SUMS.expected.txt').read_bytes(),
                      'seal == fix16 expected 7e23bbdd': seal == '7e23bbddb052a6f3ddb1915858dc03e8951d35d87cc9a3cd276f8853414d5771'}
bj = J.load(NEW/'BUILD.json'); ob = J.load(OLD/'BUILD.json'); out['BUILD'] = bj
out['BUILD_only_kit_sha256_changed'] = {k: v for k, v in bj.items() if k != 'kit_sha256'} == {k: v for k, v in ob.items() if k != 'kit_sha256'}
pc = {}
with tempfile.TemporaryDirectory() as t:
    for p in sorted((NEW/'b').glob('*.py')):
        try: py_compile.compile(str(p), cfile=str(Path(t)/(p.name + 'c')), doraise=True); pc[p.name] = 'ok'
        except py_compile.PyCompileError as e: pc[p.name] = 'FAIL ' + str(e)[:300]
out['py_compile_count'] = len(pc); out['py_compile'] = pc; out['py_compile_all_ok'] = all(v == 'ok' for v in pc.values())
out['bash_n'] = {str(p.relative_to(NEW)): subprocess.run(['bash', '-n', str(p)]).returncode for p in sorted(NEW.rglob('*.sh'))}
out['pycache_in_kit'] = sorted(str(p) for p in NEW.rglob('__pycache__'))
(OUT/'BUILD34.json').write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
print(json.dumps(out, indent=1, sort_keys=True))
