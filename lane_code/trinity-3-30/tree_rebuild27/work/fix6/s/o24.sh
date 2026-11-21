export TZ=UTC; date -u +%TZ
timeout 50 srun --overlap --jobid 174134 -N1 -n1 bash -c 'cd /tmp/a15_dbg_174134; echo "== c4"; python3 -I -B -c "
import json
c4=json.load(open(\"live/c4.json\"))
print(\"status\",c4.get(\"status\"),\"phase\",c4.get(\"phase\"))
for s,r in c4[\"streams\"].items():
    print(s,\"status\",r[\"status\"],\"refusals\",r[\"refusals\"][:8]); print(\"   counts\",r[\"counts\"]); print(\"   result\",r[\"result\"]); print(\"   keys\",r[\"protected_keys\"])
k=json.load(open(\"live/c2.json\")); print(\"c2 keys\",len(k),k[:6])
"; echo "== postb"; cat log/postb.log; echo "== h log"; tail -c 1500 log/h_n2k.log; echo; echo "== post3"; cut -c1-500 log/post3_n2k.log; ls -la n2k n2k/p/q live | cut -c1-90'
