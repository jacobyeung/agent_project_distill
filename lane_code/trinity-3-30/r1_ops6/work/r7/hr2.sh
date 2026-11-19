#!/bin/bash
# r1_ops7: receipts of run 6ed2c7aa at milestone STEP inside job 172660 (ORCH RULING 0033Z, ANSWER 0036Z, RULING 0209Z).
# Usage: timeout 1500 bash ossh.sh 'bash -s 400' < hr2.sh   (or 600). CPU only, nice, one srun step of at most 1,200 s;
# never signals the trainer. Writes RP.json/h.json (handover) and, at 400, r.json/e.json (export-only) beside the
# artifact in the node-local run dir; on pool only under H/m<STEP>/: s.tar (small closure files + MANIFEST.json),
# copies of the receipt files, step.<epoch>.log, DONE.json. A run that stopped before writing a receipt may be repeated.
# Namespace: while the trainer runs, nsenter into a rank of this job; after it has exited (the stop step), a private
# bwrap namespace rebuilt from the trainer's recorded binds (probe7, 04:18Z), read-only except the run directory.
set -uo pipefail; export TZ=UTC; umask 077
STEP=${1:?step}; [[ $STEP =~ ^(400|600)$ ]] || { echo "REFUSED: step $STEP"; exit 2; }
O=/project/community/jjyeung/okh7; KH=$O/x_ee227714; H=$O/h_6ed2c7aa; D=$H/m$STEP
ZH=$H/q2_67f8baf1.zip; ZE=$H/q3_846ead7a.zip
date -u +%FT%TZ
printf '%s  %s\n%s  %s\n' f415c69d7f8adfb6e9483c1bf53deb6f01728689f3c33806c4bda540675c4fdc "$ZH" \
  346c4cba63d5175f389c52f01451d4e5c9d30f1b7b625bd3c29f987bb4c70e9d "$ZE" | sha256sum -c --quiet || { echo "REFUSED: zip differs"; exit 3; }
[[ -f $KH/o/gcs_6ed2c7aa_m$STEP.done ]] || { echo "NOT_READY: gcs_6ed2c7aa_m$STEP.done absent (export not uploaded)"; exit 4; }
[[ ! -e $D/DONE.json ]] || { echo "REFUSED: $D/DONE.json exists"; exit 3; }
mkdir -p -m 700 "$D" || exit 3
LOG=$D/step.$(date +%s).log
timeout 1200 srun --overlap --jobid 172660 -n1 -N1 timeout -k 10 1170 nice -n 19 ionice -c2 -n7 bash -s "$STEP" "$D" "$ZH" "$ZE" > "$LOG" 2>&1 <<'STEPSCRIPT'
set -uo pipefail; export TZ=UTC; umask 077
STEP=$1 D=$2 ZH=$3 ZE=$4
NL=/tmp/jjyeung/a_6ed2c7aa; R=$NL/runs/6ed2c7aa
AS=/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung; X=$AS/ap/8865619b; XR=$X/runs/6ed2c7aa
PY=/project/community/jjyeung/c7d31ddd/venvs/rwtrain_torch211_cu129/bin/python
echo "step start $(date -u +%FT%TZ) on $(hostname -s)"
[[ -f $R/m$STEP/artifact.json ]] || { echo "NO_ARTIFACT $R/m$STEP/artifact.json"; exit 4; }
for f in RP.json h.json r.json e.json; do [[ ! -e $R/m$STEP/$f ]] || { echo "REFUSED: $f exists beside the artifact"; exit 3; }; done
# Trainer ranks of this job only: python children running .../b/w.py below job 172660's batch script.
JOBROOT=$(ps -u "$(id -u)" -o pid=,args= | awk '$0 ~ /slurmd\/job172660\/slurm_script/ {print $1; exit}')
desc() { local p; for p in $(ps -o pid= --ppid "$1"); do echo "$p"; desc "$p"; done; }
PID=""; if [[ -n $JOBROOT ]]; then
  for p in $(desc "$JOBROOT"); do tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null | grep -q -E "python.* -u $X/b/w\.py" && { PID=$p; break; }; done
