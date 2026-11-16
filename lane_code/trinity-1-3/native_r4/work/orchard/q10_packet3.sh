set -euo pipefail
export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud
cd /project/community/jjyeung/okh7/d9c35d0a
date -u +%FT%TZ
mkdir c && tar xf c.tar -C c && sha256sum c/o.py
printf '%s  %s\n' 795f7255e940af0d51528523841ebe59581499e47398bb22d40f0404d207df10 a.tar 0eadd83e9f859347438ffd3a483147a87d1ae05bc19eba28db4022ef73889664 b.tar 063e09f8e786080c61720825a5a5d8e1c5e48ea1e209a1e21ee3ba56763c4d68 c.tar 9a1de8608ea0e75e2f2436259b81f0e991b2007002a59de11d85062e8384d08f d.tar c6ad8e73aa80de875ea90bc318821a51907cb0ce28c492ed79308b5b58924b71 FAMILY.json | sha256sum -c -
for f in a.tar b.tar c.tar d.tar; do T=$(tar tvf $f | cut -c1 | sort | uniq -c | tr '\n' ' '); echo "$f types: $T"; if tar tvf $f | cut -c1 | grep -qv '^[-d]$'; then echo "FAIL member types $f"; exit 3; fi; done
timeout 900 gsutil -q cp c.tar gs://cmu-gpucloud-jjyeung/q8/d9c35d0a/c.tar; echo "cp c.tar ok"
gsutil ls -la gs://cmu-gpucloud-jjyeung/q8/d9c35d0a/
/usr/bin/python3 - <<'PY'
import json,subprocess
g={}
for k in 'abcd':
    out=subprocess.run(['gsutil','ls','-a','gs://cmu-gpucloud-jjyeung/q8/d9c35d0a/'+k+'.tar'],capture_output=True,text=True,check=True).stdout.split()
    g[k]=out[-1].rsplit('#',1)[1]
json.dump(g,open('g3.json','w'));print('g3.json',g)
PY
timeout 1800 /usr/bin/python3 -s -B c/u.py --family FAMILY.json --generations g3.json --out r3.json
echo "u.py ok"; python3 -c "import json;[print(k,v['sha256'],v['bytes'],v['generation'],v['verified']) for k,v in json.load(open('r3.json')).items()]"
/usr/bin/python3 -s -B c/o.py packet --family FAMILY.json --receipts r3.json --out /project/community/jjyeung/okh7/d9c35d0a/p/d12e2a0337651f2637e988f9 --token d12e2a0337651f2637e988f9 --deadline-utc 2026-11-16T17:35:00Z
sha256sum /project/community/jjyeung/okh7/d9c35d0a/p/d12e2a0337651f2637e988f9/*; cat /project/community/jjyeung/okh7/d9c35d0a/p/d12e2a0337651f2637e988f9/a.sh
