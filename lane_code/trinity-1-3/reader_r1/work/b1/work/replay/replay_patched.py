"""CPU replay of the own-arm reader's stage 1 (ground/gap) on cached raw-name SAM 3 proposals.

geometry 'tower'  = job 170056's G3T x own-depth-scale geometry (load_geometry on its native/geometry npz)
geometry 'hybrid' = H1-0's own pose9 + gravity (stored in each read) with G3T depth x scale (own depth is not stored)
rule 'null_argmax' = the shipped selector decode; 'candidates_argmax' = fix (a'): best candidate whenever one exists.
The SAM 3 proposals come from the dense raw-prompt cache (joint >= 0.05, cap 30, same 32 frames as the read).
"""
import sys, json, re, hashlib, collections, os
import numpy as np
sys.path[:0] = ['/scratch/jjyeung/orch_n30/reader_r1/work/b1/work/p/b', '/scratch/jjyeung/orch_n30/reader_r1/work/b1/work/p/tree']
import torch
torch.set_num_threads(1)
from student_pilot import routed_features as F
from student_pilot.ground_profiles import load_geometry
from student_pilot.scene_state import FrameMap
from student_pilot.camera_targets import to_gravity_reference_frame
from student_pilot import geometry_profiles as GP
from e2e_reader.geometry import reader_contract
from e2e_reader import stage1 as S1, grounding as GR
sys.path.insert(0, '/scratch/jjyeung/orch_n30/reader_r1/work/b1/work/p/b/heads/selector')
from selector_head import load_head

MC = 'n2r/mc/sj/mask_recall_run/results/'
HEAD, META = load_head('sel/run_iso')
MAN = {c['native']: c for c in json.load(open(MC + 'dense/MANIFEST.json'))['captures']}
ITEMS = {x['id']: x for x in json.load(open('f3/p446/items/devs1_routed.json'))['items']}
R1 = json.load(open('n2r/full_c8r/x/native/R1.json'))
PERC = {a['key'].split(':', 1)[1]: a['perception'] for a in R1['arms']['unflagged'] if a['question_type'] == 'object_abs_distance'}
del R1


def decode(rle):
    h, w = rle['size']; counts = np.asarray(rle['counts'], np.int64)
    return np.repeat(np.arange(len(counts)) % 2, counts).astype(bool).reshape((h, w), order='F')


def detections(native):
    c = json.loads(np.load(MC + 'dense/candidates/' + MAN[native]['scene'].replace('/', '__') + '.npz')['payload'].tobytes())
    def detect(name):
        ph = S1.name_key(name)
        if ph not in c['phrases']:
            return [[] for _ in range(32)]
        out = []
        for s in range(32):
            rec = c['frames'][str(s)]['phrases'].get(ph)
            frame = []
            if rec:
                for e in sorted(rec.get('instances') or [], key=lambda e: -float(e['score'])):
                    m = e['mask'] if isinstance(e['mask'], dict) else eval(e['mask'])
                    frame.append(dict(mask=F.resize(decode(m), F.SHAPE), score=float(e['score']), presence=float(rec['presence'])))
            out.append(frame)
        return out
    return c, detect


def tower_npz(item_id):
    p = PERC[item_id]['geometry']; f = 'g3t/native/geometry/' + p['path'].rsplit('/', 1)[1]
    assert hashlib.sha256(open(f, 'rb').read()).hexdigest() == p['sha256'], f
    return np.load(f)


def tower_geometry(item_id):
    # guard-free reader contract (b04 e2e_reader.geometry.from_arrays), as the in-call tower uses
    from e2e_reader.geometry import from_arrays
    z = tower_npz(item_id)
    return from_arrays(K=z['K'], canvas_to_source=z['canvas_to_source'], camera_to_world=z['camera_to_world'],
                       scale=float(z['scale']), depth_grid=z['depth_grid'], grid_uv=z['grid_uv'],
                       anchor_frame_indices=z['anchor_frame_indices']), z


