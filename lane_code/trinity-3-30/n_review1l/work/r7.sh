V=$(ls -d /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14/work/gate_174246_20261122T021543Z/in/v.json 2>/dev/null)
echo "v=$V"; [ -f "$V" ] || exit 1
D=/scratch/jjyeung/orch_n30/n_review1l/w24z14b/work/smoke_$(date -u +%H%M%S)
mkdir -p $D/in && cp $V $D/in/v.json
timeout 900 /scratch/jjyeung/orch_n30/n_review1l/w24z14b/out/admit_test.sh $D/in/v.json $D/admit > $D/admit.stdout 2>&1 < /dev/null; echo admit_rc=$?
python3 -c "
import json,sys
a=json.load(open('$D/admit/ADMIT.json')) if __import__('os').path.exists('$D/admit/ADMIT.json') else None
if a is None: print('no ADMIT.json'); sys.exit()
print('tree',a.get('tree_sha256'),'branch',a.get('branch_taken'))
from collections import Counter
print(Counter(c['status'] for c in a['checks']))
for c in a['checks'][:40]: print(c['name'],c['status'],(c.get('reason') or '')[:110])
"
ls $D/admit | head
