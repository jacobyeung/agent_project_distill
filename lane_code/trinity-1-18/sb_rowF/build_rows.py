"""Build counting form B (default) or A from pinned first-seen source rows.

The output is a kit for review, not training admission. N's unchanged validators
are exercised and their failures are reported, never waived or monkey-patched.
"""
import argparse, collections, copy, ctypes, hashlib, json, re, sys
from pathlib import Path
from source_contract import sha, dump, encoded, norm, parse, independent_truth, need, Refusal
from count_forms import render, validate

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
I = ROOT / 'inputs'
THRESHOLD = 0.10
EXPECTED_SOURCE = {'b12_cntapp_gt_v1': 10177, 'r1g': 6636,
                   'rows_rebuild_d0_T0_gaps': 290, 'rows_rebuild_d0_T1H1_gaps': 307,
                   'rows_rebuild_d0_T1H2_gaps': 279, 'rows_rebuild_d0_ARKIT_gaps': 363}

def setup():
    manifest = json.loads((I / 'INPUTS.json').read_text())
    for name, pin in manifest['pins'].items():
        path = I / name
        if path.is_file(): assert sha(path) == pin['sha256'], name
    sys.path.insert(0, manifest['tree'])
    from student_pilot.r1_rooms import Rooms
    from student_pilot.s1_exclusions import Exclusions
    pins = manifest['pins']
    authority = {k: {'path': str(I / (k + '.json')), 'sha256': pins[k + '.json']['sha256']}
                 for k in ('split', 'reserve', 'aliases', 'build', 'visits')}
    rooms = Rooms(authority)
    ex = Exclusions({'path': str(I / 'dev.json'), 'sha256': pins['dev.json']['sha256']},
                    {'path': str(I / 'bench.json'), 'sha256': pins['bench.json']['sha256']})
    return manifest, rooms, ex

def room_check(row, rooms, ex, facts, withheld):
    canonical, basis = rooms.canonical(row)
    if not canonical:
        recorded = facts.get(row['dataset'] + '/' + row['scene'])
        need(recorded is not None, 'MISSING_canonical_room_mapping')
        need(len(recorded) == 1, 'ambiguous_canonical_room_mapping')
        canonical = next(iter(recorded)); basis = 'recorded_field_and_scene_token_sha256'
    physical = rooms.room(canonical)
    probe = dict(row, canonical=canonical, physical_group=physical)
    reasons = []
    if physical in rooms.r0: reasons.append('excluded_room_R0')
    if physical in rooms.k1: reasons.append('excluded_room_K1_heldout')
    if physical in withheld: reasons.append('excluded_room_withheld80')
    matches = ex.matches(probe)
    if matches['dev']: reasons.append('excluded_room_devS1')
    if matches['benchmark']: reasons.append('excluded_room_BENCH_v2')
    need(not reasons, '|'.join(reasons))
    return canonical, physical, basis