def hybrid_geometry(item_id, pose9, gravity, hw):
    z = tower_npz(item_id)
    depth = np.asarray(z['depth_grid'], float) * float(z['scale'])
    uv = np.asarray(z['grid_uv'], float)
    R, t, fov = to_gravity_reference_frame(np.asarray(pose9, float), np.asarray(gravity, float))
    H, W = hw; C = np.tile(np.eye(4), (32, 1, 1)); C[:, :3, :3] = R; C[:, :3, 3] = t
    K = np.zeros((32, 3, 3)); K[:, 0, 0] = W / (2 * np.tan(fov[:, 1] / 2)); K[:, 1, 1] = H / (2 * np.tan(fov[:, 0] / 2))
    K[:, 0, 2] = W / 2; K[:, 1, 2] = H / 2; K[:, 2, 2] = 1
    A = np.tile(np.diag([W / 1000, H / 1000, 1.]), (32, 1, 1))
    idx = list(range(32))
    contract = reader_contract(GP)('legacy_v3122', FrameMap(tuple(idx)), idx[0], K, A, C, 1., 'vc', 'metric', 'metric', 0, 1)
    return GP.ProfileGeometry(contract, depth, uv)


def run(job):
    item_id, geo_kind, rule, names, gap_call, pose9, gravity = job
    it = ITEMS[item_id]; native = it['native']
    hw = tuple(MAN[native]['hw'])
    try:
        geom = tower_geometry(item_id)[0] if geo_kind == 'tower' else hybrid_geometry(item_id, pose9, gravity, hw)
        _, detect = detections(native)
        st = S1.StageOne(detect, HEAD, geom, rule=rule)
        sock = GR.StageOneSocket(st.propose, st.select, (240, 320), 32)
        sess = GR.ground_session(geom, sock)
        from e2e_reader.servers import ReadServers
        servers = ReadServers(geom, sess)
        out = {}; info = {}
        for n in names:
            out[n], info[n] = servers.session_call('<ground obj="%s" mode="box">' % n)
            assert len(json.dumps(info[n]['stage1'], allow_nan=False).encode()) < 64 * 1024
        gap = servers.session_call(gap_call)[0] if gap_call else None
        return dict(id=item_id, geo=geo_kind, rule=rule, ground=out, gap=gap, stage1=st.diagnostics, queries=sock.queries)
    except Exception as e:
        import traceback
        return dict(id=item_id, geo=geo_kind, rule=rule, error=repr(e)[:300], tb=traceback.format_exc()[-600:])


def jobs():
    R = [json.loads(l) for l in open('f3/r2/sj/h10sub3_b01ec87a6f29b00029ad2/items.jsonl')]
    out = []
    for x in R:
        if x['mode'] != 'none':
            continue
        names, gap = [], None
        for c in x['output']['calls']['records']:
            if c['family'] == 'ground':
                n = re.search(r'obj="([^"]*)"', c['call'])[1]
                if n not in names:
                    names.append(n)
            elif c['family'] == 'gap' and gap is None:
                gap = c['call']
        h = x['output']['heads']
        if x['id'] not in PERC or 'geometry' not in PERC[x['id']]:
            continue
        for g in ('tower', 'hybrid'):
            for r in ('null_argmax', 'candidates_argmax'):
                out.append((x['id'], g, r, names[:2], gap, h['pose9'], h['gravity']))
    return out


if __name__ == '__main__':
    from multiprocessing import Pool
    J = jobs()
    if len(sys.argv) > 1:
        J = J[:int(sys.argv[1])]
    print('jobs', len(J), flush=True)
    with Pool(int(os.environ.get('NP', '16'))) as p, open(os.environ.get('OUT', 'replay_out.jsonl'), 'w') as f:
        for i, r in enumerate(p.imap_unordered(run, J, chunksize=1)):
            f.write(json.dumps(r) + '\n'); f.flush()
            if i % 50 == 0:
                print(i, flush=True)
