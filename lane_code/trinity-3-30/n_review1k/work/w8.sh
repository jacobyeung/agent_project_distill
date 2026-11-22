export TZ=UTC; date -u +%TZ
timeout 280 srun --overlap --jobid 174246 -N1 -n1 bash -s <<'EOS'
nice -n 10 /usr/bin/python3 -B -I - <<'PY'
import json, hashlib, os
J='/tmp/q_22c714e1_174246'; NS='/tmp/q_22c714e1'
def loc(p): return J + p[len(NS):] if p.startswith(NS + '/') else p
def sh(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda: f.read(1<<24), b''): h.update(b)
    return h.hexdigest()
v=json.load(open(J+'/v.json')); ia=v['init_artifact']; print('v.json init_artifact', json.dumps(ia))
ap=loc(ia['artifact']['path']); print('artifact.json staged sha', sh(ap), '== pin', sh(ap)==ia['artifact']['sha256'])
a=json.load(open(ap)); print('artifact schema', a.get('schema'), 'step', a.get('step'), 'training_mode', a.get('training_mode'))
print('artifact.full_weights', a['full_weights']); print('artifact.heads', a['heads'])
pf=v['r1_training']['persisted_files']; print('persisted_files entries', len(pf))
fw=a['full_weights']; fwl=pf.get(fw['sha256']); print('full_weights sha in persisted_files ->', fwl)
if fwl:
    print('  staged full_weights.json sha', sh(loc(fwl)) == fw['sha256'])
    m=json.load(open(loc(fwl))); d=os.path.dirname(loc(fwl)); print('  manifest keys', sorted(m)[:10], 'index', m.get('index'))
    ok=True; n=0; tot=0
    for it in m['files']:
        p=os.path.join(d, it['name']); s=sh(p); n+=1; tot+=os.path.getsize(p)
        if s!=it['sha256']: ok=False; print('  MISMATCH', it['name'])
        if pf.get(it['sha256']) != os.path.join(os.path.dirname(fwl), it['name']): print('  persisted map differs for', it['name'], pf.get(it['sha256']))
    ix=m['index']; ixp=os.path.join(d, ix['name']); print('  index', ix['name'], sh(ixp)==ix['sha256'])
    print('  shards', n, 'bytes', tot, 'all sha equal manifest', ok)
    print('  p/q/w listing', sorted(os.listdir(d)))
hd=a['heads']; hl=pf.get(hd['sha256']); print('heads sha in persisted_files ->', hl)
cand=J+'/p/q/u/'+hd['sha256']; print('p/q/u/<heads sha> exists', os.path.isfile(cand), 'sha equal', os.path.isfile(cand) and sh(cand)==hd['sha256'])
print('p_run', json.dumps(v['r1_training'].get('p_run'))[:300]); print('init_policy', v['r1_training'].get('init_policy'))
print('handover_receipt', json.dumps(v['r1_training'].get('handover_receipt'))[:200])
PY
EOS
date -u +%TZ
