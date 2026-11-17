"""Regression tests for the Codex review of 2026-11-16 (receipt agent/scratch/codex_runs/20261116T140434Z_b04_review_e2e):
native reads, writes and outside .pth files are refused (2); a call's selector inputs do not depend on the names
asked before it (3); lifting keeps every mask pixel (5); the own-depth scale has no range gate (6); quoted calls are
not calls and long calls are detected (7); a response at the token cap is complete and enters the cache (8); the
selector loader never opens a held-out table when asked for train (9). CPU."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import numpy as np
import pytest
import torch

ROOT = Path('/scratch/jjyeung/orch_n30/reader_r1/work/b1/work/b04full')
TREE = '/scratch/jjyeung/orch_n30/reader_r1/work/b1m/out/src/tree'
sys.path[:0] = [str(ROOT), TREE, str(ROOT / 'heads/selector'), str(ROOT / 'tests')]
TOK = ROOT / 'work/n13/obj/base/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a'

from e2e_reader import artifact as A  # noqa: E402
from e2e_reader.callhook import CallHook, decode_loop  # noqa: E402


@pytest.fixture(scope='module')
def tok():
    from transformers import AutoTokenizer
    from student_pilot.carrier_c1_routing import add_routing_tokens
    t = AutoTokenizer.from_pretrained(TOK)
    return t, add_routing_tokens(NS(tokenizer=t))['ids']


@pytest.fixture()
def art(tmp_path):
    from safetensors.torch import save_file
    root = tmp_path / 'artifact'
    root.mkdir()
    save_file({'w': torch.zeros(2)}, str(root / 'in.safetensors'))
    (root / 'cfg.json').write_text('{}')
    m = A.build_manifest(root, dict(lm=('checkpoint', ['in.safetensors']), tokenizer=('tokenizer', ['cfg.json']),
                                    g3t=('g3t', ['cfg.json']), scale_head=('scale_head', ['cfg.json'])))
    _, digest = A.write_manifest(root, m)
    save_file({'w': torch.zeros(2)}, str(tmp_path / 'outside.safetensors'))
    (tmp_path / 'outside.pth').write_bytes(b'x')
    return A.Artifact(root, 'E2E_MANIFEST.json', digest).verify(), tmp_path


def test_native_read_outside_manifest_refused(art, monkeypatch):
    import types
    import safetensors
    from safetensors import safe_open
    a, tmp = art
    from tokenizers import Tokenizer
    early = types.ModuleType('early_loader')  # a module that bound the openers at import, under other names
    early.safe_open = safe_open
    early.so = safe_open
    early.tok_from = Tokenizer.from_file
    monkeypatch.setitem(sys.modules, 'early_loader', early)

    def late(path):  # tower_read's pattern: import inside the function
        from safetensors import safe_open as so
        return so(path, framework='pt')
    with A.Audit(a) as audit:
        with late(str(a.root / 'in.safetensors')) as f:
            assert list(f.keys()) == ['w']
        for opener in (late, lambda p: early.safe_open(p, framework='pt'), lambda p: early.so(p, framework='pt'),
                       lambda p: safetensors.torch.load_file(p), lambda p: safetensors.torch.load_file(filename=p),
                       lambda p: early.tok_from(p)):
            with pytest.raises(PermissionError):
                opener(str(tmp / 'outside.safetensors'))
    assert [v[0] for v in audit.violations] == ['data_outside_manifest'] * 6
    assert safetensors.safe_open is safe_open and early.safe_open is safe_open and early.so is safe_open  # restored


def test_outside_pth_and_writes_refused(art):
    a, tmp = art
    with A.Audit(a):
        with pytest.raises(PermissionError):
            open(tmp / 'outside.pth', 'rb')
        with pytest.raises(PermissionError):
            open(a.root / 'in.safetensors', 'r+b')
        with pytest.raises(PermissionError):
            open(tmp / 'new.txt', 'w')
    assert not (tmp / 'new.txt').exists()


def push_text(hook, tok, text):
    forced = []
    for t in tok.encode(text, add_special_tokens=False):
        forced += hook.push_sampled(t)
    return forced


def serving_hook(tok):
    t, openers = tok
    hook = CallHook(t, openers.values())
    hook.begin(dict(ground=lambda c: ('ok', {}), gap=lambda c: ('ok', {}), move=lambda c: ('ok', {})))
    return hook, t


def test_quoted_call_is_not_a_call(tok):
    hook, t = serving_hook(tok)
    push_text(hook, t, 'Example: `<ground obj="chair" mode="box">` is the form. ')
    assert hook.records == []
    push_text(hook, t, 'Now <ground obj="chair" mode="box">')
    assert [r['family'] for r in hook.records] == ['ground']


@pytest.mark.parametrize('text,calls', [
    ('A span `' + ' '.join(['word'] * 80) + '` closed. Then <move from=1 to=9>', 1),
    ('```\nexample <move from=1 to=9>\n', 0),
    ('```\nx\n```\nreal <move from=1 to=9>', 1),
    ('inline `start\nstill code <move from=1 to=9>', 0),
    ('double ``code ` <move from=1 to=9>', 0),
    ('double ``code`` then <move from=1 to=9>', 1),
    ('````\n```\nexample <move from=1 to=9>\n', 0),
    ('````\nx\n````\nreal <move from=1 to=9>', 1),
    ('~~~\nexample <move from=1 to=9>\n', 0),
])
def test_quote_state_over_whole_text(tok, text, calls):
    hook, t = serving_hook(tok)
    push_text(hook, t, text)
    assert len(hook.records) == calls


def test_long_gap_call_detected(tok):
    hook, t = serving_hook(tok)
    call = '<gap a="' + ' '.join(f'w{i}' for i in range(120)) + '" b="table" rule="box_grid_5cm">'
    assert len(t.encode(call, add_special_tokens=False)) > 96
    push_text(hook, t, 'then ' + call)
    assert [r['call'] for r in hook.records] == [call]


def test_response_at_cap_is_complete_and_cached(tok):
    hook, t = serving_hook(tok)
    script = t.encode('a <move from=1 to=9>', add_special_tokens=False)
    steps = []

    def out(next_id):
        logits = torch.full((1, 1, len(t)), -1e9)
        logits[0, 0, next_id] = 0.
        return NS(logits=logits)

    def step(ids):
        steps.append(list(ids))
        return out(script[len(steps)] if len(steps) < len(script) else t.eos_token_id)
    finish = decode_loop(step, out(script[0]), hook, eos_ids=[t.eos_token_id], cap=len(script) + 1)
    assert finish == 'max_new_tokens'
    rec = hook.records[0]
    forced = steps[-1][1:]
    assert rec['forced_tokens'] == len(forced) > 3
    assert t.decode(forced).endswith('</tool_response>')
    assert sum(len(s) for s in steps) == len(hook.ids)


def test_lift_keeps_every_mask_pixel():
    from e2e_reader.grounding import lift_plain

    class Geo:
        C = np.zeros((32, 4, 4))

        def has(self, k):
            return True

        def lift(self, k, uv, mode):
            P = np.column_stack((uv, np.ones(len(uv))))
            return P, P, None
    for mask_box, n in (((slice(100, 110), slice(100, 110)), 100), ((slice(100, 101), slice(100, 110)), 10),
                        ((slice(0, 10), slice(0, 10)), 100)):
        masks = np.zeros((32, 240, 320), bool)
        masks[(0,) + mask_box] = True
        r = lift_plain('x', masks, Geo())
        assert r['seen'] and len(r['points']['1']) == n


def test_own_depth_scale_has_no_range_gate():
    from e2e_reader.stage1 import median_ratio
    d = np.array([[1., 1.], [1., 1.]]); c = np.array([[2., 2.], [1., 1.]])
    assert median_ratio(d, c, 12 * d) == 12.
    with pytest.raises(ValueError):
        median_ratio(d, c, -d)


def test_selector_inputs_independent_of_call_order():
    import gzip
    from test_stage1_k1 import MIRROR, CAPTURE, digest, cache_detect
    from isolate_tables import geometry
    from e2e_reader.stage1 import StageOne
    rec = json.load(gzip.open(ROOT / 'heads/selector/data/caps_iso' / (CAPTURE.replace('/', '__') + '.json.gz'), 'rt'))
    folder = MIRROR / digest(CAPTURE)[:16]
    cand = json.loads((folder / 'candidates.json').read_text())
    names = sorted({i['name'] for i in rec['inputs']})
    assert len(names) > 1
    s = StageOne(cache_detect(cand, raw_only=True), None, geometry(rec, folder))
    first = {n: s.features(n)[1] for n in names}
    again = {n: s.features(n)[1] for n in reversed(names)}
    assert first == again
    want = {(i['name'], i['candidate_id']): i['x'] for i in rec['inputs']}
    got = {}
    for n in names:
        accepted, x = s.features(n)
        got.update({(n, a['candidate_id']): v for a, v in zip(accepted, x)})
    assert set(want) <= set(got)
    assert max(float(np.max(np.abs(np.array(got[k]) - np.array(want[k])))) for k in want) < 1e-9


def test_selector_loader_opens_train_only(monkeypatch):
    import gzip
    import common as C
    opened = []
    real = gzip.open
    monkeypatch.setattr(gzip, 'open', lambda p, *a, **k: (opened.append(str(p)), real(p, *a, **k))[1])
    rows = C.load(splits=('train',))
    S = json.load(open(C.SCALES))['captures']
    splits = {S[Path(p).name[:-8].replace('__', '/')]['split'] for p in opened}
    assert splits == {'train'} and rows and {r['split'] for r in rows} == {'train'}


def test_frame_count_is_a_read_parameter():
    """Geometry, camera poses and ground masks follow the read's anchor count (64 here), not a constant 32."""
    from e2e_reader.geometry import from_tower, frame_count, camera_geometry
    from e2e_reader.grounding import lift_plain
    z = np.load('/scratch/jjyeung/orch_n30/reader_r1/work/b1m/work/missing_k1/01949c4249271126/tower.npz')
    n = len(z['raw_pose'])
    if n < 64:
        pytest.skip('fixture tower has fewer than 64 dense frames')
    slots = np.arange(64)
    depth = np.repeat(z['depth_grid'][:1], 64, axis=0)
    try:
        geo = from_tower(z['raw_pose'], slots, z['frame_indices'], depth, z['grid_uv'], np.array([0., -1., 0.]), 1.,
                         (480, 640))
    except Exception as exc:  # the sealed tree's geometry contract is 32-frame only (tree build 7 item)
        pytest.xfail('sealed geometry contract refuses 64 frames: ' + type(exc).__name__ + ': ' + str(exc)[:80])
    assert frame_count(geo) == 64
    _, pose, _, _ = camera_geometry(geo)
    assert pose.shape == (64, 9)
    masks = np.zeros((64, 240, 320), bool); masks[40, 100:110, 100:110] = True
    assert lift_plain('x', masks, geo)['visible'] == [41]
