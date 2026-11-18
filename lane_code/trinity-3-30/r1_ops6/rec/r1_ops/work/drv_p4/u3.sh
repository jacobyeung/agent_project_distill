#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
O=/project/community/jjyeung/okh7
BUN=$O/i_69d2930d
H=$O/x_3fdda0fb
OLD=$O/i_1be16f28
KH=$O/x_69d2930d
private() { [[ -d "$1" && ! -L "$1" && $(stat -c %a "$1") == 700 ]] || { echo "REFUSED: private directory required: $1" >&2; exit 3; }; }
fresh() { [[ ! -e "$1" && ! -L "$1" ]] || { echo "REFUSED: already exists: $1" >&2; exit 3; }; }
private "$O"
private "$BUN"
python3 -B - <<'PYCODE'
import hashlib,tarfile,re,os
from pathlib import Path
b=Path('/project/community/jjyeung/okh7/i_69d2930d');archive=b/'p.tar'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='a99ab475f602c63332d4faaa4bf20f9d75e604cb973a80a041338b03a7d5f589','outer SHA differs'
with tarfile.open(archive) as tf:
 members=tf.getmembers();assert len(members)==37,'member count differs'
 names=set()
 for m in members:
  p=Path(m.name)
  assert m.isfile() and not p.is_absolute() and '..' not in p.parts and m.name not in names and m.size<32000000,'unsafe member'
  names.add(m.name)
 assert 'sums.txt' in names
 sums=tf.extractfile('sums.txt').read().decode()
 pins={}
 for line in sums.splitlines():
  h,n=line.split('  ',1);assert re.fullmatch('[0-9a-f]{64}',h) and n in names and n not in pins
  pins[n]=h
 assert set(pins)==names-{'sums.txt'},'inventory differs'
 for m in members:
  data=tf.extractfile(m).read()
  if m.name!='sums.txt':assert hashlib.sha256(data).hexdigest()==pins[m.name]
  p=b/m.name;p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
  with p.open('xb') as f:f.write(data)
  p.chmod(0o600)
print('PASS outer SHA; 37 members; sums.txt exact inventory; files 0600')
PYCODE
