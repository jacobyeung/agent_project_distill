#!/usr/bin/env python3
"""Fixture test of gate.py: one complete synthetic gate set that must PASS, and one mutation per point that must
FAIL exactly that point. Schemas follow the writers (rv.py, cs.py, sv.py, r1_population.py, carrier_c1_run.py,
admit_test.py); ADMIT.json comes from the real stand-in run of admit_test (w24z14 standin_verified) with its five
preparation-dependent checks set as a prepared v.json would give them.
Usage: python3 -I test_gate.py ADMIT_STANDIN.json ADMIT_NEGATIVE.json OUTDIR"""
import copy, gzip, hashlib, json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
N_DB = '5e35c3ce600a867be194911642caccb23098035b4bf08909e519a170a1c243df'
STREAMS = ('pose', 'vqa', 'routing', 'pointing')
KINDS = {'camera_displacement': 12428, 'camera_movement_direction': 10883, 'camera_rotation': 8127, 'absolute_distance': 10945, 'units': 718}
ADMITTED = {'pose': 90000, 'vqa': 189000, 'routing': 43101, 'pointing': 18000}
PROT = ('benchmark', 'dev', 'R0', 'withheld', 'K1_heldout', 'official')


def enc(v): return (json.dumps(v, sort_keys=True, separators=(',', ':')) + '\n').encode()
def h(b): return hashlib.sha256(b).hexdigest()


QT = {'camera_displacement': 12428, 'camera_movement_direction': 10883, 'camera_rotation': 8127, 'object_abs_distance': 11663}


