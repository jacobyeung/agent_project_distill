"""On a dev-S1 geometry that the sealed guard refuses, the reader builds the geometry and serves camera and
ground/gap calls; no code on the read path evaluates the removed check."""
import json, sys
from pathlib import Path
import numpy as np

ROOT = Path('/scratch/jjyeung/orch_n30/reader_r1/work/b1/work/b04/b04_e2ehook')
sys.path[:0] = [str(ROOT), str(ROOT / 'tests'), '/scratch/jjyeung/orch_n30/reader_r1/work/b1/work/p/tree']
GEO = ROOT / 'work/n13/ret/native/geometry'


def refused_clip():
    v = json.loads((ROOT / 'out/proofs/GUARD_VERDICTS_DEVS1.json').read_text())['per_clip']
    return sorted(c for c, x in v.items() if x['sealed_guard_refuses'])[0]


def test_refused_geometry_is_served():
    import guard_diag
    from e2e_reader import geometry as G
    from e2e_reader.grounding import StageOneSocket, ground_session
    from e2e_reader.servers import ReadServers
    geo = G.from_npz(GEO / (refused_clip() + '.npz'))
    assert guard_diag.sealed_refuses(geo)
    m = np.zeros((240, 320), bool); m[100:140, 100:160] = True
    n = np.zeros((240, 320), bool); n[60:90, 200:260] = True

    def propose(name):
        mask = m if name == 'a' else n
        return [dict(candidate_id=name + ':0', masks={k: mask for k in (3, 4, 5) if geo.has(k)})], None
    servers = ReadServers(geo, ground_session(geo, StageOneSocket(propose, lambda x: 0, (240, 320), 32)))
    texts = [servers.head('<move from=1 to=9>')[0], servers.session_call('<ground obj="a" mode="box">')[0],
             servers.session_call('<ground obj="b" mode="box">')[0],
             servers.session_call('<gap a="a" b="b" rule="box_grid_5cm">')[0]]
    assert not any('opposes_gravity' in t for t in texts), texts
    assert texts[3].startswith('distance '), texts
