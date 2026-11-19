K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24/kits/n; cd $K; ls b k | tr '\n' ' '; echo
grep -n "v\.json\|GO\b\|arm\|approv" b/*.py b/*.sh job.sh 2>/dev/null | cut -c1-220 | head -30
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json,base64;s=base64.b64decode(json.load(open('k/j.json'))['payload']).decode().split('\n')
for n,l in enumerate(s):
  if any(t in l for t in ('v.json','GO','arm','approv','t.py','u.py')): print(n,l[:240])
"
