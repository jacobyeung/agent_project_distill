#!/bin/bash
# Local rehearsal of the CPU real unit: the delivered worker in the pinned interpreter and
# production-shaped namespace, real served sources (old package code), pinned weights, all frames.
set -euo pipefail
K=/scratch/jjyeung/orch_n30/lever5/k5/kit
W=/scratch/jjyeung/orch_n30/lever5/k5/work
R=/scratch/jjyeung/orch_n30/lever1_c/r1_fixtures_old/real_cl2opr5g/j
NS=/scratch/jjyeung/b01ec87a6f29b
O=$(mktemp -d "$W/cpu_real_XXXXXXXX")
P=/scratch/jjyeung/envs/p1cpu/bin/python
$P -I -B - "$K" "$O" <<'PY'
import gzip,json,sys,time
from pathlib import Path
k,o=Path(sys.argv[1]),Path(sys.argv[2])
c=json.loads((k/'1.json').read_text())
(o/'8.bin').write_bytes(gzip.decompress((k/'8.gz').read_bytes()))
c.update(xe=time.time()+900,xl='/x/o/8.bin',xu='/x/o/9.err',xc='/x/f',xb=[b'/x/g/model.safetensors'.hex(),b'/x/g/config.json'.hex()])
(o/'1.json').write_text(json.dumps(c))
PY
start=$(date +%s)
set +e
taskset -c 0-7 /usr/bin/bwrap --ro-bind /usr /usr --symlink usr/bin /bin --symlink usr/sbin /sbin --symlink usr/lib /lib --symlink usr/lib64 /lib64 \
  --ro-bind /etc /etc --ro-bind /opt /opt --ro-bind /run /run --ro-bind /sys /sys \
  --dev-bind /dev /dev --proc /proc --dir /tmp \
  --dir /scratch --bind $R/sj /scratch/jjyeung --bind $R/fsw /scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung \
  --dir /lustre --bind $R/m/ap /lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap \
  --ro-bind $R/sj/uv-python/cpython-3.12.13-linux-x86_64-gnu /home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu \
  --ro-bind $W/old0 $NS/p \
  --dir /x --ro-bind /scratch/jjyeung/k1/g3t /x/g --ro-bind $W/f /x/f --ro-bind $K /x/k --bind $O /x/o --die-with-parent --chdir /tmp \
  env -i PATH=/usr/bin:/bin HOME=/tmp TMPDIR=/tmp OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 \
  CUDA_VISIBLE_DEVICES= CUBLAS_WORKSPACE_CONFIG=:4096:8 PYTHONDONTWRITEBYTECODE=1 \
  $NS/d/v/py -I -s -B /x/k/2.py /x/o/1.json /x/o/a2.json 2 c 1 > "$O/stdout.log" 2> "$O/stderr.log"
code=$?
set -e
echo "{\"exit\": $code, \"seconds\": $(( $(date +%s) - start )), \"work\": \"$O\"}" | tee "$O/RUN.json"
