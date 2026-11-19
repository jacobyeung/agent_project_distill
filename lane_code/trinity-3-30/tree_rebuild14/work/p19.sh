K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_n_go; date -u +%TZ
python3 -B -c "
import json,sys,base64
d=json.load(open(sys.argv[1]))
if 'payload' in d: d=json.loads(base64.b64decode(d['payload']))
def walk(x,p):
  if isinstance(x,dict):
    for k,v in x.items(): walk(v,p+'.'+str(k))
  elif isinstance(x,list):
    for i,v in enumerate(x): walk(v,p+'['+str(i)+']')
  elif isinstance(x,str) and ('93ccadab' in x or 'm544' in x): print(p, x[:300])
walk(d,'l')
" $K/k/l.json </dev/null | head -20
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild24f | head -1); ls $d | tr '\n' ' '; grep -c "at capacity" $d/transcript.log