def build(admit_standin, pooled=False):
    files = {}
    rcounts = dict({k: 0 for k in KINDS}, routing_base=43101) if pooled else dict(KINDS)
    pop = dict(schema='r1-population-v1', complete=True, after_all_filters=True, counts=dict(rcounts, relative_distance=19827, pose_cell=90000))
    rf = dict(parent=dict(path='/tmp/x/receipt.json', sha256='0' * 64), refusals={'pose': {}, 'vqa': {'ValueError:x': 3}, 'routing': {}, 'pointing': {}})
    files['reader_filters.json'] = enc(rf)
    pop['evidence'] = [dict(path='p/q/b/reader_filters.json', sha256=h(files['reader_filters.json']))]
    files['population.json'] = enc(pop)
    off, cells = 0, {}
    for k, n in KINDS.items(): cells[k] = [] if pooled else list(range(off, off + n)); off += n
    if pooled: cells['routing_base'] = list(range(43101))
    files['indices.json'] = enc(dict(population_sha256=h(files['population.json']), cells=cells))
    files['binding.json'] = enc(dict(schema='r1-sampling-v1', population=dict(path='b/population.json', sha256=h(files['population.json'])),
                                     indices=dict(path='b/indices.json', sha256=h(files['indices.json']))))
    rec = dict(streams={s: dict(count=ADMITTED[s]) for s in STREAMS})
    rec['streams']['routing']['reader_source'] = dict(count=43101, database=dict(path='/tmp/q/p/q/selection/rows.sqlite', sha256=N_DB))
    files['receipt.json'] = enc(rec)
    recs = []
    plan = ['routing'] * 16 + ['pose'] * 24 + ['vqa'] * 24 + ['pointing'] * 8
    for m, s in enumerate(plan):
        for r in range(4):
            recs.append(dict(step=1, microstep=m, rank=r, stream=s, index=m, qid='q%d_%d' % (m, r), substituted_from=None, tokens=900 + m,
                             effective_tokens=900 + m, over_10k_tokens=False, loss=1.5, components={'x': 0.2}, finite=True, seconds=0.1))
    files['f.json'] = enc(dict(schema='c1-first-batch-check-v1', ranks=[0, 1, 2, 3], steps=1, device='cuda:0', records=recs))
    v = dict(r2_sampling=dict(population=dict(path='b/population.json', sha256=h(files['population.json'])),
                              indices=dict(path='b/indices.json', sha256=h(files['indices.json']))), frame_count=32, frame_layout='duplicate', frame_markers=True)
    files['v.json'] = enc(v)
    ident = admit_standin['identity']
    files['identity.txt'] = (ident + '\n').encode()
    files['WAITING_REVIEW.json'] = enc(dict(utc='2026-11-21T09:00:00+00:00', identity=ident, v_sha256=h(files['v.json']), deadline_utc='2026-11-21T11:00:00+00:00'))
    c4 = dict(schema='r1-protected-census-v1', phase='final', config_identity=ident, status='PASS', streams={})
    for i, s in enumerate(STREAMS):
        files['c%d.json' % i] = enc([])
        k1 = {'pose': 2663, 'routing': 841}.get(s)
        c4['streams'][s] = dict(result=dict(stream=s, source_rows=ADMITTED[s] + 10, admitted_rows=ADMITTED[s], protected_rows=0,
                                            resolved=dict(authority_and_aliases=ADMITTED[s], namespace=0, unresolved=0), protected_by_resolution={},
                                            exposure=({'K1_heldout': dict(status='exposure recorded, not protected', rows=k1)} if k1 else {})), refusals=[], status='PASS',
                                protected_keys=dict(file='c%d.json' % i, sha256=h(files['c%d.json' % i]), count=0),
                                counts=dict({k: 0 for k in PROT}, source=ADMITTED[s] + 10, admitted=ADMITTED[s], unresolved=0))
        files['e%d.json' % i] = enc(dict(stream=s, admitted_rows=ADMITTED[s], answer_only=0,
                                         databases=[dict(source='0', path='/tmp/q/p/q/p/prepare_x/%s.sqlite' % s, sha256=('ab' * 32), bytes=1)],
                                         protected_rooms={'bench_v2': dict(rows=0), 'dev_s1': dict(rows=0)}, question_types=dict(QT) if s == 'routing' else {}))
    files['c4.json'] = enc(c4)
    files['s2.json'] = enc(dict(status='PASS', refusal=None, counts={s: dict({k: 0 for k in PROT}, admitted=ADMITTED[s]) for s in STREAMS}))
    W = dict(camera=(4768, 0), pointing=(3640, 2944), pool=(9546, 6183), pose_a2v3=(5618, 5039), pose_a3v2=(13440, 22160), vqa=(0, 0))
    O = dict(camera=(783, 0), pointing=(0, 0), pool=(1122, 566), pose_a2v3=(1841, 159), pose_a3v2=(0, 0), vqa=(0, 0))
    srcs = {}
    for n in W:
        keys = [[i, True, False] for i in range(O[n][0])] + [[10**6 + i, False, True] for i in range(O[n][1])]
        srcs[n] = dict(whole=dict(dev=W[n][0], test=W[n][1]), admitted=dict(dev=W[n][0] - O[n][0], test=W[n][1] - O[n][1]),
                       outside=dict(dev=O[n][0], test=O[n][1]), outside_listed_keys=keys)
    whole_pin = dict(path='/tmp/q/p/q/sc/0.json', sha256='c' * 64)
    files['s4.json'] = enc(dict(schema='r1-admitted-scene-census-v1', whole_store_census=whole_pin, sources=srcs))
    files['s1.json'] = enc(dict(schema='dev_s1_manifest_v1', exact_rebuilt_population=True, population='admitted', whole_store_census=whole_pin,
                                outside=dict(path='/tmp/q/p/q/sc/o.json', sha256=h(files['s4.json'])),
                                withheld_training_rows={n: dict(path='x', rows_withheld=W[n][0] - O[n][0], benchmark_rows_withheld=W[n][1] - O[n][1]) for n in W}))
    ad = copy.deepcopy(admit_standin)
    ad['config_sha256'] = h(files['v.json'])
    for c in ad['checks']:
        if c['name'] in ('published_identity', 'all_stream_identities', 'row_plan_digest'): c.update(status='PASS', reason='prepared')
        if c['name'] in ('continuation_boundary', 'host_receipt_assertions'): c.update(status='NOT_RUN', reason='bytes not offline')
    files['ADMIT.json'] = enc(ad)
    return repin(files)


