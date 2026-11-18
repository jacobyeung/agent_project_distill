"""Small CPU-only audit checks; synthetic state never represents live admission."""
import collections
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import subprocess
from unittest.mock import patch

sys.dont_write_bytecode = True
W = Path(__file__).resolve().parent
K = W / 'x/x_69d2930d'
B = Path('/scratch/jjyeung/orch_n30/r1_ops/work/ex_9dd2fbb7')
S = W / 'audit_state'
S.mkdir(exist_ok=True)
# Run with the node-local p1cpu Python 3.12, matching the required modern APIs.
sys.path.insert(0, str(K / 'b'))
import d
import g
import i
import r8
import gcsput
import w
results = {}
launch = json.loads((K / 'k/launch.json').read_text())
cfg = json.loads((K / launch['config']['file']).read_text())
auth = json.loads((K / 'k/4.json').read_text())
sha = lambda raw: hashlib.sha256(raw).hexdigest()
results['authority_matches_installed_file'] = (K / 'k/4.json').read_bytes() == (B.parent / 'auth1/4.train.json').read_bytes()
results['admission_contract_sha_matches'] = d.digest(d.contract(launch, cfg)) == auth['admission_contract_sha256']
results['config_identity_matches'] = i.identity(cfg) == auth['config_sha256']
with patch.object(d, 'effective', side_effect=lambda root, cfg, launch=None: cfg), patch.object(r8, 'main', return_value='t'):
    g.check(K, environment={'SLURM_JOB_ID': '171377'}, mode='t')
results['g_static_checks_with_runtime_receipts_and_slot_stubbed'] = 'PASS'
derived = dict(cfg, preparation={'path': '/synthetic/preparation.json', 'sha256': '1'*64})
with patch.object(d, 'effective', return_value=derived), patch.dict(os.environ, {
        'SLURM_JOB_ID': '171377', 'SLURM_JOB_NUM_NODES': '1', 'SLURM_GPUS_ON_NODE': '4',
        'S1_CPU_REHEARSAL': '0'}):
    for mode in ('p', 't', 'u'):
        i.authorize(K, mode, '0')
    command = i.main(str(K), 't', '0', preflight=True)
    assert '--nproc-per-node=4' in command
    assert '--standalone' in command and '--nnodes=1' in command
results['i_authorize_p_t_u_with_admission_stubbed'] = 'PASS'
results['four_rank_launcher_command'] = command
class FakeTrainer:
    def train(self, config, **kwargs):
        self.received = config, kwargs
fake = FakeTrainer()
w.dispatch(K, 't', '0', auth, dict(derived), fake, S/'unused', '171377')
assert fake.received[0]['milestone_gate'] is None
assert fake.received[1] == dict(smoke_steps=None, resume_pin=None)
results['training_dispatch_without_execution'] = 'PASS'

run = S / 'run/673bc60f'
run.mkdir(parents=True, exist_ok=True)
persist = S / 'persistent/673bc60f'
assert r8.main(run, persist, '171377') == 't'
assert r8.main(run, persist, '171377') == 't'
try:
    r8.main(run, persist, '171378')
except ValueError as exc:
    results['foreign_marker_refuses_cold_restart'] = str(exc)
else:
    raise AssertionError('foreign marker accepted')
results['same_job_repeated_marker_check'] = 'PASS'

missing = S / 'not_yet_written.receipts.jsonl'
assert gcsput.done(str(missing)) == {}
results['missing_export_receipts_are_optional'] = 'PASS'
expected = {name for m in ('m100', 'm200', 'mstop', 'mstopB', 'mstopC')
            for name in gcsput.part_names('q8/8865619b/673bc60f_'+m+'.tar', 4)}
listed = (B / 'e.txt').read_text().splitlines()
assert set(listed) == expected and len(listed) == 20
results['all_20_export_names_match'] = 'PASS'
session_check = (B / 'jb.sh').read_text().split("/usr/bin/python3 -I -c '\n", 1)[1].split("' \"$KH/sess.json\"", 1)[0]
schema_results = {}
for label, value in [('mapping_of_uris', {n: 'https://example.invalid/session' for n in expected}),
                     ('invalid_array_of_names', sorted(expected)),
                     ('invalid_null_values', {n: None for n in expected})]:
    target = S / (label+'.json')
    target.write_text(json.dumps(value))
    target.chmod(0o600)
    result = subprocess.run([sys.executable, '-I', '-c', session_check, str(target), '673bc60f'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    schema_results[label] = result.returncode
assert schema_results == {'mapping_of_uris': 0, 'invalid_array_of_names': 0, 'invalid_null_values': 0}
results['real_wrapper_session_check_accepts_invalid_shapes'] = schema_results

sys.path.insert(0, str(W / 'trainer/A'))
from student_pilot import type_mix
type_mix.validate(cfg['type_mix'], cfg['recipe'])
results['type_mix_config_validation'] = 'PASS'
results['per_rank_microsteps'] = dict(collections.Counter(cfg['recipe']['mix']))
results['global_batch'] = len(cfg['recipe']['mix']) * cfg['world_size']
assert cfg['recipe']['milestones'] == cfg['milestones'] == [100, 200]
assert cfg['h1']['stop_after_step'] == 200 and cfg['recipe']['steps'] == 1000
results['milestone_and_stop_contract'] = 'PASS'
results['limits'] = 'No real admission receipt, GPU execution, network/session request, or live slot was tested.'
(W / 'audit_checks.json').write_text(json.dumps(results, indent=2)+'\n')
print(json.dumps(results, indent=2))
