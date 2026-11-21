W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24z12/out/kit_n_go; P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%TZ
grep -n "bind\|bwrap" $K/b/z.py < /dev/null | cut -c1-300 | head -40
cd /tmp; nice -n 10 $P -I -s -B -c "
import sys;sys.path.insert(0,'$K/b')
from z import load
p=load('$K/k/p.json');print({k:(v if len(str(v))<200 else str(v)[:200]) for k,v in p.items() if not isinstance(v,(list,dict)) or len(str(v))<300})
a=load('$K/k/a.json');print('a.json',{k:a[k] for k in a if k in ('review_wait_seconds','GO','discovery')})
" < /dev/null
