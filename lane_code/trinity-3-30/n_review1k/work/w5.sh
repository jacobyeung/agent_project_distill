export TZ=UTC; date -u +%TZ
X=/project/community/jjyeung/okh7/x_22c714e1
f=$(ls $X/u/fd60ac2f* 2>/dev/null | head -1); echo "X/u copy: ${f:-none}"
timeout 120 srun --overlap --jobid 174246 -N1 -n1 bash -s <<'EOS'
/usr/bin/python3 -B -I - <<'PY'
import json, os
p = '/tmp/q_22c714e1_174246/p/q/u/fd60ac2f525727836258ae7ea0705ff3a49163ae74320f7bf8a17b66cd69f0c7'
d = json.load(open(p))
print('schema', d.get('schema'), 'feature_backing', d.get('feature_backing'))
print('encoder_copy.weights', d['encoder_copy']['weights'])
print('weights', d['weights'])
J = '/tmp/q_22c714e1_174246'
for pin in (d['encoder_copy']['weights'], d['weights']):
    staged = J + '/p/q/u/' + pin['sha256']
    print(pin['sha256'][:12], 'staged in p/q/u:', os.path.isfile(staged), 'raw path exists on node:', os.path.exists(pin['path']))
v = json.load(open(J + '/v.json')) if os.path.exists(J + '/v.json') else None
pf = (v or {}).get('r1_training', {}).get('persisted_files', {})
for pin in (d['encoder_copy']['weights'], d['weights']):
    print(pin['sha256'][:12], 'in persisted_files:', pf.get(pin['sha256']))
PY
EOS
date -u +%TZ
