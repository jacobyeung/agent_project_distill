"""Run donor2's REAL_WEIGHT_COMMAND.sh verbatim from the patched tree on donor2's fixture inputs (read-only)."""
import hashlib, json, os, subprocess
from pathlib import Path

W = Path(__file__).resolve().parent; D2 = Path('/scratch/jjyeung/orch_n30/fb_pack/donor2')
SH = D2 / 'out/REAL_WEIGHT_COMMAND.sh'; EC = D2 / 'work/export_check'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
inv = json.loads((D2 / 'out/K1_INVARIANCE.json').read_text())
res = {'script_sha256': sha(SH), 'bash_n': subprocess.run(['bash', '-n', str(SH)]).returncode}

def env_for(v, binding):
    e = dict(os.environ, PYTHON='/scratch/jjyeung/envs/p1cpu/bin/python', DONOR_IMAGE_SIDE='4',
             N_INIT_ARTIFACT=v['settings']['checkpoint']['path'], N_STEP2_ARTIFACT=v['export']['path'],
             N_PREPARATION=str(EC / 'preparation.json'), N_MODEL_CONFIG=str(EC / 'model_config.json'),
             K1_SELECTION=str(D2 / 'out/K1_SELECTION.json'), N_DONOR_BINDING=str(binding),
             N_REPLICAS=str(EC / f"replicas_{v['variant']}.json"), CUDA_VISIBLE_DEVICES='')
    for k in ('N_INIT_ARTIFACT', 'N_STEP2_ARTIFACT', 'N_PREPARATION', 'N_MODEL_CONFIG', 'K1_SELECTION', 'N_DONOR_BINDING', 'N_REPLICAS'):
        e[k + '_SHA'] = sha(e[k])
    return e

def go(tag, env):
    env = dict(env, DONOR_CHECK_OUTPUT=str(W / f'REALCMD_{tag}.json'))
    r = subprocess.run(['taskset', '-c', '0-7', 'bash', str(SH)], cwd=W / 'new', env=env, capture_output=True, text=True)
    out = W / f'REALCMD_{tag}.json'
    status = json.loads(out.read_text()).get('status') if out.exists() and r.returncode == 0 else None
    res[tag] = dict(rc=r.returncode, status=status, stderr_tail=r.stderr.strip().splitlines()[-1:] if r.stderr else [])
    print(tag, res[tag], flush=True)

for v in inv['variants']:
    go(v['variant'], env_for(v, EC / f"binding_{v['variant']}.json"))
# Negative: a binding JSON without the top-level scale_donor key must fail.
v = inv['variants'][0]; flat = W / 'binding_flat.json'; flat.write_text(json.dumps(v['settings']))
go('flat_binding', env_for(v, flat))
# Negative: a missing required variable stops before Python runs.
e = env_for(v, EC / 'binding_V1.json'); e.pop('N_STEP2_ARTIFACT_SHA'); go('missing_var', e)
(W / 'REALCMD.json').write_text(json.dumps(res, indent=1))
