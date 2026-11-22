"""relift_j1 on the real dump with toy detector outputs; equality assertions only, no cell value is printed.
  1. toy store = the bound GT instance (top proposal and box mask equal GT) -> h1 == e, h0 == e, k == e on all 117 items (cells
     and gaps), precision/recall 1 and no mask on a GT-empty anchor; statistics carry every registered field.
  2. toy store = the served masks (the selected track's mask is the only proposal) -> h1 == a on all 117 items.
  3. toy store = the dump's own proposal pool -> the pool gate and both pick gates pass on every operand-frame.
  4. refusal: the GT store fails parity; a failed pick gate drops only its own arm; compute without the text arms has no h1 or h0 anywhere and k still equals e; the full
     main() on toy detector files (GT layout) writes the k-only status; a detector directory missing a capture is refused.
  5. needed-items records exist exactly for undecided arms, and supply lists relift's exclusions.
compute() asserts that its a and e equal a fresh in-process relift.run and that relift.stats over the fresh rows equals it.
p1cpu interpreter. Writes toy detector files under j1/work/toy_detect_<stamp> and toy outputs under j1/work/toy_out_<stamp> only; deletes nothing."""
import json, sys, time
from pathlib import Path
import numpy as np
KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT))
import j1_common as G
import select_j1 as S
import relift_j1 as RJ

t0 = time.monotonic()
R = G.load_relift(); R.dependencies()
refs = {r['item_id']: r for r in json.loads(G.ITEMS.read_text())['items']}
items, objects, _ = G.eligible(R, refs)
rows = R.read_records(R.BASE/'cap/t1.gz', refs)
prompts = G.read_json(G.PROMPTS_J1)
pc = {c['capture']: c for c in prompts['captures']}
gtp = {i['capture']: i['gt_path'] for i in items}
fresh = RJ.fresh_relift(R)
print('fresh relift run done (values not shown) %.0f s' % (time.monotonic()-t0), flush=True)


def inst_of(cap):
    with np.load(gtp[cap]) as z:
        return z['inst'].copy()


class Toy:
    """capture(cap) -> dict(text, k) built by text_fn(cap, prompt, instance_id, inst) and k = GT."""
    def __init__(self, text_fn, k_fn=None):
        self.text_fn, self.k_fn, self._c = text_fn, k_fn, {}

    def capture(self, cap):
        if cap not in self._c:
            self._c.clear(); inst = inst_of(cap)
            iid = {o['prompt']: o['instance_id'] for o in pc[cap]['operands']}
            self._c[cap] = dict(text={p: self.text_fn(cap, p, iid[p], inst) for p in pc[cap]['prompts']},
                                k={u['instance_id']: (self.k_fn or (lambda c, i, inst: inst == i))(cap, u['instance_id'], inst)
                                   for u in pc[cap]['k_units']})
        return self._c[cap]


def gt_text(cap, p, i, inst):
    t = inst == i
    return [[dict(score=.9, presence=1., mask480=RJ.upsample(t[f]))] if t[f].any() else [] for f in range(32)]


served = {}
for it in items:
    for o in rows[it['item_id']]['objects']:
        key = (it['capture'], o['name'].strip().lower())
        m = R.masks_array(o['selected_masks'])
        if key in served and not np.array_equal(served[key][0], m):
            served[key][1] = False
        served.setdefault(key, [m, True])
same_served = all(v[1] for v in served.values())


def served_text(cap, p, i, inst):
    m = served.get((cap, p), [np.zeros((32,)+G.GRID, bool)])[0]
    return [[dict(score=.9, presence=1., mask480=RJ.upsample(m[f]))] if m[f].any() else [] for f in range(32)]


pool = {}
for it in items:
    for o in rows[it['item_id']]['objects']:
        pool.setdefault((it['capture'], o['name'].strip().lower()), o)


def pool_text(cap, p, i, inst):
    o = pool.get((cap, p))
    if o is None:
        return [[] for _ in range(32)]
    fr = [[] for _ in range(32)]
    for q in o['proposals']:
        fr[int(q['frame'])-1].append(dict(score=float(q['score']), presence=float(q['presence']), mask480=R.unrle(q['mask'])))
    return fr


