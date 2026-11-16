"""Q2: does the sealed trainer accept the step-544 export as init_artifact through config fields alone?
Runs the trainer's own validate() field checks and init_from_artifact() up to the weight read, on CPU, with a stub model."""
import copy, json, sys, types
sys.path.insert(0, '.')
from student_pilot import carrier_c1_run as run
W = '/scratch/jjyeung/orch_n30/cont_ops/work/d0'
cfg = json.load(open(W + '/base/k/b02e4385.json'))
art_path = W + '/base/runs/469ddece/m544/artifact.json'
spec = dict(artifact=dict(path=art_path, sha256='1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef'),
            lm='full', heads=list(cfg['init_artifact']['heads']))
out = {}
run.validate_init(spec); out['validate_init'] = 'PASS'
d0 = copy.deepcopy(cfg); d0['init_artifact'] = spec
try:
    run.validate(d0); out['validate_cfg'] = 'PASS'
except Exception as e:
    out['validate_cfg'] = f'{type(e).__name__}: {e}'[:300]
model = types.SimpleNamespace(carrier_placement=cfg['carrier_placement'], frame_layout=cfg.get('frame_layout', 'spread'),
                              carrier_position_policy='native_v1', geometry_online=None)
try:
    run.init_from_artifact(model, spec, verify=True, part='lm')
    out['init_lm'] = 'loaded (unexpected without weights)'
except Exception as e:
    out['init_lm_stops_at'] = f'{type(e).__name__}: {e}'[:300]
a = json.load(open(art_path))
out['artifact'] = {k: a[k] for k in ('schema', 'pose_backing', 'placement', 'frame_layout', 'carrier_position_policy', 'step', 'training_mode', 'config_sha256')}
out['config'] = dict(carrier_placement=cfg['carrier_placement'], frame_layout=cfg.get('frame_layout'), heads=cfg['init_artifact']['heads'])
print(json.dumps(out, indent=1))
