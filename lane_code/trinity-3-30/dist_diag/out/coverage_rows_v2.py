"""dist_diag coverage rows v2 (ORCH ORDER 20261119T0351Z; Codex review V1 fixes): routed absolute-distance rows whose question uses one of the 15
dev-set templates that lost the tower call at R1 step 200 (call rate under 90%) and that no routed row of N covers.
Each row copies one bound N row (same scene, objects, frames, tool calls, responses, ground truth, trace and answer) and
rewords only its question; qid = source qid + "_dd<template>". Non-metre rows come from N's bound units slice (aa1432cd,
trace: call, printed gap, "Converting to <unit>: g x F = y", answer y); metre rows from N's bound distance slice (aedd3b54,
trace: call, printed gap, answer). 100 rows per template and unit (15 x 4 x 100 = 6,000), each source row used once,
sources chosen by lowest sha256('dist_diag|cov|' + qid) within the unit. Checks: conversion recomputed from the printed gap
(factor, ROUND_HALF_UP to 1 cm / 0.01 ft or in, unit word), native packing + the kit validator (student_pilot.ground_rows
pack/validate of N's tree) on every row and on every used source row, question/qid consistency, K1 list exclusion.
Distance rows carry no event list in N's slice; validation rebuilds it from the suffix before packing.
v2: every cell is filled to exactly 100 (a refused row is replaced by the next source) and the run fails unless all 60
cells hold 100 rows and no source is used more than once; ground_record.unit must be present and equal the question's unit;
candidate_id is recomputed with the kit's candidate_identity formula on the new qid and question (the variant that reproduces
the source's own candidate_id when one does), in the row and in ground_record, and no output id repeats a source id.
Usage: python coverage_rows.py <templates.json> <out_dir>"""
import copy, hashlib, json, re, sys, unicodedata
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
TREE = '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w18/work/tree_r1'
sys.path.insert(0, TREE)
from student_pilot import ground_rows
from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity
W = '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16b/work/build16'
SRC = {'units': '/scratch/jjyeung/n30_mirror/rows_r1/out/vehN_units/repaired/rows_slice.jsonl',
       'absolute_distance': '/scratch/jjyeung/n30_mirror/rows_r2/out/vehN_pool_abs_distance_full/repaired/rows.jsonl'}
SHA = {'units': 'aa1432cde2aa3612e0d0e287c94aaa0aeb37dc175485a3ad044bca71f3e5ce9c',
       'absolute_distance': 'aedd3b54b913fd416b8daa53f022c86d1b3d98259f3c5e1a479e8bde528449d9'}
ROUTED = re.compile(r'Measuring from the closest point of each object, what is the distance between the (.+?) and the (.+) \(in (meters|centimeters|feet|inches)\)\?')
FACTOR = {'centimeters': ('100', Decimal('1')), 'feet': ('3.28084', Decimal('0.01')), 'inches': ('39.3701', Decimal('0.01'))}
UNIT = {'meters': 'm', 'centimeters': 'cm', 'feet': 'ft', 'inches': 'in'}
PER = 100
def sha(b): return hashlib.sha256(b).hexdigest()
def normalized(text): return ' '.join(unicodedata.normalize('NFKC', str(text)).casefold().split())
def qidentity(rec, question):
    roles = rec.get('roles', {})
    objects = sorted(normalized(v) for k, value in roles.items() if k != 'parser' for v in (value if isinstance(value, list) else [value]))
    return sha(json.dumps([rec.get('scene'), rec.get('frame_indices'), normalized(question), objects], ensure_ascii=False).encode())
def gap_value(text):
    m = re.findall(r'<tool_response>\ndistance ([0-9]+\.[0-9]+) m\n</tool_response>', text)
    return m[-1] if len(m) == 1 else None
def check_units(row, unit):
    t = row['target']; g = gap_value(t)
    m = re.findall(r'Converting to (centimeters|feet|inches): ([0-9.]+) x ([0-9.]+) = ([0-9.]+)\.', t)
    if g is None or len(m) != 1: return 'no_single_gap_or_conversion'
    u, g2, f, y = m[0]
    if u != unit: return 'conversion_unit_word'
    if g2 != g: return 'conversion_not_on_printed_gap'
    if f != FACTOR[unit][0]: return 'factor'
    want = (Decimal(g) * Decimal(f)).quantize(FACTOR[unit][1], rounding=ROUND_HALF_UP)
    if Decimal(y) != want or str(row['answer']) != y or not t.endswith('<answer>' + y + '</answer>'): return 'arithmetic_or_answer'
    if row['ground_record'].get('unit') != unit: return 'record_unit_missing_or_differs'
    return None
def check_metre(row):
    t = row['suffix']; g = gap_value(t)
    if g is None: return 'no_single_gap'
    if 'Converting' in t: return 'conversion_in_metre_row'
    if str(row['answer']) != g or not t.endswith('<answer>' + g + '</answer>'): return 'answer_not_printed_gap'
    return None
