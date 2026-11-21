"""fix11: build W/w32frm/n_go from W/w30f1/n_go: k/j.json (job folder also bound at /tmp/jjyeung/<ns>,
python steps run there, /data2 mapped to the kit's frame copy), b/pf.py frames(), b/pl.py call. Test build, not for install."""
import sys, json, shutil, hashlib, base64, subprocess, tarfile
from pathlib import Path
W = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w'); OLD = W/'w30f1/n_go'; F = W/'w32frm'; NEW = F/'n_go'
sys.path[:0] = [str(W/'w24z11b/work/build24m4x2')]
from support import J, reseal
OLDSEAL = '489f7f0fbfb9913066d0840bde40d01fc30927d2d127709e41bb479e554e2e90'
out = {}
assert J.seal(OLD) == OLDSEAL and J.load(OLD/'BUILD.json')['kit_sha256'] == OLDSEAL
if NEW.exists():
    # an earlier run of this script stopped after the copy (python 3.6); restore every member from OLD
    A = {str(p.relative_to(OLD)) for p in OLD.rglob('*') if p.is_file()}; B = {str(p.relative_to(NEW)) for p in NEW.rglob('*') if p.is_file()}
    assert A == B, A ^ B
    for n in sorted(A): shutil.copy2(OLD/n, NEW/n)
    out['restored_from_old_before_rebuild'] = True
else:
    shutil.copytree(OLD, NEW, copy_function=shutil.copy2)
assert J.seal(NEW) == OLDSEAL
expect_old = {'k/j.json': None, 'b/pf.py': '1d1d5fe3605faa6eb1d9bc8479f5331994a66ac20af40ecf0e2e2aaa8256b3f6',
              'b/pl.py': 'd014bb296ba4f84f976f8aee7706c62768ea430b18f35bd39542b13466c4c31d'}
old_j = json.loads((OLD/'k/j.json').read_text()); assert old_j['sha256'] == 'a70b7551d7a4d12eec99b26469c933e4ef74fa9cec6e954c97527e734f3cbbd4'
for name, h in expect_old.items():
    if h: assert J.sha(OLD/name) == h, name
    shutil.copyfile(F/'in'/name, NEW/name)   # keeps the member's mode
raw = base64.b64decode(json.loads((NEW/'k/j.json').read_text())['payload'])
assert hashlib.sha256(raw).hexdigest() == json.loads((NEW/'k/j.json').read_text())['sha256']
(F/'j_new.sh').write_bytes(raw)
out['j_sh_syntax'] = subprocess.run(['bash', '-n', str(F/'j_new.sh')]).returncode
seal = reseal(NEW); out['new_seal'] = seal
sys.path.insert(0, str(W/'w30f1/tree'))
from launch_r1.build import verify
out['verify_kit_tree'] = verify(NEW) == seal
def inv(k): return {str(p.relative_to(k)): (J.sha(p), p.stat().st_mode & 0o777) for p in sorted(k.rglob('*')) if p.is_file()}
a, b = inv(OLD), inv(NEW); assert set(a) == set(b)
out['changed_members'] = {n: dict(old=a[n][0], new=b[n][0], mode_old=oct(a[n][1]), mode_new=oct(b[n][1])) for n in a if a[n] != b[n]}
out['tree_tar_unchanged'] = a['k/t_e047002134f979bd.tar'] == b['k/t_e047002134f979bd.tar']
out['config_sha256'] = J.load(NEW/'BUILD.json')['config_sha256']; out['config_unchanged'] = J.sha(OLD/'k/c.json') == J.sha(NEW/'k/c.json')
tar = F/'s32frm_n_go.tar'
with tarfile.open(tar, 'w') as t: t.add(NEW, arcname='n_go')
out['tar'] = dict(path=str(tar), sha256=J.sha(tar), bytes=tar.stat().st_size)
(F/'BUILD_FRM.json').write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
print(json.dumps(out, indent=1, sort_keys=True))
