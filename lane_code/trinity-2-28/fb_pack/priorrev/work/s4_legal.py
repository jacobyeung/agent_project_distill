"""Check 4 legality: no weight-file row (and no reconstructed VQA row) belongs to a dev,
dev-S1, R0-dev, benchmark/test scene or a held QID. Own token resolution plus the
tree's own matchers as a cross-check."""
import csv, hashlib, json, pickle, re, sqlite3, sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

W = Path(__file__).resolve().parent
FB = Path('/scratch/jjyeung/orch_n30/fb_pack')
RO = FB/'ro/orch_n30'
T = RO/'tree_rebuild10_w'
F = dict(
    dev_s1=T/'w24/work/build24d/sequence/n/q_22c714e1_20/p/s/student_pilot/r2_dev_merged.json',
    bench=T/'ext/pk/benchmark_scene_exclusions.json',
    test=T/'ext/pk/dafa4a9c.json',
    held=T/'ext/pk/66c427e2.json',
    r0=W/'new/student_pilot/r0_scenes.json',
    division=T/'ext/m400real/files/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/e84d901c/z/4c230a7e.json',
    m400_dev=T/'ext/m400real/files/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/dev_scene_exclusions.json',
    arkit=T/'ext/b12/work/auth/arkit_3dod_metadata.csv',
    k1=T/'ext/b12/work/auth/K1SPLIT_R0.json',
    alias=RO/'sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json',
)
EXPECT = dict(dev_s1='a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5',
              bench='3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970',
              test='dafa4a9c8ffd1e063e0a98c5ae6087d911b74f864932e530f24d45b816cca6fb',
              held='66c427e2262331be2e0c598f2ecc39087f3a722a5155caaf1ab84a89c8cd0f6f',
              r0='f7c458176426e22a13e47908b03abd2c6f5939d3e48eb7c24e7eba45b75ad479',
              division='0d28fdd432b02ae96b6ce2aaa840b744005291a540920ce48409f0e8c90276ad')
DS = {'d1': 'd1', 'scannet': 'd1', 'd2': 'd2', 'scannetpp': 'd2', 'scannetppv2': 'd2', 'scannet++': 'd2',
      'd3': 'd3', 'arkitscenes': 'd3'}
NS = {'d1': ['scannet'], 'd2': ['scannetppv2', 'scannetpp'], 'd3': ['arkitscenes']}
FAMILIES = ('rung1 scene', 'rung2 scene', 'v590kgt scene')


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def tokens(d, native):
    out = set()
    for fam in FAMILIES:
        for ns in NS[d]:
            out.add('v'+hashlib.sha256((fam+' '+ns+'/'+native).encode()).hexdigest()[:12])
    if d == 'd3':
        out.add('v'+hashlib.sha256(('arkitscenes/'+native).encode()).hexdigest()[:12])
    return out


def norm(name):
    d, s = name.split('/', 1)
    return DS.get(d.casefold(), d.casefold()), s


def room(d, s):
    m = re.fullmatch(r'(scene\d{4})_\d\d', s) if d == 'd1' else None
    return (d, m.group(1)) if m else None


def main():
    R = {'inputs': {k: dict(path=str(p), sha256=sha(p)) for k, p in F.items()}}
    R['pin_check'] = {k: R['inputs'][k]['sha256'] == v for k, v in EXPECT.items()}
    expanded, natives, venue = build(R)
    tok2nat = {}
    for d, sc in natives:
        for t in tokens(d, sc):
            tok2nat[(d, t)] = (d, sc)
    check(R, expanded, venue, tok2nat)


