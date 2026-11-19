W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; G=$W/w24/work/build24d/go
for f in $G/v.json $W/inputs/p_configs/RUNTIME_CONFIG_171377_673bc60f.json $W/inputs/p_configs/c4_21528289.json $W/inputs/p_configs/cprime_31abe087.json; do echo "-- $f"; python3 -B -c "
import json,sys,base64
d=json.load(open(sys.argv[1]))
if 'payload' in d: d=json.loads(base64.b64decode(d['payload']))
print(sorted(k for k in d if 'r2' in k or 'persist' in k or 'durable' in k))
print('r2_persistence' in d, json.dumps(d.get('r2_persistence'))[:500])
print('output',d.get('output'),'id' , 'r2_identity' in d)
" $f </dev/null; done
