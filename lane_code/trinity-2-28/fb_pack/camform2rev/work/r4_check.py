"""Independent checks of the declaration-mode compositions built by r3_all.sh.

Absent-field byte identity, path-level diff of every row, own rule implementation, recounts per type/rule/line,
offsets, receipt agreement, counterpart targets, Filters input, non-camera rows.
"""
from pathlib import Path
import sys, json, hashlib, sqlite3, ast
from collections import Counter
W = Path(__file__).resolve().parent
RO = W.parents[1]/'ro/orch_n30'; CAM = RO/'fb_pack/cam/out'; D = W/'compose'
sys.path.insert(0, str(W/'tree_C')); sys.dont_write_bytecode = True
from student_pilot.carrier_c1_routing import render
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
src = (RO/'fb_pack/cam/work/common.py').read_text()
assert hashlib.sha256(src.encode()).hexdigest() == '4535d0f1371268cd3590b477eea75f806c0156ff5b58b824261ee352b7d01712'
consts = {t.targets[0].id: t.value.value for t in ast.parse(src).body
          if isinstance(t, ast.Assign) and isinstance(t.targets[0], ast.Name) and isinstance(t.value, ast.Constant)}
ROT_OLD, ROT_NEW = consts['ROT_OLD'], consts['ROT_NEW']
PREFIX = 'Scoring each option by the matching component:'
TYPES = ('camera_rotation', 'camera_movement_direction')

def strip_neg(s):
    """Delete ' = <signed number> m' after -dx/-dy/-dz when followed by ';' or '.' (plain string scan)."""
    out, i, n = [], 0, 0
    while i < len(s):
        hit = next((t for t in ('-dx', '-dy', '-dz') if s.startswith(t, i)), None)
        if hit and s.startswith(' = ', i+3):
            j = i+6
            if j < len(s) and s[j] in '+-': j += 1
            k = j
            while k < len(s) and s[k].isdigit(): k += 1
            ok = k > j
            if ok and k < len(s) and s[k] == '.' and k+1 < len(s) and s[k+1].isdigit():
                k += 1
                while k < len(s) and s[k].isdigit(): k += 1
            if ok and s.startswith(' m', k) and k+2 < len(s) and s[k+2] in ';.':
                out.append(hit); i = k+2; n += 1; continue
        out.append(s[i]); i += 1
    return ''.join(out), n

def mine(text):
    rules = []
    if ROT_OLD in text: text = text.replace(ROT_OLD, ROT_NEW); rules.append('CAM-ROT-WORDS-v1')
    if text.startswith(PREFIX):
        text, n = strip_neg(text)
        if n: rules.append('CAM-DIR-SYMBOL-v1')
    return text, rules

def diff(a, b, path=''):
    if type(a) != type(b): return [path]
    if isinstance(a, dict):
        out = []
        for k in set(a) | set(b):
            if k not in a or k not in b: out.append(path+'/'+k)
            else: out += diff(a[k], b[k], path+'/'+k)
        return out
    if isinstance(a, list):
        if len(a) != len(b): return [path+'#len']
        return [p for i, (x, y) in enumerate(zip(a, b)) for p in diff(x, y, path+'/'+str(i))]
    return [] if a == b else [path]

def rows(p):
    c = sqlite3.connect('file:'+str(p/'rows.sqlite')+'?mode=ro', uri=True)
    try: return [(i, json.loads(r), t) for i, r, t in c.execute('SELECT i,row,target FROM rows ORDER BY i')]
    finally: c.close()

