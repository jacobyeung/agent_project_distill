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


def build(admit_standin):
    files = {}
    pop = dict(schema='r1-population-v1', complete=True, after_all_filters=True, counts=dict(KINDS, relative_distance=19827, pose_cell=90000))
    rf = dict(parent=dict(path='/tmp/x/receipt.json', sha256='0' * 64), refusals={'pose': {}, 'vqa': {'ValueError:x': 3}, 'routing': {}, 'pointing': {}})
    files['reader_filters.json'] = enc(rf)
    pop['evidence'] = [dict(path='p/q/b/reader_filters.json', sha256=h(files['reader_filters.json']))]
    files['population.json'] = enc(pop)
    off, cells = 0, {}
    for k, n in KINDS.items(): cells[k] = list(range(off, off + n)); off += n
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
        c4['streams'][s] = dict(result=dict(stream=s, source_rows=ADMITTED[s] + 10, admitted_rows=ADMITTED[s], protected_rows=0), refusals=[], status='PASS',
                                protected_keys=dict(file='c%d.json' % i, sha256=h(files['c%d.json' % i]), count=0))
        files['e%d.json' % i] = enc(dict(stream=s, admitted_rows=ADMITTED[s], answer_only=0,
                                         databases=[dict(source='0', path='/tmp/q/p/q/p/prepare_x/%s.sqlite' % s, sha256=('ab' * 32), bytes=1)],
                                         protected_rooms={'bench_v2': dict(rows=0), 'dev_s1': dict(rows=0)}, question_types={}))
    files['c4.json'] = enc(c4)
    files['s2.json'] = enc(dict(status='PASS', refusal=None, counts={s: dict({k: 0 for k in PROT}, admitted=ADMITTED[s]) for s in STREAMS}))
    ad = copy.deepcopy(admit_standin)
    ad['config_sha256'] = h(files['v.json'])
    for c in ad['checks']:
        if c['name'] in ('published_identity', 'all_stream_identities', 'row_plan_digest'): c.update(status='PASS', reason='prepared')
        if c['name'] in ('continuation_boundary', 'host_receipt_assertions'): c.update(status='NOT_RUN', reason='bytes not offline')
    files['ADMIT.json'] = enc(ad)
    return files


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
    cases = [('pass', base, [], 0),
             ('identity_v_sha', mutate(base, 'WAITING_REVIEW.json', waiting), ['identity'], 1),
             ('d_receipt_count', mutate(base, 'receipt.json', receipt_refuse), ['d_population'], 1),
             ('P1_routing_refusal', mutate(base, 'reader_filters.json', p1), ['P1_filters'], 1),
             ('census_protected_row', mutate(base, 'c4.json', protected), ['census'], 1),
             ('item3_units_quota', mutate(base, 'population.json', quota), ['d_population', 'item3_counts'], 1),
             ('first_batch_nan', mutate(base, 'f.json', nonfinite), ['first_batch'], 1),
             ('admit_negative_pixels', dict(base, **{'ADMIT.json': enc(neg_admit)}), ['admit_test'], 1),
             ('admit_standin_unprepared', dict(base, **{'ADMIT.json': enc(dict(standin, config_sha256=h(base['v.json'])))}), ['admit_test'], 1)]
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
