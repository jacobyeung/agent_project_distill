W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W/w24z12/out
for k in kit_n kit_qd; do /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json,base64,sys
v=json.load(open('$k/k/j.json'))
raw=base64.b64decode(v['payload']) if isinstance(v,dict) and 'payload' in v else json.dumps(v).encode()
open('/tmp/tr24_j_$k.sh','wb').write(raw)"; echo "== $k $(sha256sum $k/k/j.json | cut -c1-16)"; grep -n "x.py\|MODE\|mode\b\| r \| q \| t " /tmp/tr24_j_$k.sh | grep -v "^\s*#" | head -20 | cut -c1-200; done
cmp $W/w24z12/out/kit_n/k/j.json $W/w24z12/out/kit_qd/k/j.json && echo J_SAME
grep -n "4e8e6c04\|base/rows.sqlite\|staging inventory\|pool_copy" $W/w24z11/out/ARM_LAUNCH_24M4Z11.md | cut -c1-300 | head