def repin(files):
    """The writers' pin chain: h0.json (h.py:34-39) pins c5 = c4 bytes; v.json pins h0 as r1_training.host_receipt;
    WAITING_REVIEW and ADMIT pin v.json."""
    f = dict(files)
    if 'h0.json' in f:
        h0 = json.loads(f['h0.json'])
    else:
        h0 = dict(status='PASS', assertions={}, loader_audit=dict(complete=True), config_identity=f['identity.txt'].decode().strip())
    h0['protected_census'] = dict(path='/tmp/q_22c714e1/c5.json', sha256=h(f['c4.json']))
    f['h0.json'] = enc(h0)
    v = json.loads(f['v.json']); v.setdefault('r1_training', {})['host_receipt'] = dict(path='/tmp/q_22c714e1/p/hr.json', sha256=h(f['h0.json']))
    f['v.json'] = enc(v)
    w = json.loads(f['WAITING_REVIEW.json']); w['v_sha256'] = h(f['v.json']); f['WAITING_REVIEW.json'] = enc(w)
    ad = json.loads(f['ADMIT.json']); ad['config_sha256'] = h(f['v.json']); f['ADMIT.json'] = enc(ad)
    return f


def write(files, out, gz=('indices.json', 'population.json', 'reader_filters.json', 'binding.json', 'receipt.json', 'f.json')):
    (out / 'live').mkdir(parents=True); (out / 'gate').mkdir()
    for n, b in files.items():
        if n == 'ADMIT.json': (out / n).write_bytes(b)
        elif n in gz: (out / 'gate' / (n + '.gz')).write_bytes(gzip.compress(b, 9))
        else: (out / 'live' / n).write_bytes(b)


def mutate(files, name, fn):
    f = dict(files); v = json.loads(f[name]); v = fn(v) or v; f[name] = enc(v); return f


