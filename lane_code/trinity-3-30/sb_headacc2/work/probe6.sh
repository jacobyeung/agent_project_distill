/usr/bin/python3 - <<'PYEOF'
import json, collections
K='/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/'
labs={}
for l in open(K+'K1_LABELS_CORRECTED.jsonl'):
    r=json.loads(l); labs[r['id']]=r
aud=[json.loads(l) for l in open(K+'K1_ROW_AUDIT.jsonl')]
box=json.load(open(K+'K1_BOX_AUDIT.json'))
res=collections.Counter()
for a in aud:
    r=labs[a['id']]
    if r['corrected'] is None: res['no_raster']+=1; continue
    for k in ('x1_m','x2_m','x12_m','x21_m','selective_m','stored_m'):
        v=a.get(k)
        res[(r['convention'], k, v is not None and abs(v-r['corrected'])<1e-3)]+=1
    res[(r['convention'],'statuses',tuple(a['box_statuses']))]+=1
    res[('box_keys_in_audit', all(b in box for b in a['box_keys']))]+=1
for k in sorted(res, key=str): print(k, res[k])
b=box[aud[0]['box_keys'][0]]; print('box example', aud[0]['operands'], b['box']['name'], b['box']['axesLengths'], b['status'])
print('status counts', collections.Counter(v['status'] for v in box.values()), 'boxes', len(box))
per=collections.defaultdict(set)
for a in aud: per[a['capture']].add(labs[a['id']]['convention'])
print('captures with mixed convention', sum(len(v)>1 for v in per.values()), 'of', len(per))
PYEOF
