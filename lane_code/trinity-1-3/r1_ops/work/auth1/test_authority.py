"""CPU authority regression; synthetic admission files, real unmodified gates."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import patch

W = Path(__file__).resolve().parent
SOURCE = Path('/scratch/jjyeung/orch_n30/r1_ops/work/drv_p5/tests_p5_lp0z7pgr/derived_ready')
T = Path(tempfile.mkdtemp(prefix='check_', dir=W))
K = T / 'kit'
shutil.copytree(SOURCE, K)
sys.dont_write_bytecode = True
sys.path.insert(0, str(K / 'b'))
import g
import i
import d
import r8
import w

def load(p):
    return json.loads(p.read_text())

launch = load(K / 'k/launch.json')
cfg = load(K / launch['config']['file'])
assert launch['source_revision'] == load(W / '4.train.json')['source_revision']
assert i.identity(cfg) == 'fac0705214fdecb53561c633d7d94642cd469b50b662c5de81f09d11891d115f'
run = T / 'run' / '673bc60f'
inputs = run / 'inputs'
inputs.mkdir(parents=True)
persistent = T / 'persistent' / '673bc60f'
logical = Path(launch['in_job_admission']['directory'])

def put(name, value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    (inputs / name).write_bytes(raw)
    return dict(path=str(logical / name), sha256=hashlib.sha256(raw).hexdigest())

# These receipts are synthetic unit-test evidence, never deployable admission proof.
derived = copy.deepcopy(cfg)
assert 'mdg' not in cfg and 'mdg' not in cfg['streams']
derived['streams']['pointing'] = put('pointing.json', {'unit_test': True})
routing = put('routing_materialization.json', dict(schema='s1-routing-materialization-v1',
    status='PASS', inputs=cfg['s1_routing'], legacy=cfg['streams']['routing']))
derived['streams']['routing'] = put('routing.json', dict(materialization=routing))
derived.pop('admission', None)
derived['preparation_output'] = str(logical)
seal = dict(schema='s1-run-seal-v1', tree_sha256=launch['source_seal']['tree_sha256'],
            archive=launch['source_seal']['archive'], config_sha256=i.identity(derived))
seal['sha256'] = d.digest(seal)
scenes = dict(coverage=dict(schema='s1-scene-coverage-result-v1', status='PASS',
                           policy=cfg['scene_coverage'], sources={'unit_test': True}))
counts = {name: 1 for name in cfg['streams']}
prep = dict(config_sha256=i.identity(derived), source_seal=seal,
            streams={name: dict(count=n) for name, n in counts.items()},
            scene_filter_report=scenes, stream_status={'mdg': 'absent'})
derived['preparation'] = put('preparation.json', prep)
parent = put('parent.json', dict(schema='s1-parent-grounding-v1', status='PASS',
    parent_artifact=cfg['init_artifact']['artifact'], mdg='absent',
    method='verify-parent-metadata-without-mdg', parent_base_identity=cfg['base_identity'],
    parent_weight_payloads_verified=False, full_parent_model_loaded=False))
receipt = dict(schema='s1-in-job-data-v1', status='PREPARED', production_authorized=False,
    rehearsal=False, real_frames_verified=True, gpu_first_step_pending=True,
    source_revision=launch['source_revision'], input_config={'sha256': launch['config']['sha256']},
    world_size=4, input_streams=cfg['streams'], config=put('config.json', derived),
    source_seal=seal, source_counts=counts, preparation=derived['preparation'],
    scene_exclusions=scenes, routing_materialization=routing, mdg='absent',
    frames=put('frames.json', dict(all_retained_frames_exist=True, sources={'unit_test': True})),
    parent_grounding=parent)
(inputs / 'data_receipt.json').write_text(json.dumps(receipt))

# Redirect only absent Orchard filesystem locations. All validators execute.
original_choose = r8.main
def local_choose(directory, persisted=None, job=None):
    assert directory == launch['run_directory']
    assert persisted == launch['persistent_run_root']
    return original_choose(str(run), str(persistent), job)

def local_path(value, *parts):
    if str(value) == launch['run_directory']:
        value = run
    return Path(value, *parts)

env = dict(SLURM_JOB_ID='171377', SLURM_JOB_PARTITION='advanced', SLURM_JOB_NUM_NODES='1',
           SLURM_GPUS_ON_NODE='4', SLURM_TIMELIMIT='780', SLURM_JOB_TIME_LIMIT='13:00:00',
           S1_CPU_REHEARSAL='0', CUDA_VISIBLE_DEVICES='')
results = []
def check(label, fn, refusal=None):
    try:
        fn()
    except ValueError as exc:
        if refusal != str(exc):
            raise
        result = f'PASS {label}: REFUSED: {exc}'
    else:
        assert refusal is None, label + ' unexpectedly accepted'
        result = f'PASS {label}'
    results.append(result)
    print(result, flush=True)

with patch.dict(os.environ, env, clear=True), patch.object(d, 'Path', local_path), patch.object(r8, 'main', local_choose):
    for authority in ('4.p.json', '4.train.json'):
        (K / 'k/4.json').write_bytes((W / authority).read_bytes())
        old = authority == '4.p.json'
        check(authority + ' g.check(t)', lambda: g.check(K, mode='t'),
              'Written slot authorization is absent or expires too early' if old else None)
        check(authority + ' i.authorize(t,0)', lambda: i.authorize(K, 't', '0'),
              'Operation not authorized' if old else None)
        check(authority + ' g.check(p)', lambda: g.check(K, mode='p'))
        check(authority + ' i.authorize(p,0)', lambda: i.authorize(K, 'p', '0'))
        if not old:
            check(authority + ' i.authorize(u,0)', lambda: i.authorize(K, 'u', '0'))
            for rank in range(4):
                with patch.dict(os.environ, {'RANK': str(rank)}):
                    check(f'worker {rank} authorize(t,0)', lambda: w.authorize(K, 't', '0'))
            class Run:
                @staticmethod
                def train(settings, **kwargs):
                    assert settings['milestone_gate'] is None
                    assert kwargs['resume_pin'] in (None, 'latest')
            for mode in ('t', 'u'):
                auth, effective = i.authorize(K, mode, '0')
                check('w.dispatch ' + mode, lambda: w.dispatch(K, mode, '0', auth, effective, Run, K/'o/171377', '171377'))
            with patch.dict(os.environ, {'SLURM_GPUS_ON_NODE': '3'}):
                check('wrong GPU count', lambda: i.authorize(K, 't', '0'), 'Resources differ')

for rel in ('b/g.py', 'b/i.py', 'b/w.py', 'b/d.py', 'b/r8.py', 'k/launch.json'):
    assert (K/rel).read_bytes() == (SOURCE/rel).read_bytes(), rel
print('PASS gates and launch bytes unchanged; source revision unchanged; no CUDA import or GPU use')
print('Synthetic admission receipts and filesystem relocation only; this is not a production admission test.')
(W / 'test_results.json').write_text(json.dumps(dict(results=results, fixture=str(K),
    source_revision=launch['source_revision'], environment=env,
    limitations='Synthetic admission receipts; filesystem paths redirected into lane; no training run.'), indent=2)+'\n')
