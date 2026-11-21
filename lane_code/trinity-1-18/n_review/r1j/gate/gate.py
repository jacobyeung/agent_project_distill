#!/usr/bin/env python3
"""Review-gate check for vehicle N's launch job (ORCH RULING 0211Z items 4-5). Read-only, standard library.

Usage: python3 -I gate.py DIR [DIR ...] [--admit ADMIT.json] [--map NAME=PATH ...]
Each DIR is searched recursively for the files below by name (a .gz copy is read decompressed):
  X/o/<job>/live (written there by the kit itself, j.sh:404-405):
     v.json identity.txt WAITING_REVIEW.json e0.json-e3.json (rv.py:208) c0.json-c4.json (cs.py:109-116) s2.json (sv.py:90)
  node-local N/p/q copied off the node (jn6 one-shot copy, e.g. X/o/<job>_gate):
     b/population.json b/indices.json b/reader_filters.json b/binding.json b/receipt.json (r1_population.py:148-235)
     f.json (production_proof.py:19, first_batch_check)
  ADMIT.json from W/w24z14/out/admit_test.sh run on the same v.json.
Prints one GATE line per point (PASS or FAIL with the registered values) and a final GATE ALL line; exit 0 only on all PASS.
A missing file fails its point: what cannot be checked does not pass.
"""
import argparse, gzip, hashlib, json, math, os, sys
from pathlib import Path

N_DB = '5e35c3ce600a867be194911642caccb23098035b4bf08909e519a170a1c243df'
N_ROWS = 43101
KEYSET = 'c2ba56c5'
TREE = '9d2bbb8ad209d91e21e56121785f62b0dddf3c8d9f14db8d23daf6dcd1d3591b'
# kind: (count in evidence run 173881, P's rows per step) -- ANSWER 0553Z: within 10% and units >= 0.90 per step
ROUTING = {'camera_displacement': (12428, 18.25), 'camera_movement_direction': (10883, 15.88),
           'camera_rotation': (8127, 12.53), 'absolute_distance': (10945, 16.34), 'units': (718, 1.00)}
ROUTING_ROWS_PER_STEP = 64
QUOTA_TOLERANCE = 10.0
UNITS_FLOOR = 0.90
STREAMS = ('pose', 'vqa', 'routing', 'pointing')
PROTECTED = ('benchmark', 'dev', 'R0', 'withheld', 'K1_heldout', 'official')
WORLD = 4
GLOBAL_BATCH = 288
VQA_CEILING = 189069
POINTING_CEILING = 18116
# admit_test.py (w24z14) check names. MUST_PASS run from v.json and the sealed tree alone (all PASS on the
# stand-in except the prepared-only three, which a prepared v.json must pass).
ADMIT_MUST_PASS = ('tree_seal', 'config_parse', 'kit_inline_metadata', 'config_identity', 'published_identity',
                   'deferred_inline', 'init_policy', 'recipe_geometry_frames', 'mix_and_camera_weights',
                   'stop_and_milestones', 'processor_legacy_or_b7', 'expected_N_legacy_branch', 'row_plan_present',
                   'host_receipt_pin', 'review_receipt_pin', 'routing_card_and_counts', 'input_unchanged',
                   'all_stream_identities', 'row_plan_digest')
# Only these may FAIL, and only with this reason: review.json does not exist before the gate passes.
ADMIT_PENDING = ('review_verdict_identity', 'native_admit')
PENDING_REASON = 'INDEPENDENT_REVIEW_PENDING'
LIVE = ('v.json', 'identity.txt', 'WAITING_REVIEW.json', 'e0.json', 'e1.json', 'e2.json', 'e3.json',
        'c0.json', 'c1.json', 'c2.json', 'c3.json', 'c4.json', 's2.json', 's1.json', 's4.json')
