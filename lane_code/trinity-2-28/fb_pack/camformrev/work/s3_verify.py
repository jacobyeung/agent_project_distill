"""Independent checks 2-5, 7, 9 over compose/<name>_{A_absent,C_absent,C_on}."""
from pathlib import Path
import sys, json, sqlite3, hashlib, re, random
from collections import Counter, defaultdict
W = Path(__file__).resolve().parent
RO = W.parents[1]/'ro/orch_n30'
CAM = RO/'fb_pack/cam/out'
sys.path.insert(0, str(W/'tree_C')); sys.dont_write_bytecode = True
import torch; torch.set_num_threads(8)
from student_pilot.carrier_c1_routing import render
from student_pilot.p3_provenance import digest
sha = lambda b: hashlib.sha256(b).hexdigest()
OUT = {}
TYPES = ('camera_rotation', 'camera_movement_direction')
# Spec strings of the two rules (fbp_cam REPORT / common.py literals).
ROT_FROM = 'wrapped to (-180, 180], with positive turn meaning left and a half turn reported as +180 degrees.'
ROT_TO = 'wrapped to the shortest signed turn, with positive turn meaning left and a half turn reported as positive.'
DIR_HEAD = 'Scoring each option by the matching component: '

def my_dir(text):
    """Own implementation: drop the numeric restatement after each negated component."""
    if not text.startswith(DIR_HEAD) or not text.endswith('.'):
        return text, 0
    items = text[len(DIR_HEAD):-1].split('; ')
    out, n = [], 0
    for it in items:
        parts = it.split(' = ')
        if len(parts) == 3 and parts[1] in ('-dx', '-dy', '-dz') and parts[2].endswith(' m'):
            float(parts[2][:-2]); out.append(parts[0]+' = '+parts[1]); n += 1
        else:
            out.append(it)
    return DIR_HEAD+'; '.join(out)+'.', n

def my_rewrite(text):
    rules = []
    if ROT_FROM in text:
        text = text.replace(ROT_FROM, ROT_TO); rules.append('ROT')
    text, n = my_dir(text)
    if n: rules.append('DIR')
    return text, rules

def rows_of(path):
    c = sqlite3.connect('file:'+str(path)+'?mode=ro', uri=True)
    try:
        return [(i, json.loads(r), t) for i, r, t in c.execute('SELECT i,row,target FROM rows ORDER BY i')]
    finally:
        c.close()

def diff(a, b, path=''):
    if type(a) != type(b):
        return [path]
    if isinstance(a, dict):
        out = []
        for k in set(a) | set(b):
            if k not in a or k not in b: out.append(path+'/'+k)
            else: out += diff(a[k], b[k], path+'/'+k)
        return out
    if isinstance(a, list):
        if len(a) != len(b): return [path+'#len']
        out = []
        for i, (x, y) in enumerate(zip(a, b)): out += diff(x, y, path+'/'+str(i))
        return out
    return [] if a == b else [path]

ALLOWED = re.compile(r'^(/target|/routing/events/\d+/text|/routing/tool_output_spans/\d+/(start|end)|/tool_output_spans/\d+/(start|end))$')

