"""Reviewer matrix: admission outcome per environment, directly and after P's legacy wrappers."""
import itertools, json, os, sys
from pathlib import Path
from unittest.mock import patch
W = Path(__file__).resolve().parents[1]
T = Path(sys.argv[1]).resolve(); label = sys.argv[2]
S = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21')
sys.path.insert(0, str(T))
from student_pilot.r2_intake import intake
from student_pilot.r2_materialize import materialize
from student_pilot.p3_provenance import load, pinned
from student_pilot import source_seal
from launch_r2 import distributed, host
assert Path(distributed.__file__).resolve().is_relative_to(T)
cfg = load(S/'work/build21/proofs/capacity/400/request_config.json')
manifests = [pinned(v) for v in cfg['r1_training']['routing_inputs'].values()]
OUT = W/'work'/('matrix_'+label); OUT.mkdir(parents=True, exist_ok=True)
MARK = OUT/'marked'; MARK.mkdir(exist_ok=True); (MARK/'.r2_local_node').touch()
PLAIN = OUT/'plain'; PLAIN.mkdir(exist_ok=True)
u = os.uname()
class Stop(Exception): pass
INTAKE_REFUSAL = 'Local slices must contain at most 2000 rows per family'
MAT_REFUSALS = ('Full materialization requires an explicit frame-host admission',
                'Full store forbidden on a local node; use slices of at most 2000 rows per family')
MAT_PASSED = 'Full materialization requires the bound sampling table'
counter = itertools.count()

def ops():
    out = {}
    try:
        for m in manifests:
            rows, _ = intake(m, limit=None); assert rows == []
        out['intake'] = True
    except ValueError as e:
        assert str(e) == INTAKE_REFUSAL, str(e); out['intake'] = False
    try:
        materialize(manifests, OUT/('m%d' % next(counter)), full=True); out['materialize'] = True
    except ValueError as e:
        assert str(e) in MAT_REFUSALS + (MAT_PASSED,), str(e); out['materialize'] = str(e) == MAT_PASSED
    for bad in (0, -1, 2001, True, 2000.0):
        try:
            intake(manifests[0], limit=bad); out.setdefault('limit_leak', []).append(repr(bad))
        except ValueError:
            pass
    return out

def frame(env, wrapper):
    if wrapper == 'worker':
        os.environ['K2'] = str(T)
        with patch.object(source_seal, 'inventory', side_effect=Stop):
            try: distributed.worker(OUT, 't', '0')
            except Stop: pass
        del os.environ['K2']
    elif wrapper == 'host':
        with patch.object(host, 'begin_checks', side_effect=Stop):
            try: host.execute_packet(OUT, {}, None, full=True)
            except Stop: pass
    return dict(resolved_native=os.environ.get('STUDENT_R2_FRAME_HOST'), q_e7_present='Q_E7' in os.environ, **ops())

records = []
VALUES = dict(Q_E7=(None, '0', '1', ''), STUDENT_R2_FRAME_HOST=(None, '0', '1'), K6=(None, '0', '1'),
              STUDENT_R2_LOCAL_NODE=(None, '0', '1'))
for combo in itertools.product(*VALUES.values()):
    env = {k: v for k, v in zip(VALUES, combo) if v is not None}
    for hostname in ('trinity-1-18', 'fixture-frame-host'):
        for marker in (False, True):
            for wrapper in ('direct', 'worker', 'host'):
                os.chdir(MARK if marker else PLAIN)
                with patch.dict(os.environ, env, clear=True), patch.object(os, 'uname', return_value=os.uname_result((u.sysname, hostname, u.release, u.version, u.machine))):
                    result = frame(env, wrapper)
                records.append(dict(env=env, host=hostname, marker=marker, wrapper=wrapper, **result))
os.chdir(W)
(W/'out'/('matrix_'+label+'.json')).write_text(json.dumps(dict(tree=str(T), records=records), indent=1)+'\n')
print('RECORDS', len(records), 'leaks', sum(bool(r.get('limit_leak')) for r in records))
