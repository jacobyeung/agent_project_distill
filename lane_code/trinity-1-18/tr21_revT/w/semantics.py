"""Reviewer checks of Extents scoping: C'' equivalence, validation, edge cases, counters."""
import copy, importlib.util, json, sys
from pathlib import Path

W = Path('/scratch/jjyeung/orch_n30/tr21_revT/w')
D = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24v/work/build24m4v')
sys.path.insert(0, str(W / 'patched'))
from student_pilot.extent_receipt import Extents, required, content
from student_pilot.p3_provenance import digest, file_pin

spec = importlib.util.spec_from_file_location('base_extent', W / 'base/student_pilot/extent_receipt.py',
                                              submodule_search_locations=None)
base = importlib.util.module_from_spec(spec)
base.__package__ = 'student_pilot'
spec.loader.exec_module(base)

names = json.loads((D / 'SOURCES.json').read_text())['names']
pin = file_pin(D / 'c072905b.json')
rows = [json.loads(x['row']) for x in json.loads((D / 'published/p_sample.json').read_text())['rows']]
controls = [json.loads((D / f).read_text()) for f in ('pool_row.json', 'a0_units_row.json', 'a0_recovery_row.json',
                                                     'a0_pool_abs_distance_reworded_row.json')]
pool = controls[0]

def outcome(gate, row, stream):
    try:
        gate.check(row, stream)
        return 'PASS'
    except Exception as e:
        return type(e).__name__ + ':' + str(e)

def variants(row):
    yield row
    yield dict(row, answer_form='routed')
    yield {k: v for k, v in row.items() if k != 'qid'}
    yield dict(row, r1_source=dict(family='x', sha256='0'))
    yield dict(row, qid='a0_' + str(row.get('qid')))
    r = copy.deepcopy(row); r.setdefault('provenance', {})['repair'] = {'x': 1}; yield r

report = {}
# 1. Empty or absent list: identical outcomes to C'' on every row, stream and pin.
gates = dict(base=lambda p: base.Extents(p), none=lambda p: Extents(p), explicit_none=lambda p: Extents(p, None),
             empty=lambda p: Extents(p, []))
diffs, n = [], 0
for p in (pin, None):
    built = {k: f(p) for k, f in gates.items()}
    for row in rows + controls:
        for v in variants(row):
            for stream in ('routing', 'vqa', 'pointing'):
                res = {k: outcome(g, v, stream) for k, g in built.items()}
                n += 1
                if len(set(res.values())) != 1:
                    diffs.append((v.get('qid'), stream, res))
    report['empty_or_absent_counters'] = {k: g.exempted for k, g in built.items() if k != 'base'}
report['c2_equivalence'] = dict(cases=n, differences=len(diffs), first=diffs[:3])

# 2. Validation of the config value.
val = {}
for label, value in [('tuple', tuple(names)), ('set', set(names)), ('str', 'ARKIT_gaps'), ('blank', ['']),
                     ('int', [1]), ('dict', {}), ('zero', 0), ('empty_str', ''), ('dup', names + names[:1])]:
    try:
        Extents(pin, value); val[label] = 'accepted'
    except Exception as e:
        val[label] = type(e).__name__ + ':' + str(e)
report['validation'] = val

# 3. Exemption edge cases with the configured list.
g = Extents(pin, names)
edge = {}
cases = {
    'pool_row': (pool, 'routing'),
    'pool_unlisted_name': (dict(pool, s1_source=dict(pool['s1_source'], name='ROUTE_direct')), 'routing'),
    'pool_source_string': (dict(pool, s1_source='ARKIT_gen_r2'), 'routing'),
    'pool_r1_source_empty_dict': (dict(pool, r1_source={}), 'routing'),
    'pool_r1_source_none': (dict(pool, r1_source=None), 'routing'),
    'pool_r1_source_set': (dict(pool, r1_source=dict(family='pool_full', sha256='0')), 'routing'),
    'pool_a0_prefix': (dict(pool, qid='a0_' + pool['qid']), 'routing'),
    'pool_routing_qid_a0_only': (dict(pool, routing=dict(pool['routing'], qid='a0_x')), 'routing'),
    'pool_vqa_routed': (dict(pool, answer_form='routed'), 'vqa'),
    'reworded_slice_with_copied_s1': (dict(controls[3], s1_source=pool['s1_source']), 'routing'),
    'units_slice_with_copied_s1': (dict(controls[1], s1_source=pool['s1_source']), 'routing'),
    'recovery_unprefixed_with_s1': (dict(controls[2], qid='r0rec1_abc', s1_source=pool['s1_source']), 'routing'),
}
for label, (row, stream) in cases.items():
    try:
        ex = g.exempt(row, stream)
    except Exception as e:
        ex = type(e).__name__ + ':' + str(e)
    edge[label] = dict(exempt=ex, before=outcome(base.Extents(pin), row, stream), after=outcome(Extents(pin, names), row, stream))
try:
    g.exempt(dict(pool, s1_source=dict(pool['s1_source'], name=['x'])), 'routing'); edge['unhashable_name'] = 'no error'
except Exception as e:
    edge['unhashable_name'] = type(e).__name__ + ':' + str(e)
report['edges'] = edge

# 4. Counter semantics: exempted counts calls, including rows the C'' gate passes or never checks.
c = Extents(pin, names)
non_required = copy.deepcopy(pool); non_required['routing']['question_type'] = 'camera_rotation'
certified = copy.deepcopy(pool)
c.receipt = dict(c.receipt, rows=dict(c.receipt['rows'], **{certified['qid']: dict(
    c.receipt['rows'].get(certified['qid'], {}), content_sha256=digest(content(certified)),
    box_statuses=['full'] * len(certified.get('ground_record', certified['routing'].get('ground_record', {}))
                                .get('program_audit', {}).get('independent_ordered_boxes', [])), repair_sha256=None)}))
b = base.Extents(pin); b.receipt = c.receipt
counter = dict(non_required_required=required(non_required, 'routing'), non_required_before=outcome(b, non_required, 'routing'))
c.check(non_required, 'routing'); counter['after_non_required'] = c.exempted
counter['certified_before'] = outcome(b, certified, 'routing')
c.check(certified, 'routing'); counter['after_certified'] = c.exempted
c.check(pool, 'routing'); c.check(pool, 'routing'); counter['after_same_row_twice'] = c.exempted
report['counter'] = counter

# 5. Sample: exempted vs C'' refusals.
gp, gb = Extents(pin, names), base.Extents(pin)
s = dict(rows=len(rows), exempt=0, base_refused=0, exempt_and_base_refused=0, exempt_and_base_pass=0, after_refused=0)
for r in rows:
    e = gp.exempt(r, 'routing'); before = outcome(gb, r, 'routing'); after = outcome(gp, r, 'routing')
    s['exempt'] += e; s['base_refused'] += before != 'PASS'; s['after_refused'] += after != 'PASS'
    s['exempt_and_base_refused'] += e and before != 'PASS'; s['exempt_and_base_pass'] += e and before == 'PASS'
report['sample'] = s
(W / 'SEMANTICS.json').write_text(json.dumps(report, indent=1, default=str))
print(json.dumps(report, indent=1, default=str))
