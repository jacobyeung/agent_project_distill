#!/usr/bin/env python3
"""Review-gate check for vehicle N's launch job (ORCH RULING 0211Z items 4-5).

Usage: python3 gate.py DIR [--admit ADMIT.json] [--map name=path ...]
DIR holds copies of the job's published evidence (any layout; files are found by name):
  live/: v.json identity.txt WAITING_REVIEW.json c0.json..c4.json s2.json
  p/q/b/: population.json indices.json[.gz] reader_filters.json binding.json receipt.json (prepared receipt)
  p/q/: f.json (first_batch_check records)
  ADMIT.json from w24z14 admit_test.sh run on the same v.json (or pass --admit).
Prints one GATE line per point and a final GATE ALL line. Standard library only; read-only.
"""
import argparse, gzip, hashlib, json, math, os, sys
from pathlib import Path

N_DB = '5e35c3ce600a867be194911642caccb23098035b4bf08909e519a170a1c243df'
N_ROWS = 43101
KEYSET = 'c2ba56c5'
TREE = '9d2bbb8ad209d91e21e56121785f62b0dddf3c8d9f14db8d23daf6dcd1d3591b'
ROUTING = {'camera_displacement': (12428, 18.25), 'camera_movement_direction': (10883, 15.88),
           'camera_rotation': (8127, 12.53), 'absolute_distance': (10945, 16.34), 'units': (718, 1.00)}
ROUTING_ROWS_PER_STEP = 64
QUOTA_TOLERANCE = 10.0
STREAMS = ('pose', 'vqa', 'routing', 'pointing')
PROTECTED = ('benchmark', 'dev', 'R0', 'withheld', 'K1_heldout', 'official')
WORLD = 4
GLOBAL_BATCH = 288
ADMIT_MUST_PASS = ('tree_seal', 'config_parse', 'kit_inline_metadata', 'config_identity', 'published_identity',
                   'expected_N_legacy_branch', 'deferred_inline', 'coverage_and_removal_binding',
                   'initialization_start', 'preparation_identity', 'protected_census_pin_identity', 'input_unchanged')
ADMIT_MAY_NOT_RUN = ('full_census_verification', 'caller_staging_verification', 'caller_prepared_config_equality',
                     'review_verdict_identity', 'host_receipt_assertions')
NAMES = ('v.json', 'identity.txt', 'WAITING_REVIEW.json', 'c0.json', 'c1.json', 'c2.json', 'c3.json', 'c4.json',
         's2.json', 'population.json', 'indices.json', 'reader_filters.json', 'binding.json', 'receipt.json',
         'f.json', 'ADMIT.json')

results = []


def say(point, ok, detail):
    results.append(ok)
    print('GATE %-12s %s %s' % (point, 'PASS' if ok else 'FAIL', detail), flush=True)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def raw(p):
    b = Path(p).read_bytes()
    return gzip.decompress(b) if str(p).endswith('.gz') else b


def load(p):
    v = json.loads(raw(p))
    if isinstance(v, dict) and v.get('encoding') in ('base64', 'base64-json') and 'payload' in v:
        import base64
        v = json.loads(base64.b64decode(v['payload']))
    return v


def find(root, overrides):
    found, notes = {}, []
    by_name = {}
    for dirpath, _, files in os.walk(root):
        for f in files:
            base = f[:-3] if f.endswith('.gz') else f
            by_name.setdefault(base, []).append(Path(dirpath) / f)
    for name in NAMES:
        if name in overrides:
            found[name] = Path(overrides[name]); continue
        c = sorted(by_name.get(name, []))
        if name == 'receipt.json':
            c = [p for p in c if p.parent.name == 'b'] or [p for p in c if 'b_receipt' in p.name] or c
            if len(c) > 1:
                notes.append('receipt.json ambiguous %s; pass --map receipt.json=PATH' % [str(p) for p in c]); c = []
        if c:
            found[name] = c[0]
            if len(c) > 1: notes.append('%s: %d copies, using %s' % (name, len(c), c[0]))
    return found, notes


