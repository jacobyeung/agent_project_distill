W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'
d=json.load(open(W+'/w24/out/UPLOADS_MINIMAL.json'))
names=[l.strip() for l in open(W+'/w24/out/UPLOADS_MINIMAL.list') if l.strip()]
ent={}
for k,v in d['kits'].items():
    for e in v['files']: ent.setdefault(e.get('name') or e.get('opaque_name'),e)
for n in names: print('%s  %s'%(ent[n]['sha256'],n))
PY
{ date -u +%TZ; tmux ls | grep tr13; d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild24b | head -1); tail -c 1500 $d/transcript.log | tr -cd "[:print:]\n" | grep -v "^[ +@-]" | tail -4 | cut -c1-300; tail -c 300 $W/w23/work/build23b/capacity_final_tr13.log; ls $W/w23/work/build23b/CAPACITY.json; } >&2
