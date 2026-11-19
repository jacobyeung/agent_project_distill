"""Room keys and the room exclusions of b12_cntapp rows: K1 held-out rooms (b05 TEACHER_K1 4d4736cf, k1_split) and the
R0 reserve rooms (b10_reserve R0_ROOMS.txt bdb5d402). ARKit room = venue of the capture's 3dod visit_id."""
import csv, hashlib, json, re
A = '/scratch/jjyeung/orch_n30/b12_cntapp/work/auth/'
R0 = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/b10_reserve/R0_ROOMS.txt'
def _sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
assert _sha(R0).startswith('bdb5d402') and _sha(A + 'arkit_3dod_metadata.csv').startswith('657020f2')
_K = json.load(open(A + 'K1SPLIT_R0.json')); assert _K['teacher_k1']['sha256'].startswith('4d4736cf')
VISIT = {r['video_id']: r['visit_id'] for r in csv.DictReader(open(A + 'arkit_3dod_metadata.csv'))}
K1_HELDOUT = {c['room'] for c in _K['teacher_k1']['captures'] if c['k1_split'] == 'heldout'}
K1_CAPTURES = {c['canonical']: c['k1_split'] for c in _K['teacher_k1']['captures']}
R0_ROOMS = {l.strip() for l in open(R0) if l.strip()} | {v['room'] for v in _K['r0_scenes']['captures'].values()}
AUTH = dict(teacher_k1='4d4736cf64e496a184d36d74d710e76d1673429e28790613794867ac077048a9', r0_rooms=_sha(R0),
            arkit_metadata=_sha(A + 'arkit_3dod_metadata.csv'), r0_scenes='f7c458176426e22a13e47908b03abd2c6f5939d3e48eb7c24e7eba45b75ad479')
def room(canonical):
    ds, i = canonical.split('/', 1)
    if ds == 'scannet': return 'scannet/' + re.match(r'(scene\d+)', i).group(1)
    if ds in ('scannetpp', 'scannetppv2'): return 'scannetpp/' + i
    if ds == 'arkitscenes':
        v = VISIT.get(i); return 'arkitscenes/venue' + v if v and v != 'NA' else 'arkitscenes/capture' + i
    raise ValueError(canonical)
def status(canonical):
    r = room(canonical)
    return 'r0' if r in R0_ROOMS else 'k1_heldout' if r in K1_HELDOUT else 'ok'
