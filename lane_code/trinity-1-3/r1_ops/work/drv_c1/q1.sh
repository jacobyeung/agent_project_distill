#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
O=/project/community/jjyeung/okh7
BUN=$O/i_7f1589c1
H=$O/x_3fdda0fb
OLD=$O/i_1be16f28
KH=$O/x_7f1589c1
private() { [[ -d "$1" && ! -L "$1" && $(stat -c %a "$1") == 700 ]] || { echo "REFUSED: private directory required: $1" >&2; exit 3; }; }
fresh() { [[ ! -e "$1" && ! -L "$1" ]] || { echo "REFUSED: already exists: $1" >&2; exit 3; }; }
packet() { printf '%s  %s\n' '6a5c7d009a19cb5bac690b864f2be68bb5cebc29649923c93da36328d0f96888' "$BUN/p.tar" | sha256sum -c --quiet; }
private "$O"
private "$BUN"
packet
PY_GATE=/project/community/jjyeung/latency/envs/fit/bin/python3
[[ -x "$PY_GATE" ]] || { echo 'REFUSED: authenticated H1 CPU environment missing'; exit 4; }
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
"$PY_GATE" -I -B - <<'PYCODE'
"""Authenticate and materialize the exact selector import tree in a fresh directory."""
import hashlib,json,tarfile
from pathlib import Path

def selection_tree(bundle, target):
    bundle=Path(bundle);target=Path(target)
    code=json.loads((bundle/'c.json').read_text())
    archive=bundle/'t.tar'
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=code['archive']['sha256']:
        raise ValueError('Selector archive differs')
    target.mkdir(mode=0o700)
    seen=set()
    with tarfile.open(archive) as tf:
        for member in tf:
            name=member.name;rel=Path(name)
            if (not member.isfile() or rel.is_absolute() or '..' in rel.parts or
                    name in seen or name not in code['files'] or member.size>32000000):
                raise ValueError('Unsafe selector archive member')
            raw=tf.extractfile(member).read()
            if hashlib.sha256(raw).hexdigest()!=code['files'][name]:
                raise ValueError('Selector member differs')
            path=target/rel;path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
            with path.open('xb') as stream:stream.write(raw)
            path.chmod(0o600);seen.add(name)
    if seen!=set(code['files']):raise ValueError('Selector inventory differs')
    return target

import hashlib,json,os,subprocess,sys
from pathlib import Path
assert sys.version_info >= (3,10), 'H1 authenticated CPU Python >=3.10 required'
B=Path('/project/community/jjyeung/okh7/i_7f1589c1');H=B.parent/'x_3fdda0fb'
N=B.parent/'i_1be16f28/q_6c18a2bf/o'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
assert sha(N/'q.json')=='e48ab85bb9364aab228da7b23033605935e384761f76b0e6527c5e221b1c14b4'
assert sha(N/'native/receipt.json')=='2e25a01d943cc910f58260255ae5d2943fbbee2b7114f7d86e280c509e321f68'
r=load(N/'q.json');assert r['status']=='EQUAL' and r['regenerated'] is True
assert r['differences']==[] and r['raw_differences']==[] and all(v['equal'] for v in r['indices'].values())
assert sha(N/'r.json')==r['selection_sha256']==sha(H/'k/pool_selection_eac5f9f0.json')
assert not (B/'q').exists(), 'q already exists'
tree=selection_tree(B,B/'qt')
env=dict(os.environ,PYTHONPATH=str(tree),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='')
env.pop('PYTHONOPTIMIZE',None)
subprocess.run([sys.executable,'-B',str(B/'q.py'),'--parent',str(H/'k/pool_selection_eac5f9f0.json'),'--indices',str(H/'k'),'--native-receipt',str(N/'native/receipt.json'),'--implementation',str(B/'j.json'),'--code-record',str(B/'c.json'),'--unit-binding',str(B/'u.json'),'--config',str(B/'config.json'),'--out',str(B/'q')],check=True,env=env)
p=load(B/'q/q.json');assert p['status']=='PASS' and p['native_regeneration_executed'] is True and p['native_unit_regeneration_executed'] is True
assert p['selection_sha256']==load(B/'BINDING.json')['selection_sha256']==sha(B/'q/r.json')==sha(B/'s.json')
print('PASS native receipt reused; native_unit_regeneration_executed=true; ordered indices checked; projection',p['selection_sha256'])

PYCODE