def run(out):
    p = subprocess.run([sys.executable, '-I', str(HERE / 'gate.py'), str(out / 'live'), str(out / 'gate'), '--admit', str(out / 'ADMIT.json')],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    (out / "gate.out").write_text(p.stdout)
    fails = sorted(l.split()[1] for l in p.stdout.splitlines() if l.startswith('GATE ') and ' FAIL' in l and not l.startswith('GATE ALL'))
    return p.returncode, fails


def main():
    standin, negative, root = json.load(open(sys.argv[1])), json.load(open(sys.argv[2])), Path(sys.argv[3])
    # Fixtures come from the admit test on tree 9d2bbb8a; the gate now pins tree 02fd9a95ebd9719c596b39ac80e5247b92c1d6673d6cc2f4956c70b902718041 (T-mil), so the fixtures carry it.
    OLD_TREE = standin.get('tree_sha256')
    standin['tree_sha256'] = negative['tree_sha256'] = '02fd9a95ebd9719c596b39ac80e5247b92c1d6673d6cc2f4956c70b902718041'
    root.mkdir(parents=True, exist_ok=False)
    base = build(standin)
    neg_admit = build(negative)['ADMIT.json']
    neg_admit = json.loads(neg_admit); neg_admit['config_sha256'] = h(base['v.json']); neg_admit['identity'] = standin['identity']
    def receipt_refuse(v): v['streams']['routing']['count'] = 43000
    def p1(v): v['refusals']['routing'] = {'ValueError:R1_X': 2}
    def protected(v): v['streams']['vqa']['result']['protected_rows'] = 1; v['status'] = 'PASS'
    def quota(v):
        v['counts']['units'] = 300; v['counts']['camera_rotation'] += 418
    def nonfinite(v): v['records'][5]['loss'] = float('nan'); v['records'][5]['finite'] = False
    def waiting(v): v['v_sha256'] = '1' * 64
    def k1(v): v['streams']['routing']['result']['exposure']['K1_heldout']['rows'] = 842
    def unres(v): v['streams']['pose']['result']['resolved']['unresolved'] = 3
    def outside(v): v['sources']['pose_a2v3']['outside']['dev'] = 1840; v['sources']['pose_a2v3']['admitted']['dev'] = 3778
    def s2prot(v): v['counts']['pose']['dev'] = 1
    pooled = build(standin, pooled=True)
    def short(v): v['cells']['routing_base'] = v['cells']['routing_base'][:-1]
    def rate(v): v['question_types']['camera_rotation'] -= 3000; v['question_types']['camera_displacement'] += 3000
    def unitsx(v): v['question_types']['object_abs_distance'] -= 63; v['question_types']['camera_rotation'] += 63
    def planted(v): v['streams']['routing']['counts']['dev'] = 1
    def h0pin(v): v['protected_census']['sha256'] = '0' * 64
    cases = [('pass', base, [], 0),
             ('pass_s2_absent', {k: v for k, v in base.items() if k != 's2.json'}, [], 0),
             ('pass_routing_base_pooled', pooled, [], 0),
             ('pooled_offsets_short', mutate(pooled, 'indices.json', short), ['d_population'], 1),
             ('pooled_rate_off', mutate(pooled, 'e2.json', rate), ['item3_counts'], 1),
             ('pooled_units_unknown', mutate(pooled, 'e2.json', unitsx), ['item3_counts'], 1),
             ('census_s2_protected', mutate(base, 's2.json', s2prot), ['census'], 1),
             ('census_planted_row_repinned', repin(mutate(base, 'c4.json', planted)), ['census'], 1),
             ('census_h0_pin_differs', mutate(base, 'h0.json', h0pin), ['census'], 1),
             ('census_h0_absent', {k: v for k, v in base.items() if k != 'h0.json'}, ['census'], 1),
             ('identity_v_sha', mutate(base, 'WAITING_REVIEW.json', waiting), ['identity'], 1),
             ('d_receipt_count', mutate(base, 'receipt.json', receipt_refuse), ['d_population'], 1),
             ('P1_routing_refusal', mutate(base, 'reader_filters.json', p1), ['P1_filters'], 1),
             ('census_protected_row', mutate(base, 'c4.json', protected), ['census'], 1),
             ('item3_units_quota', mutate(base, 'population.json', quota), ['d_population', 'item3_counts'], 1),
             ('first_batch_nan', mutate(base, 'f.json', nonfinite), ['first_batch'], 1),
             ('census_k1_exposure', mutate(base, 'c4.json', k1), ['census'], 1),
             ('census_unresolved', mutate(base, 'c4.json', unres), ['census'], 1),
             ('scene_outside_differs', mutate(base, 's4.json', outside), ['scene_census'], 1),
             ('scene_s4_absent', {k: v for k, v in base.items() if k != 's4.json'}, ['scene_census'], 1),
             ('admit_negative_pixels', dict(base, **{'ADMIT.json': enc(neg_admit)}), ['admit_test'], 1),
             ('admit_standin_unprepared', dict(base, **{'ADMIT.json': enc(dict(standin, config_sha256=h(base['v.json'])))}), ['admit_test'], 1),
             ('admit_old_tree', dict(base, **{'ADMIT.json': enc(dict(json.loads(base['ADMIT.json']), tree_sha256=OLD_TREE))}), ['admit_test'], 1)]
    ok_all = True
    for name, files, want, want_rc in cases:
        out = root / name; write(files, out); rc, fails = run(out)
        ok = rc == want_rc and fails == sorted(want)
        ok_all &= ok
        print('%-26s %s rc %d fails %s (expected rc %d %s)' % (name, 'OK' if ok else 'WRONG', rc, fails, want_rc, sorted(want)))
    # Missing gate directory (the jn6 copy did not happen): (d), P1, item 3 and first_batch fail; nothing passes on absence.
    out = root / 'no_gate_dir'; write(base, out); [p.unlink() for p in (out / 'gate').iterdir()]; rc, fails = run(out)
    want = sorted(['d_population', 'P1_filters', 'item3_counts', 'first_batch'])
    ok = rc == 1 and fails == want; ok_all &= ok
    print('%-26s %s rc %d fails %s (expected rc 1 %s)' % ('no_gate_dir', 'OK' if ok else 'WRONG', rc, fails, want))
    print('TEST', 'ALL_OK' if ok_all else 'SOME_WRONG')
    return 0 if ok_all else 1


if __name__ == '__main__':
    sys.exit(main())
