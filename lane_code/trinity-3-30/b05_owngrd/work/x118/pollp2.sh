S=/dev/shm/jjyeung/b05; date -u; tmux ls | grep b05; nvidia-smi -i 2 --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
grep -v -i "warn\|pynvml\|Watching" $S/pilot_console.log | tail -4 | cut -c1-300
python3 - <<'PY'
import json
rows=[json.loads(l) for l in open('/dev/shm/jjyeung/b05/pilot/train.jsonl')]
tr=[r for r in rows if r['event']=='train']; va=[r for r in rows if r['event']=='validation']
print('last step',tr[-1]['step'],'el',round(tr[-1]['elapsed_seconds']))
for lo,hi in ((0,100),(100,200),(200,300),(300,400),(400,500),(500,600),(600,700),(700,800)):
    w=[r for r in tr if lo<=r['step']<hi]
    if not w: continue
    ks=w[0]['losses'].keys()
    print('TR',lo,hi,{k:round(sum(r['losses'][k] for r in w)/len(w),3) for k in ks})
for v in va:
    print('VAL',v['step'],v['status'],v['reason'],{k:round(x,3) for k,x in v['metrics'].get('losses',{}).items()})
    print('   ',{k:(round(x,3) if isinstance(x,float) else x) for k,x in v['metrics'].items() if k!='losses'})
for r in rows:
    if r['event'] not in ('train','validation','recall_ceilings'): print(json.dumps(r)[:400])
print('keys', list(tr[-1].keys()))
PY