def equal(rr, x, y):
    return all(r[x] == r[y] and r['gaps'][x] == r['gaps'][y] for r in rr)


# 1. GT store
res = RJ.compute(R, fresh, Toy(gt_text), True)
assert len(res['rows']) == 117 and len({r['capture'] for r in res['rows']}) == 46
for k in RJ.ARMS:
    assert equal(res['rows'], k, 'e'), 'toy GT: %s differs from e' % k
for k in RJ.ARMS+('e',):
    for d, v in res['precision_recall'][k].items():
        assert v['precision'] == 1. and v['recall'] == 1. and v['pred_on_empty_gt'] == 0, (k, d)
st = {s['dataset']: s for s in res['statistics']}
assert set(st) == {'all', 'ARKit', 'ScanNet', 'ScanNet++'} and st['all']['n'] == 117 == sum(st[d]['n'] for d in G.DATASETS3)
assert all(set(s['versus_a']) == {'h1-a', 'h0-a', 'k-a', 'e-a'} and set(s['share_of_e_minus_a']) == set(RJ.ARMS) and s['rooms'] > 0
           for s in st.values())
assert set(st['all']['verdict']) == set(RJ.ARMS) and all(v in ('source', 'opens', 'closes', 'undecided') for v in st['all']['verdict'].values())
assert set(res['needed']) == {k for k, v in st['all']['verdict'].items() if v == 'undecided'}
assert len(res['records']) == 117*5 and {r['arm'] for r in res['records']} == set(RJ.CELLS)
assert all({'item_id', 'room', 'dataset', 'type', 'operands', 'lifted_distance_m', 'printed_answer', 'gt', 'score'} <= set(r) for r in res['records'])
print('PASS toy GT store: h1 == e, h0 == e, k == e on 117 items (cells and gaps); P/R 1; no mask on GT-empty anchors; '
      'statistics, verdicts, needed-items keys and 585 per-item rows present', flush=True)

# 2. served store
assert same_served, 'two items of one capture serve different masks for one name'
res2 = RJ.compute(R, fresh, Toy(served_text), True)
assert equal(res2['rows'], 'h1', 'a'), 'toy served: h1 differs from a'
assert equal(res2['rows'], 'k', 'e')
print('PASS toy served store: h1 == a on 117 items (cells and gaps)', flush=True)

# 3. dump pool store -> parity passes on every operand-frame
par = RJ.parity(R, rows, items, objects, Toy(pool_text))
assert all(par['picks'][k]['passed'] and par['picks'][k]['agree'] == par['operand_frames'] for k in ('h1', 'h0'))
assert par['passed'] and par['matched'] == par['operand_frames'] == par['strict_matched'] and par['operand_frames'] == 32*(len(objects)-par['operands_without_ground_call'])
print('PASS parity matcher on the dump pool against itself: every operand-frame matches (%d operand-frames, %d operands without '
      'a ground call)' % (par['operand_frames'], par['operands_without_ground_call']), flush=True)

# 4. refusal
par_gt = RJ.parity(R, rows, items, objects, Toy(gt_text))
assert not par_gt['passed']
read, status = RJ.gates(par_gt)
assert read == [] and 'h1 not read: pool parity' in status and 'h0 not read: pool parity' in status and status.endswith('k is read)')
fake = dict(passed=True, matched=10, operand_frames=10, picks=dict(h1=dict(agree=10, operand_frames=10, passed=True),
                                                                   h0=dict(agree=9, operand_frames=10, passed=False)))
read, status = RJ.gates(fake)
assert read == ['h1'] and 'h0 not read: h0 picks agree on 9/10' in status and 'h1 not read' not in status
res5 = RJ.compute(R, fresh, Toy(gt_text), {'h1'})
assert all('h0' not in r and 'h0' not in r['gaps'] and 'h1' in r for r in res5['rows']) and res5['arms_read'] == ['h1', 'k']
assert equal(res5['rows'], 'h1', 'e') and {r['arm'] for r in res5['records']} == {'a', 'e', 'h1', 'k'}
print('PASS pick gate: a failed h0 pick gate drops only h0 (rows, statistics, records), h1 and k still read; statuses name the cause', flush=True)
res4 = RJ.compute(R, fresh, Toy(gt_text), False)
assert all('h1' not in r and 'h0' not in r and 'h1' not in r['gaps'] for r in res4['rows'])
assert all(set(s['cells']) == {'a', 'e', 'k'} and set(s['versus_a']) == {'k-a', 'e-a'} for s in res4['statistics'])
assert equal(res4['rows'], 'k', 'e') and res4['arms_read'] == ['k'] and {r['arm'] for r in res4['records']} == {'a', 'e', 'k'}
print('PASS refusal: the GT store fails parity; without the text arms no row, statistic or record carries h1 or h0; k == e', flush=True)

stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
toy = G.ROOT/('work/toy_detect_'+stamp)          # a fresh directory per run; nothing is deleted
spec = dict(schema='j1-detect-v1', toy=True, frames_j1_sha256=G.sha256_file(G.FRAMES_J1), prompts_j1_sha256=G.sha256_file(G.PROMPTS_J1),
            anchor_limit=32)
fr = {c['capture']: c for c in G.read_json(G.FRAMES_J1)['captures']}
for cap, c in pc.items():
    inst = inst_of(cap); iid = {o['prompt']: o['instance_id'] for o in c['operands']}
    text = {p: [[dict(score=.9, presence=1., mask=G.pack(RJ.upsample(inst[f] == iid[p])))] if (inst[f] == iid[p]).any() else []
                for f in range(32)] for p in c['prompts']}
    k = {str(u['instance_id']): dict(instance_id=u['instance_id'], gt_sha256=u['gt_sha256'],
                                     anchors=[dict(slot=b['slot'], score=.9, mask=G.pack(RJ.upsample(inst[b['slot']-1] == u['instance_id'])))
                                              for b in u['boxes']]) for u in c['k_units']}
    G.write_json(toy/(G.stub(cap)+'.json.gz'), dict(contract=spec, capture=cap, anchors=32, text=text, k=k,
                                                    frames=[dict(slot=f['slot'], sha256=f['sha256']) for f in fr[cap]['frames']]), gz=True)
G.write_json(toy/'INDEX.json', dict(done=len(pc), captures=len(pc), failed=[], stopped=None, contract=spec))
out = G.ROOT/('work/toy_out_'+stamp)
import contextlib, io
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    assert RJ.main(['--detect', str(toy), '--out', str(out/'RELIFT_J1.json'), '--items-out', str(out/'ITEMS_J1.jsonl')]) == 0
got = G.read_json(out/'RELIFT_J1.json')
assert buf.getvalue().strip() == got['status'] and 'h1 not read' in got['status'] and 'h0 not read' in got['status'] and got['status'].endswith('k is read)') and not got['parity']['passed']
assert got['arms_read'] == ['k'] and equal(got['rows'], 'k', 'e') and (out/'RELIFT_J1.md').is_file()
assert sum(1 for _ in (out/'ITEMS_J1.jsonl').open()) == 117*3
assert got['supply']['excluded_items'] and {x['item_id'] for x in got['supply']['excluded_items']} == {e['item_id'] for e in fresh['exclusions']}
assert len(refs) == 117 + len(got['supply']['excluded_items'])
print('PASS main() on toy detector files: parity fails, status says h1 and h0 not read, k == e, RELIFT_J1.md and 351 per-item rows written; '
      'supply lists relift\'s %d excluded manifest items' % len(got['supply']['excluded_items']), flush=True)
victim = sorted(pc)[0]
(toy/(G.stub(victim)+'.json.gz')).rename(toy/'moved_aside.gz')
try:
    RJ.DetectStore(toy, prompts); raise AssertionError('missing capture accepted')
except FileNotFoundError:
    pass
(toy/'moved_aside.gz').rename(toy/(G.stub(victim)+'.json.gz'))
ix = G.read_json(toy/'INDEX.json'); ix['failed'] = [dict(capture=victim, status='SHA_MISMATCH slot 1')]; G.write_json(toy/'INDEX.json', ix)
try:
    RJ.DetectStore(toy, prompts); raise AssertionError('failed capture accepted')
except ValueError:
    pass
print('PASS detector store refuses a missing capture file and an INDEX with a failed capture', flush=True)
print('{"status": "PASS", "seconds": %.0f}' % (time.monotonic()-t0))
