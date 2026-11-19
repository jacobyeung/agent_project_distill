"""S2: verified rank vs follower attach -- which bytes are hashed, which identities are still enforced.

Usage: python s2_check.py <tree>  ->  S2_<tree>.json
"""
import copy, json, os, sys, tempfile, types
from pathlib import Path
from unittest import mock

W = Path(__file__).resolve().parent; NAME = sys.argv[1]; T = W / NAME
OUT = Path(tempfile.mkdtemp(prefix='s2_' + NAME + '_', dir=W))
os.environ.update(LANE_TEST_OUTPUT=str(OUT), TMPDIR=str(OUT), CUDA_VISIBLE_DEVICES='')
tempfile.tempdir = str(OUT); os.chdir(T); sys.path.insert(0, str(T))
pk = types.ModuleType('tests'); pk.__path__ = [str(T / 'tests')]; sys.modules['tests'] = pk
import torch
torch.set_num_threads(8)
from tests.test_scale_donor import fixture, source, settings
from student_pilot import scale_donor as D, p3_provenance as P, r1_persisted
from student_pilot.p3_provenance import file_pin

R, fails = {}, []
def need(ok, msg):
    if not ok: fails.append(msg)

def outcome(fn):
    try:
        d = fn(); return dict(accepted=True, pins=D.digest(d.initial_pins))
    except Exception as e:  # noqa: BLE001
        return dict(accepted=False, error=f'{type(e).__name__}: {str(e)[:160]}')

def attach_spied(cfg, verify):
    m, _, _ = fixture()
    with mock.patch.object(P, 'sha256', wraps=P.sha256) as h, mock.patch.object(D.torch, 'load', wraps=torch.load) as l:
        d = D.attach(m, cfg, verify_assets=verify)
    return d, [str(c.args[0]) for c in h.call_args_list], [dict(path=str(c.args[0]), mmap=c.kwargs.get('mmap')) for c in l.call_args_list]

model, _, _ = fixture()
pin = source(model, OUT / 'src'); cfg = settings(model, pin, 'V1')
heads = OUT / 'src/heads.pt'; art = OUT / 'src/artifact.json'
d0, h0, l0 = attach_spied(cfg, True); d1, h1, l1 = attach_spied(cfg, False)
R['verified'] = dict(hashed=h0, loads=l0); R['follower'] = dict(hashed=h1, loads=l1)
need(str(heads) in h0 and str(art) in h0, 'verified rank did not hash artifact and heads')
need(str(heads) not in h1, 'follower hashed heads'); need(str(art) in h1, 'follower skipped the artifact pin')
need(all(x['mmap'] for x in l0 + l1), 'heads not memory-mapped')
need(d0.initial_pins == d1.initial_pins, 'follower donor differs on identical bytes')

# Relocated staging: both ranks read the same relocated replica.
rep = OUT / 'replica.pt'; rep.write_bytes(heads.read_bytes())
with r1_persisted.scope({P.sha256(heads): str(rep)}):
    _, hr0, lr0 = attach_spied(cfg, True); _, hr1, lr1 = attach_spied(cfg, False)
R['relocated'] = dict(verified_hashed=hr0, verified_loads=lr0, follower_hashed=hr1, follower_loads=lr1)
need(str(rep) in hr0 and lr0[0]['path'] == str(rep) and lr1[0]['path'] == str(rep), 'relocation not shared by both ranks')

def variant(tag, mutate_cfg=None, mutate_files=None, mutate_model=None):
    c = copy.deepcopy(cfg); root = OUT / tag; root.mkdir()
    (root / 'heads.pt').write_bytes(heads.read_bytes())
    if mutate_files:
        mutate_files(root / 'heads.pt')
    a = json.loads(art.read_text()); a['heads'] = file_pin(root / 'heads.pt') if not mutate_files else dict(path=str(root / 'heads.pt'), sha256=P.sha256(heads))
    (root / 'artifact.json').write_text(json.dumps(a)); c['checkpoint'] = file_pin(root / 'artifact.json')
    if mutate_cfg:
        c = mutate_cfg(c)
    res = {}
    for verify in (True, False):
        def go():
            m, _, _ = fixture()
            if mutate_model:
                mutate_model(m)
            return D.attach(m, c, verify_assets=verify)
        res['verified' if verify else 'follower'] = outcome(go)
    return res

def tamper(key_prefix):
    def f(p):
        s = torch.load(p, weights_only=True); k = next(k for k in s if k.startswith(key_prefix))
        s[k] = s[k].clone(); s[k].reshape(-1)[0] += 1; torch.save(s, p)
    return f

def bump_visual(m):
    with torch.no_grad():
        next(m.auxiliary_heads.depth.model.visual.parameters()).reshape(-1)[0] += 1

cases = {
    'feature_contract_pin': variant('fc', mutate_cfg=lambda c: dict(c, feature_contract_sha256='0' * 64)),
    'visual_pin': variant('vp', mutate_cfg=lambda c: dict(c, visual_sha256='0' * 64)),
    'live_visual_changed': variant('lv', mutate_model=bump_visual),
    'heads_visual_tampered': variant('hv', mutate_files=tamper('depth.model.visual.')),
    'artifact_pin_wrong': variant('ap', mutate_cfg=lambda c: dict(c, checkpoint=dict(c['checkpoint'], sha256='0' * 64))),
    'heads_point_depth_tampered': variant('hp', mutate_files=tamper('depth.auxiliary_heads.camera.point_depth.')),
}
R['cases'] = cases
for k in ('feature_contract_pin', 'visual_pin', 'live_visual_changed', 'heads_visual_tampered', 'artifact_pin_wrong'):
    need(not cases[k]['verified']['accepted'] and not cases[k]['follower']['accepted'], f'{k} accepted')
need(not cases['heads_point_depth_tampered']['verified']['accepted'], 'verified rank accepted tampered heads')
R['follower_accepts_unhashed_point_depth_change'] = cases['heads_point_depth_tampered']['follower']['accepted']
R['status'] = 'PASS' if not fails else 'FAIL'; R['failures'] = fails
(W / f'S2_{NAME}.json').write_text(json.dumps(R, indent=1))
print(NAME, R['status'], fails, json.dumps({k: {r: v[r].get('error', 'accepted')[:70] for r in v} for k, v in cases.items()}, indent=0))
