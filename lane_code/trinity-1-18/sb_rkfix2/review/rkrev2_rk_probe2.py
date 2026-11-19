"""Behaviour probes on the extracted fixed kit (./kit); writes only under ./kit/tmp and ./out.

Reuses the kit's own stub fixture (tests/test_protocol.py) for torch, the sealed backend and the
paths, but drives gpu_run.run through --stage s1c/all, which no kit test launches.
"""
import contextlib, io, json, os, sys, tempfile, time, types
from pathlib import Path
from unittest.mock import patch
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H / 'kit/scripts')); sys.path.insert(0, str(H / 'kit/tests'))
import numpy as np
import common, gates, adapter, selection, gpu_run, price
import score_room_pricing as sc
import test_protocol as tp
from common import read, write, sha, digest
W = common.W; assert W == H / 'kit', W
out = {}


def err(f):
    try:
        return 'returned ' + repr(f())[:90]
    except BaseException as e:
        return type(e).__name__ + ': ' + str(e).replace(str(W), 'W')[:120]


# ---------- A. resume() states ----------
tmp = Path(tempfile.mkdtemp(dir=W / 'tmp'))
b = dict(model='da3', frames=[1, 2], item_slots=[0, 1], settings={'seed': 0}, arm='da3_f32')
d = tmp / 'done'; d.mkdir(); (d / 'pred.npz').write_bytes(b'x')
write(d / 'DONE.json', dict(binding=b, pred_sha256=sha(d / 'pred.npz'), run_id='run1', host='h1', card_uuid='GPU-a'), {'f': 'x'})
out['A1_done_receipt_under_new_run_card_host'] = err(lambda: common.resume(d, b))
out['A1_legacy_binding_with_host_card_run_changed'] = err(lambda: common.resume(d, dict(b, run_id='run2', host='h2', card_uuid='GPU-b')))
d2 = tmp / 'started'; write(d2 / 'STARTED.json', dict(binding=b, run_id='run1'), {'f': 'x'})
closed = dict(state='MANUALLY_CLOSED', authorized_by='orch', accounted_run_ids=['run1'], charged_seconds=100)
out['A2_started_only_without_closure'] = err(lambda: common.resume(d2, b))
out['A2_started_only_closure_names_run'] = err(lambda: common.resume(d2, b, closed))
out['A2_started_only_closure_names_other_run'] = err(lambda: common.resume(d2, b, dict(closed, accounted_run_ids=['x'])))
d3 = tmp / 'killed_in_savez'; write(d3 / 'STARTED.json', dict(binding=b, run_id='run1'), {'f': 'x'}); (d3 / 'pred.npz').write_bytes(b'PK\x03\x04trunc')
out['A3_started_plus_partial_npz_with_closure'] = err(lambda: common.resume(d3, b, closed))

# ---------- C. SELECTION.json gate with the real training set and real code digest ----------
code = gates.run_code_hashes(); rows, caps, ins = selection.training_set()
out['C0_training_rows'] = dict(rows=len(rows), captures=len({r['capture'] for r in rows}),
                               all_k1_train=all(caps[r['capture']]['k1_split'] == 'train' for r in rows),
                               anchors_32=all(len(caps[r['capture']]['anchor_indices']) == 32 for r in rows),
                               dense_64=all(len(caps[r['capture']]['dense_frames']) == 64 for r in rows))
froot = Path(tempfile.mkdtemp(dir=W / 'tmp'))
out['C1_missing_selection'] = err(lambda: selection.load_selection(froot, code))
forged = dict(status='COMPLETE', scope='K1 train only', rule=selection.RULE, pricing_rule='R0', arm='da3_u94',
              dense64_minus_f32=[3.0, 0.5, 6.0], rows=[dict(row_id=r['row_id'], split='train') for r in rows],
              code_sha256=digest(code))
write(froot / 'SELECTION.json', forged, {str(H / 'rk_probe2.py'): sha(H / 'rk_probe2.py')})
out['C2_forged_selection_without_any_S1c_prediction'] = err(lambda: selection.load_selection(froot, code)['arm'])
moved = {k.replace(str(W), '/elsewhere/kit'): v for k, v in code.items()}
out['C3_relocated_kit_code_identity'] = err(lambda: selection.load_selection(froot, moved))


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
            patch.object(selection, 'K1_PRED', t.root / 'dense'), patch.object(adapter, 'pipeline', pipeline), \
            patch.object(adapter, 'input_code', lambda: t.code), patch.object(t.back.Backend, 'predict', predict), \
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


def launch(t, a, host='host-1'):
    with patch.object(gpu_run.socket, 'gethostname', lambda: host), patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': 'GPU-' + t.uuid}):
        gpu_run.run(a)


def close_cost(t, run):
    c = read(t.out / 'COST.json'); c.update(state='MANUALLY_CLOSED', authorized_by='probe orchestrator', accounted_run_ids=[run], charged_seconds=60)
    write(t.out / 'COST.json', c, t.code)


