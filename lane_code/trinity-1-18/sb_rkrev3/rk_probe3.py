"""Behaviour probes on the extracted sb_rkfix2 kit (./kit); writes only under ./kit/tmp and ./out.

Port of rk_probe2.py to the edited kit: kernel.pipeline replaces adapter.pipeline, and every GO note gets the
per-run path the runner now requires, except where a probe tests the refusal of other paths.
"""
import contextlib, io, json, os, sys, tempfile, time, types
from pathlib import Path
from unittest.mock import patch
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H / 'kit/scripts')); sys.path.insert(0, str(H / 'kit/tests'))
import numpy as np
import common, gates, adapter, selection, gpu_run, price, kernel
import score_room_pricing as sc
import test_protocol as tp
from common import read, write, sha, digest
W = common.W; assert W == H / 'kit', W
out = {}


def err(f):
    try:
        return 'returned ' + repr(f())[:90]
    except BaseException as e:
        return type(e).__name__ + ': ' + str(e).replace(str(W), 'W')[:130]


# ---------- A. resume() states ----------
tmp = Path(tempfile.mkdtemp(dir=W / 'tmp'))
b = dict(model='da3', frames=[1, 2], item_slots=[0, 1], settings={'seed': 0}, arm='da3_f32')
d = tmp / 'done'; d.mkdir(); (d / 'pred.npz').write_bytes(b'x')
write(d / 'DONE.json', dict(binding=b, pred_sha256=sha(d / 'pred.npz'), run_id='run1', host='h1', card_uuid='GPU-a'), {'f': 'x'})
out['A1_done_receipt_new_run'] = err(lambda: common.resume(d, b))
closed = dict(state='MANUALLY_CLOSED', authorized_by='orch', accounted_run_ids=['run1'], charged_seconds=100)
d3 = tmp / 'killed_in_savez'; write(d3 / 'STARTED.json', dict(binding=b, run_id='run1'), {'f': 'x'}); (d3 / 'pred.npz.part').write_bytes(b'PK\x03\x04trunc')
out['A3_started_plus_part_with_closure'] = err(lambda: common.resume(d3, b, closed))
d4 = tmp / 'killed_after_replace'; write(d4 / 'STARTED.json', dict(binding=b, run_id='run1'), {'f': 'x'}); (d4 / 'pred.npz').write_bytes(b'PK')
out['A4_started_plus_npz_no_done_with_closure'] = err(lambda: common.resume(d4, b, closed))

# ---------- C. SELECTION.json gate with the real training set and real code digest ----------
code = gates.run_code_hashes(); rows, caps, ins = selection.training_set()
froot = Path(tempfile.mkdtemp(dir=W / 'tmp'))
forged = dict(status='COMPLETE', scope='K1 train only', rule=selection.RULE, pricing_rule='R0', arm='da3_u94',
              dense64_minus_f32=[3.0, 0.5, 6.0], rows=[dict(row_id=r['row_id'], capture=r['capture'], room=r['room'], gt=r['gt'], split='train',
                                                         f32=dict(area_m2=1.0), f64=dict(area_m2=r['gt']), delta=0.0) for r in rows],
              code_sha256=digest(code))
write(froot / 'SELECTION.json', forged, {str(H / 'rk_probe3.py'): sha(H / 'rk_probe3.py')})
out['C2_forged_selection_without_S1c_predictions'] = err(lambda: selection.load_selection(froot, code)['arm'])


# ---------- D. gpu_run through S1c and R0-dev with the kit's stub fixture ----------
class Probe(tp.ProtocolTests):
    def runTest(self):
        pass


def build():
    t = Probe(); t.setUp()
    frames = []
    for j in range(64):
        p = t.root / 'k1frames' / f'{j:06d}.png'; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b'k1' + bytes([j])); frames.append(p)
    anchors = list(range(0, 64, 2)); t.k1caps = {}; t.dense = {}
    (t.root / 'evidence/k1_rule_variants.py').write_bytes((W / 'evidence/k1_rule_variants.py').read_bytes())
    for i, r in enumerate(t.train):
        r.update(gt=20.0, R0=20.0 if i % 3 else 15.0)
        c = dict(canonical=r['capture'], k1_split='train', anchor_indices=anchors,
                 dense_frames=[dict(index=j, path=str(frames[j]), sha256=sha(frames[j])) for j in range(64)])
        t.k1caps[r['capture']] = c
        p = t.root / 'dense' / digest(c)[:16] / 'pred.npz'; p.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(p, frame_indices=np.arange(64), item_slots=np.asarray(anchors), depth_grid=np.ones((64, 51, 51), np.float32),
                            intrinsics=np.tile(np.eye(3), (64, 1, 1)), c2w=np.tile(np.eye(4), (64, 1, 1)), source_hw=np.array([504, 504]))
        write(p.parent / 'DONE.json', dict(pred_sha256=sha(p)), t.code); t.dense[digest(c)[:16]] = r
    t.order = []
    return t


