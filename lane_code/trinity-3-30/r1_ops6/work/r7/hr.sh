#!/bin/bash
# r1_ops7: handover receipt of run 6ed2c7aa at milestone STEP (400 rehearsal, 600 handover) inside 172660
# (ORCH RULING 0033Z, ANSWER 0036Z). Usage: ossh 'bash -s 400' < hr.sh. CPU only, nice, 20-minute limit; never
# signals the trainer. Writes RP.json + h.json beside the artifact (node-local run dir) and, on pool, H/m<STEP>/
# (s.tar of the small files of items 1-3 with MANIFEST.json, copies of h.json and RP.json, step.log, DONE.json).
set -uo pipefail; export TZ=UTC; umask 077
STEP=${1:?step}; [[ $STEP =~ ^(400|600)$ ]] || { echo "REFUSED: step $STEP"; exit 2; }
O=/project/community/jjyeung/okh7; KH=$O/x_ee227714; H=$O/h_6ed2c7aa; D=$H/m$STEP; Z=$H/q2_67f8baf1.zip
date -u +%FT%TZ
echo "f415c69d7f8adfb6e9483c1bf53deb6f01728689f3c33806c4bda540675c4fdc  $Z" | sha256sum -c --quiet || { echo "REFUSED: zip differs"; exit 3; }
echo "346c4cba63d5175f389c52f01451d4e5c9d30f1b7b625bd3c29f987bb4c70e9d  $H/q3_846ead7a.zip" | sha256sum -c --quiet || { echo "REFUSED: export-only zip differs"; exit 3; }
[[ -f $KH/o/gcs_6ed2c7aa_m$STEP.done ]] || { echo "NOT_READY: $KH/o/gcs_6ed2c7aa_m$STEP.done absent (export not uploaded)"; exit 4; }
[[ ! -e $D ]] || { echo "REFUSED: $D exists"; exit 3; }
mkdir -m 700 "$D" || exit 3
timeout 1290 srun --overlap --jobid 172660 -n1 -N1 timeout 1260 nice -n 19 ionice -c2 -n7 bash -s "$STEP" "$D" "$Z" > "$D/step.log" 2>&1 <<'STEPSCRIPT'
set -uo pipefail; export TZ=UTC; umask 077
STEP=$1 D=$2 Z=$3
R=/tmp/jjyeung/a_6ed2c7aa/runs/6ed2c7aa
X=/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b; XR=$X/runs/6ed2c7aa
echo "step start $(date -u +%FT%TZ) on $(hostname -s)"
[[ -f $R/m$STEP/artifact.json ]] || { echo "NO_ARTIFACT $R/m$STEP/artifact.json"; exit 4; }
for f in h.json RP.json e.json r.json; do [[ ! -e $R/m$STEP/$f ]] || { echo "REFUSED: $f exists"; exit 3; }; done
# ORCH 0036Z item 4: never hash while the trainer writes a checkpoint (a checkpoint dir without complete.json).
busy=1
for i in $(seq 30); do
  busy=0; for d in "$R"/checkpoint_*; do [[ -d $d && ! -f $d/complete.json ]] && busy=1; done
  (( busy == 0 )) && break; echo "checkpoint write in progress $(date -u +%T); waiting"; sleep 30
done
(( busy == 0 )) || { echo "BUSY: a checkpoint write did not finish within 15 min"; exit 5; }
CK=$(ls -d "$R"/checkpoint_000${STEP}_* 2>/dev/null | head -1)
# The trainer checkpoints on a 2-hour clock plus the stop; a milestone between checkpoints has no step-N checkpoint.
# Then the latest complete checkpoint is pinned instead, and the receipt is expected to refuse (complete.step != step).
if [[ -z $CK || ! -f $CK/complete.json ]]; then
  CK=$(for d in "$R"/checkpoint_*; do [[ -f $d/complete.json ]] && echo "$d"; done | sort -V | tail -1)
  echo "NO_STEP_CHECKPOINT for step $STEP; pinning the latest complete checkpoint ${CK##*/} (receipt expected to refuse)"
