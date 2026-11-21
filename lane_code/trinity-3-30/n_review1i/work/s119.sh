W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w27fix/n_go; T=/scratch/jjyeung/orch_n30/n_review/r1f/tcpx
date -u +%TZ
sed -n 240,262p $K/b/z.py < /dev/null | cut -c1-250; echo ...; sed -n 424,434p $K/b/z.py < /dev/null | cut -c1-250
echo "== which resolve fn does resolve.py call"; grep -n "def \|import\|resolve(" $K/b/resolve.py < /dev/null | head -20
echo "== verify kit"; (cd $T && /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import sys; sys.path.insert(0,'.'); from launch_r1.build import verify; print('verify',verify('$K'))" < /dev/null 2>&1 | tail -1); diff -rq $W/w26fix2/n_go $K < /dev/null; sha256sum $W/w27fix/s27fix_n_go.tar < /dev/null
echo "== j.sh order (launch kit k/j.json decoded)"; /scratch/jjyeung/envs/p1cpu/bin/python -I -c "
import json,base64;v=json.load(open('$K/k/j.json'));s=base64.b64decode(v['payload']).decode()
L=s.splitlines()
for i,l in enumerate(L,1):
  if any(t in l for t in ('tk_stage_model','a.py\" q','a.py q','b/a.py','--ro-bind \"\$S/c7d31ddd','tk_stage_extra()','tk_stage_model()')): print(i,l[:200])
" < /dev/null