NODE = ('population.json', 'indices.json', 'reader_filters.json', 'binding.json', 'receipt.json', 'f.json')
NAMES = LIVE + NODE + ('ADMIT.json',)
# Kit-side admitted scene census (kit cn.py, ANSWER 1604Z (d)): live/s1.json = a.json, live/s4.json = o.json.
# (dev, test) per census source; whole store and outside-admitted values proven by row keys (n_review1j RESULT 1606Z).
SCENE_WHOLE = {'camera': (4768, 0), 'pointing': (3640, 2944), 'pool': (9546, 6183), 'pose_a2v3': (5618, 5039),
               'pose_a3v2': (13440, 22160), 'vqa': (0, 0)}
SCENE_OUTSIDE = {'camera': (783, 0), 'pointing': (0, 0), 'pool': (1122, 566), 'pose_a2v3': (1841, 159),
                 'pose_a3v2': (0, 0), 'vqa': (0, 0)}
# Room census exposure (ORCH RULING 1716Z): K1 held-out protects vqa and pointing; pose and routing record their
# K1 rows as exposure (fix13 t4/t6 counts); every stream resolves every admitted row.
K1_EXPOSURE = {'pose': 2663, 'routing': 841, 'vqa': None, 'pointing': None}
E = {s: 'e%d.json' % i for i, s in enumerate(STREAMS)}   # rv.py NAMES: pose e0, vqa e1, routing e2, pointing e3

results = []


def say(point, ok, detail):
    results.append(ok)
    print('GATE %-13s %s %s' % (point, 'PASS' if ok else 'FAIL', detail), flush=True)


def raw(p):
    b = Path(p).read_bytes()
    return gzip.decompress(b) if str(p).endswith('.gz') else b


def sha_raw(p):
    return hashlib.sha256(raw(p)).hexdigest()


def load(p):
    v = json.loads(raw(p))
    if isinstance(v, dict) and v.get('encoding') in ('base64', 'base64-json') and 'payload' in v:
        import base64
        v = json.loads(base64.b64decode(v['payload']))
    return v


def find(roots, overrides):
    found, notes, by_name = {}, [], {}
    for root in roots:
        for dirpath, _, files in os.walk(root):
            for f in files:
                if f.endswith('.part'):
                    continue
                base = f[:-3] if f.endswith('.gz') else f
                by_name.setdefault(base, []).append(Path(dirpath) / f)
    for name in NAMES:
        if name in overrides:
            found[name] = Path(overrides[name]); continue
        c = sorted(set(by_name.get(name, [])))
        if name == 'receipt.json':   # only the prepared receipt N/p/q/b/receipt.json (in b/ or in the <job>_gate copy)
            c = [p for p in c if p.parent.name == 'b' or p.parent.name.endswith('_gate') or p.parent.name == 'gate']
        if len(c) > 1:
            notes.append('%s: %d candidates %s; pass --map %s=PATH' % (name, len(c), [str(p) for p in c], name)); continue
        if c:
            found[name] = c[0]
    return found, notes


