#!/bin/bash
set -euo pipefail
umask 077
export PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung CUDA_VISIBLE_DEVICES=
trap 'rc=$?; if [ "$rc" != 0 ]; then printf "phase exit %s line %s\n" "$rc" "$LINENO" >&2; fi' EXIT
/usr/bin/python3 -I -s -B - <<'PYCODE'
from pathlib import Path
import hashlib
pins={'/project/community/jjyeung/okh7/e6fc152498/g/0': 5627176960, '/project/community/jjyeung/okh7/e6fc152498/a2.tar': 5257369600, '/project/community/jjyeung/okh7/e6fc152498/a4.tar': 145274880, '/project/community/jjyeung/okh7/e6fc152498/a3.tar': 10240, '/project/community/jjyeung/okh7/af83c921/d81f4a26.tar': 797685760, '/home/jjyeung/okit/p/d59945c1/4fe70504.00': 900000000, '/home/jjyeung/okit/p/d59945c1/4fe70504.01': 721422080, '/home/jjyeung/okit/p/d59945c1/50011a59.00': 900000000, '/home/jjyeung/okit/p/d59945c1/50011a59.01': 900000000, '/home/jjyeung/okit/p/d59945c1/50011a59.02': 900000000, '/home/jjyeung/okit/p/d59945c1/50011a59.03': 900000000, '/home/jjyeung/okit/p/d59945c1/50011a59.04': 900000000, '/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.05': 900000000, '/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.06': 900000000, '/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.07': 900000000, '/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.08': 900000000, '/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.09': 366728960, '/project/community/jjyeung/bd8ae51c/p/d59945c1/371be2e2.00': 409282560, '/project/community/jjyeung/cp4tk_rt/kit/bwrap': 72160, '/project/community/jjyeung/okh7/eabcdef012345/5': 5395758080, '/project/community/jjyeung/okh7/eabcdef012345/6': 5395758080, '/project/community/jjyeung/okh7/eabcdef012345/7': 5395758080, '/project/community/jjyeung/okh7/eabcdef012345/8': 5395758080, '/project/community/jjyeung/okh7/eabcdef012345/9': 101, '/project/community/jjyeung/okh7/eabcdef012345/10': 243, '/project/community/jjyeung/okh7/eabcdef012345/11': 121, '/project/community/jjyeung/okh7/eabcdef012345/12': 401}
for name,size in pins.items():
 p=Path(name)
 if not p.is_file() or p.stat().st_size!=size:raise ValueError('Required staged input missing or size differs: '+name)
done=Path('/project/community/jjyeung/okh7/eabcdef012345/9')
if done.stat().st_size>4096 or done.read_text().split()!=['q8/8865619b/673bc60f_m200.tar', '21583032320', '795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b']:raise ValueError('Reviewed whole-tar receipt differs: '+str(done))
for name,sha in {'/project/community/jjyeung/okh7/eabcdef012345/10': '3b0051c4a9cc661d02019a645165fc3e23d658d2f24a6fd6fd86ec7877ba4fc1', '/project/community/jjyeung/okh7/eabcdef012345/11': '4c0dd9d6e4535a2945ed58754c1cdd5e9a316067be35f2e8440caa9a80e1c915', '/project/community/jjyeung/okh7/eabcdef012345/12': '7f654d2f0ae9f06083f2fc8fd793512c154b4d01ce8632fb733d4191205af770'}.items():
 p=Path(name)
 if p.stat().st_size>1048576:raise ValueError('Preparation input exceeds metadata budget: '+name)
 if hashlib.sha256(p.read_bytes()).hexdigest()!=sha:raise ValueError('Reviewed preparation differs: '+name)
print('inputs ready')
PYCODE