REVS = ('3.14', '3.13', '3.12.2')
def cid_variant(rec):
    misses = rec.get('simulated_misses') or []
    for rev in (rec.get('spec_version'), rec.get('trace_revision')) + REVS:
        if rev and candidate_identity(dict(rec, trace_revision=rev), misses) == rec['candidate_id']: return rev
    return None
def new_cid(rec_new, rev):
    return candidate_identity(dict(rec_new, trace_revision=rev or rec_new.get('spec_version') or '3.14'), rec_new.get('simulated_misses') or [])
def validate_units(row):
    rec = dict(copy.deepcopy(row['ground_record']), suffix=row['target'])
    packed = ground_rows.pack(rec, row['provenance'])
    ground_rows.validate(packed)
    for k in ('qid', 'question', 'answer', 'gt_answer', 'target', 'tool_output_spans', 'candidate_id'):
        if packed[k] != row[k]: raise ValueError('native pack differs from slice row: ' + k)
EVENT = re.compile(r'(<(?:ground|gap)\b[^>\n]*>)\n(<tool_response>\n.*?\n</tool_response>)', re.S)
def events_from_suffix(suffix):
    return [dict(call=m.group(1), response=m.group(2)) for m in EVENT.finditer(suffix)]
def validate_distance(row):
    # The distance slice rows carry no event list; rebuild it from the suffix (the calls and their printed responses),
    # pack natively and run the kit validator, as for the units rows.
    rec = dict(copy.deepcopy(row), events=events_from_suffix(row['suffix']))
    if len(rec['events']) != 3 or [e['call'][:4] for e in rec['events']] != ['<gro', '<gro', '<gap']:
        raise ValueError('distance row is not ground, ground, gap')
    packed = ground_rows.pack(rec, row.get('provenance') or {})
    ground_rows.validate(packed)
    for k in ('qid', 'question', 'answer', 'gt_answer', 'candidate_id'):
        if packed[k] != row[k]: raise ValueError('native pack differs from slice row: ' + k)
