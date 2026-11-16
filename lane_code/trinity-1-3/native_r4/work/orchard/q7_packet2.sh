set -euo pipefail
export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud
cd /project/community/jjyeung/okh7/d9c35d0a
date -u +%FT%TZ
sha256sum a.tar b.tar c.tar d.tar FAMILY.json
tar tvf b.tar | cut -c1 | sort | uniq -c
timeout 900 gsutil -q cp b.tar gs://cmu-gpucloud-jjyeung/q8/d9c35d0a/b.tar; echo "cp b.tar ok"
gsutil ls -la gs://cmu-gpucloud-jjyeung/q8/d9c35d0a/
/usr/bin/python3 - <<'PY'
import json,subprocess
g={}
for k in 'abcd':
    out=subprocess.run(['gsutil','ls','-a','gs://cmu-gpucloud-jjyeung/q8/d9c35d0a/'+k+'.tar'],capture_output=True,text=True,check=True).stdout.split()
    g[k]=out[-1].rsplit('#',1)[1]
json.dump(g,open('g2.json','w'));print('g2.json',g)
PY
timeout 1800 /usr/bin/python3 -s -B c/u.py --family FAMILY.json --generations g2.json --out r2.json
echo "u.py ok"; python3 -c "import json;[print(k,v['sha256'],v['bytes'],v['generation'],v['verified']) for k,v in json.load(open('r2.json')).items()]"
/usr/bin/python3 -s -B c/o.py packet --family FAMILY.json --receipts r2.json --out /project/community/jjyeung/okh7/d9c35d0a/p/8f7817fb16bc218af285dc61 --token 8f7817fb16bc218af285dc61 --deadline-utc 2026-11-16T16:15:00Z
sha256sum /project/community/jjyeung/okh7/d9c35d0a/p/8f7817fb16bc218af285dc61/*; cat /project/community/jjyeung/okh7/d9c35d0a/p/8f7817fb16bc218af285dc61/a.sh
squeue -p general -h -u $USER -o '%i %j %T'
