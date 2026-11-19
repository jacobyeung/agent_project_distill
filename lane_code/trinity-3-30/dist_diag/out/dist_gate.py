"""Distance call-rate gate (dist_diag, proposed 2026-11-19) for a routed dev-S1 read of leg R1, paired with step 544.

Reads the 150 dev-S1 absolute-distance items of a routed return (tower arm, candidates_argmax) through cont_ops'
score_r5.load (same identity checks), and step 544's read 171253/1 as the baseline. Prints call counts by asked unit,
the room-bootstrap call rate (10,000 draws, seed 17, 46 rooms), the trace forms, and the gate verdict:
  --rule n (vehicle N, at its entry boundary + 200): PASS when at least 143 of 150 items draw a tower call and every
  asked unit reaches 90% (m >= 39/43, ft >= 42/46, in >= 30/33, cm >= 26/28); otherwise FAIL (the coverage family is rebuilt).
  --rule p (vehicle P, steps 400 and 600): the same numbers, printed as PRINTED; P cannot take the fix, so nothing is decided.
  With --coverage COVERAGE.json the counts are also split into the 15 coverage wordings and the 6 others.
Usage (python 3.8+, numpy; run from anywhere):
  python dist_gate.py --score-dir <dir holding score_r5.py, A/, bases/> --ret <return root> --package <package dir> --step 400 --rule p|n [--coverage COVERAGE.json] [--out GATE.json]
  python dist_gate.py --score-dir ... --self-test [--coverage COVERAGE.json]   (baseline 544: PASS 149/150; step 200 A4: FAIL 88/150)
"""
import argparse, json, re, sys
from collections import Counter
from pathlib import Path
UNITS = {1.: 'm', 100.: 'cm', 1/.3048: 'ft', 1/.0254: 'in', 1000.: 'mm'}
CONV = re.compile(r'(?i)(convert\w*|\b(?:x|\*|×)\s*(?:3\.28\d*|39\.3\d*|100|0\.3048|0\.0254|12)\b|/\s*(?:0\.3048|0\.0254)\b)')
NUMU = re.compile(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)\s*(?:m\b|meters?|metres?|cm|centimet\w*|feet|foot|ft\b|inch\w*|in\b)')
REL = [re.compile(p) for p in (r'candidates ordered nearest to farthest', r'nearest-to-farthest order from', r'from nearest to farthest from',
                               r'[Tt]he question asks (?:for the closest|me to choose)', r'Step 1: find the [^,\n]{1,40}, first seen in frame \d+')]
def form(sc, out):
    rs = sc.records(out); t = out.get('text', ''); th = re.sub(r'<tool_response>.*?</tool_response>', '', t.split('</think>', 1)[0], flags=re.S)
    if out.get('finish') in ('max_calls', 'max_new_tokens', 'length') or not t.strip(): return 'other'
    if rs:
        post = re.sub(r'<tool_response>.*?</tool_response>', '', t[t.rfind('</tool_response>'):], flags=re.S)
        return 'call_convert_answer' if CONV.search(post) else 'call_answer'
    if NUMU.search(th) or re.search(r'\d', re.sub(r'frame \d+|Step \d+', '', th)): return 'nocall_estimate'
    return 'nocall_qualitative'
def summarize(S, rows, items, keys, cov=None):
    sc = S.scorers; by = Counter(); tot = Counter(); forms = Counter(); rel = 0; wc = Counter(); wt = Counter()
    for k in keys:
        u = UNITS[sc.unit_factor(items[k]['question'])]; tot[u] += 1
        out = rows[k]['output']; c = bool(sc.records(out)); by[u] += c; f = form(sc, out); forms[f] += 1
        if not c and any(p.search(out.get('text', '')) for p in REL): rel += 1
        if cov:
            g = 'coverage_wordings' if cov['item_template'].get(k) in cov['named'] else 'other_wordings'; wt[g] += 1; wc[g] += c
    called = sum(by.values()); nm = sum(by[u] for u in tot if u != 'm'); nmt = sum(tot[u] for u in tot if u != 'm')
    boot = S.bootstrap([(items[k]['room_key'], int(bool(sc.records(rows[k]['output'])))) for k in keys])
    return dict(items=len(keys), called=called, metre=[by['m'], tot['m']], non_metre=[nm, nmt],
                by_unit={u: [by[u], tot[u]] for u in ('m', 'ft', 'in', 'cm') if tot[u]}, forms=dict(forms),
                nocall_with_reldistance_phrasing=rel, call_rate_room_bootstrap=dict(value=boot['value'], ci95=boot['ci95'], rooms=boot['rooms']),
                by_wording_group={g: [wc[g], wt[g]] for g in wt})
FLOOR = {'m': 39, 'ft': 42, 'in': 30, 'cm': 26}   # 90% of 43 / 46 / 33 / 28
def verdict(s, rule='n'):
    a = s['called'] >= 143; units = {u: s['by_unit'].get(u, [0, 0])[0] >= f for u, f in FLOOR.items()}
    ok = a and all(units.values()) and s['items'] == 150
    return dict(rule=rule, at_least_143_of_150=a, every_unit_90=units, verdict=('PASS' if ok else 'FAIL') if rule == 'n' else 'PRINTED (%s on the N rule)' % ('pass' if ok else 'fail'))
def main():
    p = argparse.ArgumentParser(); p.add_argument('--score-dir', required=True); p.add_argument('--ret'); p.add_argument('--package')
    p.add_argument('--step', type=int); p.add_argument('--out'); p.add_argument('--self-test', action='store_true')
    p.add_argument('--rule', choices=('n', 'p'), default='n'); p.add_argument('--coverage'); a = p.parse_args()
    cov = json.load(open(a.coverage)) if a.coverage else None
    sys.argv = ['x']; sys.path.insert(0, str(Path(a.score_dir).resolve())); import score_r5 as S
    bd, items, _, _ = S.load(S.BASE / 'b1/work/ret', S.BASE / 'b1', 1, 544, 'candidates_argmax')
    keys = sorted(k for k, i in items.items() if i['question_type'] == S.DISTANCE and k in bd)
    base = summarize(S, bd, items, keys, cov); res = dict(baseline_544=base, baseline_verdict=verdict(base, 'n'))
    if a.self_test:
        cur, _, _, _ = S.load(S.O.parent / 'out3/A4/ret', S.O / 'A', 0, 200, 'candidates_argmax'); step = 200
    else:
        cur, _, _, _ = S.load(Path(a.ret), Path(a.package), 0, a.step, 'candidates_argmax'); step = a.step
    missing = [k for k in keys if k not in cur]
    if missing: raise SystemExit('incomplete read: %d of 150 distance items missing' % len(missing))
    s = summarize(S, cur, items, keys, cov); res.update(step=step, current=s, gate=verdict(s, a.rule))
    print(json.dumps(res, indent=1))
    if a.out: Path(a.out).write_text(json.dumps(res, indent=1) + '\n')
if __name__ == '__main__': main()