@contextlib.contextmanager
def fixture(t, fail_at=None):
    expected = {r['id']: r for r in t.dev}; byname = {r['capture']: r for r in t.train}
    def pipeline(p, dst, rule):
        p = Path(p); t.order.append(('price', str(p)))
        if 'k1_f32' in p.parts:
            r = byname[p.parent.name]; return dict(area_m2=16.0 if int(r['row_id']) % 2 else 20.0, refusal=None)
        if 'dense' in p.parts:
            return dict(area_m2=t.dense[p.parent.name]['R0'], refusal=None)
        assert (t.out / 'DECISION_REGISTRATION.json').is_file(), 'R0-dev priced before registration'
        item = t.items[int(p.parent.name)]; r = expected[item['id']]
        return dict(area_m2=r['direct'] / (10.7639104167 if r['unit'] == 'ft2' else 1), refusal=None)
    orig = t.back.Backend.predict
    def predict(backend, paths, resolution):
        t.order.append(('predict', len(paths), (t.out / 'S1C_REGISTRATION.json').is_file()))
        if fail_at is not None and len(t.calls) + 1 == fail_at:
            t.calls.append(paths); raise RuntimeError('probe interruption')
        return orig(backend, paths, resolution)
    with t.fixture(), patch.object(selection, 'training_set', lambda: (t.train, t.k1caps, dict(t.code))), \
            patch.object(selection, 'K1_PRED', t.root / 'dense'), patch.object(kernel, 'pipeline', pipeline), \
            patch.object(kernel, 'input_code', lambda: t.code), patch.object(t.back.Backend, 'predict', predict), \
            contextlib.redirect_stdout(io.StringIO()):
        yield


def note(t, run, path, stage, host='host-1'):
    prov, reader = t.root / 'provenance.json', t.root / 'reader.json'
    if not prov.exists():
        write(prov, dict(status='fixture'), t.code); write(reader, dict(status='fixture'), t.code)
    s = dict(unix_time=time.time() - 301, gpu_uuid='GPU-' + t.uuid, process_count=0, input_sha256=t.code)
    write(path, dict(decision='GO', host=host, run_id=run, gpu_uuid='GPU-' + t.uuid, manifest_sha256=sha(t.root / 'configs/R0DEV_ROOM_MANIFEST.json'),
                     code_sha256=digest(t.code), settings_sha256=digest(gates.SETTINGS), max_gpu_seconds=5400,
                     allocation_samples=[s, dict(s, unix_time=time.time() - 1)], provenance_sha256=sha(prov), reader_receipt_sha256=sha(reader)), t.code)
    return types.SimpleNamespace(stage=stage, run_id=run, go_file=str(path), provenance=str(prov), reader_receipt=str(reader))


def go(t, run):
    return t.root / 'configs' / f'GO_{run}.json'


def launch(t, a, host='host-1'):
    with patch.object(gpu_run.socket, 'gethostname', lambda: host), patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': 'GPU-' + t.uuid}):
        gpu_run.run(a)


def close_cost(t, run):
    c = read(t.out / 'COST.json'); c.update(state='MANUALLY_CLOSED', authorized_by='probe orchestrator', accounted_run_ids=[run], charged_seconds=60)
    write(t.out / 'COST.json', c, t.code)


# D1: shared and aliased GO paths are refused before anything runs.
t = build()
with fixture(t):
    out['D1_shared_GO_json'] = err(lambda: launch(t, note(t, 'run-1', t.root / 'configs/GO.json', 's1c')))
    note(t, 'run-1', go(t, 'run-1'), 's1c'); os.symlink(go(t, 'run-1'), go(t, 'run-2'))
    a = types.SimpleNamespace(stage='s1c', run_id='run-2', go_file=str(go(t, 'run-2')), provenance=str(t.root / 'provenance.json'), reader_receipt=str(t.root / 'reader.json'))
    out['D1_symlinked_GO_of_other_run'] = err(lambda: launch(t, a))
    out['D1_nothing_written'] = sorted(p.name for p in t.out.iterdir())
