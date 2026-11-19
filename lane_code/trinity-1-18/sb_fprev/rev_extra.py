"""Reviewer's checks of FPJOIN's secondary numbers (venue rows, P exclusion ids, upstream census, dev item lists)."""
import collections, gzip, hashlib, json, os
from pathlib import Path

ORCH = Path('/scratch/jjyeung/orch_n30')
AWS = ORCH / 'sb_evidence/aws_sources'
HERE = Path(__file__).resolve().parent
P = 'ap__8865619b__runs__469ddece__inputs__prepare_dd26bb95f37a43789206c6e4d4cd94bd__'
BLOBS = ORCH / 'sb_framepool/work/blobs'
KIT = ORCH / 'sb_records/out/kit/inputs'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def mint(d, s):
    return 'v' + hashlib.sha256(('rung1 scene %s/%s' % (d, s)).encode()).hexdigest()[:12]


def blob(prefix, root=BLOBS):
    m = [f for f in os.listdir(root) if f.startswith(prefix)]
    assert len(m) == 1, (prefix, m)
    p = root / m[0]
    assert sha(p).startswith(prefix)
    return p


R = {}
venue = {mint('arkitscenes', '41159526'): '41159526', mint('arkitscenes', '41159521'): '41159521'}
mix = {tuple(x) for x in json.load(open(AWS / (P + 'prepared__pose_mix_order.json')))}
order = {tuple(x) for x in json.load(open(AWS / (P + 'prepared__pose_scene_order.json')))}
v = collections.Counter(); vin = 0
for src, n in enumerate(['a2v3', 'a3v2']):
    with gzip.open(AWS / ('ap__f02f16ad__s__%s__rows.scenes.jsonl.gz' % n), 'rt') as f:
        for l in f:
            r = json.loads(l)
            if r['scene'] in venue:
                v[(n, venue[r['scene']])] += 1
                vin += (src, r['i']) in mix or (src, r['i']) in order
R['venue_pose_rows'] = dict(counts={'%s:%s' % k: c for k, c in v.items()}, in_mix_or_order=vin)

hits = json.load(open(ORCH / 'sb_framepool/work/verified_hits.json'))['rows']; hq = {h['qid'] for h in hits}
pk = json.load(open(ORCH / 'tree_rebuild10_w/ext/pk/66c427e2.json'))
R['P_exclusion_ids'] = dict(sha=sha(ORCH / 'tree_rebuild10_w/ext/pk/66c427e2.json'), keys={k: len(set(x) & hq) for k, x in pk.items()})

rc = json.load(open(AWS / (P + 'prepared__receipt.json')))
up = rc['scene_filter_report']['upstream']


def bm(x, path=''):
    out = {}
    if isinstance(x, dict):
        if 'benchmark_matches' in x and 'seen' in x: out[path] = (x['benchmark_matches'], x['seen'])
        for k, y in x.items(): out.update(bm(y, path + '/' + k))
    return out


R['upstream_census'] = {k: v for k, v in bm(up).items()}
# Per-stream step-544 receipts (pointing/routing/vqa) if present locally.
for n, h in [('pointing', 'e59329ae'), ('routing', '263eac88'), ('vqa', 'fb54c360')]:
    m = [f for f in os.listdir(KIT) if f.startswith(h)]
    if m:
        d = json.load(open(KIT / m[0]))
        R['stream_receipt_' + n] = {k: v for k, v in bm(d).items() if v[0]}
r673 = [f for f in os.listdir(KIT) if f.startswith('96969b1c')]
if r673:
    d = json.load(open(KIT / r673[0]))
    R['r1_673bc60f_vqa_receipt'] = dict(census=bm(d), heldout_overlap=d.get('heldout_overlap'), count=d.get('count'))

# Dev/kit VSTI-style item lists named in FPJOIN.
caps = {l.split('\t')[3] for l in open(ORCH / 'sb_framepool/out/CAPTURES.tsv').read().splitlines()[1:] if 'STI-Bench/ReSTI' in l.split('\t')[5]}
lists = {}
for prefix in ['b5853845', '5cd2d5f2', '7a6ac5cc', 'c1c99e4d']:
    p = blob(prefix); items = [json.loads(l) for l in open(p)]
    sc = set(); unresolved = 0
    for r in items:
        s, d, room = r.get('scene'), r.get('dataset'), r.get('room', '')
        if s and '/' in s: c = s.replace('scannetppv2/', 'scannetpp/')
        elif d and s: c = d.replace('scannetppv2', 'scannetpp') + '/' + s
        elif room.startswith(('scannet/', 'scannetpp/', 'arkitscenes/')) and s: c = room.split('/')[0] + '/' + s
        else: c = None; unresolved += 1
        if c: sc.add(c)
    lists[prefix] = dict(items=len(items), captures=len(sc), overlap_126=len(sc & caps), unresolved=unresolved,
                         keys=sorted(items[0].keys())[:12])
R['item_lists'] = lists
off = Path('/scratch/jjyeung/orch_cd/heads_up/work/h3/b14b/vsti.json')
R['official_vsti_bank'] = dict(path=str(off), exists_on_this_node=off.exists(),
                               sha256=sha(off) if off.exists() else None)
(HERE / 'rev_extra.json').write_text(json.dumps(R, indent=1, default=str) + '\n')
print(json.dumps(R, indent=1, default=str))
