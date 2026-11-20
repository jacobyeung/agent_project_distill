import hashlib, tarfile, json
from pathlib import Path
L = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24v')
man = json.load(open(L/'work/build24m4v/PACKAGE_MANIFEST.json'))['files']
want = {k for k in man if k.startswith(('work/tree_r1c/', 'out/kit_n_go/', 'out/kit_qd/', 'work/build24/kits/n/', 'work/build24/kits/q/', 'out/rcj/'))}
got, kinds = {}, {}
with tarfile.open(L/'out/tree_rebuild_b24m4v_3b4b6cff.tar', 'r:*') as a:
    for m in a:
        if m.name in want and (m.isfile() or m.islnk()):
            got[m.name] = hashlib.sha256(a.extractfile(m).read()).hexdigest()
            kinds[m.type] = kinds.get(m.type, 0) + 1
bad = [k for k in want if man[k].get('type') == 'file' and got.get(k) != man[k]['sha256']]
res = dict(wanted=len(want), found=len(got), member_types={str(k): v for k, v in kinds.items()}, mismatch=len(bad), first=bad[:5])
Path('pkg_check2.json').write_text(json.dumps(res, indent=1)); print(res)
