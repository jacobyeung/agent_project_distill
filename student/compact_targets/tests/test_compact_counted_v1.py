import copy
import unittest
from dataclasses import replace
from pathlib import Path

from student.compact_targets import compact_counted_v1 as compact


SOURCE = Path('/data2/jjyeung/agent_project_data/devin_lane_out/converter_zero_call_v3_20260918_out')
RECOVERY = SOURCE / 'diagnostic_set/recovery_20260919_0309Z/targets'
EXAMPLE = Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_design_compact_targets/out/EXAMPLE_RENDER_B.txt')


def fixture():
    definitions = [
        ('A0001', 'appearance', 'The lamp is visible in frame 1.'),
        ('M0001', 'measurement', 'The lamp is approximately 2.0 meters away.'),
        ('Q0001', 'qualification', 'The lamp measurement is approximate.'),
        ('M0002', 'measurement', 'The desk is approximately 5.0 meters away.'),
        ('M0003', 'measurement', 'The unused chair is 9.0 meters away.'),
        ('C0001', 'calculation', 'The distance is approximately 3.0 meters. Operands: M0001, M0002.'),
        ('V0001', 'convention', 'The coordinate frame is right-handed.'),
    ]
    records = {'records': [], 'appearances': [], 'calculations_v2': [], 'qualifications_v2': [], 'conventions_v2': [],
               'identities': []}
    groups = {'appearance': 'appearances', 'measurement': 'records', 'calculation': 'calculations_v2',
              'qualification': 'qualifications_v2', 'convention': 'conventions_v2'}
    quantities = {'M0001': 'centroid', 'M0002': 'centroid', 'M0003': 'centroid'}
    lines, evidence = [], []
    for number, (identifier, kind, text) in enumerate(definitions, 1):
        citations = [f'E1.L{number}']
        record = {'id': identifier, 'kind': kind, 'citations': citations}
        if identifier in quantities:
            record['quantity'] = quantities[identifier]
        if kind == 'calculation':
            record['operand_record_ids'] = ['M0001', 'M0002']
            record['operation'] = 'displacement_xy'
        records[groups[kind]].append(record)
        lines.append({**record, 'record_id': identifier, 'record_sha256': compact.digest_json(record),
                      'student_text': text, 'own_record_binding': True})
        evidence.append({'id': citations[0], 'kind': 'tool_return'})
    checks = {'answer': 'B', 'outcome': 'target', 'schema_failed': False,
              'tier_i': {'all_deterministic_checks_satisfied': True, 'findings': [],
                         'checks': dict.fromkeys(compact.TIER_I_CHECKS, 'satisfied')}}
    return lines, records, checks, {'lines': evidence}


class CompactCase(unittest.TestCase):
    def setUp(self):
        self.source, self.records, self.source_checks, self.evidence = fixture()
        self.context = compact.Context('object_rel_distance', 'How far is the lamp from the desk?')
        self.rendered = compact.render_target(self.source, 'B', self.records, self.context)

    def validate(self, rendered=None, **kwargs):
        arguments = {'source_lines': self.source, 'records': self.records, 'source_checks': self.source_checks,
                     'evidence_index': self.evidence, 'answer': 'B', 'count_tokens': lambda text: 100,
                     'context': self.context}
        arguments.update(kwargs)
        return compact.admit(rendered or self.rendered, **arguments)

    def changed(self, old, new):
        self.assertIn(old, self.rendered.target)
        return replace(self.rendered, target=self.rendered.target.replace(old, new, 1))

    def rejects(self, rendered, reason, **kwargs):
        result = self.validate(rendered, **kwargs)
        self.assertFalse(result['passed'])
        self.assertIn(reason, result['reason_codes'])
        return result


