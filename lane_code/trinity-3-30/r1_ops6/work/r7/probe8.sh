#!/bin/bash
# r1_ops7: read-only rehearsal of hr2.sh's rebuilt-namespace mode (stop step) while the trainer runs; no write
export TZ=UTC; date -u +%FT%TZ
timeout 300 srun --overlap --jobid 172660 -n1 -N1 timeout 240 nice -n 19 bash -s <<'STEP' 2>&1 | cut -c1-300
set -uo pipefail
NL=/tmp/jjyeung/a_6ed2c7aa; R=$NL/runs/6ed2c7aa
AS=/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung; X=$AS/ap/8865619b; XR=$X/runs/6ed2c7aa
PY=/project/community/jjyeung/c7d31ddd/venvs/rwtrain_torch211_cu129/bin/python
ZH=/project/community/jjyeung/okh7/h_6ed2c7aa/q2_67f8baf1.zip; ZE=/project/community/jjyeung/okh7/h_6ed2c7aa/q3_846ead7a.zip
writing() { return 1; }
  BW=/project/community/jjyeung/cp4tk_rt/kit/bwrap; [[ -x $BW ]] || { echo "NO_BWRAP"; exit 4; }
  RT=$NL/root; [[ -d $RT/aws/u && -d $NL/x_172660 && -d $RT/c7d31ddd ]] || { echo "NO_STAGED_ROOT under $NL"; ls -la "$NL"; exit 4; }
  NSCMD=("$BW")
  for entry in /* /.[!.]* /..?*; do
    case "$entry" in /home|/dev|/proc) continue ;; esac
    [[ -e "$entry" || -L "$entry" ]] || continue
    if [[ -L "$entry" ]]; then NSCMD+=(--symlink "$(readlink "$entry")" "$entry"); else NSCMD+=(--ro-bind "$entry" "$entry"); fi
  done
  NSCMD+=(--dev-bind /dev /dev --proc /proc --tmpfs /home --ro-bind "$RT/aws/u" "$AS" --ro-bind "$RT/aws/u" /lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung
         --ro-bind "$NL/x_172660" "$X" --bind "$NL/runs" "$X/runs" --ro-bind "$RT/aws/u/ap/8865619b/u" "$X/u"
         --ro-bind "$RT/c7d31ddd/data2root" "$X/data2root" --ro-bind "$RT/c7d31ddd/runs/aws128p_20261025/models" "$X/models"
         --ro-bind "$RT/c7d31ddd" /project/community/jjyeung/c7d31ddd --unshare-user --uid "$(id -u)" --gid "$(id -g)" --)
  F=(PATH=/usr/bin:/bin HOME=/tmp)
RUNPY() { local zp=$1; shift; "${NSCMD[@]}" env -i "${F[@]}" SLURM_JOB_ID=172660 CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$zp" "$PY" -s -B "$@"; }
ls -ld /project/community/jjyeung/c7d31ddd 2>&1
RUNPY "$ZE" - <<'PY'
X='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b'; R=X+'/runs/6ed2c7aa'
import os
from student_pilot.p3_provenance import file_pin, load, pinned
from launch_r1 import p_export_receipt as e, p_handover_receipt as h
cfgp=R+'/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/config.json'; cfg=load(cfgp)
rp=dict(config=file_pin(cfgp),binding=file_pin(R+'/binding.json'),preparation=cfg['preparation'])
print('rp ok', rp['config']['sha256'][:8], rp['binding']['sha256'][:8])
prep=load(pinned(cfg['preparation'])); print('prep ok; model', os.path.isfile(prep['model']['path']))
for n,p in cfg['streams'].items(): print('stream',n,os.path.isfile(p['path']))
import torch; print('torch', torch.__version__)
try: e.collect(rp,file_pin('/project/community/jjyeung/okh7/x_69d2930d/runs/673bc60f/m200/artifact.json')); print('unexpected')
except Exception as x: print('COLLECT',type(x).__name__,x)
PY
echo "py rc=$?"
STEP
echo "srun rc=${PIPESTATUS[0]}"
