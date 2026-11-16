set -euo pipefail
export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud
cd /project/community/jjyeung/okh7/d9c35d0a
date -u +%FT%TZ; ls -la
sha256sum a.tar b.tar c.tar d.tar FAMILY.json
for f in b.tar d.tar; do timeout 900 gsutil -q cp $f gs://cmu-gpucloud-jjyeung/q8/d9c35d0a/$f; echo "cp $f ok"; done
gsutil ls -la gs://cmu-gpucloud-jjyeung/q8/d9c35d0a/
/usr/bin/python3 - <<'PY'
import json,subprocess,os
g={}
for k in 'abcd':
    out=subprocess.run(['gsutil','ls','-a','gs://cmu-gpucloud-jjyeung/q8/d9c35d0a/'+k+'.tar'],capture_output=True,text=True,check=True).stdout.split()
    g[k]=out[-1].rsplit('#',1)[1]
json.dump(g,open('g.json','w'));print('g.json',g)
PY
timeout 1800 /usr/bin/python3 -s -B c/u.py --family FAMILY.json --generations g.json --out r.json
echo "u.py ok"; cat r.json; echo
/usr/bin/python3 -s -B c/o.py packet --family FAMILY.json --receipts r.json --out /project/community/jjyeung/okh7/d9c35d0a/p/ece5eea1c1ec94e169abf835 --token ece5eea1c1ec94e169abf835 --deadline-utc 2026-11-16T16:15:00Z
P=/project/community/jjyeung/okh7/d9c35d0a/p/ece5eea1c1ec94e169abf835
ls -la $P; cat $P/a.sh; cat $P/b.json; sha256sum $P/*
sbatch --nice=200 $P/a.sh
sleep 5; squeue -u $USER -o '%i %j %P %T %M %l %S %Q %y' | grep -E "JOBID|ece5eea1c1ec94e169abf835"
scontrol show job $(squeue -h -u $USER -n a15_cot_apece5eea1c1ec94e169abf835 -o %i) | grep -E "JobId|TimeLimit|Nice|Partition|TRES|StartTime|Deadline"
