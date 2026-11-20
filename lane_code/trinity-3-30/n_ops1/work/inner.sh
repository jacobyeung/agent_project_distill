Q=/tmp/q_22c714e1_$J; [[ -d $Q ]] || Q=${SLURM_TMPDIR:-/tmp}/q_22c714e1_$J
echo "@@Q $Q $(test -d $Q && echo present || echo absent)"
echo "@@TMPDF $(df -BG --output=avail /tmp | tail -1 | tr -d ' G')"
for f in q.log rooms.log h.log t.log v.json j.sh; do echo "@@LOG $f $(stat -c '%s %Y' $Q/$f 2>/dev/null || echo '-1 0')"; done
for f in q.log rooms.log h.log t.log; do test -s $Q/$f && { echo "@@TAIL $f"; grep -v "FutureWarning\|being deprecated\|warnings.warn" $Q/$f | tail -n 12 | cut -c1-400; echo "@@ERRS $f $(grep -c -E 'Traceback|Error|REFUS|E[0-9][0-9]\b|nan|inf\b' $Q/$f)"; grep -E 'Traceback|Error|REFUS' $Q/$f | tail -3 | cut -c1-400; }; done
test -s $Q/p/q/RESULT.json && echo "@@QRES $(python3 -B -c "import json,sys;d=json.load(open(sys.argv[1]));print(json.dumps({k:d.get(k) for k in ('status','init_milestone','reason','reasons','config','rows','counts')})[:1500])" $Q/p/q/RESULT.json 2>&1)"
echo "@@PROG"; find $Q/p $Q/x $Q/r $Q/train -maxdepth 4 -newermt '-3 minutes' -printf '%TT %s %P\n' 2>/dev/null | sort | tail -8 | cut -c1-200
echo "@@PCOUNT $(find $Q/p $Q/x $Q/r $Q/train -maxdepth 6 2>/dev/null | wc -l)"
if [[ $MP == - || ! -f $MP ]]; then MP=$(ls $Q/r/metrics_$J.jsonl 2>/dev/null || ls $Q/train/metrics_$J.jsonl 2>/dev/null || find $Q/r $Q/train $Q/x $Q/p $Q/rp -maxdepth 7 -name 'metrics_*.jsonl' 2>/dev/null | head -1); fi
echo "@@MP ${MP:--}"
if [[ -n $MP && -f $MP ]]; then
python3 -B - "$MP" <<'PY'
import json,sys,os,math
p=sys.argv[1];sz=os.path.getsize(p);f=open(p,'rb');f.seek(max(0,sz-1200000));raw=f.read()
lines=raw.split(b'\n');lines=lines[1:] if sz>1200000 else lines
nrows=sum(1 for _ in open(p,'rb'))
print('@@MROWS',nrows,sz)
def nf(v):
  if isinstance(v,float):return not math.isfinite(v)
  if isinstance(v,dict):return any(nf(x) for x in v.values())
  if isinstance(v,list):return any(nf(x) for x in v)
  return False
for l in lines[-6:]:
  if not l.strip():continue
  try:r=json.loads(l)
  except Exception as e:print('@@MBAD',str(e)[:80]);continue
  out=dict(step=r.get('step'),ranks=[])
  for k in r.get('ranks',[]):
    c=k.get('components',{})
    out['ranks'].append(dict(rank=k.get('rank'),wall=k.get('wall_seconds'),data=k.get('data_seconds'),skip=len(k.get('skipped_microsteps',[]) or []),
      sm=k.get('stream_means'),csum=sum(v for v in c.values() if isinstance(v,(int,float))),gn=k.get('gradient_norms'),nf=nf(k),
      peak=k.get('peak_allocated_bytes'),ck=k.get('checkpoint_seconds'),ex=k.get('export_seconds')))
  out['top_nf']=nf({x:y for x,y in r.items() if x!='ranks'})
  print('@@STEP',json.dumps(out,allow_nan=True))
PY
fi
echo "@@LSTATE"; ls -la --time-style=+%T $Q/live_spool/state 2>/dev/null | tail -n +4 | cut -c1-200 | tail -20; for m in $Q/live_spool/state/gcs_*.done $Q/live_spool/state/gcs_*.json; do test -f $m && { echo "== $m"; head -c 400 $m | sed -E 's#https://[^ "]*#<URL>#g'; echo; }; done; tail -n 3 $Q/live_spool/retry.log $Q/j2.retry.log 2>/dev/null | cut -c1-200
echo "@@TRAIN"; ls -la --time-style=+%T $Q/r $Q/train 2>/dev/null | tail -n +4 | cut -c1-160 | tail -20
echo "@@CK"; find $Q/r $Q/train $Q/x $Q/rp -maxdepth 6 -type d \( -name 'checkpoint_*' -o -name 'm[0-9][0-9]*' -o -name 'export*' \) -printf '%TT %P\n' 2>/dev/null | sort | tail -8 | cut -c1-200
find $Q/r $Q/train $Q/x $Q/rp -maxdepth 7 \( -name 'complete.json' -o -name 'artifact.json' \) -printf '%TT %P\n' 2>/dev/null | sort | tail -4 | cut -c1-200
cg=$(cut -d: -f3 /proc/self/cgroup | head -1); d=/sys/fs/cgroup$cg; for i in 1 2 3; do d=$(dirname $d); [[ -f $d/memory.max ]] && echo "@@CG $d max=$(cat $d/memory.max) cur=$(cat $d/memory.current) $(grep -E '^(anon|file|shmem) ' $d/memory.stat | tr '\n' ' ') cpu_usec=$(grep usage_usec $d/cpu.stat | head -1 | cut -d' ' -f2)"; done
echo "@@GPU"; nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>&1 | head -8
echo "@@PS"; ps -u $USER -o pid,etimes,pcpu,rss,args --sort=-pcpu | head -7 | cut -c1-200
