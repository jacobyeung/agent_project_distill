W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
K=$W/w24z8b/out/kit_qdp; G=$W/w24z11b/a_zffhb1q8/armed/kits/n_go
cat > /dev/null <<'X'
X
for k in $K $G; do echo "=====JSH $k"; python3 -I -c '
import json,base64,sys
v=json.load(open(sys.argv[1]));print(base64.b64decode(v["payload"]).decode())' $k/k/j.json | cat -n | cut -c1-300
echo "=====PJSON $k"; python3 -I -c '
import json,base64,sys
v=json.load(open(sys.argv[1]))
if isinstance(v,dict) and v.get("encoding"): v=json.loads(base64.b64decode(v["payload"]))
for key,x in v.items():
  s=json.dumps(x); print(key, s[:300] if len(s)<300 else s[:300]+"...(%d)"%len(s))' $k/k/p.json
done
echo =====RV; sed -n '250,300p' $K/b/rv.py | cat -n | sed 's/^/RV+249 /' | cut -c1-250
echo =====TARLR; tar tvf $K/k/t_e047002134f979bd.tar | grep -E "launch_r1/|carrier_c1_run|r1_persisted|p3_provenance" | cut -c1-160
