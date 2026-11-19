"""Kit unit tests (p1cpu interpreter, CPU only):  bash kit/run_cpu.sh p1cpu -m pytest -q ../tests"""
import json, os, subprocess, sys, textwrap
from pathlib import Path
import numpy as np
import pytest

KIT = Path(__file__).resolve().parents[1]/'kit'
sys.path.insert(0, str(KIT))
import mc_common as C  # noqa: E402
import mc_track_io as IO  # noqa: E402
import mc_track_pass as TP  # noqa: E402


def kit_decode(rle):
    """The stage-1 cache's decoding (sb_mask_phrase/kit.py decode, before its resize)."""
    h, w = rle['size']
    counts = np.asarray(rle['counts'], np.int64)
    return np.repeat(np.arange(len(counts)) % 2 == 1, counts).reshape((h, w), order='F')


@pytest.mark.parametrize('fill', ['random', 'empty', 'full', 'corner'])
def test_rle_round_trip_matches_cache_convention(fill):
    rng = np.random.default_rng(0)
    m = {'random': rng.random((48, 64)) > .7, 'empty': np.zeros((48, 64), bool), 'full': np.ones((48, 64), bool),
         'corner': np.pad(np.ones((1, 1), bool), ((0, 47), (0, 63)))}[fill]
    rle = C.rle_encode(m)
    assert sum(rle['counts']) == m.size
    assert np.array_equal(C.rle_decode(rle), m)
    assert np.array_equal(kit_decode(rle), m)


def test_pack_round_trip():
    m = np.random.default_rng(1).random((480, 640)) > .5
    assert np.array_equal(C.unpack(m.shape, C.pack(m)), m)


def test_iou_empty_union_is_none():
    z = np.zeros((4, 4), bool)
    assert C.iou(z, z) is None
    a = z.copy(); a[0, 0] = True
    assert C.iou(a, a) == 1.0 and C.iou(a, z) == 0.0


def test_projection_drops_trailing_sets_in_order():
    sets = ['S_A0/D64', 'S_GT/D64', 'S_A0/A32', 'S_GT/A32']
    means = {'S_A0/D64': 10., 'S_GT/D64': 10., 'S_A0/A32': 5., 'S_GT/A32': 5.}
    assert TP.plan_drop(0., 100, 2., means, sets, 1e9) == []
    assert TP.project(100., 10, 2., means, sets) == 100. + 10*32.
    assert TP.plan_drop(0., 100, 2., means, sets, 100*(2+20)+1) == ['S_A0/A32', 'S_GT/A32']
    assert TP.plan_drop(0., 100, 2., means, sets, 100*(2+10)) == ['S_GT/D64', 'S_A0/A32', 'S_GT/A32']
    assert TP.plan_drop(0., 100, 2., means, sets, 100*(2+10)-1) is None


def test_window_stays_inside_dense_frames():
    assert TP.window(64, 63, 8) == list(range(56, 64))
    assert TP.window(64, 0, 8) == list(range(8))
    assert TP.window(64, 30, 8) == list(range(26, 34))


def test_ledger_round_trip(tmp_path):
    led = TP.read_ledger(tmp_path)
    assert led['spent_seconds'] == 0 and led['stopped'] is None
    led['spent_seconds'] = 12.5; led['dropped'] = ['S_GT/A32']
    TP.save_ledger(tmp_path, led)
    assert TP.read_ledger(tmp_path) == led


def test_crash_is_recorded_as_a_stop(tmp_path):
    import time
    led = TP.read_ledger(tmp_path)
    TP.STATE.update(ledger=led, out=tmp_path, t_start=time.monotonic(), spent0=100., events=tmp_path/'EVENTS.jsonl')
    TP.record_failure(RuntimeError('boom'))
    again = TP.read_ledger(tmp_path)
    assert again['stopped'].startswith('FAILED: RuntimeError: boom') and again['spent_seconds'] >= 100.
    assert json.loads((tmp_path/'EVENTS.jsonl').read_text().splitlines()[-1])['event'] == 'FAILED'


def test_object_record_keeps_seed_and_uses_object_score():
    shape = (6, 8)
    seed = np.zeros(shape, bool); seed[1:3, 1:3] = True
    other = np.zeros(shape, bool); other[2:5, 2:6] = True
    result = {0: (other, 2.0), 1: (other, 5.0), 2: (other, -0.1), 3: (np.zeros(shape, bool), 3.0)}
    positions = [0, 1, 2, 3] + [None]*28
    rec = IO.object_record(0, 'tv', 7, 2, [10, 11, 12, 13], positions, result, seed)
    a = rec['anchors']
    assert a[1]['seed'] and np.array_equal(C.rle_decode(a[1]['rle']), seed)
    assert a[0]['carried'] and not a[2]['carried'] and not a[3]['carried']
    assert a[4]['tracked'] is False and a[4]['carried'] is False
    masks = IO.anchor_masks(json.loads(json.dumps(rec)))
    assert masks.shape == (32,)+shape and np.array_equal(masks[1], seed) and np.array_equal(masks[0], other) and not masks[2].any()


def test_gt_seed_picks_largest_valid_share_lowest_on_ties():
    import mc_seeds as S
    inst = np.zeros((32, 20, 15), np.int32)
    inst[3, :4, :4] = 5; inst[9, :4, :4] = 5; inst[12, :10, :10] = 5
    valid = np.ones(32, bool); valid[12] = False
    rec, seed = S.gt_seed(dict(inst=inst, valid=valid), 5)
    assert rec['slot'] == 4 and seed.shape == C.CANVAS
    rec, seed = S.gt_seed(dict(inst=inst, valid=valid), 6)
    assert rec['status'] == 'NOT_VISIBLE' and seed is None


