W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; S=$W/work/sel24; cd $S && tar czf - orchard PROVENANCE.md REPORT.md SELECTION_TABLE.md | base64 -w0; echo; echo "@@INV"; f=$(ls $W/w24h/work/build24m4h/INVARIANTS.json $W/w24h/out/INVARIANTS.json 2>/dev/null | head -1); nice -n 10 python3 -c "
import json,sys;d=json.load(open('$f'));s=json.dumps(d)
import re
for k in ('capsule','identity','payload'):
  pass
print(json.dumps({k:v for k,v in d.items() if 'ident' in k.lower() or 'capsule' in k.lower() or 'c.json' in k.lower()})[:1500])"