# D2: --stage s1c under run-1, then r0dev under run-2 on another host, then the one look and every bypass.
t = build()
with fixture(t):
    out['D2_s1c_run1'] = err(lambda: launch(t, note(t, 'run-1', go(t, 'run-1'), 's1c')))
    preds = [o for o in t.order if o[0] == 'predict']
    sel = read(t.out / 'SELECTION.json')
    out['D2_s1c_facts'] = dict(predict_calls=len(preds), frames_per_call=sorted({o[1] for o in preds}),
                               registration_before_first_predict=preds[0][2], selection_rows=len(sel['rows']), arm=sel['arm'],
                               interval=[round(x, 3) for x in sel['dense64_minus_f32']], priced=sum(o[0] == 'price' for o in t.order),
                               selection_binds_go_run1=str(go(t, 'run-1')) in sel['input_sha256'])
    go1 = sha(go(t, 'run-1'))
    out['D2_r0dev_run2_host2'] = err(lambda: launch(t, note(t, 'run-2', go(t, 'run-2'), 'r0dev', 'host-2'), 'host-2'))
    out['D2_r0dev_calls'] = len(t.calls) - 110
    out['D2_go_run1_unchanged'] = sha(go(t, 'run-1')) == go1
    t.order.clear()
    out['D3_price_first_look'] = err(price.run)
    table = read(t.out / 'PRICING_TABLE.json')
    out['D3_table'] = dict(r0dev_arms=list(table['sets']['R0-dev']['arms']), dev_s1_arms=list(table['sets']['dev-S1']['arms']),
                           verdict=table['decision']['verdict'], bar=table['decision']['bar'],
                           r0dev_priced=sum(o[0] == 'price' for o in t.order),
                           registration_fields=sorted(k for k in read(t.out / 'DECISION_REGISTRATION.json') if k != 'input_sha256'))
    out['D4_latch_price_again'] = err(price.run)
    out['D4_latch_gpu_run_r0dev_again'] = err(lambda: launch(t, note(t, 'run-4', go(t, 'run-4'), 'r0dev')))
    out['D4_latch_gpu_run_all_again'] = err(lambda: launch(t, note(t, 'run-5', go(t, 'run-5'), 'all')))
    with patch.object(sys, 'argv', ['x', '--direct', str(W / 'evidence/direct_m200_room134.json'), '--pred', str(t.out / 'ROOM_PRED.jsonl')]):
        out['D4_latch_scorer_cli_pred'] = err(sc.main)
    with patch.object(sys, 'argv', ['x', '--direct', str(W / 'evidence/direct_m200_room134.json')]):
        out['D4_latch_scorer_cli_no_selftest'] = err(sc.main)
    out['D4_select_again'] = err(lambda: selection.select(t.out))
# D5: --stage all interrupted inside S1c, manual COST closure, resume under a fresh per-run GO on host-2.
t = build()
with fixture(t, fail_at=5):
    out['D5_run1'] = err(lambda: launch(t, note(t, 'run-1', go(t, 'run-1'), 'all')))
started = read(t.out / 'pred/k1_f32/4/STARTED.json')
with fixture(t):
    out['D5_run2_before_closure'] = err(lambda: launch(t, note(t, 'run-2', go(t, 'run-2'), 'all', 'host-2'), 'host-2'))
    close_cost(t, 'run-1')
    out['D5_run3_after_closure'] = err(lambda: launch(t, note(t, 'run-3', go(t, 'run-3'), 'all', 'host-2'), 'host-2'))
    cost = read(t.out / 'COST.json')
    out['D5_after'] = dict(selection=(t.out / 'SELECTION.json').is_file(), predict_calls=len(t.calls), cost_state=cost['state'],
                           history_keeps_closure=any(h.get('authorized_by') == 'probe orchestrator' and h.get('accounted_run_ids') == ['run-1'] for h in cost['history']),
                           interrupted_previous_started_kept=read(t.out / 'pred/k1_f32/4/STARTED.json')['previous_started'] == started,
                           done_run_ids=sorted({read(p)['run_id'] for p in (t.out / 'pred/k1_f32').glob('*/DONE.json')}))
# D6: price.py invoked before R0-dev captures exist.
t = build()
with fixture(t):
    t.selected()
    out['D6_price_before_captures'] = err(price.run)
    out['D6_registration_consumed'] = (t.out / 'DECISION_REGISTRATION.json').is_file()

print(json.dumps(out, indent=1))
json.dump(out, open(H / 'out/RK_PROBE3.json', 'w'), indent=1)
