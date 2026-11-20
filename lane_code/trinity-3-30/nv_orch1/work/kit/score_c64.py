"""nv_orch1: score the 64-frame dev-S1 census (ORDER 0356Z) against nvkey1's 32-anchor census (C0) and dev-S1 GT rasters at the anchors.
usage: score_c64.py OUT64.jsonl [PROBE.jsonl] -> work/scores/C64_census.json + printed summary. Analysis only."""
import json, re, sys, collections
import numpy as np
W = '/scratch/jjyeung/orch_n30/nv_orch1/work/'; K2 = W + 'k228/scratch/jjyeung/orch_n30/'
cm = json.load(open(W + 'c64_map.json'))['cmap']; by_scene = {v['scene']: (k, v) for k, v in cm.items()}
man = json.load(open(K2 + 'nvkey1/work/c0/C0_MANIFEST.json'))
objs = [json.loads(l) for l in open(K2 + 'grd_funnel1/work/objects544.jsonl')]
def parse(t):
    t = (t or '').strip(); t = re.sub(r'^```(json)?', '', t).strip(); t = re.sub(r'```$', '', t).strip()
    try: return json.loads(t)
    except Exception:
        i, j = t.find('{'), t.rfind('}')
        try: return json.loads(t[i:j + 1])
        except Exception: pass
    d = {}  # tolerant fallback: per-frame blocks, kind -> null | [..] (presence only; points inside such a block may be words)
    for fk, body in re.findall(r'"(\d+)"\s*:\s*\{([^{}]*)\}', t):
        d[fk] = {k: ([0, 0] if v.startswith('[') else None) for k, v in re.findall(r'"([^"]+)"\s*:\s*(null|\[[^\]]*\])', body)}
    return d or None
def vis(d, k, n): return isinstance(((d or {}).get(str(k + 1)) or {}).get(n), list)
c32 = collections.defaultdict(dict)
for l in open(K2 + 'nvkey1/work/out/20_c0census32.jsonl'):
    r = json.loads(l); c32[r['model'].split('/')[-1][:12]][r['meta']['scene']] = parse(r['text'])
c64 = collections.defaultdict(lambda: collections.defaultdict(dict)); bad = collections.Counter(); fin = collections.Counter()
for l in open(sys.argv[1]):
    r = json.loads(l); d = parse(r['text']); fin[(r['model'], r['finish'])] += 1
    if d is None: bad[r['model']] += 1; continue
    m = r['model'].split('/')[-1][:12]
    for k in range(64):
        for n in r['meta']['kinds']: c64[m][r['meta']['c']][(k, n)] = vis(d, k, n)
gts = {}
for sc, m in man.items():
    if m['gt'] and sc in by_scene and by_scene[sc][1]['n_tower'] == 64:
        z = np.load(K2 + 'nvkey1/work/c0/' + m['gt'], allow_pickle=True); gts[sc] = ({str(n): i for i, n in enumerate(z['names'])}, z['share'], z['missing'])
