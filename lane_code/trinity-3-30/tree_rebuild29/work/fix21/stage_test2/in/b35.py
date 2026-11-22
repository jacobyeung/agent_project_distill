"""fix21: build kit w35 = kit 7e23bbdd + T-mil tree + milestones [100, 200] + init links (b/il.py) + disk plan checks
(b/dp.py) in the inner shell k/j.json. Usage: b35.py <base kit> <out kit (new)> <tree35 dir> <in dir>
Every capsule is rewritten by the writer that reproduces its base bytes (support.cap form). Writes <out>/../BUILD35.json."""
import sys, json, shutil, hashlib, base64, subprocess, tempfile, py_compile, copy
from pathlib import Path
BASE, NEW, TD, IN = (Path(a).resolve() for a in sys.argv[1:5]); OUT = NEW.parent
BASESEAL = '7e23bbddb052a6f3ddb1915858dc03e8951d35d87cc9a3cd276f8853414d5771'
OLD_TAR = 'k/t_e047002134f979bd.tar'; OLD_C0 = '53faadaa0fe7f198369ecc2cd15a01a663cf26e968ffdca6dea686fece36b47e'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def capraw(v): return (json.dumps(v, sort_keys=True, indent=2) + '\n').encode()
def cap(v):
    raw = capraw(v)
    return (json.dumps(dict(encoding='base64-json', payload=base64.b64encode(raw).decode(), sha256=hashlib.sha256(raw).hexdigest())) + '\n').encode()
def load(p):
    c = json.loads(Path(p).read_text()); raw = base64.b64decode(c['payload'], validate=True)
    assert hashlib.sha256(raw).hexdigest() == c['sha256']; return json.loads(raw)
def seal_of(k): return sha(k/'SHA256SUMS.txt')
out = {}
assert seal_of(BASE) == BASESEAL; out['base_seal_7e23bbdd_checked'] = True
t35 = json.loads((TD/'TREE35.json').read_text()); TAR = Path(t35['new_tar']); assert sha(TAR) == t35['new_tar_sha256']
NEWSEAL, NEWTARSHA = t35['new_seal'], t35['new_tar_sha256']; NEWTARNAME = 'k/t_' + NEWSEAL[:16] + '.tar'
out['tree'] = dict(seal=NEWSEAL, tar=NEWTARNAME, tar_sha256=NEWTARSHA, changed=t35['changed'])
assert not NEW.exists()
shutil.copytree(BASE, NEW, copy_function=shutil.copy2, ignore=lambda d, names: [n for n in names if Path(d, n) == BASE/OLD_TAR])
shutil.copy2(TAR, NEW/NEWTARNAME); (NEW/NEWTARNAME).chmod((BASE/OLD_TAR).stat().st_mode & 0o777)
for name in ('k/c.json', 'k/n.json', 'k/p.json', 'k/a.json', 'k/7.json', 'k/c0.json', 'BUILD.json'):
    assert cap(load(BASE/name)) == (BASE/name).read_bytes(), name
out['capsule_writer_reproduces_base'] = True
INV = {}
for side in ('old', 'new'):
    r = subprocess.run([sys.executable, '-I', '-c', 'import sys,json;sys.path.insert(0,sys.argv[1]);'
        'from student_pilot.source_seal import inventory;from student_pilot.p3_provenance import digest;'
        'f=inventory(sys.argv[1]);print(json.dumps(dict(files=f,seal=digest(f))))', str(TD/side)], capture_output=True, text=True, check=True)
    INV[side] = json.loads(r.stdout)
assert INV['old']['seal'] == '9d2bbb8ad209d91e21e56121785f62b0dddf3c8d9f14db8d23daf6dcd1d3591b' and INV['new']['seal'] == NEWSEAL
CHANGED = sorted(k for k in set(INV['old']['files']) | set(INV['new']['files']) if INV['old']['files'].get(k) != INV['new']['files'].get(k))
assert CHANGED == sorted(t35['changed']) and all(k in INV['old']['files'] and k in INV['new']['files'] for k in CHANGED), CHANGED
out['tree']['changed_files'] = {k: [INV['old']['files'][k], INV['new']['files'][k]] for k in CHANGED}
def recode(code, archive):
    code = copy.deepcopy(code)
    assert code['tree_sha256'] == INV['old']['seal'] and code['files'] == INV['old']['files']
    for f in CHANGED:
        code['files'][f] = INV['new']['files'][f]
        for k in ('sources', 'operation_sources'):
            if f in code[k]: assert code[k][f] == INV['old']['files'][f]; code[k][f] = INV['new']['files'][f]
    code.update(tree_sha256=NEWSEAL, commit='sha256:' + NEWSEAL, archive=archive)
    assert code['files'] == INV['new']['files']
    return code
