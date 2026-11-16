"""The real reader's stage-1 socket, fed one K1 capture's cached SAM 3 detections, reproduces the training table's
selector inputs exactly (same producers, same geometry), and its argmax runs on them. CPU."""
import gzip, hashlib, json, sys
from pathlib import Path
import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
TREE = '/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449'
sys.path[:0] = [str(ROOT), TREE, str(ROOT / 'heads/selector')]
MIRROR = Path('/scratch/jjyeung/n30_mirror/k1_ops3/run_tower_sam_2')
CAPTURE = 'scannetpp/dfa70fb232'


def digest(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, allow_nan=False).encode()).hexdigest()


def rle_decode(m):
    h, w = m['size']
    v = np.repeat(np.arange(len(m['counts'])) % 2 == 1, m['counts'])
    return v.reshape((h, w), order='F')


def cache_detect(cand, raw_only=False):
    """Cached SAM 3 detections; raw_only keeps the instances of the raw-name prompt (what the in-call tower sees)."""
    from student_pilot import routed_features as F

    def detect(name):
        out = []
        for slot in range(32):
            r = cand['frames'][str(slot)]['phrases'].get(name)
            if r is None:
                out.append([]); continue
            inst = [e for e in r.get('instances') or [] if not raw_only or e.get('source_prompt', name) == name]
            pres = float(inst[0]['source_presence']) if raw_only and inst and 'source_presence' in inst[0] else float(r['presence'])
            out.append([dict(mask=F.resize(rle_decode(e['mask']), F.SHAPE), score=float(e['score']), presence=pres)
                        for e in sorted(inst, key=lambda e: -float(e['score']))])
        return out
    return detect


@pytest.fixture(scope='module')
def capture():
    folder = MIRROR / digest(CAPTURE)[:16]
    rec = json.load(gzip.open(ROOT / 'heads/selector/data/caps' / (CAPTURE.replace('/', '__') + '.json.gz'), 'rt'))
    with np.load(folder / 'tower.npz') as z:
        tower = {k: z[k] for k in z.files}
    receipt = json.loads((folder / 'PHASE_COMPLETE.json').read_text())
    return folder, rec, tower, receipt


@pytest.mark.parametrize('raw_only', [False, True])
def test_stage1_inputs_equal_training_table(capture, raw_only):
    from e2e_reader.geometry import from_tower
    from e2e_reader.stage1 import StageOne
    from student_pilot import camera_targets
    folder, rec, tower, receipt = capture
    if raw_only:
        rec = json.load(gzip.open(ROOT / 'heads/selector/data/caps_raw' / (CAPTURE.replace('/', '__') + '.json.gz'), 'rt'))
    raw = tower['raw_pose'][tower['anchor_slots']]
    R = np.array([camera_targets.rotation_from_xyzw(p[3:7]).T for p in raw])
    g = np.mean(-R[:, :, 1], axis=0); g /= np.linalg.norm(g)
    geo = from_tower(tower['raw_pose'], tower['anchor_slots'], tower['frame_indices'], tower['depth_grid'],
                     tower['grid_uv'], g, rec['scale'], receipt['source_hw'])
    cand = json.loads((folder / 'candidates.json').read_text())
    s = StageOne(cache_detect(cand, raw_only), None, geo)
    for name in cand['phrases']:
        s.features(name)
    got = {}
    for name in cand['phrases']:
        accepted, x = s.features(name)
        got.update({(name, a['candidate_id']): v for a, v in zip(accepted, x)})
    want = {(i['name'], i['candidate_id']): i['x'] for i in rec['inputs']}
    assert set(want) <= set(got)
    err = max(float(np.max(np.abs(np.array(got[k]) - np.array(want[k])))) for k in want)
    assert err < 1e-9, err


def test_stage1_select_runs(capture):
    from e2e_reader.geometry import from_tower
    from e2e_reader.stage1 import StageOne
    from selector_head import load_head
    folder, rec, tower, receipt = capture
    head, _ = load_head(ROOT / 'heads/selector/work/run_raw')
    x = torch.tensor([i['x'] for i in rec['inputs'] if i['name'] == rec['inputs'][0]['name']], dtype=torch.float64)
    k = StageOne.select(type('S', (), {'head': head})(), dict(x=x, name=rec['inputs'][0]['name']))
    assert -1 <= k < len(x)


def test_ground_and_gap_on_k1_capture(capture):
    """Full in-call ground/gap on real K1 tensors: cached detections -> StageOne (trained head) -> lift_plain ->
    min-area box -> v3.14 formatter."""
    from e2e_reader.geometry import from_tower
    from e2e_reader.grounding import StageOneSocket, ground_session
    from e2e_reader.servers import ReadServers
    from e2e_reader.stage1 import StageOne
    from selector_head import load_head
    from student_pilot import camera_targets
    folder, rec, tower, receipt = capture
    raw = tower['raw_pose'][tower['anchor_slots']]
    R = np.array([camera_targets.rotation_from_xyzw(p[3:7]).T for p in raw])
    g = np.mean(-R[:, :, 1], axis=0); g /= np.linalg.norm(g)
    geo = from_tower(tower['raw_pose'], tower['anchor_slots'], tower['frame_indices'], tower['depth_grid'],
                     tower['grid_uv'], g, rec['scale'], receipt['source_hw'])
    cand = json.loads((folder / 'candidates.json').read_text())
    head, _ = load_head(ROOT / 'heads/selector/work/run_raw')
    s = StageOne(cache_detect(cand, raw_only=True), head, geo)
    servers = ReadServers(geo, ground_session(geo, StageOneSocket(s.propose, s.select, (240, 320))))
    a, b = cand['phrases'][:2]
    texts = [servers.session_call(f'<ground obj="{a}" mode="box">')[0], servers.session_call(f'<ground obj="{b}" mode="box">')[0],
             servers.session_call(f'<gap a="{a}" b="{b}" rule="box_grid_5cm">')[0]]
    print(texts)
    assert all(isinstance(t, str) and t for t in texts)
    assert texts[2].startswith(('distance ', 'error: ', 'not seen'))
    assert [q['choice'] >= 0 for q in servers.session.socket.queries][:2] == [not texts[0].endswith('not seen'), not texts[1].endswith('not seen')]


def test_scale_head_call_equals_head(capture):
    sys.path.insert(0, str(ROOT / 'heads/scale'))
    from scale_head import load_head, prepare_inputs
    from e2e_reader.stage1 import ScaleHeadCall
    folder, rec, tower, receipt = capture
    head = load_head(ROOT / 'heads/scale/work/run1')
    t = dict(raw_pose9=tower['raw_pose'], anchor_slots=tower['anchor_slots'], depth_grid=tower['depth_grid'],
             depth_conf_grid=tower['depth_conf_grid'], points_grid=tower['points_grid'], grid_uv=tower['grid_uv'])
    with torch.no_grad():
        assert float(ScaleHeadCall(head)(t)) == float(head(**prepare_inputs(folder / 'tower.npz'))[0])