class SelectionTests(CompactCase):
    def test_appearance_and_operands_follow_file_order(self):
        selected = compact.select_lines(self.source, self.records)
        self.assertEqual([line['id'] for line in selected.observations], ['A0001', 'M0001', 'M0002'])
        self.assertEqual([line['id'] for line in selected.derivations], ['C0001'])
        self.assertEqual([line['id'] for line in selected.omitted], ['Q0001', 'M0003', 'V0001'])

    def test_unreferenced_measurements_do_not_select_themselves(self):
        source = [line for line in self.source if line['kind'] != 'calculation']
        self.assertEqual([line['id'] for line in compact.select_lines(source, self.records).observations], ['A0001'])

    def test_quantity_free_operand_is_dropped_from_the_selection(self):
        self.source[5]['student_text'] = 'A calculation. Operands: Q0001.'
        selected = compact.select_lines(self.source, self.records)
        self.assertEqual([line['id'] for line in selected.observations], ['A0001'])
        self.assertEqual(selected.operands['C0001'], {'operation': 'displacement_xy', 'raw': ['Q0001'],
                                                      'quantities': {'Q0001': None}, 'kept': [], 'dropped': ['Q0001']})

    def test_referenced_qualification_with_an_admissible_quantity_is_selected(self):
        self.records['qualifications_v2'][0]['quantity'] = 'centroid'
        self.source[2]['record_sha256'] = compact.digest_json(self.records['qualifications_v2'][0])
        self.source[5]['student_text'] = 'A calculation. Operands: Q0001.'
        self.assertEqual([line['id'] for line in compact.select_lines(self.source, self.records).observations],
                         ['A0001', 'Q0001'])

    def test_repeated_operands_do_not_repeat_observations(self):
        self.source[5]['student_text'] += ' Operands: M0001, M0002.'
        selected = compact.select_lines(self.source, self.records)
        self.assertEqual(len(selected.observations), 3)
        rendered = compact.render_target(self.source, 'B', self.records, self.context)
        self.assertEqual(rendered.target.count('Uses observations 2, 3.'), 2)

    def test_operand_order_is_preserved(self):
        self.source[5]['student_text'] = 'A calculation. Operands: M0002, M0001.'
        self.assertIn('Uses observations 3, 2.', compact.render_target(self.source, 'B', self.records, self.context).target)

    def test_calculation_without_operands_is_preserved(self):
        self.source[5]['student_text'] = 'A numerical result is approximately 3.0 in unspecified units.'
        rendered = compact.render_target(self.source, 'B', self.records, self.context)
        self.assertIn('Derivations (1)', rendered.target)
        self.assertNotIn('Uses observations', rendered.target)

    def test_dangling_operand_defers(self):
        self.source[5]['student_text'] = 'A calculation. Operands: M9999.'
        with self.assertRaisesRegex(compact.Deferral, 'unresolved_operand'):
            compact.select_lines(self.source, self.records)

    def test_malformed_operand_clause_defers(self):
        for suffix in ('Operands:', 'Operands: M0001', 'Operands: M0001 and M0002.', 'Operands: nonsense.'):
            with self.subTest(suffix=suffix):
                self.source[5]['student_text'] = 'A calculation. ' + suffix
                with self.assertRaisesRegex(compact.Deferral, 'malformed_operands'):
                    compact.select_lines(self.source, self.records)

    def test_convention_cannot_become_an_observation(self):
        self.source[5]['student_text'] = 'A calculation. Operands: V0001.'
        with self.assertRaisesRegex(compact.Deferral, 'invalid_operand_kind'):
            compact.select_lines(self.source, self.records)

    def test_calculation_cannot_become_an_observation(self):
        self.source[5]['student_text'] = 'A calculation. Operands: C0001.'
        with self.assertRaisesRegex(compact.Deferral, 'invalid_operand_kind'):
            compact.select_lines(self.source, self.records)

    def test_duplicate_source_ids_defer(self):
        self.source.append(copy.deepcopy(self.source[0]))
        with self.assertRaisesRegex(compact.Deferral, 'duplicate_line_id'):
            compact.select_lines(self.source, self.records)

    def test_multiline_source_is_not_silently_reflowed(self):
        self.source[0]['student_text'] += '\nAnother sentence.'
        with self.assertRaisesRegex(compact.Deferral, 'source_line_schema'):
            compact.select_lines(self.source, self.records)