def main():
    templates = json.load(open(sys.argv[1])); out = sys.argv[2]
    gen_sha = sha(open(__file__, 'rb').read())
    mem = json.load(open(W + '/proofs/census/membership.json'))['sources']
    k1 = set(json.loads(l)['row_key'] for l in open(W + '/inputs/s.json') if l.strip())
    rep = dict(generator_sha256=gen_sha, templates=templates, sources={}, refused=Counter(), source_validation=Counter(), out={})
    pools = defaultdict(list)
    for fam, path in SRC.items():
        data = open(path, 'rb').read()
        if sha(data) != SHA[fam]: raise SystemExit('source sha differs: ' + fam)
        bound = set(mem[fam]['rows']); n = 0
        for line in data.decode().splitlines():
            if not line.strip(): continue
            r = json.loads(line); n += 1
            if r['qid'] not in bound: rep['refused'][fam + ':not_bound'] += 1; continue
            if r['qid'] in k1: rep['refused'][fam + ':k1'] += 1; continue
            m = ROUTED.fullmatch(r['question'])
            if not m: rep['refused'][fam + ':question_not_routed_template'] += 1; continue
            a, b, unit = m.groups()
            if fam == 'absolute_distance':
                roles = r.get('roles') or {}
                if unit != 'meters' or (roles.get('a'), roles.get('b')) != (a, b): rep['refused'][fam + ':roles_or_unit'] += 1; continue
            elif unit == 'meters': rep['refused'][fam + ':metre_unit_row'] += 1; continue
            pools[UNIT[unit]].append((sha(('dist_diag|cov|' + r['qid']).encode()), fam, a, b, unit, r))
        rep['sources'][fam] = dict(path=path, sha256=SHA[fam], rows=n, bound=len(bound))
    rep['bound_split'] = {u: len(v) for u, v in pools.items()}
    rows_u, rows_d, read = [], [], []
    uses = Counter(); src_cids = set(); out_cids = set(); rep['candidate_id_rule'] = Counter()
    for u in ('m', 'ft', 'in', 'cm'):
        cand = sorted(pools[u], key=lambda x: x[0]); filled = Counter(); ptr = 0
        for h, fam, a, b, unit, r in cand:
            todo = [t for t in range(len(templates)) if filled[t] < PER]
            if not todo: break
            tid = todo[ptr % len(todo)]
            err = check_units(r, unit) if fam == 'units' else check_metre(r)
            if err: rep['refused']['source_check:' + err] += 1; continue
            try:
                (validate_units if fam == 'units' else validate_distance)(r); rep['source_validation'][fam + ':pass'] += 1
            except Exception as e:
                rep['source_validation'][fam + ':fail:' + str(e)[:60]] += 1; continue
            q = templates[tid].format(a=a, b=b, u=unit)
            if q.count(unit) != 1 or 'the ' + a not in q or 'the ' + b not in q: rep['refused']['wording'] += 1; continue
            x = copy.deepcopy(r); src_qid = r['qid']; x['qid'] = '%s_dd%02d' % (src_qid, tid); x['question'] = q
            rec_src = dict(r['ground_record'], suffix=r['target']) if fam == 'units' else r
            rev = cid_variant(rec_src); src_cids.add(r['candidate_id'])
            edit = dict(rule='dist_diag_coverage_v2', template_id=tid, template=templates[tid], before=r['question'], after=q,
                        reworded_from=src_qid, candidate_id_before=r['candidate_id'],
                        candidate_id_rule='formula_variant_' + rev if rev else 'formula_fresh_spec_version', generator_sha256=gen_sha)
            if fam == 'units':
                g = x['ground_record']; g['qid'] = x['qid']; g['question'] = q
                if 'question_identity' in g: g['question_identity'] = qidentity(g, q)
                x['candidate_id'] = g['candidate_id'] = new_cid(dict(g, suffix=x['target']), rev)
                x.setdefault('provenance', {}).setdefault('details', {})['question_edit'] = edit
            else:
                if 'question_identity' in x: x['question_identity'] = qidentity(x, q)
                x['candidate_id'] = new_cid(x, rev)
                x.setdefault('provenance', {})['dist_diag_question_edit'] = edit
            err = check_units(x, unit) if fam == 'units' else check_metre(x)
            if err: rep['refused']['row_check:' + err] += 1; continue
            if x['candidate_id'] in out_cids or x['candidate_id'] == r['candidate_id']: rep['refused']['row_candidate_id_not_new'] += 1; continue
            try: (validate_units if fam == 'units' else validate_distance)(x)
            except Exception as e: rep['refused']['row_validate:' + str(e)[:60]] += 1; continue
            (rows_u if fam == 'units' else rows_d).append(x); out_cids.add(x['candidate_id']); uses[src_qid] += 1
            filled[tid] += 1; ptr += 1; rep['candidate_id_rule'][edit['candidate_id_rule']] += 1
            rep['out'].setdefault('%02d|%s' % (tid, u), 0); rep['out']['%02d|%s' % (tid, u)] += 1
        short = {t: PER - filled[t] for t in range(len(templates)) if filled[t] < PER}
        if short: raise SystemExit('unit %s cells short: %s' % (u, short))
    if len(rows_u) + len(rows_d) != PER * len(templates) * 4: raise SystemExit('total rows differ')
    if max(uses.values()) > 1: raise SystemExit('a source is used more than once')
    if out_cids & src_cids: raise SystemExit('an output candidate_id repeats a source candidate_id')
    rep['candidate_id_rule'] = dict(rep['candidate_id_rule'])
    by = {}
    for x in rows_d: by.setdefault((int(x['qid'][-2:]), 'm'), x)
    for x in rows_u: by.setdefault((int(x['qid'][-2:]), UNIT[x['ground_record'].get('unit') or re.search(r'Converting to (\w+):', x['target']).group(1)]), x)
    for tid in range(len(templates)):
        for u in (('m', 'in') if tid % 2 == 0 else ('ft', 'cm')):
            x = by.get((tid, u))
            if x is None: continue
            t = x['target'] if 'target' in x else x['suffix']
            read.append('%s | %s\n  Q: %s\n  T: %s' % (x['qid'], u, x['question'], re.sub(r'<tool_response>\n(.*?)\n.*?</tool_response>', lambda mm: '<resp ' + mm.group(1)[:50] + '>', t, flags=re.S).replace('\n', ' / ')))
    qids = [r['qid'] for r in rows_u + rows_d]
    if len(set(qids)) != len(qids): raise SystemExit('duplicate qid')
    srcs = Counter(re.sub(r'_dd\d\d$', '', q) for q in qids)
    rep['max_rewordings_per_source'] = max(srcs.values()) if srcs else 0
    import os; os.makedirs(out, exist_ok=True)
    for name, rows in (('COVERAGE_UNITS_V2.jsonl', rows_u), ('COVERAGE_DISTANCE_V2.jsonl', rows_d)):
        blob = ''.join(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for r in rows).encode()
        open(out + '/' + name, 'wb').write(blob); rep['out'][name] = dict(rows=len(rows), bytes=len(blob), sha256=sha(blob))
    rep['refused'] = dict(rep['refused']); rep['source_validation'] = dict(rep['source_validation'])
    json.dump(rep, open(out + '/SUMMARY.json', 'w'), indent=1, sort_keys=True)
    open(out + '/READ30.txt', 'w').write('\n'.join(read[:30]) + '\n')
    print(json.dumps({k: rep[k] for k in ('bound_split', 'refused', 'source_validation', 'max_rewordings_per_source', 'candidate_id_rule')}, indent=1))
    print(json.dumps({k: v for k, v in rep['out'].items() if k.endswith('.jsonl')}, indent=1))
if __name__ == '__main__': main()
