set -euo pipefail
export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud
cd /project/community/jjyeung/okh7/d9c35d0a
date -u +%FT%TZ
printf '%s  %s
' 795f7255e940af0d51528523841ebe59581499e47398bb22d40f0404d207df10 a.tar 0eadd83e9f859347438ffd3a483147a87d1ae05bc19eba28db4022ef73889664 b.tar dc40cf60212a34c2789a9821bb558e0592074c4d81b0bb1239e55c238f093eaa c.tar 9a1de8608ea0e75e2f2436259b81f0e991b2007002a59de11d85062e8384d08f d.tar 3cf68794ee715bdad6936486ce64edc72c40b08165f9e0763c126aaa685eecf6 FAMILY.json | sha256sum -c -
for f in a.tar b.tar c.tar d.tar; do tar tvf $f | cut -c1 | sort | uniq -c > /dev/shm/types_$$; echo "$f types: $(tr '\n' ' ' < /dev/shm/types_$$)"; if awk '$2!="-" && $2!="d"{bad=1} END{exit !bad}' /dev/shm/types_$$; then echo "FAIL member types $f"; exit 3; fi; done
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
