F=/scratch/jjyeung/orch_n30/fb_pack; /scratch/jjyeung/envs/p1cpu/bin/python - <<'P'
import json; d=json.load(open('/scratch/jjyeung/orch_n30/fb_pack/prior2/out/MISSING_INPUTS.json'))
print({k:v for k,v in d.items() if k!='missing'})
for m in d['missing']: print(m.get('status'), m.get('bytes'), m['path'][:200], (m.get('sha256') or '')[:8], {k:v for k,v in m.items() if k not in ('path','sha256','bytes','expected_mirror_path','status')})
P
echo ==J; ls /scratch/jjyeung/orch_n30/tree_rebuild15_w24l 2>&1 | head
echo ==pointD; P=$(tmux list-panes -t fbp_pointD -F '#{pane_pid}'); echo pane $P; pstree -p $P | head -8; tail -c 300 $F/pointD/STATUS.md
