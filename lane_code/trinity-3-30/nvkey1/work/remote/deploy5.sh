set +x
K=/scratch/jjyeung/orch_n30/nvkey1/work; P=/scratch/jjyeung/envs/p1cpu/bin/python; cd $K
cat > $K/kit/c2_jobs.py <<'PYEOF'
"""nvkey1 C2: pointing-row audit tasks. One call = up to CHUNK rows of one clip, each row one frame (a red ring at the row's point for a visible
row; no ring for an absent row) and its claim. Rows: the pointing store rows whose frame is on this node, minus the K1-heldout removal list.
usage: c2_jobs.py OUT.jsonl MODEL EFFORT [CHUNK=40] [ROWS=all|path to a json list of store indices]  (C1_EXTRA env adds request fields)"""
import json, os, sys, sqlite3, random, collections
K = '/scratch/jjyeung/orch_n30/nvkey1/work'
STORE = '/scratch/jjyeung/orch_n30/fb_pack/point/out/rows_pointing_locate.sqlite'
HELD = '/scratch/jjyeung/orch_n30/fb_pack/k1point/REMOVE_POINTING_K1_HELDOUT.jsonl'
ROOTS = ['/scratch/jjyeung/k1_frames', '/scratch/jjyeung/devs1_frames']
PROMPT = ('You are auditing labels of a pointing dataset. Each row below shows one video frame of an indoor room and one claim about it.\n'
          '- A "point" row has a red ring drawn on the image. Its claim: the centre of the ring lies on a visible part of an object of the named kind.\n'
          '- An "absent" row has no ring. Its claim: no object of the named kind is visible anywhere in the image.\n'
          'Judge every claim from its image alone, and answer for each row:\n'
          '"present": is at least one object of the named kind visible in the image, fully or partly? true or false.\n'
          '"on_object": point rows only: is the centre of the ring on a visible part of an object of the named kind? true or false; null for absent rows.\n'
          '"name_fits": point rows only: would most people call the object under the centre of the ring by the given name or a close synonym? true or false; null for absent rows.\n'
          '"point": when present is true and the claim is wrong (an absent row, or on_object false), one point on a visible part of the named object as [x, y] '
          'in 0-1000 image coordinates (x = 0 left edge, 1000 right edge; y = 0 top edge, 1000 bottom edge); otherwise null.\n'
          'Reply with one JSON object and nothing else: {{"<row id>": {{"present": ..., "on_object": ..., "name_fits": ..., "point": ...}}, ...}} with all {n} row ids.')
def frame_path(sha):
    for r in ROOTS:
        p = '%s/%s/%s.png' % (r, sha[:2], sha)
        if os.path.exists(p): return p
def held_ids():
    s = set()
    if os.path.exists(HELD):
        for l in open(HELD):
            try:
                d = json.loads(l); s.add(str(d.get('qid') or d.get('id') or d.get('row_id') or d.get('i')))
            except Exception: pass
    return s
def load_rows(only=None):
    c = sqlite3.connect('file:%s?mode=ro' % STORE, uri=True); held = held_ids(); out = []
    for i, s in c.execute('select i,row from rows'):
        if only is not None and i not in only: continue
        d = json.loads(s); p = d['pointing']; f = frame_path(p.get('rgb_sha256') or '')
        if not f or d.get('qid') in held: continue
        out.append(dict(i=i, qid=d.get('qid'), scene=d['scene'], dataset=d['dataset'], kind=p['kind'], label=p['label'], frame=p['frame'], area=p.get('area_fraction') or 0.0,
                        stratum=p.get('stratum'), uv=(p.get('selected') or {}).get('uv'), path=f, canonical=(d.get('provenance') or {}).get('canonical_scene')))
    return out, len(held)
