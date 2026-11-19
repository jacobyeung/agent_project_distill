python3 - <<'PY'
import json,tarfile,hashlib,os
t=tarfile.open('/project/community/jjyeung/okh7/h_6ed2c7aa/m400/s.tar')
P='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/e84d901c/arm/frozen/6f27ae81/model.json'
m=json.load(t.extractfile('files'+P)); r=m['root']; print('root exists on login node:',os.path.isdir(r))
for n,s in sorted(m['files'].items()):
  if n.endswith('.safetensors'): continue
  p=os.path.join(r,n)
  if not os.path.isfile(p): print('ABSENT',n); continue
  h=hashlib.sha256(open(p,'rb').read()).hexdigest(); print('OK' if h==s else 'MISMATCH',n,os.path.getsize(p),h[:8])
PY
