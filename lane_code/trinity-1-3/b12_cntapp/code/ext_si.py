"""student_input for extension scenes (frame-map scenes outside the D0 v5 VQA store) -> work/si_ext_by_alias.json.
frames: kit frame map 17aa3e9e (d, s, i -> path, sha256) at the raster pins; fps: ARKit 10, ScanNet from SCENE.json;
timestamps = index / fps; total_num_frames: ARKit = depth-listing length (checked against D0 pool captures by
--check), ScanNet from SCENE.json. Usage: ext_si.py [--check]"""
import gzip, json, sys, collections
W = '/scratch/jjyeung/orch_n30/b12_cntapp/work/'
FM = '/scratch/jjyeung/orch_n30/rows_rebuild/work/s0/pull/m3/frame_map.jsonl.gz'
FM_SHA = '17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3'
SI = json.load(open(W + 'si_by_alias.json'))
ark = json.load(open(W + 'streams_ark_jobs.json')); scn = json.load(open(W + 'streams_scn_jobs.json'))
def depth_n(i):
    try: return len(open(f'{W}inputs/ark_lists/{i}.depth_list.txt').read().split())
    except OSError: return None
if '--check' in sys.argv:
    c = collections.Counter()
    for j in ark:
        if j['inpool'] and j['alias'] in SI:
            n = depth_n(j['id'])
            if n is not None: c[(SI[j['alias']]['total_num_frames'] == n, SI[j['alias']]['fps'], SI[j['alias']]['frame_indices'] == j['pins'])] += 1
    print('pool ARKit (total == depth listing, fps, pins equal):', dict(c)); sys.exit()
want = {}
for j in ark:
    if not j['inpool']: want[j['alias']] = dict(pins=j['pins'], fps=10.0, total=depth_n(j['id']))
scn_log = {}
for l in open(W + 'inputs/scn/reader_scn.log'):
    if l.startswith('{'): d = json.loads(l); scn_log[d['id']] = d
for j in scn:
    if j['pins'] or j['id'] not in scn_log or scn_log[j['id']]['status'] != 'ok': continue
    s = json.load(open(W + 'inputs/scn/' + scn_log[j['id']]['scene_json'].lstrip('/')))['student_input']
    want[j['alias']] = dict(pins=list(s['frame_indices']), fps=float(s['fps']), total=s.get('total_num_frames'))
frames = collections.defaultdict(dict)
with gzip.open(FM, 'rt') as f:
    for line in f:
        v = json.loads(line); a = v['d'] + '/' + v['s']
        if a in want: frames[a][v['i']] = dict(path=v['path'], sha256=v['sha256'])
out = {}; st = collections.Counter()
for a, w in want.items():
    fr = frames.get(a, {})
    if w['total'] is None: st['no total_num_frames'] += 1; continue
    if any(p not in fr for p in w['pins']): st['pin frame not in frame map'] += 1; continue
    if max(w['pins']) >= w['total']: st['pin beyond total'] += 1; continue
    out[a] = dict(fps=w['fps'], timestamps=[p / w['fps'] for p in w['pins']], total_num_frames=w['total'], frame_indices=w['pins'],
                  frames=[fr[p] for p in w['pins']], src_qid=None, frame_map_sha256=FM_SHA, frame_store='k6tk')
    st['ok'] += 1
json.dump(out, open(W + 'si_ext_by_alias.json', 'w')); print(dict(st))