def main():
    out, model, effort = sys.argv[1], sys.argv[2], sys.argv[3]; chunk = int(sys.argv[4]) if len(sys.argv) > 4 else 40
    only = set(json.load(open(sys.argv[5]))) if len(sys.argv) > 5 and sys.argv[5] != 'all' else None
    effort = None if effort == 'none' else effort; extra = json.loads(os.environ.get('C1_EXTRA', '{}')); tag = model.split('/')[-1]
    rows, nheld = load_rows(only); byc = collections.defaultdict(list)
    for r in rows: byc[r['scene']].append(r)
    rng = random.Random(20261120); n = 0; meta_rows = {}
    with open(out, 'a') as f:
        for sc in sorted(byc):
            rs = byc[sc][:]; rng.shuffle(rs)
            for j in range(0, len(rs), chunk):
                part = rs[j:j + chunk]; content = [{'text': PROMPT.format(n=len(part))}]
                for r in part:
                    rid = 'r%d' % r['i']
                    if r['kind'] == 'gt_absent':
                        content += [{'text': 'Row %s (absent row): kind = "%s"' % (rid, r['label'])}, {'image': r['path'], 'max_side': 640}]
                    else:
                        content += [{'text': 'Row %s (point row): kind = "%s"' % (rid, r['label'])}, {'image': r['path'], 'max_side': 640, 'mark': r['uv']}]
                f.write(json.dumps({'id': 'c2_%s_%d_%s' % (sc, j // chunk, tag), 'model': model, 'effort': effort, 'max_tokens': 32768, 'extra': extra,
                                    'content': content, 'meta': {'scene': sc, 'rows': [r['i'] for r in part]}}) + '\n'); n += 1
                for r in part: meta_rows[r['i']] = {k: r[k] for k in ('qid', 'scene', 'dataset', 'kind', 'label', 'frame', 'area', 'stratum', 'uv', 'canonical')}
    json.dump(meta_rows, open(K + '/c2_rows_meta.json', 'w'))
    print('rows', len(rows), 'clips', len(byc), 'tasks', n, 'heldout ids in list', nheld, 'kinds', dict(collections.Counter(r['kind'] for r in rows)))
if __name__ == '__main__': main()
PYEOF
cat > $K/kit/score_c0.py <<'PYEOF'
"""nvkey1 C0 scoring: (1) calibration of the census labels against dev-S1 GT rasters (38 captures); (2) the visibility census joined to the
step-544 routed reads (grd_funnel1 items544/objects544); (3) the points file for the GPU ceiling read (cont_ops24 format).
usage: score_c0.py OUT.jsonl  -> work/scores/C0_*.json, work/c0/POINTS_<model>.json"""
import json, re, sys, os, collections, random, hashlib
import numpy as np
K = '/scratch/jjyeung/orch_n30/nvkey1/work'; G = '/scratch/jjyeung/orch_n30/grd_funnel1/work'
sys.path.insert(0, K + '/kit')
man = json.load(open(K + '/c0/C0_MANIFEST.json'))
items = {json.loads(l)['item_id']: json.loads(l) for l in open(G + '/items544.jsonl')}
objs = [json.loads(l) for l in open(G + '/objects544.jsonl')]
from c1_jobs import PROMPT
def parse(t):
    if not t: return None
    t = t.strip(); t = re.sub(r'^```(json)?', '', t).strip(); t = re.sub(r'```$', '', t).strip()
    try: return json.loads(t)
    except Exception:
        i, j = t.find('{'), t.rfind('}')
        try: return json.loads(t[i:j + 1])
        except Exception: return None
def band(s): return 'absent' if s == 0 else ('<0.2%' if s < 0.002 else ('0.2-1%' if s < 0.01 else ('1-5%' if s < 0.05 else '>=5%')))
def get(d, k, n):
    v = (d or {}).get(str(k + 1))
    if not isinstance(v, dict): return 'MISSING'
    return v.get(n, 'MISSING')
lab = collections.defaultdict(dict)   # model -> scene -> parsed
for l in open(sys.argv[1]):
    r = json.loads(l); lab[r['model'].split('/')[-1]][r['meta']['scene']] = parse(r['text'])
res = collections.OrderedDict()
for model, per in lab.items():
    out = collections.OrderedDict(); rows = []
    for sc, d in per.items():
        m = man[sc]
        if not m['gt']: continue
        z = np.load(K + '/c0/' + m['gt'], allow_pickle=True); H, W = [int(x) for x in z['shape']]
        mask = np.unpackbits(z['mask'], axis=-1)[..., :W].astype(bool)
        for ci, n in enumerate([str(x) for x in z['names']]):
            for k in range(32):
                if z['missing'][k]: continue
                s = float(z['share'][ci, k]); b = band(s)
                if b == '<0.2%': continue
                v = get(d, k, n); said = None if (v == 'MISSING' or d is None) else (isinstance(v, (list, tuple)) and len(v) == 2)
                hit = None
                if said and b != 'absent':
                    x = min(W - 1, max(0, int(float(v[0]) / 1000.0 * W))); y = min(H - 1, max(0, int(float(v[1]) / 1000.0 * H))); hit = bool(mask[ci, k][max(0, y - 1):y + 2, max(0, x - 1):x + 2].any()); hit0 = bool(mask[ci, k][y, x])
                rows.append(dict(cap=sc, band=b, truth=b != 'absent', said=said, hit=hit))
    def acc(S):
        S = [r for r in S if r['said'] is not None]; return round(100.0 * sum(r['said'] == r['truth'] for r in S) / len(S), 1) if S else None
    def pt(S):
        S = [r for r in S if r['truth'] and r['said']]; return round(100.0 * sum(bool(r['hit']) for r in S) / len(S), 1) if S else None
    def boot(S, f):
        caps = sorted(set(r['cap'] for r in S)); by = collections.defaultdict(list)
        for r in S: by[r['cap']].append(r)
        rng = random.Random(11); v = []
        for _ in range(2000):
            x = f([r for c in (rng.choice(caps) for _ in caps) for r in by[c]])
            if x is not None: v.append(x)
        v.sort(); return [v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]] if v else None
    cal = collections.OrderedDict(facts=len(rows), captures=len(set(r['cap'] for r in rows)))
    cal['presence_all'] = [acc(rows), boot(rows, acc)]
    for b in ('>=5%', '1-5%', '0.2-1%', 'absent'):
        S = [r for r in rows if r['band'] == b]; cal['presence_' + b] = [acc(S), boot(S, acc), len(S)]
    for b in ('>=5%', '1-5%', '0.2-1%'):
        S = [r for r in rows if r['band'] == b]; cal['point_tol1_' + b] = [pt(S), boot(S, pt), sum(1 for r in S if r['said'])]
    out['calibration_devS1_gt'] = cal
    # census
    cen = []; 
    for o in objs:
        sc = o['scene']; d = per.get(sc)
        if d is None: continue
        v = [get(d, k, o['name']) for k in range(32)]; vis = [isinstance(x, (list, tuple)) and len(x) == 2 for x in v]
        it = items[o['item_id']]
        cen.append(dict(item=o['item_id'], op=o['operand'], name=o['name'], V=sum(vis), R=o.get('selected_frame_count') or 0, state=o.get('state'),
                        gap=it.get('gap_score'), score=it.get('score'), group=it.get('group'), parsed=d is not None,
                        unanswered=sum(1 for x in v if x == 'MISSING')))
    tab = collections.Counter(('V0' if c['V'] == 0 else 'V1-2' if c['V'] < 3 else 'V3+', 'R<3' if c['R'] < 3 else 'R3+') for c in cen)
    out['census_objects'] = len(cen); out['census_V_by_R'] = {'%s|%s' % k: v for k, v in sorted(tab.items())}
    out['census_V_hist'] = dict(collections.Counter(min(c['V'], 10) for c in cen))
    # items: worst object
    byi = collections.defaultdict(list)
    for c in cen: byi[c['item']].append(c)
    grp = collections.defaultdict(list)
    for i, cs in byi.items():
        sparse = [c for c in cs if c['R'] < 3]
        if not sparse: g = 'reader>=3 on both'
        elif all(c['V'] >= 3 for c in sparse): g = 'reader<3 but labeller sees >=3 (proposal/selection limit)'
        elif any(c['V'] == 0 for c in sparse): g = 'reader<3 and labeller sees 0 (absent from the 32 frames)'
        else: g = 'reader<3 and labeller sees 1-2 (frame-count limit)'
        grp[g].append(cs[0])
    out['items_by_group'] = {g: dict(n=len(v), gap_mean=round(float(np.mean([c['gap'] for c in v if c['gap'] is not None])), 2) if any(c['gap'] is not None for c in v) else None,
                                     answer_mean=round(float(np.mean([c['score'] for c in v if c['score'] is not None])), 2) if any(c['score'] is not None for c in v) else None)
                             for g, v in sorted(grp.items())}
    res[model] = out
    print(model, json.dumps(out))
    # points for the GPU ceiling read
    P = {}
    for iid, it in items.items():
        sc = it['scene']; d = per.get(sc)
        if d is None: continue
        src = it['source_frame_indices']; P[iid] = {}
        for n in it['names']:
            P[iid][n] = {str(src[k]): ([round(float(v[0]) / 1000.0, 4), round(float(v[1]) / 1000.0, 4)] if isinstance(v, (list, tuple)) and len(v) == 2 else None)
                         for k, v in ((k, get(d, k, n)) for k in range(32))}
    shas = {sc: [os.path.basename(f).split('.')[0] for f in man[sc]['frames']] for sc in per}
    json.dump({'model': model, 'prompt_template_sha256': hashlib.sha256(PROMPT.encode()).hexdigest(), 'frame_sha256_by_scene': shas, 'points': P},
              open(K + '/c0/POINTS_%s.json' % model, 'w'))
os.makedirs(K + '/scores', exist_ok=True); json.dump(res, open(K + '/scores/C0_census32.json', 'w'), indent=1)
PYEOF
head -c 600 /scratch/jjyeung/orch_n30/fb_pack/k1point/REMOVE_POINTING_K1_HELDOUT.jsonl; echo
Q=$K/queue/40_c2audit.jsonl
[ -f $Q ] || { $P -B kit/c2_jobs.py $Q.tmp gcp/google/gemini-4-argon high 40 && $P -B kit/c2_jobs.py $Q.tmp openai/openai/gpt-6.2-astra high 40 && mv $Q.tmp $Q; }
wc -l $Q; echo 16 > $K/ctl/INFLIGHT
tail -4 $K/runner.log; cat $K/meter/METER.json; wc -l $K/out/*.jsonl
grep -v '"status": 200' $K/meter/CALLS.jsonl | tail -3 | cut -c1-300