# k/7.json (the kit config's code record) and k/c0.json (the job's source_code.json)
c7 = load(BASE/'k/7.json'); assert c7['archive'] == dict(path=OLD_TAR, sha256='5f2d77c4bc9905d877a259b666ac4a7fa6005de538730b806ceb249468699e38')
n7 = recode(c7, dict(path=NEWTARNAME, sha256=NEWTARSHA)); (NEW/'k/7.json').write_bytes(cap(n7))
c0 = load(BASE/'k/c0.json'); assert hashlib.sha256(capraw(c0)).hexdigest() == OLD_C0
n0 = recode(c0, dict(c0['archive'], sha256=NEWTARSHA)); (NEW/'k/c0.json').write_bytes(cap(n0))
C0SHA = hashlib.sha256(capraw(n0)).hexdigest(); C0BYTES = len(capraw(n0))
(OUT/('u_' + C0SHA)).write_bytes(capraw(n0))
out['code_records'] = dict(k7_json=sha(NEW/'k/7.json'), c0_decoded_sha256=C0SHA, c0_decoded_bytes=C0BYTES,
    install_upload=f'X/n/u/{C0SHA} (bytes of {OUT}/u_{C0SHA})', note='p.json uploads entry replaces 53faadaa; that file must be on X/n/u before the job stages')
# k/a.json source
a = load(BASE/'k/a.json'); a['source'] = dict(path=NEWTARNAME, sha256=NEWTARSHA, tree_sha256=NEWSEAL); (NEW/'k/a.json').write_bytes(cap(a))
# k/p.json code record pins
p = load(BASE/'k/p.json'); assert p['code_sha256'] == OLD_C0
p['code_sha256'] = C0SHA
pp = p['pin_paths']; assert pp.pop(OLD_C0) == p['namespace'] + '/u/' + OLD_C0; pp[C0SHA] = p['namespace'] + '/u/' + C0SHA
p['pin_paths'] = dict(sorted(pp.items()))
idx = [i for i, u in enumerate(p['uploads']) if u['sha256'] == OLD_C0]; assert len(idx) == 1
p['uploads'][idx[0]] = dict(bytes=C0BYTES, opaque_name='u/' + C0SHA, sha256=C0SHA)
(NEW/'k/p.json').write_bytes(cap(p))
# configs: milestones [100, 200] top level and recipe, plan exports 3, code pins; nothing else
MS = [100, 200]
def reconfig(cfg, code):
    cfg = copy.deepcopy(cfg)
    assert cfg['milestones'] == cfg['recipe']['milestones'] == [100, 200, 400, 600, 800, 1000]
    assert cfg['checkpoint_disk_guard'] == dict(extra_full_states=2, planned_full_states=14, planned_weight_exports=7, reserve_bytes=200000000000, retained_archive_copies=1)
    cfg['milestones'] = list(MS); cfg['recipe']['milestones'] = list(MS)
    cfg['checkpoint_disk_guard'] = dict(cfg['checkpoint_disk_guard'], planned_weight_exports=3)
    cfg['code'] = code; return cfg
c = load(BASE/'k/c.json'); c2 = reconfig(c, dict(path='k/7.json', sha256=sha(NEW/'k/7.json'))); (NEW/'k/c.json').write_bytes(cap(c2))
n = load(BASE/'k/n.json'); assert n['code'] == dict(path='u/' + OLD_C0, sha256=OLD_C0)
n2 = reconfig(n, dict(path='u/' + C0SHA, sha256=C0SHA)); (NEW/'k/n.json').write_bytes(cap(n2))
out['config_keys_changed'] = {'k/c.json': sorted(k for k in set(c) | set(c2) if c.get(k) != c2.get(k)),
                              'k/n.json': sorted(k for k in set(n) | set(n2) if n.get(k) != n2.get(k))}
out['recipe_keys_changed'] = sorted(k for k in c['recipe'] if c['recipe'][k] != c2['recipe'][k])
# inner shell
jc = json.loads((BASE/'k/j.json').read_text()); jsh = base64.b64decode(jc['payload'], validate=True).decode()
assert hashlib.sha256(jsh.encode()).hexdigest() == jc['sha256'] == '9f7a02bb958028e52a3ae177e43e0db21a3d006eed2c82c0adb7a7d2add47bc8'
def jcap(raw): return (json.dumps(dict(encoding='base64', payload=base64.b64encode(raw).decode(), sha256=hashlib.sha256(raw).hexdigest()), sort_keys=True) + '\n').encode()
assert jcap(jsh.encode()) == (BASE/'k/j.json').read_bytes()
def rep(s, a, b):
    assert s.count(a) == 1, a; return s.replace(a, b)