class LayoutTests(CompactCase):
    def test_exact_default_layout_and_no_trailing_newline(self):
        expected = ('Observations (3)\n1. The lamp is visible in frame 1.\n'
                    '2. The lamp is approximately 2.0 meters away.\n'
                    '3. The desk is approximately 5.0 meters away.\n'
                    'Derivations (1)\n1. The distance is approximately 3.0 meters. Uses observations 2, 3.\n'
                    'End of reasoning.\nB')
        self.assertEqual(self.rendered.target, expected)
        self.assertEqual(len(self.rendered.lines), 4)
        self.assertEqual(set(self.rendered.lines[0]), {'index', 'id', 'record_id', 'record_sha256', 'citations', 'kind'})
        self.assertEqual([line['index'] for line in self.rendered.lines], [1, 2, 3, 1])

    def test_empty_derivations_have_no_header_and_defer_the_type(self):
        source = [line for line in self.source if line['kind'] != 'calculation']
        rendered = compact.render_target(source, 'B', self.records, self.context)
        self.assertEqual(rendered.target, 'Observations (1)\n1. The lamp is visible in frame 1.\nEnd of reasoning.\nB')
        self.rejects(rendered, 'no_calculations', source_lines=source)

    def test_appearance_order_is_admitted_without_derivations(self):
        source = [line for line in self.source if line['kind'] != 'calculation']
        context = compact.Context('obj_appearance_order', 'Which of these appeared first?')
        rendered = compact.render_target(source, 'B', self.records, context)
        self.assertTrue(self.validate(rendered, source_lines=source, context=context)['passed'])

    def test_derivation_citations_are_opt_in_and_derivations_only(self):
        rendered = compact.render_target(self.source, 'B', self.records, self.context, derivation_citations=True)
        self.assertIn('Uses observations 2, 3. [E1.L6]', rendered.target)
        self.assertEqual(rendered.target.count('['), 1)
        self.assertTrue(self.validate(rendered, derivation_citations=True)['passed'])

    def test_citation_ranges_are_lossless_and_sorted(self):
        citations = ['E2.L9', 'E1.L3', 'E1.L1', 'E1.L2', 'E2.L9', 'E2.L11']
        self.assertEqual(compact.citation_suffix(citations), ' [E1.L1-L3, E2.L9, E2.L11]')

    def test_reference_replacement_preserves_suffix_bytes(self):
        self.source[5]['student_text'] += ' Precision stays unchanged.'
        rendered = compact.render_target(self.source, 'B', self.records, self.context)
        self.assertIn('Uses observations 2, 3. Precision stays unchanged.', rendered.target)
        self.assertTrue(self.validate(rendered)['passed'])

    def test_utf8_text_remains_byte_identical(self):
        self.source[0]['student_text'] = 'The café’s lamp is visible in frame 1.'
        rendered = compact.render_target(self.source, 'B', self.records, self.context)
        self.assertEqual(rendered.target.split('\n')[1][3:].encode(), self.source[0]['student_text'].encode())
        self.assertTrue(self.validate(rendered)['passed'])

    def test_numeric_answer_is_copied_without_numeric_grounding_from_observations(self):
        self.source_checks['answer'] = '24'
        rendered = compact.render_target(self.source, '24', self.records, self.context)
        self.assertTrue(self.validate(rendered, answer='24')['passed'])
        self.assertTrue(rendered.target.endswith('End of reasoning.\n24'))

    def test_answer_whitespace_is_not_normalized(self):
        for answer in (' B', 'B ', 'B\n', 'Answer: B', ''):
            with self.subTest(answer=answer), self.assertRaisesRegex(compact.Deferral, 'answer_schema'):
                compact.render_target(self.source, answer, self.records, self.context)