def build(R):
    # Universe of natives for token resolution
    natives = {('d1', 'scene%04d_%02d' % (a, b)) for a in range(0, 900) for b in range(0, 10)}
    with F['arkit'].open() as f:
        natives |= {('d3', r['video_id']) for r in csv.DictReader(f)}
    alias = json.loads(F['alias'].read_text())['aliases']
    for v in alias.values():
        c = v.get('canonical')
        if isinstance(c, str) and '/' in c: natives.add(norm(c))
    # list members
    lists = {}
    dev = json.loads(F['dev_s1'].read_text())
    s = set()
    for key in ('natives', 'rooms', 'physical_groups'):
        s |= {norm(x) for x in dev[key]}
    for key in ('canonical', 'aliases'):
        for k, vs in dev[key].items():
            s |= {norm(k)} | {norm(x) for x in vs}
    lists['dev_s1'] = s
    b = json.loads(F['bench'].read_text())
    s = {norm(x) for x in b['scenes']} | {norm(x) for x in b['physical_groups']}
    s |= {(DS.get(d, d), t) for d, t in b['rung1_tokens']}
    for k, m in b['members'].items():
        s.add(norm(k)); s.add(norm(m['group']))
    lists['bench'] = s
    lists['test'] = {norm(x) for x in json.loads(F['test'].read_text())['names']}
    r0 = json.loads(F['r0'].read_text())
    lists['r0'] = {norm(x) for x in r0['captures']}
    div = json.loads(F['division'].read_text())
    R['division_keys'] = sorted(div)[:20]
    lists['division_heldout'] = {norm(x) for x in div.get('heldout_scenes', [])}
    m400 = json.loads(F['m400_dev'].read_text())
    R['m400_dev_schema'] = m400.get('schema')
    if m400.get('schema') == 'dev_s1_withhold_v1':
        s = set()
        for key in ('natives', 'rooms', 'physical_groups'):
            s |= {norm(x) for x in m400[key]}
        for key in ('canonical', 'aliases'):
            for k, vs in m400[key].items():
                s |= {norm(k)} | {norm(x) for x in vs}
        lists['m400_dev'] = s
    # expand: every listed native contributes its tokens; scannet rooms cover every capture
    k1 = json.loads(F['k1'].read_text())
    venue = {}
    for cap in k1['teacher_k1']['captures']:
        venue[norm(cap['canonical'])] = norm(cap['room'])
    with F['arkit'].open() as f:
        for r in csv.DictReader(f):
            if r['visit_id'] not in ('', 'NA'):
                venue[('d3', r['video_id'])] = ('d3', 'venue'+r['visit_id'].split('.')[0])
    expanded = {}
    for name, members in lists.items():
        e = set(members)
        rooms = {x for x in members if x[0] == 'd1' and re.fullmatch(r'scene\d{4}', x[1])}
        for d, sc in list(members):
            if d in NS and not sc.startswith('venue') and not re.fullmatch(r'v[0-9a-f]{12}', sc):
                e |= {(d, t) for t in tokens(d, sc)}
                r = room(d, sc)
                if r: rooms.add(r)
        for d, sc in natives:
            if d == 'd1' and room(d, sc) in rooms:
                e.add((d, sc)); e |= {(d, t) for t in tokens(d, sc)}
        expanded[name] = e
        R.setdefault('list_sizes', {})[name] = [len(members), len(e)]
    return expanded, natives, venue


def check(R, expanded, venue, tok2nat):
    held = set(json.loads(F['held'].read_text())['vqa'])
    recs = pickle.loads((W/'rows.pkl').read_bytes())
    weights = json.loads((FB/'prior2/out/TOWARD_HARD_WEIGHTS.json').read_text())
    wq = {x['qid'] for c in weights['cells'].values() for x in c['rows']}
    hits = Counter(); unresolved = Counter(); examples = []
    for r in recs:
        d = DS.get(str(r['dataset']).casefold(), r['dataset'])
        key = (d, r['scene'])
        nat = tok2nat.get(key) if re.fullmatch(r'v[0-9a-f]{12}', str(r['scene'])) else key
        if nat is None: unresolved[(r['fam_tree'] in ('direction', 'facing_pairs'), d)] += 1
        keys = {key} | ({nat} if nat else set())
        if nat and room(*nat): keys.add(room(*nat))
        if nat in venue: keys.add(venue[nat])
        for name, e in expanded.items():
            if keys & e:
                hits[name, 'all'] += 1
                if r['qid'] in wq: hits[name, 'weights'] += 1
                if r['fam_tree'] in ('direction', 'facing_pairs'): hits[name, 'direction_cells'] += 1
                if len(examples) < 5: examples.append((name, r['qid'], sorted(map(list, keys))))
        if r['qid'] in held or set(r.get('label_row_keys') or []) & held:
            hits['held_qid', 'all'] += 1
            if r['qid'] in wq: hits['held_qid', 'weights'] += 1
    R['own_hits'] = {'|'.join(k): v for k, v in hits.items()}
    R['own_examples'] = examples
    R['unresolved_tokens'] = {f'{k[0]}|{k[1]}': v for k, v in unresolved.items()}
    R['weights_rows'] = len(wq)
    (W/'S4_LEGAL_own.json').write_text(json.dumps(R, indent=1) + '\n')
    print(json.dumps({k: v for k, v in R.items() if k not in ('inputs',)}, indent=1))


if __name__ == '__main__':
    main()