def verify(name):
    R = dict()
    d = W/'compose'
    A, Cabs, Con = d/(name+'_A_absent'), d/(name+'_C_absent'), d/(name+'_C_on')
    # (2) absent field: byte identity at the same output path.
    R['absent_bytes'] = {f: (sha((A/f).read_bytes()), sha((Cabs/f).read_bytes()), sha((A/f).read_bytes()) == sha((Cabs/f).read_bytes()))
                         for f in ('rows.sqlite', 'membership.json', 'receipt.json')}
    ra, rc = json.loads((A/'receipt.json').read_text()), json.loads((Con/'receipt.json').read_text())
    R['receipt_other_fields_equal'] = {k: ra.get(k) == rc.get(k) for k in set(ra) | set(rc) if k not in ('database', 'source_membership', 'camera_trace_form')}
    R['membership_bytes_equal_on'] = (A/'membership.json').read_bytes() == (Con/'membership.json').read_bytes()
    R['receipt_camera_trace_form'] = rc.get('camera_trace_form')
    # Filters judged the unrewritten row in the enabled run.
    base = json.loads((d/(name+'_base.json')).read_text())
    src = {r['qid']: digest(r) for _, r, _ in rows_of(Path(base['database']['path']))}
    seen = json.loads(Path(str(Con)+'.filters_seen.json').read_text())
    R['filters_saw_source_rows'] = (len(seen), sum(src[q] == h for q, h in seen.items()))
    old, new = rows_of(A/'rows.sqlite'), rows_of(Con/'rows.sqlite')
    assert [i for i, _, _ in old] == [i for i, _, _ in new]
    viol, changed_rows, changed_lines, lines_by_rule, rule_mismatch = [], Counter(), Counter(), Counter(), []
    unchanged = Counter(); types = Counter(); offset_bad = []; ids_by_row = {}
    for (i, a, ta), (_, b, tb) in zip(old, new):
        typ = (a.get('routing') or {}).get('question_type') or a.get('question_type') or a.get('type')
        types[typ] += 1
        if ta != tb: viol.append((a['qid'], 'target_column'))
        paths = diff(a, b)
        if not paths:
            unchanged[typ] += 1
            # A row the rules would have touched must not stay unchanged.
            if typ in TYPES and any(my_rewrite(e.get('text', ''))[1] for e in a['routing']['events'] if e['kind'] in ('plan', 'canonical_text')):
                viol.append((a['qid'], 'unrewritten_match'))
            continue
        changed_rows[typ] += 1
        if typ not in TYPES: viol.append((a['qid'], 'non_camera_change:'+typ)); continue
        bad = [p for p in paths if not ALLOWED.match(p)]
        if bad: viol.append((a['qid'], 'path', bad)); continue
        ev_a, ev_b = a['routing']['events'], b['routing']['events']
        row_rules = set()
        for k, (x, y) in enumerate(zip(ev_a, ev_b)):
            if x != y:
                if x['kind'] not in ('plan', 'canonical_text'): viol.append((a['qid'], 'event_kind', x['kind']))
                exp, rules = my_rewrite(x['text'])
                if exp != y['text'] or not rules: rule_mismatch.append(a['qid'])
                row_rules.update(rules)
            elif x['kind'] in ('plan', 'canonical_text') and my_rewrite(x['text'])[1]:
                rule_mismatch.append(a['qid'])
        ids_by_row[a['qid']] = sorted(row_rules)
        # Lines.
        la, lb = a['target'].split('\n'), b['target'].split('\n')
        if len(la) != len(lb): viol.append((a['qid'], 'line_count')); continue
        for x, y in zip(la, lb):
            if x != y:
                changed_lines[typ] += 1
                rule = 'ROT' if ROT_FROM in x else 'DIR' if x.startswith(DIR_HEAD) else 'OTHER'
                lines_by_rule[(typ, rule)] += 1
                if my_rewrite(x)[0] != y: rule_mismatch.append(a['qid'])
        # Calls, responses, values, answers, GT, question/options/frames.
        for key in ('answer', 'gt_answer', 'gt_pose9', 'gt_up', 'canonical', 'physical_group', 'source_row_sha256', 'qid'):
            if a['routing'].get(key) != b['routing'].get(key): viol.append((a['qid'], key))
        if a['student_input'] != b['student_input'] or a['qid'] != b['qid']: viol.append((a['qid'], 'student_input'))
        if a['target'].rsplit('</think>', 1)[1] != b['target'].rsplit('</think>', 1)[1]: viol.append((a['qid'], 'answer_suffix'))
        if [e for e in ev_a if e['kind'] not in ('plan', 'canonical_text')] != [e for e in ev_b if e['kind'] not in ('plan', 'canonical_text')]:
            viol.append((a['qid'], 'non_prose_event'))
        # Offsets: stored spans equal a fresh render and slice the identical response bytes.
        rt, rs = render(ev_b, b['routing']['answer'])
        spans = b['routing']['tool_output_spans']
        ok = rt == b['target'] and [(s['start'], s['end'], s['call_id']) for s in spans] == [(s['start'], s['end'], s['call_id']) for s in rs]
        for sa, sb in zip(a['routing']['tool_output_spans'], spans, strict=True):
            ev = ev_b[sb['event_index']]
            ok &= b['target'][sb['start']:sb['end']] == a['target'][sa['start']:sa['end']] == '<tool_response>'+ev['text']+'</tool_response>'
            ok &= ev['kind'] == 'tool_response' and ev['call_id'] == sb['call_id']
        if 'tool_output_spans' in b: ok &= b['tool_output_spans'] == spans
        if not ok: offset_bad.append(a['qid'])
    R.update(types=types, changed_rows=changed_rows, unchanged_rows=unchanged, changed_lines_by_type=changed_lines,
             changed_lines_by_type_rule={f'{t}|{r}': n for (t, r), n in lines_by_rule.items()},
             rows_by_rule=Counter(r for v in ids_by_row.values() for r in v),
             violations=viol[:50], violation_count=len(viol), rule_mismatch=sorted(set(rule_mismatch))[:50],
             offset_bad=offset_bad[:50], offset_checked=sum(changed_rows[t] for t in TYPES))
    return R, new

