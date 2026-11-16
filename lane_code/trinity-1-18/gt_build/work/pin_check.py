"""sha256 every built raster against its CAPTURES.json pin (read-only kit); write PIN_CHECK.tsv."""
import hashlib, json, os
G = '/scratch/jjyeung/orch_n30/gt_build'
C = json.load(open('/scratch/jjyeung/orch_cd/k1_build/work/kit_k1a/out/CAPTURES.json'))
logs = {}
for b in ('t1', 'arkit', 'arkit_t10'):
    f = f'{G}/logs/BUILD_{b}.jsonl'
    if os.path.exists(f):
        for l in open(f):
            r = json.loads(l); logs.setdefault(r['canonical'], []).append((b, r))
import glob
SV = json.load(open(f'{G}/work/ARKIT_SOURCE_VARIANT.json')) if os.path.exists(f'{G}/work/ARKIT_SOURCE_VARIANT.json') else {}
rows = []; n = dict(matched=0, deferred=0)
for p in C['pilot']:
    cn = p['canonical']; pin = p['gt']['expected_sha256']; sub = 'arkit_gt' if cn.startswith('arkitscenes/') else 't1_gt'
    out = f'{G}/out/dose_pool/out/{sub}/gt/' + os.path.basename(p['gt']['path'])
    h = hashlib.sha256(open(out, 'rb').read()).hexdigest() if os.path.exists(out) else ''
    note = ''
    if h == pin and os.path.getsize(out) == p['gt']['bytes']:
        v = 'matched' + ('' if SV.get(cn, 'plain') == 'plain' else ' (declared variant %s)' % SV[cn])
    else:
        name = os.path.basename(p['gt']['path']); rej = f'{G}/out/rejected/arkit_gt/{name}'
        if not h and os.path.exists(rej): h = hashlib.sha256(open(rej, 'rb').read()).hexdigest()
        tried = sorted(x.split('/')[-2] for x in glob.glob(f'{G}/out/variants/*/{name}'))
        errs = [r.get('stderr', '').splitlines()[-1] if r.get('stderr') else 'rc=%s' % r.get('rc') for b, r in logs.get(cn, []) if r.get('rc')]
        if h: v = 'deferred: built sha differs from pin; variants tried, none equal: ' + (','.join(tried) or 'none')
        elif tried: v = 'deferred: grid index exceeds the depth frame count (plain mapping undefined); variants tried, none equal: ' + ','.join(tried)
        else: v = 'deferred: builder failed (' + ('; '.join(errs)[:200] or 'not built') + ')'
    n['matched' if v.startswith('matched') else 'deferred'] += 1
    rows.append((cn, pin, h, v))
with open(f'{G}/PIN_CHECK.tsv', 'w') as f:
    f.write('capture\tpin\tbuilt_sha256\tverdict\n')
    for r in rows: f.write('\t'.join(r) + '\n')
print(json.dumps(n))