fi
ckdirs() { for d in "$R"/checkpoint_*; do [[ -d $d ]] && echo "$d"; done; }
writing() { for d in $(ckdirs); do [[ -f $d/complete.json ]] || { echo "$d"; return 0; }; done; return 1; }
latest() { for d in $(ckdirs); do [[ -f $d/complete.json ]] && echo "$d"; done | sort -V | tail -1; }
if [[ -n $PID ]]; then
  MODE=nsenter
  # ORCH 0036Z item 4: the trainer checkpoints about every 7,200 s; hash only if the next save is at least 25 min away.
  if w=$(writing); then echo "BUSY: checkpoint write in progress ($w); rerun after it completes"; exit 5; fi
  age=$(( $(date +%s) - $(stat -c %Y "$(latest)/complete.json") ))
  (( age <= 5700 )) || { echo "NEAR_CHECKPOINT: last checkpoint is ${age} s old; rerun after the next one completes"; exit 5; }
  echo "trainer rank $PID; last checkpoint $(basename "$(latest)") ${age} s old"
  NSCMD=(nsenter -t "$PID" -U -m -r -w --preserve-credentials)
  mapfile -d '' E < /proc/$PID/environ; F=()
  for v in "${E[@]}"; do case "${v%%=*}" in CUDA_VISIBLE_DEVICES|PYTHONPATH|LOCAL_RANK|RANK|GROUP_RANK|ROLE_RANK|LOCAL_WORLD_SIZE|WORLD_SIZE|MASTER_ADDR|MASTER_PORT|TORCHELASTIC_*|TORCH_NCCL_*|NCCL_*|OMP_NUM_THREADS|MKL_NUM_THREADS|OPENBLAS_NUM_THREADS) ;; *) F+=("$v");; esac; done
else
  MODE=rebuilt
  # Stop step: the trainer has exited; nothing writes checkpoints any more. Rebuild its view (probe7 mountinfo).
  if w=$(writing); then echo "BUSY: checkpoint dir without complete.json and no trainer ($w)"; exit 5; fi
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
  echo "no trainer process; rebuilt namespace"