R, new = verify('extract'); OUT['extract'] = R
R2, new2 = verify('mixed2'); OUT['mixed2'] = R2
# (4) Counterparts in fbp_cam rows for the same source ids.
forms = json.loads((CAM/'SOURCE_FORMS.json').read_text())
assert sha((CAM/'rows/camera_wording.jsonl').read_bytes()).startswith('e8cbda99')
mapping = {r['source_qid']: r['training_qid'] for r in forms['records']}
peers = {}
with (CAM/'rows/camera_wording.jsonl').open() as f:
    for line in f:
        r = json.loads(line); peers[r['qid']] = r
match, mism, missing = Counter(), [], []
for _, b, _ in new:
    typ = b['routing']['question_type']; p = peers.get(mapping[b['qid']])
    if p is None: missing.append(b); continue
    same = (p['target'] == b['target'] and p['routing']['tool_output_spans'] == b['routing']['tool_output_spans']
            and [e.get('text') for e in p['routing']['events']] == [e.get('text') for e in b['routing']['events']]
            and p['routing']['answer'] == b['routing']['answer'] and p['routing']['gt_answer'] == b['routing']['gt_answer'])
    if same: match[typ] += 1
    else: mism.append(b['qid'])
random.seed(20261119)
pick = random.sample([b['qid'] for _, b, _ in new if mapping[b['qid']] in peers and b['routing']['question_type'] in TYPES], 300)
OUT['counterparts'] = dict(matched_by_type=match, mismatched=mism[:50], mismatched_count=len(mism), missing=len(missing),
                           sample300_all_match=all(q not in mism for q in pick), sample300_first5=pick[:5])
# 21 rows without counterpart: rules satisfied, no residual old forms, shared grammar passes.
from student_pilot.r2_adapters import normalize
from student_pilot.r2_grammar import legacy_program, shared
def shared_errors(raw):
    row = normalize(raw); target, _ = legacy_program(row)
    body = re.search(r'<think>(.*?)</think>', target, re.S).group(1)
    body = re.sub(r'Call: measure ', 'I will measure ', body)
    for e in row['events']:
        if e['kind'] in ('ground_call', 'tool_call', 'calculator_call'): body = body.replace(e['token'].strip(), '<call>')
    return shared.validate_trace(body, form='program', question=row['question'], n_frames=len(row['student_input']['frames']))
resid = re.compile(r'\(-180, 180\]|reported as \+180|-d[xyz] = [+-]?\d')
miss = []
for b in missing:
    txt = b['target'].split('</think>')[0]
    miss.append(dict(qid=b['qid'], expected=mapping[b['qid']], type=b['routing']['question_type'],
                     residual_old_form=bool(resid.search(txt)), grammar_errors=[str(e) for e in shared_errors(b)][:3]))
OUT['missing21'] = miss
# Grammar over all rewritten extract rows (superset sanity check).
gram = Counter()
for _, b, _ in new:
    t = b['routing']['question_type']
    gram[(t, 'pass' if not shared_errors(b) else 'fail')] += 1
OUT['grammar_extract'] = {f'{t}|{s}': n for (t, s), n in gram.items()}
# Residual old forms after enabling, per source.
for nm, rows in (('extract', new), ('mixed2', new2)):
    res = Counter()
    for _, b, _ in rows:
        t = (b.get('routing') or {}).get('question_type')
        if t in TYPES and resid.search(b['target'].split('</think>')[0]): res[t] += 1
    OUT[nm+'_residual_old_forms'] = res
# (9) shortcut probes on direction/rotation rows.
lab = Counter(); opts_rot = Counter(); hidden_winner = Counter(); letters = Counter()
for _, b, _ in new:
    t = b['routing']['question_type']
    if t == 'camera_rotation': opts_rot[len(b['student_input'].get('options') or [])] += 1
    if t == 'camera_movement_direction':
        ans = b['routing']['answer']; opt = {o.split('.', 1)[0]: o.split('.', 1)[1].strip().lower() for o in b['student_input']['options']}
        win = opt[ans]; letters[ans] += 1
        line = next(e['text'] for e in b['routing']['events'] if e['kind'] == 'canonical_text' and e['text'].startswith(DIR_HEAD))
        shown = {it.split(' = ')[0] for it in line[len(DIR_HEAD):-1].split('; ') if len(it.split(' = ')) == 3}
        hidden_winner['hidden' if win not in shown else 'shown'] += 1
        lab[(win in ('left', 'backward', 'down'), win not in shown)] += 1
OUT['shortcut'] = dict(rotation_option_counts=opts_rot, direction_answer_letters=letters, direction_winner_number=hidden_winner,
                       winner_negated_vs_hidden={str(k): v for k, v in lab.items()})
(W/'S3_VERIFY.json').write_text(json.dumps(OUT, indent=1, default=lambda o: dict(o) if isinstance(o, Counter) else str(o)))
print(json.dumps(OUT, indent=1, default=lambda o: dict(o) if isinstance(o, Counter) else str(o))[:12000])