class WordingFilter:
    def __init__(self):
        corpus = json.loads((I / 'wording_corpus_expanded.json').read_text())
        self.wordings = sorted({norm(x) for x in corpus['questions']})
        self.cache = {}; self.comparisons = 0
        self.fn = ctypes.CDLL(str(ROOT / 'ned_filter.so')).bounded_distance
        self.fn.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        self.fn.restype = ctypes.c_int

    def distance(self, a, b, limit):
        if abs(len(a) - len(b)) > limit: return limit + 1
        if a.isascii() and b.isascii():
            result = self.fn(a.encode(), b.encode(), limit)
            if result < 0: raise MemoryError('edit distance allocation failed')
            return result
        previous = list(range(len(b) + 1))
        for i, char in enumerate(a, 1):
            current = [i] + [limit + 1] * len(b)
            for j in range(max(1, i - limit), min(len(b), i + limit) + 1):
                current[j] = min(current[j-1] + 1, previous[j] + 1, previous[j-1] + (char != b[j-1]))
            if min(current) > limit: return limit + 1
            previous = current
        return previous[-1]

    def check(self, target):
        body = target.split('<think>\n', 1)[1].split('\n</think>', 1)[0]
        texts = {norm(body)} | {norm(re.sub(r'^Step \d+: ', '', line)) for line in body.splitlines()}
        for text in texts:
            if text not in self.cache:
                hit = None
                for question in self.wordings:
                    limit = int(THRESHOLD * max(len(text), len(question)))
                    self.comparisons += 1
                    if self.distance(text, question, limit) <= limit:
                        hit = hashlib.sha256(question.encode()).hexdigest(); break
                self.cache[text] = hit
            need(self.cache[text] is None, 'new_trace_near_eval_wording')

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--form', choices=('A', 'B'), default='B')
    ap.add_argument('--out', default='out')
    ap.add_argument('--census-only', action='store_true')
    args = ap.parse_args()
    out = (ROOT / args.out).resolve(); assert out.is_relative_to(ROOT)
    out.mkdir(parents=True, exist_ok=True)
    manifest, rooms, ex = setup()
    from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity
    from student_pilot.trace_grammar import validate_row
    from student_pilot.r1_training import row_check
    from student_pilot.finetune_lane import validate_student_input
    from student_pilot.r2_contract import validate as native_validate
    from student_pilot import ground_rows, r1_counting
    facts = json.loads((I / 'scene_facts.json').read_text())['facts']
    withheld = set(json.loads((I / 'withheld.json').read_text())['rooms'])
    source_ids = json.loads((I / 'source_ids.json').read_text())['ids']
    oldids = {x[0] for x in source_ids}; oldcids = {x[1] for x in source_ids if x[1]}
    z_records = [json.loads(l) for l in (I / 'z.json').open() if l.strip()]
    n_records = [json.loads(l) for l in (I / 'n.json').open() if l.strip()]
    zids = {r['row_key'] for r in z_records}; nids = {r['row_key'] for r in n_records}
    expected = None if args.census_only else json.loads((I / 'EXPECTED_CELLS.json').read_text())
    pins = {k: v['sha256'] for k, v in manifest['pins'].items()}
    pins.update({name: sha(ROOT / name) for name in ('prepare_inputs.py', 'source_contract.py', 'build_rows.py', 'count_forms.py', 'ned_filter.c', 'ned_filter.so')})
    pins['INPUTS.json'] = sha(I / 'INPUTS.json')
    if expected is not None: pins['EXPECTED_CELLS.json'] = sha(I / 'EXPECTED_CELLS.json')
    lineage = {k: pins[k] for k in ('store', 'source_rows.jsonl', 'INPUTS.json', 'build_rows.py', 'source_contract.py', 'count_forms.py', 'TREE_SEAL.json', 'wording_corpus_expanded.json')}
    sources = collections.Counter(); mechanical = collections.Counter(); eligible_cells = collections.Counter()
    refused_cells = collections.Counter(); reasons = collections.Counter(); truth = collections.Counter()
    bases = collections.Counter(); validation = collections.Counter(); errors = collections.defaultdict(collections.Counter)
    examples = {}; output_rows = []; mapping = []; refused = []; remove = []; eligibility = []
    newids = set(); newcids = set(); source_use = collections.Counter(); mechanical_ids = set()
    wf = WordingFilter()

    def kit_check(row, tag):
        for label, fn in [('student_input', lambda: validate_student_input(row['student_input'])),
                          ('row_schema', lambda: row_check(row, 'vqa')),
                          ('native_validate', lambda: native_validate(row, 'vqa')),
                          ('ground_pack_validate', lambda: ground_rows.validate(ground_rows.pack(row, row['provenance'])))]:
            try: fn(); validation[tag + '_' + label + '_pass'] += 1
            except (ValueError, KeyError, TypeError, AssertionError) as err:
                key = tag + '_' + label
                validation[key + '_fail'] += 1
                message = type(err).__name__ + ':' + str(err)
                errors[key][message] += 1
                examples.setdefault(key, {'qid': row['qid'], 'error': message})
        errs = validate_row(row)
        validation[tag + '_trace_grammar_' + ('fail' if errs else 'pass')] += 1
        errors[tag + '_trace_grammar'].update({e.rule_id for e in errs})
        if errs: examples.setdefault(tag + '_trace_grammar', {'qid': row['qid'], 'errors': [e._asdict() for e in errs]})

    for line in (I / 'source_rows.jsonl').open():
        row = json.loads(line); qid = row['qid']; sources[row['pool']] += 1
        cell = row['pool'] + '|' + ('multiple' if row.get('count_kind') == 'total' else 'single')
        canonical = None
        if not args.census_only: kit_check(row, 'source')
        try:
            cats = parse(row)
            cell = row['pool'] + '|' + ('single' if len(cats) == 1 else 'multiple')
            mechanical[cell] += 1; mechanical_ids.add(qid)
            basis = independent_truth(row, cats)
            # Each number is a sampled-frame index, never a timestamp.
            need(len(row['student_input']['frames']) == 32, 'not_32_sampled_frames')
            for name, entries in cats:
                need(all(type(f) is int and 1 <= f <= 32 for f, _ in entries), 'frame_outside_1_32')
            canonical, physical, canonical_basis = room_check(row, rooms, ex, facts, withheld)
            target = render(cats, row['answer'], args.form)
            actual, totals = validate(target, row['answer'], args.form)
            assert actual == {name: collections.Counter(entries) for name, entries in cats}
            if not args.census_only: wf.check(target)
            eligible_cells[cell] += 1
            eligibility.append(qid)
            if args.census_only: continue
            x = copy.deepcopy(row)
            x['qid'] = 'sb_rowF_' + args.form + '_' + hashlib.sha256(qid.encode()).hexdigest()[:24]
            x['target'] = target
            record = {'qid': x['qid'], 'scene': row['scene'], 'frame_indices': row['student_input']['frame_indices'],
                      'type': row['question_type'], 'question': row['student_input']['question'],
                      'options': row['student_input']['options'], 'trace_revision': 'sb_rowF-v1-' + args.form}
            x['candidate_id'] = candidate_identity(record)
            note = {'source_qid': qid, 'source_row_sha256': hashlib.sha256(line.rstrip('\n').encode()).hexdigest(),
                    'source_target_sha256': hashlib.sha256(row['target'].encode()).hexdigest(),
                    'input_sha256': lineage, 'form': args.form, 'canonical': canonical, 'physical_room': physical,
                    'canonical_basis': canonical_basis, 'truth_basis': basis, 'candidate_identity_record': record,
                    'status': 'KIT_ONLY_NOT_ADMITTED'}
            x['provenance']['sb_rowF'] = note
            unchanged = copy.deepcopy(x); unchanged['qid'] = row['qid']; unchanged['target'] = row['target']
            if 'candidate_id' in row: unchanged['candidate_id'] = row['candidate_id']
            else: unchanged.pop('candidate_id')
            unchanged['provenance'].pop('sb_rowF')
            assert unchanged == row, qid
            assert x['qid'] not in newids and x['qid'] not in oldids
            assert x['candidate_id'] not in newcids and x['candidate_id'] not in oldcids
            kit_check(x, 'new')
            try: r1_counting.admit(x, 'totals' if len(cats) > 1 else 'counting'); validation['counting_admission_pass'] += 1
            except ValueError as err:
                validation['counting_admission_fail'] += 1
                errors['counting_admission'][str(err).split(':')[0]] += 1
            newids.add(x['qid']); newcids.add(x['candidate_id']); source_use[qid] += 1
            output_rows.append(x); truth[min(int(row['answer']), 10)] += 1; bases[basis] += 1
            mapping.append({'old_qid': qid, 'new_qid': x['qid'], 'candidate_id': x['candidate_id'], 'cell': cell,
                            'truth': int(row['answer']), 'category_totals': totals, 'canonical': canonical,
                            'physical_room': physical, 'input_sha256': lineage,
                            'already_removed_z': qid in zids, 'already_removed_n': qid in nids})
            if qid not in zids | nids:
                remove.append({'pool': row['pool'], 'question_type': row['question_type'],
                               'reason': 'count_first_seen_replaced_by_sb_rowF_' + args.form,
                               'row_key': qid, 'scene': row['dataset'] + '/' + row['scene']})
        except Refusal as err:
            row_reasons = str(err).split('|'); reasons.update(row_reasons); refused_cells[cell] += 1
            item = {'old_qid': qid, 'cell': cell, 'truth': row['answer'], 'reasons': row_reasons,
                    'input_sha256': lineage}
            if 'MISSING_independent_instance_annotations' in row_reasons:
                item['missing_expected_location'] = 'source_rows.jsonl[qid=' + qid + ']: provenance.instances, provenance.total_categories, or retrace_a2.cited'
            if 'MISSING_canonical_room_mapping' in row_reasons:
                item['missing_expected_location'] = 'inputs/aliases.json or inputs/scene_facts.json: ' + row['dataset'] + '/' + row['scene']
            refused.append(item)

    assert dict(sources) == EXPECTED_SOURCE, dict(sources)
    assert sum(sources.values()) == 18052
    assert sum(eligible_cells.values()) + len(refused) == 18052
    census = {'input_sha256': pins, 'source_cells': dict(sources), 'mechanical_cells': dict(mechanical),
              'eligible_cells': dict(eligible_cells), 'refusal_cells': dict(refused_cells),
              'refusal_reasons': dict(reasons), 'eligible_source_qids_sha256': hashlib.sha256(encoded(eligibility).encode()).hexdigest(),
              'refused_source_qids_sha256': hashlib.sha256(encoded([r['old_qid'] for r in refused]).encode()).hexdigest()}
    if args.census_only:
        dump(I / 'EXPECTED_CELLS.json', census)
        print(json.dumps({k: v for k, v in census.items() if k != 'input_sha256'})); return
    for key in ('source_cells', 'mechanical_cells', 'eligible_cells', 'refusal_cells', 'refusal_reasons',
                'eligible_source_qids_sha256', 'refused_source_qids_sha256'):
        assert census[key] == expected[key], (key, census[key], expected[key])
    assert max(source_use.values(), default=0) == 1
    assert len(newids) == len(newcids) == len(output_rows) == sum(eligible_cells.values())
    sealed = json.loads((I / 'TREE_SEAL.json').read_text())['files']
    imported = {}
    for module in list(sys.modules.values()):
        path = getattr(module, '__file__', None)
        if path and path.endswith('.py') and Path(path).is_relative_to(manifest['tree']):
            relative = str(Path(path).relative_to(manifest['tree']))
            assert sha(path) == sealed[relative], relative
            imported[relative] = sealed[relative]
    for name, rows in [('rows.jsonl', output_rows), ('QID_MAP.jsonl', mapping), ('REFUSALS.jsonl', refused), ('REMOVE.json', remove)]:
        with (out / name).open('w') as f:
            for row in rows: f.write(encoded(row) + '\n')
    dump(out / 'CENSUS.json', census)
    histogram = {'input_sha256': pins, 'definition': 'One row per final stored answer; 10+ means truth >=10.',
                 'all_sources': {}, 'converted': {str(i) if i < 10 else '10+': truth[i] for i in range(11)}, 'by_cell': {}}
    for cell in eligible_cells:
        c = collections.Counter(min(m['truth'], 10) for m in mapping if m['cell'] == cell)
        histogram['by_cell'][cell] = {str(i) if i < 10 else '10+': c[i] for i in range(11)}
    hist_source = collections.Counter(min(int(r['answer']), 10) for r in map(json.loads, (I / 'source_rows.jsonl').open()))
    histogram['all_sources'] = {str(i) if i < 10 else '10+': hist_source[i] for i in range(11)}
    dump(out / 'TRUTH_HISTOGRAM.json', histogram)
    dump(out / 'REMOVE_RECEIPT.json', {'input_sha256': pins, 'format': 'N n.json JSONL: pool, question_type, reason, row_key, scene',
         'replacement_rows': len(mapping), 'already_removed_by_z': sum(m['already_removed_z'] for m in mapping),
         'already_removed_by_n': sum(m['already_removed_n'] for m in mapping), 'additional_removals': len(remove),
         'remove_sha256': sha(out / 'REMOVE.json'), 'rule': 'Converted source qids minus union of all n.json and z.json removal qids.'})
    checks = {'input_sha256': pins, 'form': args.form, 'status': 'KIT_ONLY_BLOCKED_BY_UNCHANGED_N_VALIDATORS',
              'all_required_checks_pass': False, 'tree': manifest['tree'], 'tree_sha256': manifest['tree_sha256'],
              'source_rows': sum(sources.values()), 'mechanically_exact_rows': len(mechanical_ids),
              'emitted_rows': len(output_rows), 'refused_rows': len(refused), 'refusal_reasons': dict(reasons),
              'exact_cells_asserted': census['eligible_cells'], 'source_reuse_max_per_form': max(source_use.values()),
              'qid_unique': len(newids), 'candidate_id_unique': len(newcids), 'old_new_id_intersections': 0,
              'allowed_field_diff': ['qid', 'candidate_id', 'target', 'provenance.sb_rowF'],
              'independent_truth_basis': dict(bases), 'proposed_form_validator_pass': len(output_rows),
              'room_rule_pass': len(output_rows), 'validation': dict(validation),
              'validation_errors': {k: dict(v) for k, v in errors.items()}, 'validation_examples': examples,
              'pack_limitation': 'ground_rows.pack is a routed ground-record API requiring suffix/events/spec_version. Direct store counting rows have none. Every attempted source and new pack fails; no synthetic record was invented.',
              'wording_filter': {'threshold': THRESHOLD, 'normalization': 'Unicode NFKC, casefold, whitespace collapse; character Levenshtein divided by max length',
                  'scope': 'New complete think bodies and each new line with Step label removed, versus all available corpus question/prompt wordings.',
                  'new_questions': 0, 'inherited_questions_unchanged': len(output_rows), 'reference_wordings': len(wf.wordings),
                  'unique_authored_texts': len(wf.cache), 'comparisons': wf.comparisons, 'removed': reasons['new_trace_near_eval_wording'],
                  'full_external_eval_corpora': 'MISSING from supplied local kit; available fixture and R0 VSTI wordings checked.'},
              'imported_kit_sha256': imported,
              'artifact_sha256': {name: sha(out / name) for name in ('rows.jsonl', 'QID_MAP.jsonl', 'REFUSALS.jsonl', 'REMOVE.json', 'REMOVE_RECEIPT.json', 'CENSUS.json', 'TRUTH_HISTOGRAM.json')}}
    dump(out / 'CHECKS.json', checks)
    selected = []; selected_ids = set()
    def add(row):
        if row['qid'] not in selected_ids and len(selected) < 30:
            selected.append(row); selected_ids.add(row['qid'])
    for cell in sorted(eligible_cells):
        for row, m in zip(output_rows, mapping):
            if m['cell'] == cell: add(row); break
    for arity in ('single', 'multiple'):
        for bucket in range(11):
            for row, m in zip(output_rows, mapping):
                if m['cell'].endswith('|' + arity) and min(m['truth'], 10) == bucket: add(row); break
    for row in sorted(output_rows, key=lambda r: hashlib.sha256(r['qid'].encode()).hexdigest()): add(row)
    assert len(selected) == 30
    with (out / 'READ30.md').open('w') as f:
        f.write(f'Thirty full form {args.form} rows, stratified by pool, category arity, and truth bucket.\n\n')
        for index, row in enumerate(selected, 1):
            f.write(f'## {index}. {row["qid"]}\n\nQuestion: {row["student_input"]["question"]}\n\n```text\n{row["target"]}\n```\n\n```json\n{encoded(row)}\n```\n\n')
    (ROOT / 'STATUS.md').write_text(f'Conversion stage complete for form {args.form}: {len(output_rows):,} rows emitted from 18,052 first-seen sources, with {len(refused):,} explicit refusals. Exact cell counts, identities, source field differences, annotation truth, room exclusions, and form syntax pass. N\'s unchanged native validators and routed pack API remain incompatible; their actual results are in CHECKS.json. Independent auditing and READ30 review are next.\n')
    print(json.dumps({k: checks[k] for k in ('form', 'emitted_rows', 'refused_rows', 'refusal_reasons', 'exact_cells_asserted', 'validation')}))

if __name__ == '__main__': main()