PRE = '''if [[ "${Q_MODE:-q}" != r ]]; then
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/g.py"
fi
'''
jsh = rep(jsh, PRE, '''# Whole-leg disk plan right after staging: the tree's own plan on the kit configuration against the free space of
# the job folder's filesystem (the run output's); free must exceed the plan by 300 GB.
if [[ "${Q_MODE:-q}" != r ]]; then
set +e
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/dp.py" preflight "$Q_KIT" "$Q_NS" 300000000000 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/dp.log"
rc=${PIPESTATUS[0]}
set -e
tk_step "disk plan after staging rc=$rc: $(tail -n 1 "$Q_ROOT/dp.log" | cut -c1-900)"
if [[ "$rc" != 0 ]]; then exit "$rc"; fi
fi
''' + PRE)
TRAIN = '''if [[ "$rc" == 0 ]]; then
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/t.py"'''
jsh = rep(jsh, TRAIN, '''# Ranks 1-3 read the init artifact's own weight and head paths under the mount's runs folder: link them to the
# staged copies named by the persisted-file map (b/il.py), then recheck the disk plan on the job configuration.
if [[ "$rc" == 0 ]]; then
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/il.py" "$Q_NS/v.json" "$X" 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/il.log"
rc=${PIPESTATUS[0]}
tk_step "init links rc=$rc: $(tail -n 1 "$Q_ROOT/il.log" | cut -c1-900)"
fi
if [[ "$rc" == 0 ]]; then
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/dp.py" train "$Q_KIT" - 0 "$Q_NS/v.json" "$Q_NS/p/s" 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/dp2.log"
rc=${PIPESTATUS[0]}
tk_step "disk plan at training start rc=$rc: $(tail -n 1 "$Q_ROOT/dp2.log" | cut -c1-900)"
fi
''' + TRAIN)
(OUT/'j_old.sh').write_bytes(base64.b64decode(jc['payload'])); (OUT/'j_new.sh').write_text(jsh)
(NEW/'k/j.json').write_bytes(jcap(jsh.encode())); (NEW/'k/j.json').chmod(0o644)
out['j'] = dict(decoded_sha256=hashlib.sha256(jsh.encode()).hexdigest(), json_sha256=sha(NEW/'k/j.json'),
                bash_n_rc=subprocess.run(['bash', '-n', str(OUT/'j_new.sh')]).returncode)
for f in ('il.py', 'dp.py', 'pc.py'):
    shutil.copyfile(IN/'b'/f, NEW/'b'/f); (NEW/'b'/f).chmod(0o644)
# reseal (support.reseal form) and verify with the new tree
files = {str(q.relative_to(NEW)): sha(q) for q in NEW.rglob('*') if q.is_file() and q.name not in ('BUILD.json', 'SHA256SUMS.txt')}
(NEW/'SHA256SUMS.txt').write_text(''.join(h + '  ' + k + '\n' for k, h in sorted(files.items()))); (NEW/'SHA256SUMS.txt').chmod(0o644)
b = load(BASE/'BUILD.json'); b['kit_sha256'] = seal_of(NEW); (NEW/'BUILD.json').write_bytes(cap(b))
sys.path.insert(0, str(TD/'new'))
from launch_r1.build import verify
out['seal'] = seal_of(NEW); out['verify_new_tree'] = verify(NEW) == out['seal']
def inv(k): return {str(q.relative_to(k)): sha(q) for q in sorted(k.rglob('*')) if q.is_file()}
A, B = inv(BASE), inv(NEW)
out['members_added'] = sorted(set(B) - set(A)); out['members_removed'] = sorted(set(A) - set(B))
out['members_changed'] = {k: [A[k], B[k]] for k in sorted(set(A) & set(B)) if A[k] != B[k]}
pc = {}
with tempfile.TemporaryDirectory() as t:
    for q in sorted((NEW/'b').glob('*.py')):
        try: py_compile.compile(str(q), cfile=str(Path(t)/(q.name + 'c')), doraise=True); pc[q.name] = 'ok'
        except py_compile.PyCompileError as e: pc[q.name] = 'FAIL ' + str(e)[:200]
out['py_compile_all_ok'] = all(v == 'ok' for v in pc.values()); out['py_compile_count'] = len(pc)
out['bash_n'] = {str(q.relative_to(NEW)): subprocess.run(['bash', '-n', str(q)]).returncode for q in sorted(NEW.rglob('*.sh'))}
out['pycache_in_kit'] = sorted(str(q) for q in NEW.rglob('__pycache__'))
(OUT/'BUILD35.json').write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
print(json.dumps(out, indent=1, sort_keys=True))