def walk_sha(x, out, path=''):
    if isinstance(x, dict):
        for k, v in x.items():
            if k == 'sha256' and isinstance(v, str): out.append((path, v))
            walk_sha(v, out, path + '/' + str(k))
    elif isinstance(x, list):
        for i, v in enumerate(x): walk_sha(v, out, path + '[%d]' % i)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dir'); ap.add_argument('--admit'); ap.add_argument('--map', action='append', default=[])
    a = ap.parse_args()
    overrides = dict(m.split('=', 1) for m in a.map)
    if a.admit: overrides['ADMIT.json'] = a.admit
    F, notes = find(a.dir, overrides)
    for n in notes: print('NOTE', n)
    for name in NAMES:
        print('FILE %-20s %s' % (name, ('%s %s %d B' % (sha(F[name]), F[name], F[name].stat().st_size)) if name in F else 'ABSENT'))
    need = lambda *names: [n for n in names if n not in F]
    ctx = {}

    # G1 identity of the reviewed config
    miss = need('v.json', 'identity.txt', 'WAITING_REVIEW.json')
    if miss: say('identity', False, 'missing ' + ','.join(miss))
    else:
        cfg = load(F['v.json']); ctx['cfg'] = cfg
        ident = F['identity.txt'].read_text().strip(); ctx['identity'] = ident
        w = load(F['WAITING_REVIEW.json'])
        ok = w.get('identity') == ident and w.get('v_sha256') == sha(F['v.json']) and len(ident) == 64
        say('identity', ok, 'identity %s v.json %s waiting.identity %s waiting.v_sha256 %s deadline %s' % (
            ident, sha(F['v.json']), w.get('identity'), w.get('v_sha256'), w.get('deadline_utc')))

    # G2 (d) sampler population equals N's routing database
    miss = need('population.json', 'indices.json', 'receipt.json')
    if miss: say('d_population', False, 'missing ' + ','.join(miss))
    else:
        pop = load(F['population.json']); idx = load(F['indices.json']); rec = load(F['receipt.json'])
        ctx['pop'] = pop; ctx['rec'] = rec
        counts = pop.get('counts', {})
        problems = []
        if pop.get('schema') != 'r1-population-v1' or pop.get('complete') is not True or pop.get('after_all_filters') is not True:
            problems.append('population schema/complete/after_all_filters %s/%s/%s' % (pop.get('schema'), pop.get('complete'), pop.get('after_all_filters')))
        if idx.get('population_sha256') != sha(F['population.json']):
            problems.append('indices.population_sha256 %s != population.json' % idx.get('population_sha256'))
        cfg = ctx.get('cfg') or {}
        samp = cfg.get('r2_sampling') or {}
        for key, name in (('population', 'population.json'), ('indices', 'indices.json')):
            pin = (samp.get(key) or {}).get('sha256')
            if pin != hashlib.sha256(raw(F[name])).hexdigest():
                problems.append('v.json r2_sampling.%s.sha256 %s != %s bytes' % (key, pin, name))
        missing_types = [t for t in ROUTING if t not in counts]
        if missing_types: problems.append('routing types absent from population: %s' % missing_types)
        routing_total = sum(counts.get(t, 0) for t in ROUTING)
        offsets = [o for t in ROUTING for o in idx.get('cells', {}).get(t, [])]
        if len(offsets) != len(set(offsets)): problems.append('duplicate routing offsets %d' % (len(offsets) - len(set(offsets))))
        rstream = (rec.get('streams') or {}).get('routing') or {}
        rcount = rstream.get('count')
        if set(offsets) != set(range(N_ROWS)): problems.append('routing offsets cover %d of range(%d)' % (len(set(offsets) & set(range(N_ROWS))), N_ROWS))
        if routing_total != N_ROWS or rcount != N_ROWS: problems.append('routing population %d receipt count %s expected %d' % (routing_total, rcount, N_ROWS))
        shas = []; walk_sha(rstream, shas)
        if not any(v == N_DB for _, v in shas): problems.append('routing receipt names no %s; sha256 fields: %s' % (N_DB[:8], [(p, v[:8]) for p, v in shas][:12]))
        say('d_population', not problems, ('routing population %d = receipt count %s; offsets = range(%d); database %s (key set %s established on the same database bytes in evidence run 173881)' % (
            routing_total, rcount, N_ROWS, N_DB[:8], KEYSET)) if not problems else '; '.join(problems))

    # G3 P1 reader_filters
    miss = need('reader_filters.json')
    if miss: say('P1_filters', False, 'missing reader_filters.json')
    else:
        rf = load(F['reader_filters.json']); ref = rf.get('refusals')
        other = {s: sum(v.values()) for s, v in (ref or {}).items() if s != 'routing' and isinstance(v, dict)}
        ok = isinstance(ref, dict) and ref.get('routing') == {}
        say('P1_filters', ok, 'routing refusals %s; other streams refused (information) %s' % (json.dumps((ref or {}).get('routing'))[:400], other))

    # G4 census: zero admitted protected rows in every stream
    miss = need('c4.json', 's2.json', 'c0.json', 'c1.json', 'c2.json', 'c3.json')
    if miss: say('census', False, 'missing ' + ','.join(miss))
    else:
        c4 = load(F['c4.json']); s2 = load(F['s2.json']); problems = []; summary = []
        if c4.get('schema') != 'r1-protected-census-v1' or c4.get('phase') != 'final' or c4.get('status') != 'PASS':
            problems.append('c4 schema/phase/status %s/%s/%s' % (c4.get('schema'), c4.get('phase'), c4.get('status')))
        if ctx.get('identity') and c4.get('config_identity') != ctx['identity']:
            problems.append('c4 config_identity %s != identity.txt' % c4.get('config_identity'))
        rec_streams = (ctx.get('rec') or {}).get('streams') or {}
        for i, s in enumerate(STREAMS):
            r = (c4.get('streams') or {}).get(s)
            if r is None: problems.append('c4 lacks stream ' + s); continue
            res = r.get('result') or {}
            keys = load(F['c%d.json' % i]); kf = (r.get('protected_keys') or {})
            if res.get('protected_rows') != 0 or r.get('refusals') or r.get('status') != 'PASS' or keys != [] or kf.get('count') != 0:
                problems.append('%s protected_rows %s refusals %s status %s keys %s' % (s, res.get('protected_rows'), r.get('refusals'), r.get('status'), len(keys) if isinstance(keys, list) else keys))
            if kf.get('file') != 'c%d.json' % i or kf.get('sha256') != sha(F['c%d.json' % i]):
                problems.append('%s protected_keys pin %s does not match c%d.json' % (s, kf, i))
            sc = (s2.get('counts') or {}).get(s) or {}
            hits = {k: sc.get(k) for k in PROTECTED if sc.get(k)}
            if hits or any(k not in sc for k in PROTECTED): problems.append('s2 %s protected counts %s' % (s, {k: sc.get(k) for k in PROTECTED}))
            rc = (rec_streams.get(s) or {}).get('count')
            if not (res.get('admitted_rows') == sc.get('admitted') == rc):
                problems.append('%s admitted c4 %s s2 %s receipt %s differ' % (s, res.get('admitted_rows'), sc.get('admitted'), rc))
            summary.append('%s admitted %s source %s protected %s' % (s, res.get('admitted_rows'), res.get('source_rows'), res.get('protected_rows')))
        if s2.get('status') != 'PASS' or s2.get('refusal'): problems.append('s2 status %s refusal %s' % (s2.get('status'), s2.get('refusal')))
        say('census', not problems, '; '.join(summary) if not problems else '; '.join(problems))

    # G5 item 3: actual counts, routing per-type within 10% of P's quotas
    if 'pop' not in ctx: say('item3_counts', False, 'population.json absent')
    else:
        counts = ctx['pop'].get('counts', {}); total = sum(counts.get(t, 0) for t in ROUTING); problems = []; rows = []
        for t, (expected, quota) in ROUTING.items():
            n = counts.get(t, 0)
            per_step = n / total * ROUTING_ROWS_PER_STEP if total else 0.0
            off = (per_step - quota) / quota * 100
            rows.append('%s %d (173881 %d) %.3f/step vs P %.2f = %+.2f%%' % (t, n, expected, per_step, quota, off))
            if abs(off) > QUOTA_TOLERANCE: problems.append('%s %+.2f%% beyond %.0f%%' % (t, off, QUOTA_TOLERANCE))
        info = {s: ((ctx.get('rec') or {}).get('streams') or {}).get(s, {}).get('count') for s in STREAMS}
        print('INFO item3 stream counts (receipt): %s; VQA list stage 181,098 + 7,971 twins = 189,069; pointing 18,116 before the shape filter' % info)
        print('INFO item3 population counts by cell: %s' % json.dumps(counts, sort_keys=True))
        print('INFO item3 relative_distance cell %s (card ceiling 19,827; list census 19,833)' % counts.get('relative_distance'))
        if (info.get('vqa') or 0) > 189069: problems.append('vqa %s exceeds 189,069' % info.get('vqa'))
        if (info.get('pointing') or 0) > 18116: problems.append('pointing %s exceeds 18,116' % info.get('pointing'))
        say('item3_counts', not problems, ' | '.join(rows) if not problems else '; '.join(problems + rows))

    # G6 item 8: first batch per stream
    miss = need('f.json')
    if miss: say('first_batch', False, 'missing f.json')
    else:
        f = load(F['f.json']); recs = f.get('records') or []; problems = []
        if f.get('schema') != 'c1-first-batch-check-v1': problems.append('schema %s' % f.get('schema'))
        if len(recs) != GLOBAL_BATCH: problems.append('%d records, expected %d' % (len(recs), GLOBAL_BATCH))
        bad = [(r.get('rank'), r.get('stream'), r.get('qid'), r.get('error')) for r in recs if r.get('finite') is not True or r.get('error')]
        if bad: problems.append('non-finite or error rows %d, first %s' % (len(bad), bad[:3]))
        ranks = sorted({r.get('rank') for r in recs})
        if ranks != list(range(WORLD)): problems.append('ranks %s' % ranks)
        per = {}
        for r in recs: per.setdefault(r.get('stream'), []).append(r)
        lines = []
        for s, rs in sorted(per.items(), key=lambda kv: str(kv[0])):
            tok = [r.get('tokens', 0) for r in rs]; eff = [r.get('effective_tokens', 0) for r in rs]; loss = [r['loss'] for r in rs if isinstance(r.get('loss'), (int, float))]
            if min(tok) <= 0: problems.append('%s has a zero-token row' % s)
            if not loss or not all(math.isfinite(x) for x in loss): problems.append('%s loss not finite' % s)
            lines.append('%s rows %d ranks %s tokens %d-%d effective max %d over10k %d loss %.4f-%.4f mean %.4f substituted %d' % (
                s, len(rs), sorted({r.get('rank') for r in rs}), min(tok), max(tok), max(eff), sum(bool(r.get('over_10k_tokens')) for r in rs),
                min(loss) if loss else float('nan'), max(loss) if loss else float('nan'), sum(loss) / len(loss) if loss else float('nan'),
                sum(bool(r.get('substituted_from')) for r in rs)))
        cfg = ctx.get('cfg') or {}
        print('INFO first_batch processor fields in v.json: %s' % {k: cfg.get(k) for k in ('b7_inputs', 'min_pixels', 'max_pixels', 'frame_count', 'frame_layout', 'frame_markers')})
        say('first_batch', not problems, ' | '.join(lines) if not problems else '; '.join(problems + lines))

    # G7 item 8 ground (iii): admit test on the job's own v.json
    miss = need('ADMIT.json', 'v.json')
    if miss: say('admit_test', False, 'missing ' + ','.join(miss))
    else:
        ad = load(F['ADMIT.json']); problems = []
        checks = {c['name']: c for c in ad.get('checks', [])}
        if ad.get('config_sha256') != sha(F['v.json']): problems.append('ADMIT config_sha256 %s != v.json' % ad.get('config_sha256'))
        if ad.get('tree_sha256') != TREE: problems.append('tree %s' % ad.get('tree_sha256'))
        if ad.get('branch_taken') != 'legacy_C_prime': problems.append('branch %s' % ad.get('branch_taken'))
        if ctx.get('identity') and ad.get('identity') != ctx['identity']: problems.append('identity %s != identity.txt' % ad.get('identity'))
        for n in ADMIT_MUST_PASS:
            st = (checks.get(n) or {}).get('status')
            if st != 'PASS': problems.append('%s %s %s' % (n, st, (checks.get(n) or {}).get('reason', '')[:200]))
        na = checks.get('native_admit') or {}
        if na.get('status') != 'PASS' and 'INDEPENDENT_REVIEW_PENDING' not in str(na.get('reason')):
            problems.append('native_admit %s %s' % (na.get('status'), str(na.get('reason'))[:300]))
        for n, c in checks.items():
            if n in ADMIT_MUST_PASS or n == 'native_admit': continue
            if c.get('status') == 'FAIL' or (c.get('status') == 'NOT_RUN' and n not in ADMIT_MAY_NOT_RUN):
                problems.append('%s %s %s' % (n, c.get('status'), str(c.get('reason'))[:200]))
        say('admit_test', not problems, ('branch legacy_C_prime; native_admit stops at %s; NOT_RUN %s' % (
            str(na.get('reason'))[:120], [n for n, c in checks.items() if c.get('status') == 'NOT_RUN'])) if not problems else '; '.join(problems))

    ok = all(results) and len(results) == 7
    print('GATE ALL %s (%d of %d points)' % ('PASS' if ok else 'FAIL', sum(results), len(results)))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
