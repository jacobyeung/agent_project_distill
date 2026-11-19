P=/project/community/jjyeung; X=$P/okh7/x_22c714e1; M=$P/okh7/h_6ed2c7aa/m400
timeout 60 gsutil ls -l gs://cmu-gpucloud-jjyeung/q8/8865619b/ 2>&1 | grep m400 | head
cd $X/q/b && timeout 120 python3 -I -s -B - <<'PY'
import sys,json,hashlib
sys.path.insert(0,'.')
import z
from pathlib import Path
M=Path('/project/community/jjyeung/okh7/h_6ed2c7aa/m400')
values,metadata=z.small_archive(M/'s.tar')
e=json.load(open(M/'e.json'));pins=e['pins']
print('pins',sorted(pins))
man=metadata[pins['preparation']['sha256']]['model'];print('model manifest',man)
model=metadata.get(man['sha256'])
if model is None: print('MODEL MANIFEST NOT IN METADATA'); sys.exit()
print('root',model['root']); 
need=[(n,h) for n,h in model['files'].items() if n.endswith(('.json','.txt','.jinja','.model')) and h not in values]
print('need',json.dumps(need))
print('allfiles',len(model['files']),[n for n in model['files'] if not n.endswith('.safetensors')][:40])
PY
tar tvf $P/cp4tk_rt/kit/model_qwen35_9b_c2022362.tar 2>/dev/null | grep -v safetensors | head -30