fi
CKN=${CK##*/}
echo "checkpoints: $(ls -d "$R"/checkpoint_* | sed 's#.*/##' | tr '\n' ' ')"
PID=$(ps -u "$(id -u)" -o pid=,rss=,comm= --sort=-rss | awk '$3=="python"{print $1; exit}')
[[ -n $PID ]] || { echo "NO_TRAINER_PROCESS"; exit 4; }
NS="nsenter -t $PID -U -m -r -w --preserve-credentials"
PY=/project/community/jjyeung/c7d31ddd/venvs/rwtrain_torch211_cu129/bin/python
mapfile -d '' E < /proc/$PID/environ; F=()
for v in "${E[@]}"; do case "${v%%=*}" in CUDA_VISIBLE_DEVICES|PYTHONPATH|LOCAL_RANK|RANK|GROUP_RANK|ROLE_RANK|LOCAL_WORLD_SIZE|WORLD_SIZE|MASTER_ADDR|MASTER_PORT|TORCHELASTIC_*|TORCH_NCCL_*|NCCL_*|OMP_NUM_THREADS|MKL_NUM_THREADS|OPENBLAS_NUM_THREADS) ;; *) F+=("$v");; esac; done
ZP=$Z
RUNPY() { $NS env -i "${F[@]}" SLURM_JOB_ID=172660 CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ZP" "$PY" -s -B "$@"; }
rc_receipt=9
if [[ -n $CKN && -f $CK/complete.json ]]; then
  # RP.json: config, binding, preparation (verbatim config.preparation), checkpoint, as seen in the job.
  TC=$(RUNPY - "$XR" "$STEP" "$CKN" <<'PY'
import json,sys
from student_pilot.p3_provenance import file_pin, load, write
XR,STEP,CKN=sys.argv[1:4]
cfgp=XR+'/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/config.json'
cfg=load(cfgp); b=load(XR+'/binding.json')
rp=dict(config=file_pin(cfgp),binding=file_pin(XR+'/binding.json'),preparation=cfg['preparation'],checkpoint=file_pin(XR+'/'+CKN+'/complete.json'))
write(XR+'/m'+STEP+'/RP.json',rp)
print(b['trainer_commit'])
PY
)
  echo "RP written; trainer_commit $TC"
  t0=$(date +%s)
  RUNPY -m launch_r1.p_handover_receipt --run-pins "$XR/m$STEP/RP.json" --artifact "$XR/m$STEP/artifact.json" --output "$XR/m$STEP/h.json" --trainer-commit "$TC" 2>&1 | tail -5
  rc_receipt=${PIPESTATUS[0]}
  echo "receipt rc=$rc_receipt in $(( $(date +%s) - t0 )) s"
else
  echo "NO_CHECKPOINT at all; receipt not run (BLOCKER); copying the small files anyway"
fi
# ORCH RULING 0209Z item 3: at a non-stop milestone also the export-only receipt (build 17, p_export_receipt; r.json has
# config, binding, preparation and no checkpoint pin), e.json beside the artifact.
rc_export=na
if [[ $STEP == 400 ]]; then
  ZP=${Z%/*}/q3_846ead7a.zip
  TC2=$(RUNPY - "$XR" "$STEP" <<'PY'
import sys
from student_pilot.p3_provenance import file_pin, load, write
XR,STEP=sys.argv[1:3]
cfgp=XR+'/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/config.json'
cfg=load(cfgp); b=load(XR+'/binding.json')
write(XR+'/m'+STEP+'/r.json',dict(config=file_pin(cfgp),binding=file_pin(XR+'/binding.json'),preparation=cfg['preparation']))
print(b['trainer_commit'])
PY
)
  t0=$(date +%s)
  RUNPY -m launch_r1.p_export_receipt --run-pins "$XR/m$STEP/r.json" --artifact "$XR/m$STEP/artifact.json" --output "$XR/m$STEP/e.json" --trainer-commit "$TC2" 2>&1 | tail -5
  rc_export=${PIPESTATUS[0]}
  echo "export-only receipt rc=$rc_export in $(( $(date +%s) - t0 )) s"
  ZP=$Z
fi
# Items 1-3 small files (ORCH 0036Z item 2, tree_rebuild10 0140Z): every existing pinned file up to 64 MB reachable
# from the artifact, the checkpoint manifest, config, binding, data receipt and the preparation/model receipts; never shards.
RUNPY - "$XR" "$STEP" "$CKN" > "$D/s.tar.part" 2> "$D/s.err" <<'PY'
import json,sys,os,io,hashlib,tarfile
from pathlib import Path
XR,STEP,CKN=sys.argv[1:4]; CAP=64<<20; TOTAL=1536<<20
def sha(p):
  h=hashlib.sha256()
  with open(p,'rb') as f:
    for b in iter(lambda:f.read(1<<20),b''): h.update(b)
  return h.hexdigest()
seen={}; skipped=[]; queue=[]
def add(path,want=None,why='',level=0):
  p=str(path)
  if p in seen: return
  if not os.path.isfile(p): skipped.append(dict(path=p,reason='absent',why=why)); seen[p]=None; return
  n=os.path.getsize(p)
  if n>CAP: skipped.append(dict(path=p,reason='over 64 MB',bytes=n,why=why)); seen[p]=None; return
  s=sha(p); seen[p]=dict(path=p,bytes=n,sha256=s,pin=want,match=(want is None or want==s),why=why)
  if p.endswith('.json') and level<3 and os.path.basename(p)!='frames.json': queue.append((p,level+1))
def walk(v,why,level):
  if isinstance(v,dict):
    if isinstance(v.get('path'),str) and isinstance(v.get('sha256'),str) and v['path'].startswith('/'):
      add(v['path'],v['sha256'],why,level)
    for x in v.values(): walk(x,why,level)
  elif isinstance(v,list):
    for x in v: walk(x,why,level)
M=XR+'/m'+STEP
for f in ('artifact.json','RP.json','h.json','r.json','e.json'): add(M+'/'+f,None,'milestone')
for f in ('binding.json','attempt_172660.json','inputs/data_receipt.json','inputs/first_step_172660.json',
          'inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/config.json'): add(XR+'/'+f,None,'run')
if CKN:
  c=XR+'/'+CKN; add(c+'/complete.json',None,'checkpoint')
  try:
    for name,pin in json.load(open(c+'/complete.json')).get('files',{}).items():
      if not name.startswith('shards/') and name!='replicated.pt': add(c+'/'+name,pin.get('sha256'),'checkpoint file')
  except Exception as e: skipped.append(dict(path=c,reason='complete.json unreadable '+repr(e)))
done=set()
while queue:
  p,level=queue.pop(0)
  if p in done: continue
  done.add(p)
  try: v=json.load(open(p))
  except Exception: continue
  walk(v,'pinned by '+p,level)
  if len(done)>400: break
items=[v for v in seen.values() if v]; total=sum(v['bytes'] for v in items)
man=dict(schema='r7-handover-small-files-v1',run='6ed2c7aa',step=int(STEP),checkpoint=CKN,files=items,skipped=skipped,bytes=total)
if total>TOTAL: man['truncated']=True
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as t:
  raw=json.dumps(man,indent=1,sort_keys=True).encode(); ti=tarfile.TarInfo('MANIFEST.json'); ti.size=len(raw); t.addfile(ti,io.BytesIO(raw))
  acc=0
  for v in items:
    acc+=v['bytes']
    if acc>TOTAL: break
    t.add(v['path'],arcname='files'+v['path'],recursive=False)
print('files',len(items),'bytes',total,'skipped',len(skipped),'mismatch',sum(1 for v in items if not v['match']),file=sys.stderr)
PY
echo "copy rc=$? $(tail -1 "$D/s.err")"
mv "$D/s.tar.part" "$D/s.tar" && sha256sum "$D/s.tar"
for f in h.json RP.json e.json r.json; do [[ -f $R/m$STEP/$f ]] && cat "$R/m$STEP/$f" > "$D/$f" && sha256sum "$R/m$STEP/$f" "$D/$f"; done
printf '{"step": %s, "checkpoint": "%s", "receipt_rc": %s, "export_receipt_rc": "%s", "utc": "%s"}\n' "$STEP" "$CKN" "$rc_receipt" "$rc_export" "$(date -u +%FT%TZ)" > "$D/DONE.json"
echo "step end $(date -u +%FT%TZ)"
STEPSCRIPT
echo "srun rc=$?"
cut -c1-300 "$D/step.log" | tail -30
ls -la "$D"; [[ -f $D/e.json ]] && python3 -c "
import json,sys; h=json.load(open(sys.argv[1])); print('e.json schema',h['schema'],'step',h['step'],'stop',h['stop_step'],h['checkpoint_status'],'pins',len(h['pins']))" "$D/e.json"; [[ -f $D/h.json ]] && python3 -c "
import json,sys; h=json.load(open(sys.argv[1])); print('h.json schema',h['schema'],'step',h['step'],'job',h['job_id'],'pins',len(h['pins']))" "$D/h.json"
