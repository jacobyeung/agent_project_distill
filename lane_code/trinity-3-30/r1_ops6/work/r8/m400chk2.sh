#!/bin/bash
export TZ=UTC; D=/project/community/jjyeung/okh7/h_6ed2c7aa/m400
python3 - $D <<'PY'
import json,sys,tarfile
D=sys.argv[1]; t=tarfile.open(D+'/s.tar'); man=json.load(t.extractfile('MANIFEST.json'))
P='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/e84d901c/arm/frozen/6f27ae81/model.json'
f=[x for x in man['files'] if x['path']==P][0]; print('model.json why:',f['why'][-140:],'pin match',f['match'])
print(json.dumps(json.load(t.extractfile('files'+P)))[:1500])
for x in man['files']:
  if 'tokenizer' in x['path'] or x['path'].endswith('config.json'): print('TOK/CFG',x['path'][-100:],x['sha256'][:8],x['why'][-80:])
for x in man['skipped']:
  if 'tokenizer' in x['path'] or 'D451299D' in x['path'] or '478d0140' in x['path']: print('SKIPWHY',x['path'][-70:],x.get('why','')[-110:])
PY
