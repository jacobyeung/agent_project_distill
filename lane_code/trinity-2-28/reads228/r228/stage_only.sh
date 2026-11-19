#!/bin/bash
# swarm_opt5: manifest check then kit stage-only sequence on trinity-2-28 (no card, no run dir)
set -euo pipefail
date -u
test "$(hostname -s)" = trinity-2-28
kit_dir=/scratch/jjyeung/orch_n30/reads228/kit
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
nice -n 10 /usr/bin/python3 -I -s -B - "$kit_dir" <<'PY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]);manifest=json.loads((root/'DELIVERY_MANIFEST.json').read_text())
actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='DELIVERY_MANIFEST.json'}
assert actual==set(manifest['files']),sorted(actual^set(manifest['files']))
for name,spec in manifest['files'].items():
    path=root/name
    assert path.is_file() and not path.is_symlink(),name
    assert path.stat().st_size==spec['bytes'],name
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    assert digest.hexdigest()==spec['sha256'],name
print('DELIVERY_MANIFEST verified: '+str(len(manifest['files']))+' files')
PY
date -u
df -h /scratch | tail -1
bash "$kit_dir/coordinator228.sh" --stage-only
echo STAGE_ONLY_RC=$?
date -u
df -h /scratch | tail -1
