python3 - <<'PY'
import json,tarfile
t=tarfile.open('/project/community/jjyeung/okh7/h_6ed2c7aa/m400/s.tar')
P='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/e84d901c/arm/frozen/6f27ae81/model.json'
m=json.load(t.extractfile('files'+P)); m.pop('files'); print(json.dumps(m)[:1200])
PY
