W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24z12/out/kit_n_go
date -u +%TZ
grep -n "n_root\|'--bind'\|\"--bind\"\|bind-try\|'o'/\|/'o'\|live" $K/b/z.py < /dev/null | cut -c1-260 | head -50
grep -n "n_root" $K/k/p.json < /dev/null | cut -c1-200; python3 -c "import json;d=json.load(open('$K/k/p.json'));print({k:v for k,v in d.items() if 'root' in k})" < /dev/null
grep -n "review_wait_seconds" $K/k/a.json < /dev/null
