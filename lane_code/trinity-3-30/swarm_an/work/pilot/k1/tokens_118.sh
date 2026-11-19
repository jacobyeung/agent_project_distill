set -u
OMP_NUM_THREADS=1 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import json, hashlib, os
W='/scratch/jjyeung/orch_n30'
man=json.load(open(W+'/geo_k1/stage/K1_MANIFEST.arkit_timing.json')); caps=man['captures']
held=set(c['room'] for c in caps if c.get('k1_split')!='train' or c.get('split')!='train')
out={}
for c in caps:
    if c.get('k1_split')!='train' or c.get('split')!='train' or c['room'] in held: continue
    ds, sc = c['canonical'].split('/'); ds2={'scannetpp':'scannetppv2'}.get(ds, ds)
    ok = all(os.path.isfile(c['dense_frames'][s]['path']) for s in c['anchor_slots'])
    out['v'+hashlib.sha256(('rung1 scene %s/%s' % (ds2, sc)).encode()).hexdigest()[:12]] = [ds, ok, c['dense_frames'][c['anchor_slots'][0]]['sha256'][:16]]
print('JSONBEGIN'); print(json.dumps(out)); print('JSONEND')
PY