def test_maskfail_declarations_load_without_module_body():
    import mc_measure as MS
    mf = MS.maskfail()
    a = np.zeros((4, 4), bool); a[:2] = True
    b = np.zeros((4, 4), bool); b[1:3] = True
    value, inter, area = mf.metrics(a, b)
    assert abs(value - 1/3) < 1e-12 and inter == 4 and area == 8
    assert 'analyze' not in sys.modules


def test_cpu_redirect_maps_cuda_to_cpu():
    import torch
    import mc_tracker as MT
    with MT.CpuRedirect():
        x = torch.zeros(3, device='cuda')
        y = torch.arange(4, device='cuda:0').cuda().to('cuda')
        z = torch.ones(2).pin_memory()
        w = torch.empty(2, pin_memory=True)
    assert x.device.type == y.device.type == z.device.type == w.device.type == 'cpu'


FAKE = textwrap.dedent('''\
    #!/bin/bash
    n=$(cat "{state}" 2>/dev/null || echo 0); echo $((n+1)) > "{state}"
    if [ "$n" = 0 ]; then printf '%s\\n' {r1}; else printf '%s\\n' {r2}; fi
    ''')


def launch(tmp_path, host, r1, r2, budget=None, extra=None):
    out = tmp_path/'track'; out.mkdir(exist_ok=True)
    if budget is not None:
        (out/'BUDGET.json').write_text(json.dumps(budget, indent=1))
    smi = tmp_path/'nvidia-smi'
    smi.write_text(FAKE.format(state=tmp_path/'n', r1=' '.join(f"'{x}'" for x in r1), r2=' '.join(f"'{x}'" for x in r2)))
    smi.chmod(0o755)
    (tmp_path/'n').unlink(missing_ok=True)
    env = dict(os.environ, MC_DRY_LAUNCH='1', MC_NVIDIA_SMI=str(smi), MC_WAIT_SECONDS='0', MC_HOST=host,
               MC_TEST_OUT=str(out), MC_SKIP_PREFLIGHT='1', **(extra or {}))
    p = subprocess.run(['bash', str(KIT/'launch_gpu.sh')], env=env, capture_output=True, text=True)
    events = [json.loads(line) for line in (out/'EVENTS.jsonl').read_text().splitlines()] if (out/'EVENTS.jsonl').exists() else []
    return p.returncode, events


needs_manifest = pytest.mark.skipif(not (KIT.parent/'out/KIT_MANIFEST.sha256').exists(), reason='manifest is written at packaging')
GOOD = ['0, 49140, 8000', '1, 49140, 3', '2, 24564, 0']


@pytest.mark.parametrize('host,reason', [('trinity', 'head_node'), ('trinity-0-13', 'trinity-0-13_is_excluded'), ('babel-1', 'not_a_trinity_compute_node')])
def test_launcher_refuses_hosts(tmp_path, host, reason):
    code, events = launch(tmp_path, host, GOOD, GOOD)
    assert code == 1 and events[-1]['event'] == 'LAUNCH_REFUSED' and events[-1]['reason'] == reason


@needs_manifest
def test_launcher_picks_empty_large_card_in_both_readings(tmp_path):
    code, events = launch(tmp_path, 'trinity-1-18', GOOD, GOOD)
    assert code == 0 and events[-1]['event'] == 'LAUNCH' and events[-1]['gpu'] == '1'


@needs_manifest
def test_launcher_refuses_card_used_in_second_reading_or_small(tmp_path):
    code, events = launch(tmp_path, 'trinity-1-18', GOOD, ['0, 49140, 8000', '1, 49140, 1500', '2, 24564, 0'])
    assert code == 1 and events[-1]['reason'].startswith('no_card')
    code, events = launch(tmp_path, 'trinity-1-18', ['0, 24564, 0'], ['0, 24564, 0'])
    assert code == 1 and events[-1]['reason'].startswith('no_card')
    code, events = launch(tmp_path, 'trinity-1-18', ['0, 49140, 1024'], ['0, 49140, 1024'])
    assert code == 0 and events[-1]['gpu'] == '0'


@needs_manifest
def test_launcher_reports_a_recorded_stop_instead_of_rerunning(tmp_path):
    killed = dict(spent_seconds=3000., runs=[], dropped=[], stopped='KILLED by signal 15')
    code, events = launch(tmp_path, 'trinity-1-18', GOOD, GOOD, budget=killed)
    assert code == 1 and events[-1]['reason'] == 'ledger_records_stop_or_kill_report_it'
    code, events = launch(tmp_path, 'trinity-1-18', GOOD, GOOD, budget=killed, extra=dict(MC_RESUME_AFTER_STOP='1'))
    assert code == 0 and events[-1]['resume_after_stop'] == '1' and events[-1]['timeout_seconds'] == '4200'
    code, events = launch(tmp_path, 'trinity-1-18', GOOD, GOOD, budget=dict(spent_seconds=7000., runs=[], dropped=[], stopped=None))
    assert code == 1 and events[-1]['reason'].startswith('budget_spent')
    code, events = launch(tmp_path, 'trinity-1-18', GOOD, GOOD, budget=dict(spent_seconds=1200., runs=[], dropped=[], stopped=None))
    assert code == 0 and events[-1]['timeout_seconds'] == '6000'