class AdmissionTests(CompactCase):
    def test_positive_case_passes_every_check(self):
        result = self.validate()
        self.assertTrue(result['passed'], result)
        self.assertTrue(all(result['checks'].values()))
        self.assertEqual(result['reason_codes'], [])
        self.assertFalse(result['training_eligible'])
        self.assertEqual(result['independent_review'], 'pending')

    def test_observation_rewording_fails_byte_fidelity(self):
        self.rejects(self.changed('lamp is visible', 'lamp appears'), 'byte_fidelity_changed')

    def test_unit_change_fails_byte_fidelity(self):
        self.rejects(self.changed('2.0 meters', '2.0 feet'), 'byte_fidelity_changed')

    def test_derivation_rewording_fails_byte_fidelity(self):
        self.rejects(self.changed('distance is approximately', 'distance equals'), 'byte_fidelity_changed')

    def test_rerounding_fails_byte_fidelity_and_numeric_multiset(self):
        result = self.rejects(self.changed('3.0 meters', '3 meters'), 'byte_fidelity_changed')
        self.assertIn('ungrounded_numeric_tokens', result['reason_codes'])

    def test_invented_number_fails_numeric_multiset(self):
        self.rejects(self.changed('2.0 meters', '2.5 meters'), 'ungrounded_numeric_tokens')

    def test_numeric_multiset_rejects_duplicate_supported_number(self):
        self.rejects(self.changed('2.0 meters', '2.0 and 2.0 meters'), 'ungrounded_numeric_tokens')

    def test_number_tokens_preserve_sign_precision_and_exponents(self):
        self.assertEqual(compact.numeric_tokens('-6.010, +2.0, .5, 1e-3 and M0001'),
                         {'-6.010': 1, '+2.0': 1, '.5': 1, '1e-3': 1})

    def test_unknown_record_hash_fails_binding(self):
        rendered = copy.deepcopy(self.rendered)
        rendered.lines[0]['record_sha256'] = '0' * 64
        self.rejects(rendered, 'record_binding_failed')

    def test_record_content_drift_fails_binding(self):
        self.records['appearances'][0]['extra'] = 'drift'
        self.rejects(self.rendered, 'record_binding_failed')

    def test_missing_record_fails_binding(self):
        self.records['appearances'] = []
        self.rejects(self.rendered, 'record_binding_failed')

    def test_missing_sidecar_line_fails_binding(self):
        self.rejects(replace(self.rendered, lines=self.rendered.lines[:-1]), 'record_binding_failed')

    def test_sidecar_record_identity_cannot_change(self):
        rendered = copy.deepcopy(self.rendered)
        rendered.lines[0]['record_id'] = 'M0001'
        self.rejects(rendered, 'record_binding_failed')

    def test_sidecar_citations_cannot_change(self):
        rendered = copy.deepcopy(self.rendered)
        rendered.lines[0]['citations'] = ['E1.L7']
        self.rejects(rendered, 'record_binding_failed')

    def test_header_count_mismatch_fails(self):
        for old, new in (('Observations (3)', 'Observations (4)'), ('Derivations (1)', 'Derivations (2)')):
            with self.subTest(header=old):
                self.rejects(self.changed(old, new), 'counted_layout_invalid')

    def test_noncontiguous_indices_fail(self):
        self.rejects(self.changed('2. The lamp', '4. The lamp'), 'counted_layout_invalid')

    def test_sidecar_index_mismatch_fails(self):
        rendered = copy.deepcopy(self.rendered)
        rendered.lines[1]['index'] = 7
        self.rejects(rendered, 'counted_layout_invalid')

    def test_missing_derivations_header_fails(self):
        self.rejects(self.changed('Derivations (1)\n', ''), 'counted_layout_invalid')

    def test_invalid_observation_indices_fail(self):
        for value in ('0', '4', '-1', '2.5', '02'):
            with self.subTest(value=value):
                self.rejects(self.changed('Uses observations 2, 3.', f'Uses observations {value}, 3.'), 'invalid_observation_reference')

    def test_existing_but_wrong_operand_index_fails(self):
        self.rejects(self.changed('Uses observations 2, 3.', 'Uses observations 1, 3.'), 'invalid_observation_reference')

    def test_missing_reference_fails(self):
        self.rejects(self.changed(' Uses observations 2, 3.', ''), 'invalid_observation_reference')

    def test_answer_and_marker_terminal_contract(self):
        variants = [self.rendered.target + '\n', self.rendered.target + '\nextra',
                    self.rendered.target.replace('End of reasoning.\n', ''),
                    self.rendered.target.replace('End of reasoning.', 'End of reasoning.\nEnd of reasoning.'),
                    self.rendered.target.replace('End of reasoning.\nB', 'B\nEnd of reasoning.'),
                    self.rendered.target[:-1] + 'A', self.rendered.target[:-1] + 'Answer: B']
        for target in variants:
            with self.subTest(tail=target[-60:]):
                self.rejects(replace(self.rendered, target=target), 'terminal_answer_invalid')

    def test_each_recorded_tier_i_check_is_required(self):
        for name in compact.TIER_I_CHECKS:
            with self.subTest(check=name):
                checks = copy.deepcopy(self.source_checks)
                checks['tier_i']['checks'][name] = 'defect'
                self.rejects(self.rendered, 'source_tier_i_failed', source_checks=checks)

    def test_missing_tier_i_check_is_not_a_pass(self):
        self.source_checks['tier_i']['checks'].pop('schema')
        self.rejects(self.rendered, 'source_tier_i_failed')

    def test_tier_i_findings_and_summary_are_required_to_be_clean(self):
        for key, value in (('findings', [{'reason': 'defect'}]), ('all_deterministic_checks_satisfied', False)):
            with self.subTest(key=key):
                checks = copy.deepcopy(self.source_checks)
                checks['tier_i'][key] = value
                self.rejects(self.rendered, 'source_tier_i_failed', source_checks=checks)

    def test_native_final_citation_fails_even_when_recorded_checks_pass(self):
        self.evidence['lines'][0]['kind'] = 'native_final'
        self.rejects(self.rendered, 'source_tier_i_failed')

    def test_unresolved_evidence_citation_fails(self):
        self.evidence['lines'] = self.evidence['lines'][1:]
        self.rejects(self.rendered, 'source_tier_i_failed')

    def test_own_record_binding_flag_must_remain_true(self):
        self.source[0]['own_record_binding'] = False
        self.rejects(self.rendered, 'source_tier_i_failed')

    def test_recorded_answer_must_agree(self):
        self.source_checks['answer'] = 'A'
        self.rejects(self.rendered, 'source_tier_i_failed')

    def test_budget_boundary_is_inclusive(self):
        self.assertTrue(self.validate(count_tokens=lambda text: 1536)['passed'])
        self.rejects(self.rendered, 'over_budget', count_tokens=lambda text: 1537)

    def test_zero_selected_observations_defers(self):
        source = [line for line in self.source if line['kind'] not in ('appearance', 'calculation')]
        rendered = compact.render_target(source, 'B', self.records, self.context)
        self.rejects(rendered, 'no_selected_observations', source_lines=source)

    def test_default_inline_citations_fail(self):
        self.rejects(self.changed('1. The lamp is visible in frame 1.', '1. The lamp is visible in frame 1. [E1.L1]'), 'citation_policy_failed')

    def test_variant_does_not_allow_observation_citations(self):
        rendered = compact.render_target(self.source, 'B', self.records, self.context, derivation_citations=True)
        rendered = replace(rendered, target=rendered.target.replace('frame 1.', 'frame 1. [E1.L1]', 1))
        self.rejects(rendered, 'citation_policy_failed', derivation_citations=True)

    def test_variant_requires_exact_derivation_citations(self):
        rendered = compact.render_target(self.source, 'B', self.records, self.context, derivation_citations=True)
        rendered = replace(rendered, target=rendered.target.replace('[E1.L6]', '[E1.L7]'))
        self.rejects(rendered, 'citation_policy_failed', derivation_citations=True)

    def test_calculation_operands_must_match_typed_record(self):
        self.records['calculations_v2'][0]['operand_record_ids'] = ['M0001']
        self.source[5]['record_sha256'] = compact.digest_json(self.records['calculations_v2'][0])
        rendered = compact.render_target(self.source, 'B', self.records, self.context)
        self.rejects(rendered, 'source_tier_i_failed')

    def select_qualification(self):
        original = {'id': 'Q_SOURCE', 'scope': {'object': 'lamp'}, 'source_text': self.source[2]['student_text']}
        self.records['qualifications'] = [original]
        qualification = self.records['qualifications_v2'][0]
        qualification.update(source_qualification_id=original['id'], scope=copy.deepcopy(original['scope']),
                             source_text=original['source_text'], source_scope_sha256=compact.digest_json(original['scope']),
                             student_text=original['source_text'], quantity='centroid')
        self.source[2]['record_sha256'] = compact.digest_json(qualification)
        self.records['calculations_v2'][0]['operand_record_ids'] = ['Q0001']
        self.source[5]['record_sha256'] = compact.digest_json(self.records['calculations_v2'][0])
        self.source[5]['student_text'] = 'The distance is approximately 3.0 meters. Operands: Q0001.'
        return compact.render_target(self.source, 'B', self.records, self.context)

    def test_selected_qualification_preserves_original_scope(self):
        self.assertTrue(self.validate(self.select_qualification())['passed'])

    def test_selected_qualification_rejects_scope_drift(self):
        rendered = self.select_qualification()
        self.records['qualifications'][0]['scope']['object'] = 'desk'
        self.rejects(rendered, 'source_tier_i_failed')


