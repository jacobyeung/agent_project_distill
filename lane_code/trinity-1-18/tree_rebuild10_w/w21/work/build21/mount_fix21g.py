from pathlib import Path
import base64,hashlib,json,sys,subprocess
L=Path(__file__).resolve().parents[2];B=L/'work/build21';K=B/'kits/q';D=L/'work/build21g'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
from jobtest import rawcap,reseal
from launch_r2.build import capsule_json
subprocess.run(['date','-u'],check=True)
old='BW+=(--dev-bind /dev /dev --proc /proc'
new='BW+=(--tmpfs /tmp --bind "$Q_ROOT" "$Q_ROOT" --dev-bind /dev /dev --proc /proc'
shell=base64.b64decode(J.load_raw(K/'k/j.json')['payload']).decode()
assert shell.count(old)==1
shell=shell.replace(old,new)
(K/'k/j.json').write_bytes(rawcap(shell.encode()))
reseal(K)
build=J.load(K/'BUILD.json');build['kit_sha256']=J.seal(K)
(K/'BUILD.json').write_bytes(capsule_json(build))
uploads=J.load(B/'UPLOADS.json')
for row in uploads['files']:
    if row['opaque_name'].startswith('q/'):
        p=K/row['opaque_name'][2:];row.update(bytes=p.stat().st_size,sha256=J.sha(p))
uploads['total_bytes']=sum(x['bytes'] for x in uploads['files'])
J.write(B/'UPLOADS.json',uploads)
J.write(D/'KIT_CHANGE.json',dict(before=J.load(D/'START.json')['kit_seal'],after=J.seal(K),
    change='Private /tmp, then restore Q_ROOT, before the remaining binds; host pool unchanged.'))
print(J.seal(K))
