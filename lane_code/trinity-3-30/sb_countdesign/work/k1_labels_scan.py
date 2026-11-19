"""Lane sb_countdesign: K1 (286 captures) SAM 3 teacher labels (b05_owngrd, floor 0.2, cap 10) -> per (capture, GT name):
truth T (distinct GT ids visible >= 20 px in >= 1 of 32 anchors), ever-proposed ids, per-frame maxima. CPU, read-only. Writes K1_PAIRS.json."""
import json, gzip, glob, os, collections
L = '/scratch/jjyeung/orch_n30/b05_owngrd/work/labels_k1'
pairs = []
clsc = collections.Counter()
for p in sorted(glob.glob(L + '/*.labels.json.gz')):
    d = json.load(gzip.open(p))
    for name, role in d['roles'].items():
        if role != 'gt': continue
        vis = set(); pos = set(); per_frame_gt = []; per_frame_prop = []; per_frame_pos = []
        for k in range(32):
            f = d['frames'][str(k)].get(name)
            if f is None: per_frame_gt.append(0); per_frame_prop.append([]); per_frame_pos.append(0); continue
            vis |= set(f['gt_visible']); pos |= set(f['pos_inst'])
            per_frame_gt.append(len(f['gt_visible'])); per_frame_pos.append(len(set(f['pos_inst'])))
            pr = []
            for q in f['proposals']:
                clsc[q['cls']] += 1
                pr.append((round(q['joint'], 4), q['cls'], q.get('inst'), q.get('inst_name'), q['k'], q.get('area')))
            per_frame_prop.append(pr)
        pairs.append(dict(capture=d['canonical'], split=d['k1_split'], name=name, T=len(vis), ever=len(pos & vis), gt_ids=sorted(vis),
                          max_gt_frame=max(per_frame_gt), max_pos_frame=max(per_frame_pos), props=per_frame_prop, raster_hw=d['raster_hw']))
json.dump(pairs, open('K1_PAIRS.json', 'w'))
print('pairs', len(pairs), 'captures', len(set(p['capture'] for p in pairs)), 'proposal classes', clsc)
print('T hist', sorted(collections.Counter(min(p['T'], 12) for p in pairs).items()))
big = [p for p in pairs if p['T'] >= 5]
print('T>=5 pairs', len(big), 'captures', len(set(p['capture'] for p in big)), 'by split', collections.Counter(p['split'] for p in big), 'by dataset', collections.Counter(p['capture'].split('/')[0] for p in big))
print('names', collections.Counter(p['name'] for p in big).most_common(25))
