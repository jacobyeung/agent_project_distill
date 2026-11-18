O=/project/community/jjyeung/okh7; B=$O/i_1be16f28
date -u +%TZ; pgrep -f "i_1be16f28/g.sh" >/dev/null && echo GATE_RUNNING || echo GATE_NOT_RUNNING
tail -n 15 $O/t_c94bbc4e.g2.log 2>/dev/null | cut -c1-300
test -f $B/gate.json && python3 -c "import json;d=json.load(open('$B/gate.json'));print({k:v for k,v in d.items() if not isinstance(v,(list,dict))}); print({k:v for k,v in d.items() if isinstance(v,dict)})" 2>&1 | cut -c1-1500