def shas(x, out=None, path=''):
    out = [] if out is None else out
    if isinstance(x, dict):
        for k, v in x.items():
            if k == 'sha256' and isinstance(v, str): out.append((path, v))
            shas(v, out, path + '/' + str(k))
    elif isinstance(x, list):
        for i, v in enumerate(x): shas(v, out, path + '[%d]' % i)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dirs', nargs='+'); ap.add_argument('--admit'); ap.add_argument('--map', action='append', default=[])
    a = ap.parse_args()
    overrides = dict(m.split('=', 1) for m in a.map)
    if a.admit: overrides['ADMIT.json'] = a.admit
    F, notes = find(a.dirs, overrides)
    for n in notes: print('NOTE', n)
    for name in NAMES:
        print('FILE %-20s %s' % (name, ('raw_sha256 %s %s %d B' % (sha_raw(F[name]), F[name], F[name].stat().st_size)) if name in F else 'ABSENT'))
    need = lambda *names: [n for n in names if n not in F]
    ctx = {}
    for name in ('v.json', 'population.json', 'receipt.json'):
        if name in F:
            try: ctx[name] = load(F[name])
            except Exception as e: print('NOTE %s unreadable %s' % (name, e)); F.pop(name)
    if 'receipt.json' in ctx and not isinstance(ctx['receipt.json'].get('streams'), dict):
        print('NOTE receipt.json %s has no streams map (not a prepared receipt); treated as absent' % F['receipt.json']); F.pop('receipt.json'); ctx.pop('receipt.json')
    for s in STREAMS:
        if E[s] in F:
            try: ctx[E[s]] = load(F[E[s]])
            except Exception as e: print('NOTE %s unreadable %s' % (E[s], e)); F.pop(E[s])
    if 'identity.txt' in F: ctx['identity'] = raw(F['identity.txt']).decode().strip()

    # G1 identity of the reviewed config
    miss = need('v.json', 'identity.txt', 'WAITING_REVIEW.json')
    if miss: say('identity', False, 'missing ' + ','.join(miss))
    else:
        ident = ctx['identity']; w = load(F['WAITING_REVIEW.json']); vsha = sha_raw(F['v.json'])
        ok = len(ident) == 64 and w.get('identity') == ident and w.get('v_sha256') == vsha
        say('identity', ok, 'identity.txt %s; WAITING_REVIEW identity %s v_sha256 %s; v.json %s; waiting since %s deadline %s' % (
            ident, w.get('identity'), w.get('v_sha256'), vsha, w.get('utc'), w.get('deadline_utc')))

    # G2 (d) sampler population equals N's routing database
    miss = need('v.json', 'population.json', 'indices.json', 'receipt.json', 'e2.json')
    if miss: say('d_population', False, 'missing ' + ','.join(miss))
    else:
        pop, idx, rec, cfg, e2 = ctx['population.json'], load(F['indices.json']), ctx['receipt.json'], ctx['v.json'], ctx['e2.json']
        counts = pop.get('counts', {}); problems = []
        if pop.get('schema') != 'r1-population-v1' or pop.get('complete') is not True or pop.get('after_all_filters') is not True:
            problems.append('population schema/complete/after_all_filters %s/%s/%s' % (pop.get('schema'), pop.get('complete'), pop.get('after_all_filters')))
        if idx.get('population_sha256') != sha_raw(F['population.json']):
            problems.append('indices.population_sha256 %s != population.json' % idx.get('population_sha256'))
        samp = cfg.get('r2_sampling') or {}
        for key, name in (('population', 'population.json'), ('indices', 'indices.json')):
            pin = (samp.get(key) or {}).get('sha256')
            if pin != sha_raw(F[name]): problems.append('v.json r2_sampling.%s.sha256 %s != %s bytes %s' % (key, pin, name, sha_raw(F[name])))
        if 'binding.json' in F:
            b = load(F['binding.json'])
            for key, name in (('population', 'population.json'), ('indices', 'indices.json')):
                if (b.get(key) or {}).get('sha256') != sha_raw(F[name]): problems.append('binding.json %s pin differs' % key)
        absent = [t for t in ROUTING if t not in counts]
        if absent: problems.append('routing kinds absent from population: %s' % absent)
        total = sum(counts.get(t, 0) for t in ROUTING)
        offsets = [o for t in ROUTING for o in (idx.get('cells') or {}).get(t, [])]
        if len(offsets) != len(set(offsets)): problems.append('duplicate routing offsets %d' % (len(offsets) - len(set(offsets))))
        if set(offsets) != set(range(N_ROWS)): problems.append('routing offsets cover %d of range(%d), %d outside' % (
            len(set(offsets) & set(range(N_ROWS))), N_ROWS, len(set(offsets) - set(range(N_ROWS)))))
        rs = (rec.get('streams') or {}).get('routing') or {}
        rcount, ecount = rs.get('count'), e2.get('admitted_rows')
        if not (total == rcount == ecount == N_ROWS):
            problems.append('routing rows population %d prepared receipt %s e2 %s expected %d' % (total, rcount, ecount, N_ROWS))
        hits = [p for p, v in shas(rs) if v == N_DB] + ['e2.databases' for d in e2.get('databases', []) if d.get('sha256') == N_DB]
        if not hits: problems.append('neither the prepared routing stream nor e2.databases names %s; e2.databases %s' % (
            N_DB[:8], [(d.get('sha256', '')[:8], d.get('bytes')) for d in e2.get('databases', [])]))
        say('d_population', not problems, ('routing rows %d = prepared receipt %s = e2 %s; offsets exactly range(%d); database %s named at %s; '
            'e2 reader databases %s. Key set %s was established on these database bytes in evidence run 173881; with P1 empty and full offsets the population is that key set.' % (
            total, rcount, ecount, N_ROWS, N_DB[:8], hits[:3], [(d.get('sha256', '')[:8], d.get('bytes')) for d in e2.get('databases', [])], KEYSET))
            if not problems else '; '.join(problems))

    # G3 P1 reader_filters: no routing refusals
    miss = need('reader_filters.json')
    if miss: say('P1_filters', False, 'missing reader_filters.json')
    else:
        rf = load(F['reader_filters.json']); ref = rf.get('refusals')
        other = {s: sum(v.values()) for s, v in (ref or {}).items() if s != 'routing' and isinstance(v, dict)}
        pinned = 'population.json' in ctx and sha_raw(F['reader_filters.json']) in [v for _, v in shas(ctx['population.json'])]
        ok = isinstance(ref, dict) and ref.get('routing') == {} and pinned
        say('P1_filters', ok, 'routing refusals %s; pinned in population.evidence %s; other streams refused (information) %s' % (
            json.dumps((ref or {}).get('routing'))[:400], pinned, other))

    # G4 census: zero admitted protected rows in every stream
    miss = need('c0.json', 'c1.json', 'c2.json', 'c3.json', 'c4.json', 's2.json', *[E[s] for s in STREAMS])
    if miss: say('census', False, 'missing ' + ','.join(miss))
    else:
        c4 = load(F['c4.json']); s2 = load(F['s2.json']); problems = []; summary = []
        if c4.get('schema') != 'r1-protected-census-v1' or c4.get('phase') != 'final' or c4.get('status') != 'PASS':
            problems.append('c4 schema/phase/status %s/%s/%s' % (c4.get('schema'), c4.get('phase'), c4.get('status')))
        if ctx.get('identity') and c4.get('config_identity') != ctx['identity']:
            problems.append('c4 config_identity %s != identity.txt' % c4.get('config_identity'))
        if s2.get('status') != 'PASS' or s2.get('refusal'): problems.append('s2 status %s refusal %s' % (s2.get('status'), s2.get('refusal')))
        for i, s in enumerate(STREAMS):
            r = (c4.get('streams') or {}).get(s)
            if r is None: problems.append('c4 lacks stream ' + s); continue
            res = r.get('result') or {}; keys = load(F['c%d.json' % i]); kf = r.get('protected_keys') or {}
            if res.get('protected_rows') != 0 or r.get('refusals') or r.get('status') != 'PASS' or keys != [] or kf.get('count') != 0:
                problems.append('%s protected_rows %s refusals %s status %s keys %s' % (s, res.get('protected_rows'), r.get('refusals'), r.get('status'), len(keys) if isinstance(keys, list) else keys))
            if kf.get('file') != 'c%d.json' % i or kf.get('sha256') != sha_raw(F['c%d.json' % i]):
                problems.append('%s protected_keys pin %s does not match c%d.json' % (s, kf, i))
            sc = (s2.get('counts') or {}).get(s) or {}
            if any(sc.get(k) != 0 for k in PROTECTED): problems.append('s2 %s protected counts %s' % (s, {k: sc.get(k) for k in PROTECTED}))
            ev = ctx[E[s]]; rooms = {k: (v or {}).get('rows') for k, v in (ev.get('protected_rooms') or {}).items()}
            if ev.get('stream') != s or not rooms or any(v != 0 for v in rooms.values()):
                problems.append('%s %s protected_rooms %s' % (E[s], s, rooms))
            if not (res.get('admitted_rows') == sc.get('admitted') == ev.get('admitted_rows')):
                problems.append('%s admitted c4 %s s2 %s %s %s differ' % (s, res.get('admitted_rows'), sc.get('admitted'), E[s], ev.get('admitted_rows')))
            resolved = res.get('resolved') or {}; exp = ((res.get('exposure') or {}).get('K1_heldout') or {})
            if resolved.get('unresolved') != 0: problems.append('%s resolved.unresolved %s' % (s, resolved.get('unresolved')))
            if res.get('protected_by_resolution'): problems.append('%s protected_by_resolution %s' % (s, res.get('protected_by_resolution')))
            if K1_EXPOSURE[s] is None:
                if exp: problems.append('%s records K1 exposure %s but K1 protects it' % (s, exp.get('rows')))
            elif exp.get('rows') != K1_EXPOSURE[s] or exp.get('status') != 'exposure recorded, not protected':
                problems.append('%s K1 exposure %s (%s), expected %d' % (s, exp.get('rows'), exp.get('status'), K1_EXPOSURE[s]))
            summary.append('%s admitted %s (source %s) protected 0 in c4, s2 and %s; unresolved 0; K1 exposure %s' % (s, res.get('admitted_rows'), res.get('source_rows'), E[s], exp.get('rows', 'none')))
        say('census', not problems, '; '.join(summary) if not problems else '; '.join(problems))

    # G5 item 3: actual routing counts within 10% of P's quotas; stream totals under their list ceilings
    miss = need('population.json')
    if miss: say('item3_counts', False, 'missing population.json')
    else:
        counts = ctx['population.json'].get('counts', {}); total = sum(counts.get(t, 0) for t in ROUTING); problems = []; rows = []
        for t, (expected, quota) in ROUTING.items():
            n = counts.get(t, 0); per = n / total * ROUTING_ROWS_PER_STEP if total else 0.0; off = (per - quota) / quota * 100
            rows.append('%s %d (173881 %d) %.3f/step vs P %.2f = %+.2f%%' % (t, n, expected, per, quota, off))
            if abs(off) > QUOTA_TOLERANCE: problems.append('%s %+.2f%% beyond %.0f%%' % (t, off, QUOTA_TOLERANCE))
        units = counts.get('units', 0) / total * ROUTING_ROWS_PER_STEP if total else 0.0
        if units < UNITS_FLOOR: problems.append('units %.3f/step below %.2f' % (units, UNITS_FLOOR))
        admitted = {s: ctx[E[s]].get('admitted_rows') if E[s] in ctx else None for s in STREAMS}
        prepared = {s: (((ctx.get('receipt.json') or {}).get('streams') or {}).get(s) or {}).get('count') for s in STREAMS}
        print('INFO item3 admitted rows (e0-e3) %s; prepared receipt counts %s; VQA list stage 181,098 + 7,971 twins = 189,069; pointing 18,116 before the shape filter' % (admitted, prepared))
        print('INFO item3 population counts by cell: %s' % json.dumps(counts, sort_keys=True))
        print('INFO item3 relative_distance cell %s (card ceiling 19,827; list census 19,833)' % counts.get('relative_distance'))
        if 'e2.json' in ctx: print('INFO item3 e2 routing question_types %s' % json.dumps(ctx['e2.json'].get('question_types'), sort_keys=True))
        if (admitted.get('vqa') or 0) > VQA_CEILING: problems.append('vqa %s exceeds %d' % (admitted.get('vqa'), VQA_CEILING))
        if (admitted.get('pointing') or 0) > POINTING_CEILING: problems.append('pointing %s exceeds %d' % (admitted.get('pointing'), POINTING_CEILING))
        if any(v is None for v in admitted.values()): problems.append('admitted rows unknown for %s' % [s for s, v in admitted.items() if v is None])
        say('item3_counts', not problems, ' | '.join(rows) if not problems else '; '.join(problems + rows))

    # G6 item 8: first batch per stream (one forward per (microstep, rank) of step 1)
    miss = need('f.json')
    if miss: say('first_batch', False, 'missing f.json')
    else:
        f = load(F['f.json']); recs = f.get('records') or []; problems = []
        if f.get('schema') != 'c1-first-batch-check-v1': problems.append('schema %s' % f.get('schema'))
        if len(recs) != GLOBAL_BATCH: problems.append('%d records, expected %d (global batch on %d ranks)' % (len(recs), GLOBAL_BATCH, WORLD))
        slots = [(r.get('step'), r.get('microstep'), r.get('rank')) for r in recs]
        if len(slots) != len(set(slots)): problems.append('duplicate (step, microstep, rank) records %d' % (len(slots) - len(set(slots))))
        bad = [(r.get('rank'), r.get('stream'), r.get('qid'), r.get('error')) for r in recs if r.get('finite') is not True or r.get('error')]
        if bad: problems.append('non-finite or error rows %d, first %s' % (len(bad), bad[:3]))
        ranks = sorted({r.get('rank') for r in recs})
        if ranks != list(range(WORLD)): problems.append('ranks %s' % ranks)
        per = {}
        for r in recs: per.setdefault(r.get('stream'), []).append(r)
        if [s for s in STREAMS if s not in per]: problems.append('streams absent from step 1: %s' % [s for s in STREAMS if s not in per])
        lines = []
        for s, rs in sorted(per.items(), key=lambda kv: str(kv[0])):
            tok = [r.get('tokens') or 0 for r in rs]; eff = [r.get('effective_tokens') or 0 for r in rs]
            loss = [r['loss'] for r in rs if isinstance(r.get('loss'), (int, float))]
            if min(tok) <= 0: problems.append('%s has a zero-token row' % s)
            if len(loss) != len(rs) or not all(math.isfinite(x) for x in loss): problems.append('%s loss missing or not finite' % s)
            lines.append('%s rows %d ranks %s tokens %d-%d effective max %d over10k %d loss %.4f-%.4f mean %.4f substituted %d' % (
                s, len(rs), sorted({r.get('rank') for r in rs}), min(tok), max(tok), max(eff), sum(bool(r.get('over_10k_tokens')) for r in rs),
                min(loss) if loss else float('nan'), max(loss) if loss else float('nan'), sum(loss) / len(loss) if loss else float('nan'),
                sum(bool(r.get('substituted_from')) for r in rs)))
        cfg = ctx.get('v.json') or {}
        print('INFO first_batch frame and pixel fields in v.json (legacy branch keeps processor defaults; admit_test checks them): %s' % json.dumps(
            {k: cfg.get(k) for k in ('b7_inputs', 'min_pixels', 'max_pixels', 'frame_count', 'frames', 'frame_layout', 'frame_markers')}, default=str)[:600])
        say('first_batch', not problems, ' | '.join(lines) if not problems else '; '.join(problems + lines))

    # G7 item 8 ground (iii): admit test on the job's own v.json
    miss = need('ADMIT.json', 'v.json')
    if miss: say('admit_test', False, 'missing ' + ','.join(miss))
    else:
        ad = load(F['ADMIT.json']); problems = []
        checks = {c.get('name'): c for c in ad.get('checks', [])}
        if ad.get('config_sha256') != sha_raw(F['v.json']): problems.append('ADMIT config_sha256 %s != v.json' % ad.get('config_sha256'))
        if ad.get('tree_sha256') != TREE: problems.append('tree %s' % ad.get('tree_sha256'))
        if ad.get('branch_taken') != 'legacy_C_prime': problems.append('branch %s' % ad.get('branch_taken'))
        if ctx.get('identity') and ad.get('identity') != ctx['identity']: problems.append('identity %s != identity.txt' % ad.get('identity'))
        for n in ADMIT_MUST_PASS:
            st = (checks.get(n) or {}).get('status')
            if st != 'PASS': problems.append('%s %s %s' % (n, st, str((checks.get(n) or {}).get('reason', ''))[:200]))
        for n, c in checks.items():
            if n in ADMIT_MUST_PASS or c.get('status') in ('PASS', 'NOT_RUN'): continue
            if n in ADMIT_PENDING and PENDING_REASON in str(c.get('reason')): continue
            problems.append('%s %s %s' % (n, c.get('status'), str(c.get('reason'))[:200]))
        na = checks.get('native_admit') or {}
        say('admit_test', not problems, ('branch legacy_C_prime; %d checks PASS incl. all %d required; native_admit %s %s; pending %s; NOT_RUN (bytes not offline) %s' % (
            sum(c.get('status') == 'PASS' for c in checks.values()), len(ADMIT_MUST_PASS), na.get('status'), str(na.get('reason'))[:100],
            [n for n, c in checks.items() if c.get('status') == 'FAIL'], [n for n, c in checks.items() if c.get('status') == 'NOT_RUN'])) if not problems else '; '.join(problems))

    # G8 admitted scene census (kit-side form of s1_exclusions:319): whole store = admitted + outside, the outside
    # rows are the proven ones, and the reference prepare compared with (s1 = a.json) holds the admitted numbers
    miss = need('s1.json', 's4.json')
    if miss: say('scene_census', False, 'missing ' + ','.join(miss))
    else:
        s1 = load(F['s1.json']); s4 = load(F['s4.json']); problems = []; summary = []
        if s4.get('schema') != 'r1-admitted-scene-census-v1': problems.append('s4 schema %s' % s4.get('schema'))
        if s1.get('exact_rebuilt_population') is not True or s1.get('population') != 'admitted' or s1.get('schema') != 'dev_s1_manifest_v1':
            problems.append('s1 exact %s population %s schema %s' % (s1.get('exact_rebuilt_population'), s1.get('population'), s1.get('schema')))
        if (s1.get('outside') or {}).get('sha256') != sha_raw(F['s4.json']): problems.append('s1 outside pin %s != s4.json' % (s1.get('outside') or {}).get('sha256'))
        if s1.get('whole_store_census') != s4.get('whole_store_census'): problems.append('s1/s4 whole_store_census pins differ')
        src = s4.get('sources') or {}; ref = s1.get('withheld_training_rows') or {}
        if set(src) != set(SCENE_WHOLE) or set(ref) != set(SCENE_WHOLE): problems.append('sources s4 %s s1 %s' % (sorted(src), sorted(ref)))
        for n in sorted(SCENE_WHOLE):
            r = src.get(n) or {}; pair = lambda d: ((d or {}).get('dev'), (d or {}).get('test'))
            w, a, o = pair(r.get('whole')), pair(r.get('admitted')), pair(r.get('outside'))
            keys = r.get('outside_listed_keys') or []
            flags = (sum(bool(k[-2]) for k in keys), sum(bool(k[-1]) for k in keys))
            rr = ref.get(n) or {}
            if None in a or None in o or w != (a[0] + o[0], a[1] + o[1]): problems.append('%s whole %s != admitted %s + outside %s' % (n, w, a, o))
            if w != SCENE_WHOLE[n] or o != SCENE_OUTSIDE[n]: problems.append('%s whole %s outside %s, proven %s %s' % (n, w, o, SCENE_WHOLE[n], SCENE_OUTSIDE[n]))
            if flags != o: problems.append('%s outside keys flag %s != outside %s' % (n, flags, o))
            if (rr.get('rows_withheld'), rr.get('benchmark_rows_withheld')) != a: problems.append('%s s1 reference %s != admitted %s' % (n, (rr.get('rows_withheld'), rr.get('benchmark_rows_withheld')), a))
            summary.append('%s %d/%d = %d/%d + %d/%d' % (n, w[0] or 0, w[1] or 0, a[0] or 0, a[1] or 0, o[0] or 0, o[1] or 0))
        say('scene_census', not problems, '; '.join(summary) if not problems else '; '.join(problems))

    ok = all(results) and len(results) == 8
    print('GATE ALL %s (%d of %d points)' % ('PASS' if ok else 'FAIL', sum(results), len(results)))
    return 0 if ok else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        import traceback; traceback.print_exc()
        print('GATE ALL FAIL (gate.py raised; see traceback; no point counts as passed)')
        sys.exit(2)
