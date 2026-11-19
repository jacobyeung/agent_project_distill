F=/scratch/jjyeung/orch_n30/fb_pack; /scratch/jjyeung/envs/p1cpu/bin/python - <<'P'
import json,os; d=json.load(open('/scratch/jjyeung/orch_n30/fb_pack/prior2/out/MISSING_INPUTS.json'))
for k,v in d.items():
  if k in ('missing','status','production_gate'): continue
  if isinstance(v,list):
    for m in v: print(k, m.get('status'), m.get('path','')[:160], (m.get('sha256') or '')[:8], os.path.exists(m.get('expected_mirror_path','/nonexist')))
  else: print(k, str(v)[:300])
P
P=$(tmux list-panes -t fbp_pointD -F '#{pane_pid}'); C=$(pgrep -P $(pgrep -P $(pgrep -P $P)) -x codex | head -1); echo codex=$C; [ -n "$C" ] && kill -STOP $C $(pgrep -P $C) && ps -o pid,stat,cmd -p $C | cut -c1-80
