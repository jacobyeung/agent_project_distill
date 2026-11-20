/scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import json, os, collections
G = '/scratch/jjyeung/orch_n30/grd_funnel1'
items = [json.loads(l) for l in open(G + '/work/items544.jsonl')]
objs = [json.loads(l) for l in open(G + '/work/objects544.jsonl')]
caps = collections.OrderedDict()
for it in items: caps.setdefault(it['scene'], []).append(it)
print('items', len(items), 'captures', len(caps), 'objects', len(objs))
A = '/scratch/jjyeung/devs1_r2/anchors'; F = '/scratch/jjyeung/devs1_frames'
st = collections.Counter(); ex = []
for sc, its in caps.items():
    name = sc.replace('/', '__'); src = its[0]['source_frame_indices']
    assert all(i['source_frame_indices'] == src for i in its)
    for g in ('g3s32', 'g3s64'):
        p = '%s/%s/%s/A_MANIFEST.json' % (A, g, name)
        if not os.path.exists(p): st[g + ' missing'] += 1; continue
        m = json.load(open(p)); s = m['selections'][0]; idx = s['frame_indices']
        have = sum(os.path.exists(F + '/' + f['path']) for f in s['frames'])
        st['%s n%d' % (g, len(idx))] += 1
        if g == 'g3s32': st['g3s32 same indices' if idx == src else 'g3s32 DIFFERENT indices'] += 1
        else: st['g3s64 contains read anchors' if set(src) <= set(idx) else 'g3s64 not nested'] += 1
        st['%s frames present %s' % (g, 'all' if have == len(idx) else 'partial')] += 1
        if g == 'g3s64' and len(ex) < 1: ex.append((sc, idx[:8], src[:4], s.get('total_num_frames')))
print(dict(st)); print(ex)
gs = json.load(open(G + '/kit/rerun2/gt_staging.json'))
print('gt staging', gs.get('schema'), len(gs['files']), collections.Counter(bool(f.get('bytes')) for f in gs['files']))
print([ (f['capture'], f['relative_path'], f.get('bytes')) for f in gs['files'][:3]])
names = collections.Counter(o['name'] for o in objs); print('distinct names', len(names), names.most_common(12))
json.dump({'captures': list(caps), 'gt': [(f['capture'], f['path']) for f in gs['files']]}, open('/scratch/jjyeung/orch_n30/nvkey1/work/c0_caps.json', 'w'))
PY
