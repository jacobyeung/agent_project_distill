"""Count served stage-1 pools whose instances carry differing presences in one frame.

K1 (step 544): stored stage-1 caches, one per training capture of the 1,037-row A0 set.
Served reads (steps 200 and 544): per-call journals of the r1route out3 returns.
Writes work/MIXING.json. Read-only on every input.
"""
import collections, hashlib, io, json, sys, tarfile
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
K1 = Path('/scratch/jjyeung/k1/run_convert_2')
KBOX = Path('/scratch/jjyeung/orch_n30/sb_kbox4')
ROWSET = Path('/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_TRAIN_1037.txt')
OUT3 = Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3')
TOL = 1e-6
SERVED_CODE = ('b/e2e_reader/stage1.py', 'tree/student_pilot/routed_features.py',
               'tree/student_pilot/routed_candidates.py')
READS = {  # read label -> (export step, journal root)
    'A4/read0': (200, OUT3/'A4/ret/metadata/reads/0/metadata/journals'),
    'B5/read0': (200, OUT3/'B5/ret/metadata/reads/0/metadata/journals'),
    'b1/read0': (544, OUT3/'bases/b1/work/ret/metadata/reads/0/metadata/journals'),
    'b1/read1': (544, OUT3/'bases/b1/work/ret/metadata/reads/1/metadata/journals'),
    'b2/read0': (544, OUT3/'bases/b2/work/ret/metadata/reads/0/metadata/journals'),
}
PACKAGES = {'A4': OUT3/'A4', 'B5': OUT3/'B5', 'b1': OUT3/'bases/b1', 'b2': OUT3/'bases/b2'}
STEP400 = Path('/scratch/jjyeung/step400/ret')
sys.path.insert(0, str(OUT3/'A4/src/b/heads/selector/sl118'))
from selector_inputs import FIELDS  # noqa: E402
# sam_presence_members averages raw entries; presence_min/max come from lifted proposals.
RAW_PRESENCE, LIFT_MIN, LIFT_MAX = (FIELDS.index(k) for k in ('sam_presence_members', 'presence_min', 'presence_max'))


def sha(b):
    return hashlib.sha256(b).hexdigest()


def digest(v):
    return sha(json.dumps(v, sort_keys=True, allow_nan=False).encode())


def mixed(presences):
    return len(presences) > 1 and any(abs(p-presences[0]) > TOL for p in presences[1:])


def pools(record, name):
    """The pools one frame record can feed to cache_for, each in lift's score order."""
    pres = float(record['presence'])
    entries = sorted(record.get('instances') or [], key=lambda p: -float(p['score']))
    own = [(float(p['score']), float(p.get('source_presence', pres)), p.get('source_prompt', name)) for p in entries]
    raw = [v for v in own if v[2] == name]
    # sb_kbox4.predicted.cache_detect: raw-name entries, first raw presence, joint >= .05, cap 30.
    rp = raw[0][1] if raw else pres
    served = [v for v in raw if v[0]*rp >= .05][:30]
    merged = [v for v in own if v[0]*v[1] >= .05][:30]
    return dict(raw_all=raw, served=served, served_lift=[v for v in served if v[0] >= .3],
                merged_all=own, merged=merged, merged_lift=[v for v in merged if v[0] >= .3])


def capture(job):
    canonical, operands = job
    key = digest(canonical)[:16]
    path = K1/key/'candidates.json'
    if not path.is_file():
        return dict(capture=canonical, status='MISSING', path=str(path))
    data = path.read_bytes()
    cache = json.loads(data)
    count = collections.Counter()
    examples = []
    raw_presence_mismatch = 0
    for name in cache['phrases']:
        name_mixed = set()
        for slot in range(32):
            record = cache['frames'][str(slot)]['phrases'].get(name)
            if record is None:
                continue
            p = pools(record, name)
            if p['raw_all'] and any(abs(v[1]-float(record['presence'])) > TOL for v in p['raw_all']):
                raw_presence_mismatch += 1
            scopes = ('all', 'operand') if name in operands else ('all',)
            for scope in scopes:
                count[(scope, 'alias_only', 'frames')] += bool(p['merged_all'] and not p['raw_all'])
                for kind, values in p.items():
                    count[(scope, kind, 'frames')] += bool(values)
                    count[(scope, kind, 'multi')] += len(values) > 1
                    if mixed([v[1] for v in values]):
                        name_mixed.add((scope, kind))
                        count[(scope, kind, 'mixed')] += 1
                        count[(scope, kind, 'mixed_instances')] += sum(abs(v[1]-values[0][1]) > TOL for v in values[1:])
                        if kind == 'merged_lift' and scope == 'operand' and len(examples) < 3:
                            examples.append(dict(name=name, slot=slot, presences=[v[1] for v in values][:6],
                                                 prompts=[v[2] for v in values][:6], scores=[v[0] for v in values][:6]))
        for scope in ('all', 'operand') if name in operands else ('all',):
            count[(scope, 'names', 'total')] += 1
        for scope, kind in name_mixed:
            count[(scope, kind, 'mixed_names')] += 1
    return dict(capture=canonical, status='OK', path=str(path), sha256=sha(data), contract=cache.get('contract'),
                counts={'|'.join(k): v for k, v in count.items()}, raw_presence_mismatch=raw_presence_mismatch,
                examples=examples)


