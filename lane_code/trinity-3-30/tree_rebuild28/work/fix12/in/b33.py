"""fix12: build a merged kit from W/w30f1/n_go (489f7f0f) + fix10 census diff + fix11 frame diff (+ any later
overlay listed in overlay.json), reseal with support.reseal, verify with the tree's launch_r1.build.verify, run checks.
Usage: b33.py <out kit dir> <in dir>. Writes <out>/../BUILD33.json."""
import sys, json, shutil, hashlib, subprocess, tempfile, py_compile
from pathlib import Path
W = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w'); OLD = W/'w30f1/n_go'; OLDEST = W/'w28fix/n_go'
NEW = Path(sys.argv[1]); IN = Path(sys.argv[2]); OUT = NEW.parent
sys.path[:0] = [str(W/'w24z11b/work/build24m4x2')]
from support import J, cap, reseal
OLDSEAL = '489f7f0fbfb9913066d0840bde40d01fc30927d2d127709e41bb479e554e2e90'
out = dict(python=sys.version.split()[0])
assert J.seal(OLD) == OLDSEAL and J.load(OLD/'BUILD.json')['kit_sha256'] == OLDSEAL
out['old_seal_489f7f0f_checked'] = True
assert not NEW.exists(), str(NEW) + ' exists'
shutil.copytree(OLD, NEW, copy_function=shutil.copy2)
ov = json.loads((IN/'overlay.json').read_text())
# overlay: member -> {src, sha256 (expected new bytes), old (expected old bytes or null for a new file)}
for name, e in sorted(ov.items()):
    if name == 'k/j.json':
        continue
    src = IN/e['src']; assert J.sha(src) == e['sha256'], name
    if e.get('old'): assert J.sha(OLD/name) == e['old'], name + ' old'
    else: assert not (OLD/name).exists(), name + ' expected new'
    if (NEW/name).exists(): shutil.copyfile(src, NEW/name)   # keeps the member's mode
    else:
        shutil.copyfile(src, NEW/name); (NEW/name).chmod((NEW/e['mode_from']).stat().st_mode & 0o777)
# k/j.json: capsule of the patched inner shell, written with the kit's own capsule tool
e = ov['k/j.json']; new_sh = (IN/e['src']).read_bytes(); assert hashlib.sha256(new_sh).hexdigest() == e['decoded_sha256']
try:
    old_obj = J.load(OLD/'k/j.json'); out['j_load_type'] = type(old_obj).__name__
    with tempfile.TemporaryDirectory() as t:
        cap(Path(t)/'x.json', old_obj); out['j_cap_roundtrip'] = (Path(t)/'x.json').read_bytes() == (OLD/'k/j.json').read_bytes()
    assert out['j_cap_roundtrip']
    newval = new_sh if isinstance(old_obj, bytes) else new_sh.decode()
    cap(NEW/'k/j.json', newval); out['j_method'] = 'support.cap'
except Exception as err:
    # fallback: fix11's tested capsule, accepted only if its decoded payload is our patched shell
    out['j_cap_error'] = type(err).__name__ + ': ' + str(err)[:200]
    import base64
    f11 = json.loads((W/'w32frm/n_go/k/j.json').read_text())
    assert hashlib.sha256(base64.b64decode(f11['payload'])).digest() == hashlib.sha256(new_sh).digest()
    shutil.copyfile(W/'w32frm/n_go/k/j.json', NEW/'k/j.json'); out['j_method'] = 'fix11 capsule, decoded payload checked'
out['j_json_sha256'] = J.sha(NEW/'k/j.json'); out['j_json_equals_fix11_w32frm'] = J.sha(NEW/'k/j.json') == J.sha(W/'w32frm/n_go/k/j.json')
out['j_decoded_sha256'] = json.loads((NEW/'k/j.json').read_text())['sha256']
(OUT/'j_merged.sh').write_bytes(new_sh)
out['j_bash_n_rc'] = subprocess.run(['bash', '-n', str(OUT/'j_merged.sh')]).returncode
seal = reseal(NEW); out['seal'] = seal
sys.path.insert(0, str(W/'w30f1/tree'))
from launch_r1.build import verify
out['verify_kit_tree_equals_seal'] = verify(NEW) == seal
out['zseal_equals'] = J.seal(NEW) == seal
def inv(k): return {str(p.relative_to(k)): (J.sha(p), oct(p.stat().st_mode & 0o777)) for p in sorted(k.rglob('*')) if p.is_file()}
a, b, c = inv(OLD), inv(NEW), inv(OLDEST)
out['members_added'] = sorted(set(b) - set(a)); out['members_removed'] = sorted(set(a) - set(b))
out['changed_vs_489f7f0f'] = {n: dict(old=a.get(n, [None])[0], new=b[n][0], mode_old=a.get(n, [None, None])[1], mode_new=b[n][1]) for n in b if a.get(n) != b[n]}
out['changed_vs_9e809db4'] = {n: dict(old=c.get(n, [None])[0], new=b[n][0], mode_old=c.get(n, [None, None])[1], mode_new=b[n][1]) for n in sorted(set(b) | set(c)) if c.get(n) != b.get(n)}
out['oldest_seal'] = J.seal(OLDEST)
T = 'k/t_e047002134f979bd.tar'
out['pins'] = {n: b[n][0] for n in (T, 'k/c.json', 'k/n.json', 'k/p.json', 'k/y.json', 'k/c0.json')}
out['unchanged_vs_f1'] = {n: a[n] == b[n] for n in (T, 'k/c.json', 'k/n.json', 'k/p.json', 'k/y.json', 'k/c0.json')}
out['y_unchanged_vs_9e809db4'] = c['k/y.json'] == b['k/y.json']
bj = J.load(NEW/'BUILD.json'); out['BUILD'] = bj; out['config_sha256_eq_cjson'] = bj.get('config_sha256') == b['k/c.json'][0]
# merged members equal the tested builds of fix10 / fix11
eq = {}
for n, src in (('b/cn.py', 'w31cen'), ('b/sc.py', 'w31cen'), ('b/pf.py', 'w32frm'), ('k/j.json', 'w32frm')):
    eq[n + '==' + src] = b[n] == inv(W/src/'n_go')[n]
out['equal_to_tested'] = eq
# py_compile every b/*.py to a temp dir (no __pycache__ in the kit); bash -n every *.sh
pc = {}
with tempfile.TemporaryDirectory() as t:
    for p in sorted((NEW/'b').glob('*.py')):
        try: py_compile.compile(str(p), cfile=str(Path(t)/(p.name + 'c')), doraise=True); pc[p.name] = 'ok'
        except py_compile.PyCompileError as e: pc[p.name] = 'FAIL ' + str(e)[:300]
out['py_compile'] = pc; out['py_compile_all_ok'] = all(v == 'ok' for v in pc.values())
out['bash_n'] = {str(p.relative_to(NEW)): subprocess.run(['bash', '-n', str(p)]).returncode for p in sorted(NEW.rglob('*.sh'))}
out['pycache_in_kit'] = sorted(str(p) for p in NEW.rglob('__pycache__'))
(OUT/'BUILD33.json').write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
print(json.dumps(out, indent=1, sort_keys=True))