def counting_fixture(names=('monitor A', 'monitor B', 'monitor C'), label='monitor'):
    """A counting source whose teacher trace has no Calculations section: the instances are named only by
    the typed identity records and the measurement lines that carry them."""
    identities = [{'id': f'I{index}', 'name': name, 'label': name.rsplit(' ', 1)[0], 'instance_id': str(index),
                   'citations': [f'E1.L{index}']} for index, name in enumerate(names, 1)]
    records = {'records': [], 'appearances': [], 'calculations_v2': [], 'qualifications_v2': [], 'conventions_v2': [],
               'identities': identities}
    lines, evidence = [], []
    definitions = [('A0001', 'appearance', f'For the {label}, the recorded visible frames are 3, 4 and 7.', None)]
    definitions += [(f'M000{index}', 'measurement', f'In frame {index}, the {name} is visible in the image.', identity)
                    for index, (name, identity) in enumerate(zip(names, identities), 1)]
    for number, (identifier, kind, student_text, identity) in enumerate(definitions, 1):
        citations = [f'E2.L{number}']
        record = {'id': identifier, 'kind': kind, 'citations': citations, 'quantity': 'visibility'}
        records['appearances' if kind == 'appearance' else 'records'].append(record)
        line = {**record, 'record_id': identifier, 'record_sha256': compact.digest_json(record),
                'student_text': student_text, 'own_record_binding': True}
        if identity:
            line.update(identity_id=identity['id'], identity_name=identity['name'])
        lines.append(line)
        evidence.append({'id': citations[0], 'kind': 'tool_return'})
    checks = {'answer': str(len(names)), 'outcome': 'target', 'schema_failed': False,
              'tier_i': {'all_deterministic_checks_satisfied': True, 'findings': [],
                         'checks': dict.fromkeys(compact.TIER_I_CHECKS, 'satisfied')}}
    return lines, records, checks, {'lines': evidence}


