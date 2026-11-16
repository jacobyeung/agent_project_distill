S=/dev/shm/jjyeung/b05; date -u; grep -v -i "warn\|pynvml\|Watching" $S/pilot_console.log | tail -5 | cut -c1-400; ls $S/pilot; python3 - <<'PY'
import json
try:
    rows=[json.loads(l) for l in open('/dev/shm/jjyeung/b05/pilot/train.jsonl')]
except Exception as e: print('no train.jsonl', e); rows=[]
tr=[r for r in rows if r['event']=='train']; va=[r for r in rows if r['event']=='validation']
if tr: r=tr[-1]; print('step',r['step'],'total',round(r['losses']['total'],3),'gn',round(r['grad_norm'],1),'el',round(r['elapsed_seconds']))
for v in va[-2:]: print('VAL',v['step'],{k:(round(x,3) if isinstance(x,float) else x) for k,x in v['metrics'].items() if k!='losses'},v['status'],v['reason'])
for r in rows:
    if r['event'] not in ('train','validation'): print(json.dumps(r)[:300])
PY
python3 -c "import json;d=json.load(open('/dev/shm/jjyeung/b05/pilot/RUN.json'));print({k:d[k] for k in d if 'ceil' in k or 'bar' in k})" 2>&1 | tail -1
nvidia-smi -i 2 --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader; tmux ls | grep b05
