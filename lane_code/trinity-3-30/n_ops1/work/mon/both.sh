# n_ops1 batched Orchard check (read-only). Placeholders: 174113 (job id or 0), - (cached metrics path or -)
export TZ=UTC; J=174113; MP='-'; X=/project/community/jjyeung/okh7/x_22c714e1
echo "@@NOW $(date -u +%FT%TZ)"
echo "@@SQ"; squeue -u $USER -h -o "%i|%j|%P|%T|%M|%l|%L|%R|%N|%S"
echo "@@NEWEST $(ls $X/j/ 2>/dev/null | grep -E '^[0-9]+\.out$' | sort -n | tail -1)"
echo "@@DF $(df -BG --output=avail /project/community | tail -1 | tr -d ' G')"
if [[ $J != 0 ]]; then
 echo "@@SACCT"; sacct -j $J -X -n -P -o JobID,JobName%40,Partition,State,ExitCode,Elapsed,Timelimit,AllocTRES%90,NodeList,Submit,Start,End
 echo "@@SCTL"; scontrol show job $J 2>/dev/null | tr ' ' '\n' | grep -E '^(JobName|Command|WorkDir|StdOut|StdErr|TimeLimit|RunTime|NodeList|Partition|JobState|Reason)=' | cut -c1-300
 O=$X/j/$J.out; [[ -f $O ]] || { O2=$(ls $X/j/*_$J.log 2>/dev/null | head -1); [[ -n $O2 ]] && O=$O2; }
 echo "@@JOUT $(stat -c %s $O 2>/dev/null || echo -1)"
 test -f $O && grep -v "_cgroup_procs_check\|unable to read" $O | grep -E "gpu0|resolve|^[0-9a-f]{64}$|stage |frames f|init mirror|overlay on|^\{\"v\"|ADMIT|REFUS|Traceback|Error|error|E[0-9][0-9]|job done|rc=|Killed|CANCEL|DUE TO|oom" | cut -c1-300 | tail -40
 echo "@@JTAIL"; test -f $O && grep -v "_cgroup_procs_check\|unable to read" $O | tail -6 | cut -c1-300
 E2=${O%.log}.err; [[ $O == *.log && -s $E2 ]] && { echo "@@JERR $(stat -c %s $E2)"; grep -v "_cgroup_procs_check\|unable to read\|FutureWarning\|warnings.warn" $E2 | tail -8 | cut -c1-300; }
 echo "@@LIVE"; ls -la --time-style=+%T $X/o/$J/live 2>/dev/null | tail -n +4 | cut -c1-200 | tail -25; for m in $X/o/$J/live/gcs_*.done $X/o/$J/live/gcs_*.json; do test -f $m && { echo "== $m"; head -c 600 $m; echo; }; done
 echo "@@NR"; ls -la --time-style=+%T $X/n_r 2>/dev/null | tail -n +4; for m in $X/o/$J/live/WAITING_REVIEW*; do test -f $m && { echo "== $m"; head -c 400 $m; echo; }; done
 echo "@@NCK"; ls -la --time-style=+%T /project/community/jjyeung/okh7/n_ck/$J 2>/dev/null | tail -n +2 | head -8
 echo "@@ODIR"; ls -la --time-style=+%T $X/o/$J 2>/dev/null | tail -n +4
 test -f $X/o/$J/o.tar && { echo "@@OTAR"; cat $X/o/$J/RESULT.json 2>/dev/null; echo; for m in q.log rooms.log t.log; do tar xzOf $X/o/$J/o.tar $m 2>/dev/null | tail -4 | cut -c1-400; done; }
 if squeue -j $J -h -o %T 2>/dev/null | grep -q RUNNING; then
  echo "@@NODE"
  timeout 150 srun --overlap --jobid $J -n1 -N1 timeout 120 nice -n 19 bash -s <<'INNER' 2>&1 | cut -c1-600
J=174113; MP='-'
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
echo "@@RCPT $(cat $Q/live_spool/private/*.receipts.jsonl 2>/dev/null | wc -l)"
echo "@@TRAIN"; ls -la --time-style=+%T $Q/r $Q/train 2>/dev/null | tail -n +4 | cut -c1-160 | tail -20
echo "@@CK"; find $Q/r $Q/train $Q/x $Q/rp -maxdepth 6 -type d \( -name 'checkpoint_*' -o -name 'm[0-9][0-9]*' -o -name 'export*' \) -printf '%TT %P\n' 2>/dev/null | sort | tail -8 | cut -c1-200
find $Q/r $Q/train $Q/x $Q/rp -maxdepth 7 \( -name 'complete.json' -o -name 'artifact.json' \) -printf '%TT %P\n' 2>/dev/null | sort | tail -4 | cut -c1-200
cg=$(cut -d: -f3 /proc/self/cgroup | head -1); d=/sys/fs/cgroup$cg; for i in 1 2 3; do d=$(dirname $d); [[ -f $d/memory.max ]] && echo "@@CG $d max=$(cat $d/memory.max) cur=$(cat $d/memory.current) $(grep -E '^(anon|file|shmem|file_dirty|file_writeback) ' $d/memory.stat | tr '\n' ' ') oom=$(grep -E '^oom ' $d/memory.events 2>/dev/null | cut -d' ' -f2) oom_kill=$(grep -E '^oom_kill ' $d/memory.events 2>/dev/null | cut -d' ' -f2) high=$(grep -E '^high ' $d/memory.events 2>/dev/null | cut -d' ' -f2) cpu_usec=$(grep usage_usec $d/cpu.stat | head -1 | cut -d' ' -f2)"; done
echo "@@GPU"; nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>&1 | head -8
echo "@@PS"; ps -u $USER -o pid,etimes,pcpu,rss,args --sort=-pcpu | head -7 | cut -c1-200
echo "@@ATT"; timeout 25 nice -n 19 python3 -B - "$Q" "/project/community/jjyeung/okh7/x_22c714e1/o/$J/live" <<'PY' 2>&1 | head -40 | cut -c1-400
import os,sys,json,re
seen=set()
for root in sys.argv[1:]:
  if not os.path.isdir(root):continue
  base=root.rstrip('/').count('/')
  for d,ds,fs in os.walk(root):
    if d.count('/')-base>=3:ds[:]=[]
    for f in fs:
      p=os.path.join(d,f)
      try:
        sz=os.path.getsize(p)
        if sz==0 or sz>60e6 or f.endswith(('.tar','.tgz')):continue
        h=open(p,'rb').read(4096)
      except Exception:continue
      if b'"http"' not in h or b'"name"' not in h:continue
      ob={};n=0
      for l in open(p,errors='replace'):
        try:r=json.loads(l)
        except Exception:continue
        nm=r.get('name');t=r.get('time')
        if not isinstance(nm,str) or not isinstance(t,(int,float)):continue
        n+=1;m=re.match(r'^(.*?)\.j(\d+)\.part(\d\d)-of-\d\d$',nm)
        if not m:continue
        o=ob.setdefault(m.group(1),{'p':{},'att':0,'err':0})
        q=o['p'].setdefault(m.group(3),[t,None]);o['att']+=1;o['err']+=bool(r.get('error'))
        if r.get('http') in (200,201):q[1]=t
      key=(sz,n)
      if key in seen:continue
      seen.add(key);print('@@ATTF',p.replace(sys.argv[1],'$Q'),sz,n)
      for k,o in sorted(ob.items()):
        ps=o['p'];dn={a:b for a,b in ps.items() if b[1]}
        print('@@ATTO',json.dumps({'f':f,'obj':k,'parts':len(ps),'done':len(dn),'first':min(v[0] for v in ps.values()),'last_done':max([v[1] for v in dn.values()] or [None]) if dn else None,'att':o['att'],'err':o['err'],'part_walls':{a:round(b[1]-b[0],2) for a,b in dn.items()}}))
PY
INNER
  echo "@@SRUN rc=${PIPESTATUS[0]}"
 fi
fi
echo "@@EXTRA"
true
echo "@@END"