def extent_fixture(operation='extent_xyz'):
    """An extent calculation whose operand list also names a centroid and a floor elevation."""
    definitions = [('A0001', 'appearance', 'For the trash bin, the recorded visible frames are 1 and 32.', None),
                   ('M0019', 'measurement', 'In frame 1, the trash bin centre is at 0.318 meters along X.', 'centroid'),
                   ('M0020', 'measurement', 'In frame 1, the trash bin spans 0.256 meters along X.', 'extent_xyz_p90'),
                   ('M0021', 'measurement', 'In frame 1, the floor under the trash bin is at -1.355 meters.', 'floor_z_estimate'),
                   ('M0022', 'measurement', 'In frame 1, the trash bin upper corner is at 0.455 meters along X.', 'max_xyz_p95'),
                   ('M0023', 'measurement', 'In frame 1, the trash bin lower corner is at 0.199 meters along X.', 'min_xyz_p5'),
                   ('C0001', 'calculation',
                    'For the trash bin, the calculated span is approximately 0.304 meters along X. '
                    'Operands: M0019, M0020, M0021, M0022, M0023.', None)]
    records = {'records': [], 'appearances': [], 'calculations_v2': [], 'qualifications_v2': [], 'conventions_v2': []}
    groups = {'appearance': 'appearances', 'measurement': 'records', 'calculation': 'calculations_v2'}
    lines, evidence = [], []
    for number, (identifier, kind, student_text, quantity) in enumerate(definitions, 1):
        citations = [f'E3.L{number}']
        record = {'id': identifier, 'kind': kind, 'citations': citations}
        if quantity:
            record['quantity'] = quantity
        if kind == 'calculation':
            record.update(operation=operation, operand_record_ids=['M0019', 'M0020', 'M0021', 'M0022', 'M0023'])
        records[groups[kind]].append(record)
        lines.append({**record, 'record_id': identifier, 'record_sha256': compact.digest_json(record),
                      'student_text': student_text, 'own_record_binding': True})
        evidence.append({'id': citations[0], 'kind': 'tool_return'})
    checks = {'answer': 'B', 'outcome': 'target', 'schema_failed': False,
              'tier_i': {'all_deterministic_checks_satisfied': True, 'findings': [],
                         'checks': dict.fromkeys(compact.TIER_I_CHECKS, 'satisfied')}}
    return lines, records, checks, {'lines': evidence}


class RosterTests(unittest.TestCase):
    def setUp(self):
        self.source, self.records, self.source_checks, self.evidence = counting_fixture()
        self.context = compact.Context('object_counting', 'What is the exact count of monitor(s) present here?')
        self.answer = '3'
        self.rendered = compact.render_target(self.source, self.answer, self.records, self.context)

    def validate(self, rendered=None, **kwargs):
        arguments = {'source_lines': self.source, 'records': self.records, 'source_checks': self.source_checks,
                     'evidence_index': self.evidence, 'answer': self.answer, 'count_tokens': lambda text: 100,
                     'context': self.context}
        arguments.update(kwargs)
        return compact.admit(rendered or self.rendered, **arguments)

    def rejects(self, rendered, reason, **kwargs):
        result = self.validate(rendered, **kwargs)
        self.assertFalse(result['passed'])
        self.assertIn(reason, result['reason_codes'])
        return result

    def test_roster_supports_the_counted_answer(self):
        self.assertEqual(self.rendered.target,
                         'Observations (2)\n1. For the monitor, the recorded visible frames are 3, 4 and 7.\n'
                         '2. Distinct instances observed: monitor A, monitor B, monitor C.\n'
                         'End of reasoning.\n3')
        self.assertTrue(self.validate()['passed'], self.validate())

    def test_roster_binds_every_name_to_its_identity_record(self):
        roster = self.rendered.lines[-1]
        self.assertEqual((roster['index'], roster['id'], roster['kind']), (2, 'ROSTER', 'roster'))
        self.assertEqual([item['name'] for item in roster['identities']], ['monitor A', 'monitor B', 'monitor C'])
        for item, identity in zip(roster['identities'], self.records['identities']):
            self.assertEqual(item['record_sha256'], compact.digest_json(identity))

    def test_roster_count_must_equal_a_numeric_answer(self):
        self.source_checks['answer'] = '4'
        rendered = compact.render_target(self.source, '4', self.records, self.context)
        self.rejects(rendered, 'roster_answer_mismatch', answer='4')

    def test_roster_cannot_invent_an_instance(self):
        self.records['identities'].append({'id': 'I4', 'name': 'monitor D', 'label': 'monitor',
                                           'instance_id': '4', 'citations': ['E1.L4']})
        self.source_checks['answer'] = '4'
        rendered = compact.render_target(self.source, '4', self.records, self.context)
        self.assertIn('monitor D', rendered.target)
        self.rejects(rendered, 'roster_identity_mismatch', answer='4')

    def test_roster_cannot_omit_an_instance(self):
        target = self.rendered.target.replace(', monitor C', '')
        self.rejects(replace(self.rendered, target=target), 'byte_fidelity_changed')

    def test_identity_record_drift_fails_the_sidecar_binding(self):
        self.records['identities'][0]['citations'] = ['E1.L9']
        self.rejects(self.rendered, 'record_binding_failed')

    def test_only_the_counted_category_is_rostered(self):
        self.records['identities'].append({'id': 'I4', 'name': 'door', 'label': 'door',
                                           'instance_id': '4', 'citations': ['E1.L4']})
        rendered = compact.render_target(self.source, self.answer, self.records, self.context)
        self.assertIn('monitor A, monitor B, monitor C.', rendered.target)
        self.assertNotIn('door', rendered.target)

    def test_unresolved_category_defers(self):
        for question in ('How many chair(s) are here?', 'How many monitors are here?', ''):
            with self.subTest(question=question), self.assertRaisesRegex(compact.Deferral, 'roster_category_unresolved'):
                compact.render_target(self.source, self.answer, self.records,
                                      compact.Context('object_counting', question))

    def test_a_counting_trace_with_calculations_keeps_its_derivations(self):
        record = {'id': 'C0001', 'kind': 'calculation', 'citations': ['E2.L9'], 'operation': 'raw_result',
                  'operand_record_ids': []}
        self.records['calculations_v2'].append(record)
        self.source.append({**record, 'record_id': 'C0001', 'record_sha256': compact.digest_json(record),
                            'student_text': 'A numerical result is approximately 3 in unspecified units.',
                            'own_record_binding': True})
        self.evidence['lines'].append({'id': 'E2.L9', 'kind': 'tool_return'})
        rendered = compact.render_target(self.source, self.answer, self.records, self.context)
        self.assertNotIn('Distinct instances observed', rendered.target)
        self.assertIn('Derivations (1)', rendered.target)
        self.assertTrue(self.validate(rendered)['passed'])


