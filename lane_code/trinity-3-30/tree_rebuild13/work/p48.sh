K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24/kits/q; cd $K
sed -n 1,14p b/f.sh; echo ===; grep -n "f\.sh" b/*.py b/*.sh job.sh | cut -c1-220
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json,base64;s=base64.b64decode(json.load(open('k/j.json'))['payload']).decode().split('\n')
for n,l in enumerate(s):
  if 'f.sh' in l: print(n,l[:260])
"
sed -n 18,26p job.sh
