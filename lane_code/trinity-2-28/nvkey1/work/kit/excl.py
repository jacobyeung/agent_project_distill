"""nvkey scene exclusion assert, loaded by every job builder and by the sender (nvrun.py).
Six protected sets, each pinned by sha256 in K/excl: BENCH v2 (VSI-Bench, ReVSI from REVSI_SCENE_EXCLUSIONS_v1, VSTI, STI-Bench/ReSTI, DSI, OSI,
MindCube; rooms expanded to every capture), dev-S1, R0 (reserve rooms), withheld-80, K1 held-out (K1 manifest k1_split/split != train; teacher list
4d4736cf). ARKit rooms come from the pinned arkit_3dod_metadata.csv (visit_id). A scene is refused when its capture name or its room is in any set.
usage as a module: import excl; excl.reasons('arkitscenes/41048124') -> []; excl.assert_train(scenes) raises on any hit.
usage as a script: excl.py -> prints the pins and the set sizes (the V0 receipt)."""
import csv, hashlib, json, os, re, sys
K = os.environ.get('NVK', '/scratch/jjyeung/orch_n30/nvkey1/work')
E = K + '/excl'
PINS = {'bench_v2': ('benchmark_scene_exclusions.json', '3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970'),
        'dev_s1': ('dev_scene_exclusions.json', '969cdb56ce508eff79390d67099c889b92bd360e93dc42ba07f3683ec216a986'),
        'r0': ('R0_ROOMS.txt', 'bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3'),
        'withheld80': ('WITHHELD_ROOMS_80.json', '634820b44927b1a50c18db9b90246b4b99f8954b0d7f5f2893e547f1c92879ed'),
        'k1_teacher': ('TEACHER_K1.raw', '4d4736cf64e496a184d36d74d710e76d1673429e28790613794867ac077048a9'),
        'arkit_visits': ('arkit_3dod_metadata.csv', '657020f2d1119220b5068176ffc7298a8585076468407b60d8f5e3e6223442ca')}
K1MAN = K + '/k1r/geo_k1/stage/K1_MANIFEST.arkit_timing.json'
DS = {'d1': 'scannet', 'd2': 'scannetpp', 'd3': 'arkitscenes', 'scannetppv2': 'scannetpp', 'scannet++': 'scannetpp', 'scannetpp': 'scannetpp',
      'scannet': 'scannet', 'arkitscenes': 'arkitscenes', 'arkit': 'arkitscenes'}
_S = None
def _read(role):
    name, sha = PINS[role]; raw = open(os.path.join(E, name), 'rb').read()
    assert hashlib.sha256(raw).hexdigest() == sha, 'exclusion list %s differs from its pin' % role
    return raw
def norm(name):
    ds, s = str(name).split('/', 1); d = DS.get(ds.lower())
    if d is None: raise ValueError('unknown dataset prefix in %r' % name)
    return d + '/' + s
def room(canonical, visits=None):
    c = norm(canonical); ds, s = c.split('/', 1)
    if ds == 'scannet':
        m = re.fullmatch(r'(scene\d{4})_\d{2}', s); return 'scannet/' + (m.group(1) if m else s)
    if ds == 'arkitscenes':
        if s.startswith('venue'): return c
        v = (visits or _sets()['visits']).get(s)
        return 'arkitscenes/venue' + v if v and v != 'NA' else c
    return c
def _sets():
    global _S
    if _S is not None: return _S
    visits = {r['video_id']: r['visit_id'] for r in csv.DictReader(_read('arkit_visits').decode().splitlines())}
    S = {'visits': visits, 'names': {}, 'rooms': {}}
    b = json.loads(_read('bench_v2'))
    S['names']['bench_v2'] = {norm(x) for x in b['scenes']}; S['rooms']['bench_v2'] = {norm(x) for x in b['physical_groups']}
    d = json.loads(_read('dev_s1'))
    nm = {norm(x) for x in d['natives']}
    for k in ('canonical', 'aliases'):
        for a, al in d[k].items(): nm.add(norm(a)); nm.update(norm(x) for x in al if not re.fullmatch(r'v[0-9a-f]{12}', x.split('/', 1)[1]))
    S['names']['dev_s1'] = nm; S['rooms']['dev_s1'] = {norm(x) for x in d['rooms'] + d['physical_groups']}
    r0 = [x for x in _read('r0').decode().split() if x]
    S['names']['r0'] = set(); S['rooms']['r0'] = {room(x, visits) for x in r0}
    w = json.loads(_read('withheld80'))
    S['names']['withheld80'] = {norm(x) for al in w['aliases'].values() for x in al if not re.fullmatch(r'v[0-9a-f]{12}', x.split('/', 1)[1])}
    S['rooms']['withheld80'] = {room(x, visits) for x in w['rooms']}
    _read('k1_teacher')
    man = json.load(open(K1MAN)); held = [c for c in man['captures'] if c.get('k1_split') != 'train' or c.get('split') != 'train']
    S['names']['k1_heldout'] = {norm(c['canonical']) for c in held}
    S['rooms']['k1_heldout'] = {room(c['canonical'], visits) for c in held} | {norm(c['room']) for c in held if isinstance(c.get('room'), str) and '/' in c['room']}
    S['k1_train'] = {norm(c['canonical']) for c in man['captures'] if c.get('k1_split') == 'train' and c.get('split') == 'train'}
    _S = S; return S
def reasons(canonical):
    S = _sets(); c = norm(canonical); r = room(c)
    return sorted(k for k in S['names'] if c in S['names'][k] or r in S['rooms'][k])
def assert_train(scenes):
    bad = {s: reasons(s) for s in scenes}; bad = {s: v for s, v in bad.items() if v}
    if bad: raise AssertionError('protected scenes in a train job: %s' % json.dumps(dict(list(bad.items())[:10])))
    return True
def receipt():
    S = _sets()
    return {'pins': {k: v[1] for k, v in PINS.items()}, 'k1_manifest_sha256': hashlib.sha256(open(K1MAN, 'rb').read()).hexdigest(),
            'names': {k: len(v) for k, v in S['names'].items()}, 'rooms': {k: len(v) for k, v in S['rooms'].items()}, 'k1_train_captures': len(S['k1_train'])}
if __name__ == '__main__':
    print(json.dumps(receipt(), indent=0))