class OperandFilterTests(unittest.TestCase):
    def setUp(self):
        self.source, self.records, self.source_checks, self.evidence = extent_fixture()
        self.context = compact.Context('object_size_estimation', 'How long is the trash bin?')
        self.rendered = compact.render_target(self.source, 'B', self.records, self.context)

    def validate(self, rendered=None, **kwargs):
        arguments = {'source_lines': self.source, 'records': self.records, 'source_checks': self.source_checks,
                     'evidence_index': self.evidence, 'answer': 'B', 'count_tokens': lambda text: 100,
                     'context': self.context}
        arguments.update(kwargs)
        return compact.admit(rendered or self.rendered, **arguments)

    def test_extent_keeps_only_the_operands_its_result_uses(self):
        self.assertIn('Uses observations 2, 3, 4.', self.rendered.target)
        self.assertEqual([line['id'] for line in compact.select_lines(self.source, self.records).observations],
                         ['A0001', 'M0020', 'M0022', 'M0023'])
        self.assertTrue(self.validate()['passed'], self.validate())

    def test_dropped_operands_leave_the_visible_target(self):
        selected = compact.select_lines(self.source, self.records)
        self.assertEqual([line['id'] for line in selected.omitted], ['M0019', 'M0021'])
        for identifier in ('centre is at', 'floor under'):
            self.assertNotIn(identifier, self.rendered.target)

    def test_sidecar_keeps_the_source_operand_list(self):
        operands = self.rendered.lines[-1]['operands']
        self.assertEqual(operands['operation'], 'extent_xyz')
        self.assertEqual(operands['source'], ['M0019', 'M0020', 'M0021', 'M0022', 'M0023'])
        self.assertEqual(operands['used'], ['M0020', 'M0022', 'M0023'])
        self.assertEqual(operands['dropped'], ['M0019', 'M0021'])
        self.assertEqual(operands['dropped_quantities'], {'M0019': 'centroid', 'M0021': 'floor_z_estimate'})

    def test_quantity_free_operands_lose_the_clause_and_keep_the_target(self):
        self.source, self.records, self.source_checks, self.evidence = extent_fixture('closest_point_distance')
        rendered = compact.render_target(self.source, 'B', self.records, self.context)
        self.assertNotIn('Uses observations', rendered.target)
        self.assertTrue(rendered.target.split('\n')[-3].endswith('0.304 meters along X.'))
        result = self.validate(rendered)
        self.assertTrue(result['passed'], result)
        self.assertEqual(result['unbound_derivations'], ['C0001'])
        self.assertEqual(result['operand_filter']['C0001']['kept'], [])

    def test_the_defer_policy_still_defers_an_unbound_derivation(self):
        self.source, self.records, self.source_checks, self.evidence = extent_fixture('closest_point_distance')
        rendered = compact.render_target(self.source, 'B', self.records, self.context)
        result = self.validate(rendered, unbound_policy='defer')
        self.assertFalse(result['passed'])
        self.assertEqual(result['reason_codes'], ['unbound_derivation'])

    def test_both_policies_render_the_same_bytes(self):
        self.source, self.records, self.source_checks, self.evidence = extent_fixture('closest_point_distance')
        rendered = compact.render_target(self.source, 'B', self.records, self.context)
        for policy in compact.UNBOUND_POLICIES:
            with self.subTest(policy=policy):
                result = self.validate(rendered, unbound_policy=policy)
                self.assertTrue(result['checks']['byte_fidelity'])
                self.assertEqual(result['unbound_derivations'], ['C0001'])
                self.assertEqual(result['passed'], policy == 'drop_clause')

    def test_unknown_operation_defers(self):
        self.source, self.records, self.source_checks, self.evidence = extent_fixture('mystery_operation')
        with self.assertRaisesRegex(compact.Deferral, 'unknown_operation'):
            compact.render_target(self.source, 'B', self.records, self.context)

    def test_every_operation_in_the_table_admits_the_kinds_the_sources_carry(self):
        self.assertEqual(compact.OPERAND_QUANTITIES['extent_xyz'], ('extent_xyz_p90', 'max_xyz_p95', 'min_xyz_p5'))
        self.assertEqual(compact.OPERAND_QUANTITIES['closest_point_distance'], ())
        self.assertNotIn('visibility', {kind for kinds in compact.OPERAND_QUANTITIES.values() for kind in kinds})


