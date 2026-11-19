"""Independent check of coverage rows v1 against their 6,000 source rows (diff of every field), conversion recomputation,
template wording, qid lineage, and the kit validator from the mirrored tree (ops_mirror tr10_b17_core)."""
import gzip, json, re, sys, copy, hashlib
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
R = '/scratch/jjyeung/orch_n30/dist_diag/review_cov2/'
sys.path.insert(0, R + 'tree/work/tree_r1')
from student_pilot import ground_rows
from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity
cids = Counter(); srccids = set()
SPEC = json.load(open(R + 'pub/TEMPLATES_V2H.json')); T = SPEC['train_dev'] + SPEC['new']
def _rx(t): return re.compile('^' + re.escape(t).replace(re.escape('{a}'), '(.+)').replace(re.escape('{b}'), '(.+)').replace(re.escape('{u}'), '(meters|centimeters|feet|inches)') + '$')
HELD = [_rx(t) for t in SPEC['held_out']]
src = {}
for l in gzip.open(R + 'sources/COVERAGE_SOURCES_V2H.jsonl.gz', 'rt'):
    r = json.loads(l); src[r['qid']] = r
ROUTED = re.compile(r'Measuring from the closest point of each object, what is the distance between the (.+?) and the (.+) \(in (meters|centimeters|feet|inches)\)\?')
F = {'centimeters': ('100', Decimal('1')), 'feet': ('3.28084', Decimal('0.01')), 'inches': ('39.3701', Decimal('0.01'))}
EV = re.compile(r'(<(?:ground|gap)\b[^>\n]*>)\n(<tool_response>\n.*?\n</tool_response>)', re.S)
c = Counter(); diffs = Counter(); per = Counter(); srcuse = Counter()
def strip(d, keys):
    d = copy.deepcopy(d)
    for k in keys: d.pop(k, None)
    return d
for name in ('COVERAGE_UNITS_V2H.jsonl.gz', 'COVERAGE_DISTANCE_V2H.jsonl.gz'):
    for l in gzip.open(R + 'pub/' + name, 'rt'):
        x = json.loads(l); c['rows'] += 1
        m = re.fullmatch(r'(.+)_dh(\d\d)', x['qid']); s = src.get(m.group(1)) if m else None
        if s is None: c['no_source'] += 1; continue
        srcuse[m.group(1)] += 1; tid = int(m.group(2))
        a, b, unit = ROUTED.fullmatch(s['question']).groups()
        if x['question'] != T[tid].format(a=a, b=b, u=unit): c['wording_mismatch'] += 1
        per['%02d|%s' % (tid, unit)] += 1
        if any(h.match(x['question']) for h in HELD): c['held_out_wording_in_row'] += 1
        units = 'ground_record' in x
        # every field equals the source except the edited ones
        if units:
            allowed = {'qid', 'question', 'provenance', 'candidate_id'}
            if strip(x, allowed | {'ground_record'}) != strip(s, allowed | {'ground_record'}): diffs['top_level_other'] += 1
            gx, gs = x['ground_record'], s['ground_record']
            if strip(gx, {'qid', 'question', 'question_identity', 'candidate_id'}) != strip(gs, {'qid', 'question', 'question_identity', 'candidate_id'}): diffs['ground_record_other'] += 1
            if gx.get('unit') != unit: diffs['ground_record_unit'] += 1
            if gx['candidate_id'] != x['candidate_id']: diffs['cid_row_vs_record'] += 1
            if gx['qid'] != x['qid'] or gx['question'] != x['question']: diffs['ground_record_qid_question'] += 1
            px = copy.deepcopy(x['provenance']); e = px.get('details', {}).pop('question_edit', None)
            if px != s['provenance'] or not e or e['before'] != s['question'] or e['after'] != x['question'] or e['reworded_from'] != s['qid']: diffs['provenance'] += 1
            t = x['target']
            g = re.findall(r'<tool_response>\ndistance ([0-9]+\.[0-9]+) m\n</tool_response>', t)
            cv = re.findall(r'Converting to (centimeters|feet|inches): ([0-9.]+) x ([0-9.]+) = ([0-9.]+)\.', t)
            ok = len(g) == 1 and len(cv) == 1 and cv[0][0] == unit and cv[0][1] == g[0] and cv[0][2] == F[unit][0] and \
                 Decimal(cv[0][3]) == (Decimal(g[0]) * Decimal(F[unit][0])).quantize(F[unit][1], rounding=ROUND_HALF_UP) and x['answer'] == cv[0][3] and t.endswith('<answer>%s</answer>' % cv[0][3])
            c['conversion_ok' if ok else 'conversion_bad'] += 1
            packed = ground_rows.pack(dict(copy.deepcopy(gx), suffix=t), x['provenance'])
        else:
            allowed = {'qid', 'question', 'question_identity', 'provenance', 'candidate_id'}
            if strip(x, allowed) != strip(s, allowed): diffs['top_level_other'] += 1
            px = copy.deepcopy(x['provenance']); e = px.pop('dist_diag_question_edit', None)
            if px != s['provenance'] or not e or e['before'] != s['question'] or e['after'] != x['question']: diffs['provenance'] += 1
            t = x['suffix']; g = re.findall(r'<tool_response>\ndistance ([0-9]+\.[0-9]+) m\n</tool_response>', t)
            ok = unit == 'meters' and len(g) == 1 and x['answer'] == g[0] and 'Converting' not in t and t.endswith('<answer>%s</answer>' % g[0])
            c['metre_answer_ok' if ok else 'metre_answer_bad'] += 1
            packed = ground_rows.pack(dict(copy.deepcopy(x), events=[dict(call=mm.group(1), response=mm.group(2)) for mm in EV.finditer(t)]), x['provenance'])
        rec = dict(gx, suffix=x['target']) if units else x
        rule = e['candidate_id_rule'] if e else ''
        rev = rule.rsplit('_', 1)[-1] if rule.startswith('formula_variant_') else (rec.get('spec_version') or '3.14')
        if x['candidate_id'] != candidate_identity(dict(rec, trace_revision=rev), rec.get('simulated_misses') or []): diffs['cid_not_formula'] += 1
        if x['candidate_id'] == s['candidate_id'] or e['candidate_id_before'] != s['candidate_id']: diffs['cid_not_new'] += 1
        cids[x['candidate_id']] += 1; srccids.add(s['candidate_id'])
        try: ground_rows.validate(packed); c['validator_pass'] += 1
        except Exception as ex: c['validator_fail:' + str(ex)[:50]] += 1
        if 'question_identity' in (x.get('ground_record') or x) and (x.get('ground_record') or x)['question_identity'] == (s.get('ground_record') or s).get('question_identity'): diffs['question_identity_unchanged'] += 1
c['cid_unique'] = sum(1 for v in cids.values() if v == 1); c['cid_overlap_sources'] = len(set(cids) & srccids)
print(dict(c)); print('diffs', dict(diffs)); bad_q = [k for k, v in per.items() if v != (50 if int(k[:2]) < 10 else 25)]
print('cells', len(per), 'quota mismatches', len(bad_q), 'min', min(per.values()), 'max', max(per.values()), 'max uses per source', max(srcuse.values()), 'sources', len(srcuse))
json.dump(dict(counts=c, diffs=diffs, cells=per), open('/scratch/jjyeung/orch_n30/dist_diag/work/q5/CHECK_COV_V2H.json', 'w'), indent=1)