def journals():
    out = {}
    for label, (step, root) in READS.items():
        if not root.is_dir():
            out[label] = dict(step=step, status='MISSING', path=str(root))
            continue
        c = collections.Counter()
        fields = set()
        for items in sorted(root.glob('*/*/items.jsonl')):
            for line in items.read_text().splitlines():
                item = json.loads(line)
                c['items'] += 1
                for rec in ((item.get('output') or {}).get('calls') or {}).get('records') or []:
                    s1 = rec.get('stage1') or {}
                    if rec.get('family') == 'gap':
                        c['gap_calls'] += 1
                    if rec.get('family') != 'ground':
                        continue
                    if 'sam3' not in s1:
                        c['ground_calls_without_pool'] += 1
                        continue
                    c['stage1_pools'] += 1
                    kept = s1['sam3']['kept_per_frame']
                    c['frames_kept'] += sum(k > 0 for k in kept)
                    c['frames_multi'] += sum(k > 1 for k in kept)
                    fields.update(s1['sam3'])
                    for cand in s1['candidates']:
                        x = cand['inputs']
                        # raw-side mean member presence must lie in lift's [min, max]; journal floats are float32.
                        raw_mean, low, high = x[RAW_PRESENCE], x[LIFT_MIN], x[LIFT_MAX]
                        c['candidates_checked'] += 1
                        c['candidates_outside_lift_range'] += not (low - 1e-6 <= raw_mean <= high + 1e-6)
                        if len(cand['frames']) == 1:
                            c['single_member_checked'] += 1
                            c['single_member_mismatch'] += not (abs(raw_mean-low) <= 1e-6 and abs(raw_mean-high) <= 1e-6)
        out[label] = dict(step=step, status='OK', path=str(root), counts=dict(c), sam3_fields=sorted(fields),
                          per_instance_presence_journaled='instances' in fields or 'presences' in fields)
    return out


def code_identity():
    out = {}
    for label, root in PACKAGES.items():
        src, tgz = root/'src', root/'package/0.tgz'
        files = {}
        if tgz.is_file():
            with tarfile.open(tgz) as t:
                for n in SERVED_CODE:
                    files[n] = sha(t.extractfile(n).read())
        elif src.is_dir():
            files = {n: sha((src/n).read_bytes()) for n in SERVED_CODE}
        out[label] = files
    return out


def main():
    rows = set(ROWSET.read_text().splitlines())
    pinned = json.loads((KBOX/'pinned_train.json').read_text())
    jobs = []
    for c in pinned['captures']:
        mine = [r for r in c['rows'] if r['id'] in rows]
        if mine:
            jobs.append((c['canonical'], sorted({n for r in mine for n in r['operands']})))
    assert len(jobs) == 209, len(jobs)
    with Pool(8) as pool:
        caps = pool.map(capture, jobs)
    total = collections.Counter()
    for c in caps:
        total.update(c.get('counts', {}))
    result = dict(
        tolerance=TOL, captures=len(caps), missing=[c for c in caps if c['status'] != 'OK'],
        k1_totals=dict(sorted(total.items())),
        k1_raw_presence_vs_record_mismatch_frames=sum(c.get('raw_presence_mismatch', 0) for c in caps),
        k1_contracts=sorted({json.dumps(c.get('contract'), sort_keys=True) for c in caps}),
        k1_examples=[dict(capture=c['capture'], **e) for c in caps for e in c.get('examples', [])][:6],
        served_reads=journals(), served_code_sha256=code_identity(),
        step400=dict(status='OK' if STEP400.is_dir() else 'MISSING', expected=str(STEP400)),
        k1_per_capture=[{k: v for k, v in c.items() if k != 'examples'} for c in caps])
    (HERE/'MIXING.json').write_text(json.dumps(result, indent=1)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'k1_per_capture'}, indent=1))


if __name__ == '__main__':
    main()