forms = json.loads((CAM/'SOURCE_FORMS.json').read_text()); peer = {r['source_qid']: r['training_qid'] for r in forms['records']}
report = {}
for X, Y in (('A', 'C'), ('A2', 'C2')):
    for K in ('prod', 'mixed'):
        r = {}
        xa, ya, yo = D/f'{X}_{K}_absent', D/f'{Y}_{K}_absent', D/f'{Y}_{K}_on'
        r['absent_bytes_identical'] = {f: sha(xa/f) == sha(ya/f) for f in ('rows.sqlite', 'membership.json', 'receipt.json')}
        r['absent_sha256'] = {f: sha(ya/f)[:16] for f in ('rows.sqlite', 'membership.json', 'receipt.json')}
        r['filters_input_identical_absent_vs_on'] = (D/f'{X}_{K}_absent.filters.json').read_bytes() == (D/f'{Y}_{K}_on.filters.json').read_bytes()
        old, new = rows(ya), rows(yo)
        assert [x[0] for x in old] == [x[0] for x in new]
        r['rows'] = len(new)
        r['target_column_identical'] = sum(a[2] == b[2] for a, b in zip(old, new))
        viol, other = Counter(), Counter()
        rows_by_type, unchanged_by_type, rule_rows, tl_type, el_type, rule_lines = Counter(), Counter(), Counter(), Counter(), Counter(), Counter()
        render_ok = spans_ok = mine_ok = residual = 0; slice_same = slice_n = 0; tl_ne_el = 0
        targets_on = {b['qid']: b['target'] for _, b, _ in new}; targets_off = {a['qid']: a['target'] for _, a, _ in old}
        pairs = pairs_on = pairs_off = 0
        for (_, a, _), (_, b, _) in zip(old, new):
            assert a['qid'] == b['qid']
            qt = a.get('routing', {}).get('question_type')
            if 'r1_source' in a:
                slice_n += 1; slice_same += a == b; continue
            paths = diff(a, b)
            if not paths:
                unchanged_by_type[qt] += 1
                if qt in TYPES:
                    exp = [mine(e['text'])[0] == e['text'] for e in a['routing']['events'] if e['kind'] in ('plan', 'canonical_text')]
                    mine_ok += all(exp)
                continue
            rows_by_type[qt] += 1
            for p in paths:
                parts = p.split('/')
                okp = (p == '/target' or
                       (qt in TYPES and len(parts) == 5 and parts[1:3] == ['routing', 'events'] and parts[4] == 'text'
                        and a['routing']['events'][int(parts[3])]['kind'] in ('plan', 'canonical_text')) or
                       (len(parts) == 5 and parts[1:3] == ['routing', 'tool_output_spans'] and parts[4] in ('start', 'end')) or
                       (len(parts) == 4 and parts[1] == 'tool_output_spans' and parts[3] in ('start', 'end')))
                if not okp: viol[p] += 1
            rules_here = set(); good = True
            for ea, eb in zip(a['routing']['events'], b['routing']['events'], strict=True):
                if ea['kind'] not in ('plan', 'canonical_text'): continue
                exp, rl = mine(ea['text']); good &= exp == eb['text']; rules_here |= set(rl)
                residual += ROT_OLD in eb['text'] or (eb['text'].startswith(PREFIX) and strip_neg(eb['text'])[1] > 0)
                for la, lb in zip(ea['text'].splitlines(), eb['text'].splitlines(), strict=True):
                    if la != lb:
                        el_type[qt] += 1
                        if ROT_OLD in la: rule_lines['CAM-ROT-WORDS-v1'] += 1
                        if ea['text'].startswith(PREFIX) and strip_neg(la)[1]: rule_lines['CAM-DIR-SYMBOL-v1'] += 1
            mine_ok += good
            for x in rules_here: rule_rows[x] += 1
            tl = sum(u != v for u, v in zip(a['target'].split('\n'), b['target'].split('\n'), strict=True)); tl_type[qt] += tl
            t, sp = render(b['routing']['events'], b['routing']['answer']); render_ok += t == b['target']
            st = b['routing']['tool_output_spans']
            ok = ([(s['start'], s['end'], s['call_id']) for s in st] == [(s['start'], s['end'], s['call_id']) for s in sp]
                  and all(a['target'][x['start']:x['end']] == b['target'][y['start']:y['end']] for x, y in zip(a['routing']['tool_output_spans'], st, strict=True))
                  and ('tool_output_spans' not in b or b['tool_output_spans'] == st))
            spans_ok += ok
            if K == 'prod' and peer.get(a['qid']) in targets_on:
                pairs += 1; pairs_on += b['target'] == targets_on[peer[a['qid']]]; pairs_off += a['target'] == targets_off[peer[a['qid']]]
        if K == 'prod':  # pairs for unchanged rows (displacement) as well
            for (_, a, _), (_, b, _) in zip(old, new):
                if 'r1_source' not in a and not diff(a, b) and peer.get(a['qid']) in targets_on:
                    pairs += 1; pairs_on += b['target'] == targets_on[peer[a['qid']]]; pairs_off += a['target'] == targets_off[peer[a['qid']]]
        changed = sum(rows_by_type.values())
        rec = json.loads((yo/'receipt.json').read_text())['camera_trace_form']
        r.update(slice_rows=slice_n, slice_rows_identical=slice_same, changed_rows_by_type=dict(rows_by_type), unchanged_base_by_type=dict(unchanged_by_type),
                 path_violations=dict(viol), my_rule_matches=mine_ok, my_rule_checked=changed + sum(unchanged_by_type[t] for t in TYPES),
                 residual_old_form=residual, rows_by_rule=dict(rule_rows), event_lines_by_type=dict(el_type), target_lines_by_type=dict(tl_type),
                 lines_by_rule=dict(rule_lines), render_ok=render_ok, spans_ok=spans_ok, changed_rows=changed,
                 receipt_agrees=dict(rows_by_type=rec['rewritten_base_rows_by_type'] == {t: rows_by_type[t] for t in TYPES},
                                     rows_by_rule=rec['rewritten_base_rows_by_rule'] == {k: rule_rows[k] for k in rec['rewritten_base_rows_by_rule']},
                                     lines_by_type=rec['changed_base_lines_by_type'] == {t: tl_type[t] for t in TYPES},
                                     lines_by_rule=rec['changed_base_lines_by_rule'] == {k: rule_lines[k] for k in rec['changed_base_lines_by_rule']},
                                     totals=(rec['rewritten_base_rows'], rec['changed_base_lines']) == (changed, sum(tl_type.values())),
                                     admitted=rec['admitted_base_rows_by_type'] == {t: rows_by_type[t] + unchanged_by_type[t] for t in TYPES}),
                 receipt_counts=dict(rows=rec['rewritten_base_rows_by_type'], lines=rec['changed_base_lines_by_type'], lines_by_rule=rec['changed_base_lines_by_rule']))
        if K == 'prod': r.update(base_slice_pairs=pairs, pairs_same_target_on=pairs_on, pairs_same_target_absent=pairs_off)
        report[f'{Y}_{K}'] = r
for K in ('prod', 'mixed'):
    report[f'C_vs_C2_{K}_on_rows_sqlite_identical'] = sha(D/f'C_{K}_on/rows.sqlite') == sha(D/f'C2_{K}_on/rows.sqlite')
    report[f'A_vs_A2_{K}_absent_rows_sqlite_identical'] = sha(D/f'A_{K}_absent/rows.sqlite') == sha(D/f'A2_{K}_absent/rows.sqlite')
report['builder_absent_rows_sqlite_sha'] = 'a4c2da6e58201cc3'
(W/'R4_CHECK.json').write_text(json.dumps(report, indent=1)); print(json.dumps(report, indent=1))
