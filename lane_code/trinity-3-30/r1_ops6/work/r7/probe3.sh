#!/bin/bash
# r1_ops7: read-only in-allocation rehearsal of the handover receipt's environment (no write anywhere)
export TZ=UTC; date -u +%FT%TZ
timeout 300 srun --overlap --jobid 172660 -n1 -N1 timeout 240 nice -n 19 bash -s <<'STEP' 2>&1 | cut -c1-400
set -uo pipefail
R=/tmp/jjyeung/a_6ed2c7aa/runs/6ed2c7aa
PID=$(ps -u $(id -u) -o pid=,rss=,comm= --sort=-rss | awk '$3=="python"{print $1; exit}')
echo "rank pid $PID"; ps -o pid,ppid,etimes,comm -p $PID
ls -d $R/checkpoint_*; for d in $R/checkpoint_*; do [[ -f $d/complete.json ]] || echo "IN PROGRESS $d"; done
CK=$(ls -d $R/checkpoint_* | sort -V | tail -1); CKN=${CK##*/}; echo "CKN=$CKN"
NS="nsenter -t $PID -U -m --preserve-credentials --wd=/"
PY=/project/community/jjyeung/c7d31ddd/venvs/rwtrain_torch211_cu129/bin/python
$NS ls -la /scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/6ed2c7aa | head -12
$NS env -i PATH=/usr/bin:/bin HOME=/tmp SLURM_JOB_ID=172660 CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=/project/community/jjyeung/okh7/h_6ed2c7aa/q2_67f8baf1.zip timeout 180 $PY -s -B - "$CKN" <<'PY'
import json,sys,hashlib
from pathlib import Path
X='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b'; R=X+'/runs/6ed2c7aa'
from student_pilot.p3_provenance import file_pin, load
from launch_r1 import p_handover_receipt as h
from student_pilot.r1_handover import export_identity
from student_pilot.carrier_c1_sweep import recipe_for
print('python',sys.version.split()[0],'module',h.__file__)
cfgp=R+'/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/config.json'
cfg=load(cfgp); b=load(R+'/binding.json')
ck=R+'/'+sys.argv[1]+'/complete.json'; c=load(ck)
rp=dict(config=file_pin(cfgp),binding=file_pin(R+'/binding.json'),preparation=cfg['preparation'],checkpoint=file_pin(ck))
print('RP',json.dumps(rp))
print('identity',export_identity(cfg),'binding',b['config_sha256'],'milestones',recipe_for(cfg)['milestones'])
print('complete step',c.get('step'),'schema',c.get('schema'),'files',sorted(c.get('files',{}))[:12],'layouts',type(c.get('layouts')).__name__,len(c.get('layouts') or []),'binding==',c.get('binding')==b)
prep=load(cfg['preparation']['path']); print('prep model',json.dumps(prep.get('model')))
try:
  h.collect(rp,file_pin('/project/community/jjyeung/okh7/x_69d2930d/runs/673bc60f/m200/artifact.json'))
  print('COLLECT unexpected success')
except Exception as e: print('COLLECT',type(e).__name__,e)
PY
echo "py rc=$?"
STEP
echo "srun rc=${PIPESTATUS[0]}"
