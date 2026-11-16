set -euo pipefail
export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud
cd /project/community/jjyeung/okh7/d9c35d0a
date -u +%FT%TZ
mkdir c && tar xf c.tar -C c && sha256sum c/o.py
printf '%s  %s\n' 795f7255e940af0d51528523841ebe59581499e47398bb22d40f0404d207df10 a.tar 0eadd83e9f859347438ffd3a483147a87d1ae05bc19eba28db4022ef73889664 b.tar 6a3192ac727292b1c7badf5a55847ed17d3639991927b1dc05163d8a27d4a88b c.tar 9a1de8608ea0e75e2f2436259b81f0e991b2007002a59de11d85062e8384d08f d.tar 249ce1a1310c4ec8ca0dc04730b4bb3326b2279324868993c279dd389ba9f26f FAMILY.json | sha256sum -c -
for f in a.tar b.tar c.tar d.tar; do T=$(tar tvf $f | cut -c1 | sort | uniq -c | tr '\n' ' '); echo "$f types: $T"; if tar tvf $f | cut -c1 | grep -qv '^[-d]$'; then echo "FAIL member types $f"; exit 3; fi; done
timeout 900 gsutil -q cp c.tar gs://cmu-gpucloud-jjyeung/q8/d9c35d0a/c.tar; echo "cp c.tar ok"
gsutil ls -la gs://cmu-gpucloud-jjyeung/q8/d9c35d0a/
/usr/bin/python3 - <<'PY'
import json,subprocess
g={}
for k in 'abcd':
    out=subprocess.run(['gsutil','ls','-a','gs://cmu-gpucloud-jjyeung/q8/d9c35d0a/'+k+'.tar'],capture_output=True,text=True,check=True).stdout.split()
    g[k]=out[-1].rsplit('#',1)[1]
json.dump(g,open('g4.json','w'));print('g4.json',g)
PY
timeout 1800 /usr/bin/python3 -s -B c/u.py --family FAMILY.json --generations g4.json --out r4.json
echo "u.py ok"; python3 -c "import json;[print(k,v['sha256'],v['bytes'],v['generation'],v['verified']) for k,v in json.load(open('r4.json')).items()]"
/usr/bin/python3 -s -B c/o.py packet --family FAMILY.json --receipts r4.json --out /project/community/jjyeung/okh7/d9c35d0a/p/d627d31523064791d2ce3456 --token d627d31523064791d2ce3456 --deadline-utc 2026-11-16T17:33:00Z
sha256sum /project/community/jjyeung/okh7/d9c35d0a/p/d627d31523064791d2ce3456/*; cat /project/community/jjyeung/okh7/d9c35d0a/p/d627d31523064791d2ce3456/a.sh
