"""Package a self-checking opaque CPU-only operator script."""
import base64, hashlib, json, zlib
from pathlib import Path
H=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ids=json.loads((H/'ids.json').read_text())
authority=dict(tag='8c74b291',job_name='a15_cot_ap8c74b291',
 kh='/project/community/jjyeung/okh7/x_'+ids['tokens']['kit'],
 bun='/project/community/jjyeung/okh7/i_1be16f28',
 persistent_root='/project/community/jjyeung/okh7/r/'+ids['tokens']['root'],
 identity=ids['identity'],contract=ids['contract'],wrapper_sha256=sha(H/'payload/jb.sh'),
 selection_sha256=sha(H/'payload/d_eac5f9f01587803b.json'),
 equality_sha256=sha(H/'payload/d_e48ab85bb9364aab.json'),
 runtime={n:sha(H/'build/fx'/n) for n in ('job.sh','b/p0.sh','b/p0.py','b/c.sh','b/r.sh','b/g.py','b/i.py','b/w.py','b/d.py','b/r8.py')})
raw=(H/'tools/proof_prepare.py').read_bytes()
blob=base64.b64encode(zlib.compress(raw,9)).decode()
s='''#!/bin/bash
#SBATCH -A mt01 -p general -N1 --ntasks=1 -c 48 --mem=800G -t 04:00:00
#SBATCH --no-requeue
set -euo pipefail
umask 077
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
exec /usr/bin/python3 -I -B - <<'P'
import base64,hashlib,zlib
'''+f"raw=zlib.decompress(base64.b64decode({blob!r}))\nassert hashlib.sha256(raw).hexdigest()=={sha(H/'tools/proof_prepare.py')!r}\nexec(compile(raw,'<sealed>','exec'))\nraise SystemExit(main({authority!r}))\nP\n"
for n in ('build/a_8c74b291.sh','payload/a_8c74b291.sh'):
 (H/n).write_text(s);(H/n).chmod(0o700)
(H/'evidence/fix8_admission/proof_authority.json').write_text(json.dumps(authority,indent=2)+'\n')
print('a_8c74b291.sh',len(s),sha(H/'build/a_8c74b291.sh'))
