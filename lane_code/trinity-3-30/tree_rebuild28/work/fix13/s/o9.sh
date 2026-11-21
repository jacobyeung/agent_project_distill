export TZ=UTC; date -u +%TZ
timeout 40 srun --overlap --jobid 174134 -N1 -n1 bash -c 'cd /tmp/a15_f13_174134; for f in t3 t4; do echo == $f; grep "^EV" log/$f.log | grep -v "LAYOUT\|STREAM\|cs.publish (d" | cut -c1-1500 | tail -3; done; echo == live c4; ls -la --time-style=+%H:%M:%S live; python3 -c "
import json; v=json.load(open(\"live/c4.json\")); import base64; v=json.loads(base64.b64decode(v[\"payload\"])) if \"payload\" in v else v
for s,r in v[\"streams\"].items(): print(s, r[\"status\"], json.dumps(r[\"counts\"]), r[\"refusals\"][:3], json.dumps(r[\"result\"])[:2500])
"; ps -u $(id -un) -o pid,etime,pcpu,args --width 150 | grep -E "t1.py" | grep -v grep'
