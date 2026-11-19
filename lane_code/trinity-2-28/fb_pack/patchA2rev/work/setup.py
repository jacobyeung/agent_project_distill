"""Stage independent copies, verify seals, apply patches with zero fuzz, compare inventories."""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
FB = Path('/scratch/jjyeung/orch_n30/fb_pack')
BASE_SRC = FB/'ro/orch_n30/tree_rebuild10_w/w24/work/tree_r1'
BASE_LIST = FB/'ro/orch_n30/tree_rebuild10_w/w24/out/TREE_FILES.sha256'
LIVE_SRC = FB/'patchA2/work/live_base'
LIVE_SEAL = Path('/scratch/jjyeung/orch_n30/tree_rebuild15_w24l/out24j/TREE24J_SEAL.json')
PA = FB/'patchA/out/PATCH_A.patch'
PA2 = FB/'patchA2/out/PATCH_A2.patch'
DELTA = FB/'patchA2/out/PATCH_A2_DELTA.patch'
CAMFORM = FB/'camform/out/PATCH_CAMFORM.patch'
FT = FB/'patchA2/out/FILES_TOUCHED.json'

sys.path.insert(0, str(BASE_SRC))
from student_pilot.source_seal import inventory  # noqa: E402
from student_pilot.p3_provenance import digest  # noqa: E402


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def stage(src, dst):
    dst = W/dst
    if dst.exists():
        raise SystemExit('exists: '+str(dst))
    shutil.copytree(src, dst, symlinks=True)
    return dst


def apply(tree, patch):
    r = subprocess.run(['patch', '-p1', '--fuzz=0', '--no-backup-if-mismatch', '-i', str(patch)],
                       cwd=tree, capture_output=True, text=True)
    return dict(patch=str(patch), tree=str(tree), returncode=r.returncode, stdout=r.stdout, stderr=r.stderr,
                fuzz='fuzz' in r.stdout.lower(), offset='offset' in r.stdout.lower())


def changed(a, b):
    return {p: [a.get(p), b.get(p)] for p in sorted(set(a) | set(b)) if a.get(p) != b.get(p)}


out = dict(inputs_sha256={str(p): sha(p) for p in (BASE_LIST, LIVE_SEAL, PA, PA2, DELTA, CAMFORM, FT)})
listed = {n: v for v, n in (l.split('  ', 1) for l in BASE_LIST.read_text().splitlines())}
base = stage(BASE_SRC, 'base')
inv = {'base': inventory(base)}
out['base'] = dict(files=len(inv['base']), digest=digest(inv['base']), equals_list=inv['base'] == listed)
live_seal = json.loads(LIVE_SEAL.read_text())
live = stage(LIVE_SRC, 'live_base')
inv['live_base'] = inventory(live)
out['live_base'] = dict(files=len(inv['live_base']), digest=digest(inv['live_base']),
                        equals_seal_files=inv['live_base'] == live_seal['files'],
                        seal_digest_of_files=digest(live_seal['files']),
                        differs_from_base=changed(inv['base'], inv['live_base']))
applies = []
for name, src, patches in (('a', BASE_SRC, [PA]), ('a2', BASE_SRC, [PA2]), ('ad', BASE_SRC, [PA, DELTA]),
                           ('live_a2', LIVE_SRC, [PA2]), ('a2_camform', BASE_SRC, [PA2, CAMFORM]),
                           ('a_camform', BASE_SRC, [PA, CAMFORM]), ('live_a2_camform', LIVE_SRC, [PA2, CAMFORM])):
    t = stage(src, name)
    for p in patches:
        applies.append(dict(name=name, **apply(t, p)))
    inv[name] = inventory(t)
out['apply'] = applies
out['digests'] = {k: dict(files=len(v), digest=digest(v)) for k, v in inv.items()}
ft = json.loads(FT.read_text())
ft_map = {f['path']: [f['base_sha256'], f['new_sha256']] for f in ft['files']}
out['a2_vs_base'] = changed(inv['base'], inv['a2'])
out['a2_equals_files_touched'] = out['a2_vs_base'] == ft_map
out['files_touched_extra_keys'] = sorted(k for k in ft if k not in ('files', 'inputs_sha256'))
out['ad_equals_a2'] = inv['ad'] == inv['a2']
out['a_vs_a2'] = changed(inv['a'], inv['a2'])
out['a_vs_base'] = changed(inv['base'], inv['a'])
out['live_a2_vs_live_base'] = changed(inv['live_base'], inv['live_a2'])
out['live_patch_effect_equals_base_patch_effect'] = (
    {p: v[1] for p, v in out['live_a2_vs_live_base'].items()} == {p: v[1] for p, v in out['a2_vs_base'].items()})
out['a2_camform_vs_a_camform'] = changed(inv['a_camform'], inv['a2_camform'])
(W/'SETUP.json').write_text(json.dumps(out, indent=2)+'\n')
print(json.dumps({k: v for k, v in out.items() if k not in ('apply',)}, indent=1)[:6000])
for a in applies:
    print(a['name'], Path(a['patch']).name, a['returncode'], 'fuzz' if a['fuzz'] else '', 'offset' if a['offset'] else '')
    print(a['stdout'].strip(), a['stderr'].strip())