def bucket(v): return '0' if v == 0 else ('1-2' if v < 3 else '3+')
def band(s): return 'GT<0.2%' if s < 0.002 else ('0.2-1%' if s < 0.01 else ('1-5%' if s < 0.05 else '>=5%'))
res = collections.OrderedDict(); res['parse_failures'] = dict(bad); res['finish'] = {'%s|%s' % k: v for k, v in fin.items()}
for model in ('gemini-4-arg', 'gpt-6.2-astr'):
    rows = []; seen = set()
    for o in objs:
        sc = o['scene']; key = (sc, o['name'])
        if sc not in by_scene or by_scene[sc][1]['n_tower'] != 64 or key in seen: continue
        cid, cv = by_scene[sc]; slots = cv['slots']; d64 = c64[model].get(cid)
        if not d64 or (0, o['name']) not in d64: continue
        seen.add(key)
        v32 = sum(vis(c32[model].get(sc), k, o['name']) for k in range(32))
        v64 = sum(d64[(k, o['name'])] for k in range(64)); v64a = sum(d64[(s, o['name'])] for s in slots)
        inter = [k for k in range(64) if k not in set(slots)]; v64i = sum(d64[(k, o['name'])] for k in inter)
        row = dict(scene=sc, name=o['name'], R=o.get('selected_frame_count') or 0, v32=v32, v64=v64, v64a=v64a, v64i=v64i)
        if sc in gts and o['name'] in gts[sc][0]:
            idx, sh, miss = gts[sc]; ci = idx[o['name']]
            g = [(not miss[k]) and sh[ci, k] >= 0.002 for k in range(32)]
            lab = [d64[(slots[k], o['name'])] for k in range(32)]; lab32 = [vis(c32[model].get(sc), k, o['name']) for k in range(32)]
            row.update(G2=int(sum(g)), maxshare=float(max(sh[ci, k] for k in range(32) if not miss[k])),
                       tp=int(sum(a and b for a, b in zip(lab, g))), fp=int(sum(a and not b for a, b in zip(lab, g))), fn=int(sum(b and not a for a, b in zip(lab, g))),
                       tp32=int(sum(a and b for a, b in zip(lab32, g))), fp32=int(sum(a and not b for a, b in zip(lab32, g))), nanch=int(sum(not miss[k] for k in range(32))))
            prec = row['tp'] / (row['tp'] + row['fp']) if row['tp'] + row['fp'] else 0.0
            row['est64'] = row['G2'] + prec * v64i  # GT-visible anchors + interleaved labeller frames scaled by this object's anchor precision
        rows.append(row)
    sp = [r for r in rows if r['R'] < 3]; fc = [r for r in sp if 1 <= r['v32'] <= 2]
    out = collections.OrderedDict()
    out['objects'] = len(rows); out['sparse_R<3'] = len(sp)
    out['sparse: v32 bucket -> v64 bucket'] = {'%s->%s' % k: v for k, v in sorted(collections.Counter((bucket(r['v32']), bucket(r['v64'])) for r in sp).items())}
    out['frame-count group (R<3, v32 1-2)'] = len(fc); out['  moved to v64>=3'] = sum(r['v64'] >= 3 for r in fc)
    out['  of those, >=3 already at the 64-call anchors (form change, not new frames)'] = sum(r['v64'] >= 3 and r['v64a'] >= 3 for r in fc)
    out['  moved by band (GT max share at anchors)'] = {b: '%d of %d' % (sum(r['v64'] >= 3 for r in fc if r.get('maxshare') is not None and band(r['maxshare']) == b), sum(1 for r in fc if r.get('maxshare') is not None and band(r['maxshare']) == b)) for b in ('GT<0.2%', '0.2-1%', '1-5%', '>=5%')}
    out['  moved, no GT'] = '%d of %d' % (sum(r['v64'] >= 3 for r in fc if r.get('maxshare') is None), sum(1 for r in fc if r.get('maxshare') is None))
    g = [r for r in rows if 'G2' in r]; gsp = [r for r in g if r['R'] < 3]
    out['GT subset objects'] = len(g); out['GT subset sparse'] = len(gsp)
    out['GT sparse: GT-anchor bucket (>=0.2%)'] = dict(collections.Counter(bucket(r['G2']) for r in gsp))
    out['GT sparse with GT 1-2 at 32: est64>=3 (GT anchors + precision-scaled interleaved)'] = '%d of %d' % (sum(r['est64'] >= 3 for r in gsp if 1 <= r['G2'] <= 2), sum(1 for r in gsp if 1 <= r['G2'] <= 2))
    out['GT sparse with GT 1-2 at 32: labeller v64>=3'] = sum(r['v64'] >= 3 for r in gsp if 1 <= r['G2'] <= 2)
    tp = sum(r['tp'] for r in g); fp = sum(r['fp'] for r in g); fn = sum(r['fn'] for r in g); tp32 = sum(r['tp32'] for r in g); fp32 = sum(r['fp32'] for r in g)
    out['anchor frames, 64-call: precision / recall vs GT>=0.2%'] = [round(tp / max(1, tp + fp), 3), round(tp / max(1, tp + fn), 3)]
    out['anchor frames, 32-call (C0): precision vs GT>=0.2%'] = round(tp32 / max(1, tp32 + fp32), 3)
    out['over-count on GT subset: labeller visible anchors / GT visible anchors (64-call, 32-call)'] = [round((tp + fp) / max(1, tp + fn), 3), round((tp32 + fp32) / max(1, sum(r['G2'] for r in g)), 3)]
    out['over-count, sparse GT subset: labeller 3+ at anchors where GT 1-2'] = '%d of %d' % (sum(r['v64a'] >= 3 for r in gsp if 1 <= r['G2'] <= 2), sum(1 for r in gsp if 1 <= r['G2'] <= 2))
    out['rows'] = rows
    res[model] = out
json.dump(res, open(W + 'scores/C64_census.json', 'w'), indent=1)
for m, o in res.items():
    if isinstance(o, dict) and 'rows' in o:
        print('==', m); [print(' ', k, v) for k, v in o.items() if k != 'rows']
    else: print(m, o)