fi
RUNPY() { local zp=$1; shift; "${NSCMD[@]}" env -i "${F[@]}" SLURM_JOB_ID=172660 CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$zp" "$PY" -s -B "$@"; }
CK=$(ls -d "$R"/checkpoint_000${STEP}_* 2>/dev/null | head -1)
if [[ -z $CK || ! -f $CK/complete.json ]]; then
  CK=$(latest); echo "NO_STEP_CHECKPOINT for step $STEP; pinning the latest complete checkpoint ${CK##*/} (handover receipt expected to refuse)"
fi
CKN=${CK##*/}; echo "mode $MODE; checkpoints: $(ckdirs | sed 's#.*/##' | tr '\n' ' ')"
before=$(ckdirs | tr '\n' ' ')
# Handover receipt (items 1-5): RP.json = config, binding, preparation (verbatim config.preparation), checkpoint.
TC=$(RUNPY "$ZH" - "$XR" "$STEP" "$CKN" <<'PY'
import sys
from student_pilot.p3_provenance import file_pin, load, write
XR,STEP,CKN=sys.argv[1:4]
cfgp=XR+'/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/config.json'
cfg=load(cfgp); b=load(XR+'/binding.json')
write(XR+'/m'+STEP+'/RP.json',dict(config=file_pin(cfgp),binding=file_pin(XR+'/binding.json'),preparation=cfg['preparation'],checkpoint=file_pin(XR+'/'+CKN+'/complete.json')))
if STEP=='400':
  write(XR+'/m'+STEP+'/r.json',dict(config=file_pin(cfgp),binding=file_pin(XR+'/binding.json'),preparation=cfg['preparation']))
print(b['trainer_commit'])
PY
); rc_pins=$?
echo "pins rc=$rc_pins trainer_commit $TC"
rc_h=9; rc_e=na
if (( rc_pins == 0 )); then
  t0=$(date +%s)
  RUNPY "$ZH" -m launch_r1.p_handover_receipt --run-pins "$XR/m$STEP/RP.json" --artifact "$XR/m$STEP/artifact.json" --output "$XR/m$STEP/h.json" --trainer-commit "$TC" > "$D/h.out" 2>&1
  rc_h=$?; echo "handover receipt rc=$rc_h in $(( $(date +%s) - t0 )) s: $(tail -1 "$D/h.out" | cut -c1-200)"
  if [[ $STEP == 400 ]]; then
    t0=$(date +%s)
    RUNPY "$ZE" -m launch_r1.p_export_receipt --run-pins "$XR/m$STEP/r.json" --artifact "$XR/m$STEP/artifact.json" --output "$XR/m$STEP/e.json" --trainer-commit "$TC" > "$D/e.out" 2>&1
    rc_e=$?; echo "export-only receipt rc=$rc_e in $(( $(date +%s) - t0 )) s: $(tail -1 "$D/e.out" | cut -c1-200)"
  fi
fi
after=$(ckdirs | tr '\n' ' '); overlap=no; [[ "$after" == "$before" ]] && ! writing > /dev/null || overlap=yes
echo "checkpoint dirs unchanged during hashing: $([[ $overlap == no ]] && echo yes || echo NO)"
# Items 1-3 small files (ORCH 0036Z item 2, tree_rebuild10 0140Z/0259Z): every existing pinned file up to 64 MB reachable
# from the receipts, artifact, checkpoint manifest, config, binding, data receipt and the preparation/model receipts.
# Checkpoint shards, replicated.pt and full-weight shards are excluded in add() whatever pins them.
RUNPY "$ZH" - "$XR" "$STEP" "$CKN" > "$D/s.tar.part" 2> "$D/s.err" <<'PY'
import json,sys,os,io,hashlib,tarfile,re
XR,STEP,CKN=sys.argv[1:4]; CAP=64<<20; TOTAL=1536<<20
def sha(p):
  h=hashlib.sha256()
  with open(p,'rb') as f:
    for b in iter(lambda:f.read(1<<20),b''): h.update(b)
  return h.hexdigest()
def excluded(p):
  if re.search(r'/checkpoint_[^/]+/(shards/|replicated\.pt$)',p): return 'checkpoint shard'
  if re.search(r'/m\d+/full_weights/',p) and not p.endswith('/full_weights.json'): return 'export shard (GCS tar)'
  if p.endswith(('.sqlite','.db','.safetensors','.bin')): return 'store or weights'
  return None
seen={}; skipped=[]; queue=[]
def add(p,want=None,why='',level=0):
  p=str(p)
  if p in seen:
    if want and seen[p] and seen[p]['pin'] is None: seen[p]['pin']=want; seen[p]['match']=(want==seen[p]['sha256'])
    elif want and seen[p] and want!=seen[p]['pin']: seen[p].setdefault('other_pins',[]).append(want)
    return
  x=excluded(p)
  if x: skipped.append(dict(path=p,reason=x,why=why)); seen[p]=None; return
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
add(M+'/full_weights/full_weights.json',None,'milestone')
for f in ('binding.json','attempt_172660.json','inputs/data_receipt.json','inputs/first_step_172660.json',
          'inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/config.json'): add(XR+'/'+f,None,'run')
if CKN:
  c=XR+'/'+CKN; add(c+'/complete.json',None,'checkpoint')
  try:
    for name,pin in json.load(open(c+'/complete.json')).get('files',{}).items(): add(c+'/'+name,pin.get('sha256'),'checkpoint file')
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
items=[v for v in seen.values() if v]; keep=[]; acc=0
for v in items:
  if acc+v['bytes']>TOTAL: skipped.append(dict(path=v['path'],reason='total cap')); continue
  acc+=v['bytes']; keep.append(v)
man=dict(schema='r7-handover-small-files-v1',run='6ed2c7aa',step=int(STEP),checkpoint=CKN,files=keep,skipped=skipped,bytes=acc)
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as t:
  raw=json.dumps(man,indent=1,sort_keys=True).encode(); ti=tarfile.TarInfo('MANIFEST.json'); ti.size=len(raw); t.addfile(ti,io.BytesIO(raw))
  for v in keep: t.add(v['path'],arcname='files'+v['path'],recursive=False)
print('files',len(keep),'bytes',acc,'skipped',len(skipped),'mismatch',sum(1 for v in keep if not v['match']),file=sys.stderr)
PY
rc_copy=$?; echo "copy rc=$rc_copy $(tail -1 "$D/s.err")"
if (( rc_copy == 0 )); then mv "$D/s.tar.part" "$D/s.tar" && sha256sum "$D/s.tar"; else mv "$D/s.tar.part" "$D/s.tar.failed"; fi
for f in RP.json h.json r.json e.json; do [[ -f $R/m$STEP/$f ]] && cat "$R/m$STEP/$f" > "$D/$f" && sha256sum "$R/m$STEP/$f" "$D/$f"; done
if [[ $STEP == 400 ]]; then ok=$(( rc_e == 0 && rc_copy == 0 )); else ok=$(( rc_h == 0 && rc_copy == 0 )); fi
printf '{"step": %s, "mode": "%s", "checkpoint": "%s", "handover_rc": %s, "export_only_rc": "%s", "copy_rc": %s, "checkpoint_overlap": "%s", "ok": %s, "utc": "%s"}\n' \
  "$STEP" "$MODE" "$CKN" "$rc_h" "$rc_e" "$rc_copy" "$overlap" "$ok" "$(date -u +%FT%TZ)" > "$D/DONE.json"
echo "step end $(date -u +%FT%TZ) ok=$ok"
(( ok == 1 )) || exit 1
STEPSCRIPT
rc=$?; echo "srun rc=$rc"
cut -c1-300 "$LOG" | tail -30; ls -la "$D"; cat "$D/DONE.json" 2>/dev/null
for f in e.json h.json; do [[ -f $D/$f ]] && python3 -c "
import json,sys; h=json.load(open(sys.argv[1])); print(sys.argv[1].split('/')[-1],'schema',h['schema'],'step',h['step'],'pins',len(h['pins']),h.get('checkpoint_status',''))" "$D/$f"; done
exit $rc
