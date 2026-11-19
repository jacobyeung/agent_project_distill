W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr10; tail -5 $W/work/build15_dispatch.log; RB=$(ls -td /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild15 | head -1); echo RB=$RB; ls $RB; tail -c 600 $W/w15/work/build15/STATUS.md 2>/dev/null
echo "== div search (w14 kits, inputs, mirrors rows_r1/rows_r2 json)"; for d in $W/w14/work/build14/kits $W/w14/work/n1fix2/inputs $W/w14/work/build13 /scratch/jjyeung/n30_mirror/rows_r1 /scratch/jjyeung/n30_mirror/rows_r2 /scratch/jjyeung/n30_mirror/count_diag; do find $d -name '*.json' -size +100k -size -20M 2>/dev/null; done | xargs -r sha256sum | grep -E '^0d28fdd4' | head
echo "== kit_config pins"; /scratch/jjyeung/envs/p1cpu/bin/python -I -s - <<'PY'
import json,os
c=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w14/work/build14/inputs/kit_config.json'))
def walk(o,k=''):
    if isinstance(o,dict):
        if 'path' in o and 'sha256' in o: print(('OK ' if os.path.exists(o['path']) else 'MISSING ')+k, o['path'][:150], str(o['sha256'])[:8])
        for a,b in o.items(): walk(b,k+'.'+a)
    elif isinstance(o,list):
        for i,b in enumerate(o): walk(b,k+'[%d]'%i)
walk(c)
print(sorted(c.keys()))
PY