# D1/D2: one --stage s1c run, then R0-dev under a fresh GO written to the same configs/GO.json path (OPERATOR.md).
t = build()
with fixture(t):
    G = t.root / 'configs/GO.json'
    out['D1_s1c_run'] = err(lambda: launch(t, note(t, 'run-1', G, 's1c')))
    preds = [o for o in t.order if o[0] == 'predict']
    sel = read(t.out / 'SELECTION.json')
    out['D1_s1c_facts'] = dict(predict_calls=len(preds), frames_per_call=sorted({o[1] for o in preds}),
                               registration_before_first_predict=preds[0][2], selection_rows=len(sel['rows']), arm=sel['arm'],
                               interval=[round(x, 3) for x in sel['dense64_minus_f32']], priced=sum(o[0] == 'price' for o in t.order),
                               card_verified=read(t.out / 'RUN_RECEIPT.json')['card_verified'],
                               selection_binds_go_file=str(G) in sel['input_sha256'])
    out['D2_r0dev_fresh_GO_same_path'] = err(lambda: launch(t, note(t, 'run-2', G, 'r0dev')))
    out['D2_then_fresh_GO_new_path'] = err(lambda: launch(t, note(t, 'run-3', t.root / 'configs/GO_run-3.json', 'r0dev')))
# D2b/D3/D4: same, but each GO note gets its own file.
t = build()
with fixture(t):
    out['D2b_s1c_run'] = err(lambda: launch(t, note(t, 'run-1', t.root / 'configs/GO_run-1.json', 's1c')))
    out['D2b_r0dev_fresh_GO_new_path'] = err(lambda: launch(t, note(t, 'run-2', t.root / 'configs/GO_run-2.json', 'r0dev', 'host-2'), 'host-2'))
    out['D2b_r0dev_calls'] = len(t.calls) - 110
    t.order.clear()
    out['D3_price_first_look'] = err(price.run)
    print(json.dumps(out, indent=1), file=sys.stderr, flush=True)
    table = read(t.out / 'PRICING_TABLE.json')
    out['D3_table'] = dict(r0dev_arms=list(table['sets']['R0-dev']['arms']), dev_s1_arms=list(table['sets']['dev-S1']['arms']),
                           verdict=table['decision']['verdict'], bar=table['decision']['bar'],
                           r0dev_priced=sum(o[0] == 'price' for o in t.order),
                           registration_fields=sorted(k for k in read(t.out / 'DECISION_REGISTRATION.json') if k != 'input_sha256'))
    out['D4_latch_price_again'] = err(price.run)
    out['D4_latch_gpu_run_r0dev_again'] = err(lambda: launch(t, note(t, 'run-4', t.root / 'configs/GO_run-4.json', 'r0dev')))
    out['D4_latch_gpu_run_all_again'] = err(lambda: launch(t, note(t, 'run-5', t.root / 'configs/GO_run-5.json', 'all')))
    with patch.object(sys, 'argv', ['x', '--direct', str(W / 'evidence/direct_m200_room134.json'), '--pred', str(t.out / 'ROOM_PRED.jsonl')]):
        out['D4_latch_scorer_cli_pred'] = err(sc.main)
    with patch.object(sys, 'argv', ['x', '--direct', str(W / 'evidence/direct_m200_room134.json')]):
        out['D4_latch_scorer_cli_no_selftest'] = err(sc.main)
    out['D4_select_again'] = err(lambda: selection.select(t.out))

# D5: --stage all interrupted inside S1c, manual COST closure, resume under a fresh GO.
for label, same in [('same_path', True), ('new_path', False)]:
    t = build()
    with fixture(t, fail_at=5):
        G = t.root / 'configs/GO.json'
        out[f'D5_{label}_run1'] = err(lambda: launch(t, note(t, 'run-1', G, 'all')))
    with fixture(t):
        close_cost(t, 'run-1')
        out[f'D5_{label}_run2'] = err(lambda: launch(t, note(t, 'run-2', G if same else t.root / 'configs/GO_run-2.json', 'all', 'host-2'), 'host-2'))
        cost = read(t.out / 'COST.json')
        out[f'D5_{label}_after'] = dict(selection=(t.out / 'SELECTION.json').is_file(), predict_calls=len(t.calls),
                                        cost_keeps_closure=('accounted_run_ids' in cost or 'authorized_by' in cost), cost_state=cost['state'],
                                        interrupted_STARTED_run_id=read(t.out / 'pred/k1_f32/4/STARTED.json')['run_id'])

# D6: price.py invoked before R0-dev captures exist.
t = build()
with fixture(t):
    t.selected()
    out['D6_price_before_captures'] = err(price.run)
    out['D6_registration_consumed'] = (t.out / 'DECISION_REGISTRATION.json').is_file()
    out['D6_price_after_captures'] = err(lambda: (launch(t, note(t, 'run-1', t.root / 'configs/GO_run-1.json', 'r0dev')), price.run()))

# E. Second GO freshness check: authorize() re-runs preauthorize() after prerequisite hashing and CUDA init.
s = dict(unix_time=time.time() - 890, gpu_uuid='GPU-x', process_count=0, input_sha256={str(H / 'rk_probe2.py'): sha(H / 'rk_probe2.py')})
n = dict(decision='GO', host='h', run_id='r', gpu_uuid='GPU-x', manifest_sha256='m', code_sha256='c', settings_sha256=digest(gates.SETTINGS),
         max_gpu_seconds=5400, allocation_samples=[s, dict(s, unix_time=time.time() - 590)])
out['E_preauthorize_at_590s'] = err(lambda: gates.preauthorize(n, 'r', 'm', 'c', 'GPU-x', 'h'))
for x in n['allocation_samples']:
    x['unix_time'] -= 15
out['E_authorize_15s_later'] = err(lambda: gates.authorize(n, 'r', 'm', 'c', dict(uuid='GPU-x', total_memory=51_527_024_640), 1, 'GPU-x', 'h'))

print(json.dumps(out, indent=1))
json.dump(out, open(H / 'out/RK_PROBE2.json', 'w'), indent=1)