class UtilityTests(unittest.TestCase):
    def test_configuration_hash_changes_with_citation_mode(self):
        base = compact.renderer_config('tokenizer', False)
        alternate = compact.renderer_config('tokenizer', True)
        self.assertNotEqual(compact.digest_json(base), compact.digest_json(alternate))
        self.assertEqual(base['max_tokens'], 1536)

    def test_drop_clause_is_the_default_policy_and_defer_remains_available(self):
        self.assertEqual(compact.UNBOUND_POLICIES[0], 'drop_clause')
        self.assertEqual(compact.renderer_config('tokenizer')['unbound_policy'], 'drop_clause')
        self.assertEqual(compact.renderer_config('tokenizer', False, 'defer')['unbound_policy'], 'defer')
        self.assertNotEqual(compact.digest_json(compact.renderer_config('tokenizer')),
                            compact.digest_json(compact.renderer_config('tokenizer', False, 'defer')))
        with self.assertRaisesRegex(compact.Deferral, 'unknown_unbound_policy'):
            compact.renderer_config('tokenizer', False, 'keep_everything')

    def test_quantiles_use_linear_interpolation(self):
        self.assertEqual(compact.distribution([1, 2, 3, 4])['median'], 2.5)
        self.assertEqual(compact.distribution([1])['p99'], 1)
        self.assertIsNone(compact.distribution([])['max'])

    def test_stratification_is_seeded_and_covers_all_types(self):
        rows = [{'qid': f'{kind}_{index}', 'question_type': kind} for kind in 'abcdef' for index in range(12)]
        first = compact.pilot_sample(rows)
        self.assertEqual(first, compact.pilot_sample(list(reversed(rows))))
        self.assertEqual(len(first), 16)
        self.assertEqual(len({row['qid'] for row in first}), 16)
        self.assertEqual({row['question_type'] for row in first}, set('abcdef'))

    def test_protected_paths_are_rejected_before_open(self):
        for path in ('/data2/x/offline_labels/y.json', '/data2/x/answer_bank/y.json', '/data2/ANSWER_BANKS/x'):
            with self.subTest(path=path), self.assertRaisesRegex(compact.Deferral, 'protected_path'):
                compact.safe_path(path)

    def test_qid_path_traversal_is_rejected(self):
        for qid in ('../x', '/tmp/x', 'x/y', 'x\\y', '.'):
            with self.subTest(qid=qid), self.assertRaisesRegex(compact.Deferral, 'qid_schema'):
                compact.safe_qid(qid)


class GoldenTests(unittest.TestCase):
    def test_vsi590k_037500_matches_design_with_bare_answer(self):
        source = compact.load_json(RECOVERY / 'vsi590k_037500/rendered_lines.json')
        checks = compact.load_json(RECOVERY / 'vsi590k_037500/checks.json')
        records = compact.load_json(RECOVERY / 'vsi590k_037500/records.json')
        context = compact.Context('object_rel_direction_medium', 'Which direction is the chair from the door?')
        rendered = compact.render_target(source, checks['answer'], records, context)
        example = compact.safe_path(EXAMPLE).read_text(encoding='utf-8').splitlines()
        self.assertEqual(example[0], '# vsi590k_037500')
        self.assertEqual(example[-1], 'Answer: ' + checks['answer'])
        self.assertEqual(rendered.target, '\n'.join(example[1:-1] + [checks['answer']]))
        result = compact.admit(rendered, source, records, checks,
                               compact.load_json(RECOVERY / 'vsi590k_037500/evidence_index.json'),
                               checks['answer'], lambda text: len(text.split()), context)
        self.assertTrue(result['passed'], result)


if __name__ == '__main__':
    unittest.main()
