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
    records = {'records': [], 'appearances': [], 'calculations_v2': [], 'qualifications_v2': [], 'conventions_v2': []}
    groups = {'appearance': 'appearances', 'measurement': 'records', 'calculation': 'calculations_v2',
              'qualification': 'qualifications_v2', 'convention': 'conventions_v2'}
    lines, evidence = [], []
    for number, (identifier, kind, text) in enumerate(definitions, 1):
        citations = [f'E1.L{number}']
        record = {'id': identifier, 'kind': kind, 'citations': citations}
        if kind == 'calculation':
            record['operand_record_ids'] = ['M0001', 'M0002']
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
        self.rendered = compact.render_target(self.source, 'B')

    def validate(self, rendered=None, **kwargs):
        arguments = {'source_lines': self.source, 'records': self.records, 'source_checks': self.source_checks,
                     'evidence_index': self.evidence, 'answer': 'B', 'count_tokens': lambda text: 100}
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
        selected = compact.select_lines(self.source)
        self.assertEqual([line['id'] for line in selected.observations], ['A0001', 'M0001', 'M0002'])
        self.assertEqual([line['id'] for line in selected.derivations], ['C0001'])
        self.assertEqual([line['id'] for line in selected.omitted], ['Q0001', 'M0003', 'V0001'])

    def test_unreferenced_measurements_do_not_select_themselves(self):
        source = [line for line in self.source if line['kind'] != 'calculation']
        self.assertEqual([line['id'] for line in compact.select_lines(source).observations], ['A0001'])

    def test_referenced_qualification_is_selected(self):
        self.source[5]['student_text'] = 'A calculation. Operands: Q0001.'
        self.assertEqual([line['id'] for line in compact.select_lines(self.source).observations], ['A0001', 'Q0001'])

    def test_repeated_operands_do_not_repeat_observations(self):
        self.source[5]['student_text'] += ' Operands: M0001, M0002.'
        selected = compact.select_lines(self.source)
        self.assertEqual(len(selected.observations), 3)
        rendered = compact.render_target(self.source, 'B')
        self.assertEqual(rendered.target.count('Uses observations 2, 3.'), 2)

    def test_operand_order_is_preserved(self):
        self.source[5]['student_text'] = 'A calculation. Operands: M0002, M0001.'
        self.assertIn('Uses observations 3, 2.', compact.render_target(self.source, 'B').target)

    def test_calculation_without_operands_is_preserved(self):
        self.source[5]['student_text'] = 'A numerical result is approximately 3.0 in unspecified units.'
        rendered = compact.render_target(self.source, 'B')
        self.assertIn('Derivations (1)', rendered.target)
        self.assertNotIn('Uses observations', rendered.target)

    def test_dangling_operand_defers(self):
        self.source[5]['student_text'] = 'A calculation. Operands: M9999.'
        with self.assertRaisesRegex(compact.Deferral, 'unresolved_operand'):
            compact.select_lines(self.source)

    def test_malformed_operand_clause_defers(self):
        for suffix in ('Operands:', 'Operands: M0001', 'Operands: M0001 and M0002.', 'Operands: nonsense.'):
            with self.subTest(suffix=suffix):
                self.source[5]['student_text'] = 'A calculation. ' + suffix
                with self.assertRaisesRegex(compact.Deferral, 'malformed_operands'):
                    compact.select_lines(self.source)

    def test_convention_cannot_become_an_observation(self):
        self.source[5]['student_text'] = 'A calculation. Operands: V0001.'
        with self.assertRaisesRegex(compact.Deferral, 'invalid_operand_kind'):
            compact.select_lines(self.source)

    def test_calculation_cannot_become_an_observation(self):
        self.source[5]['student_text'] = 'A calculation. Operands: C0001.'
        with self.assertRaisesRegex(compact.Deferral, 'invalid_operand_kind'):
            compact.select_lines(self.source)

    def test_duplicate_source_ids_defer(self):
        self.source.append(copy.deepcopy(self.source[0]))
        with self.assertRaisesRegex(compact.Deferral, 'duplicate_line_id'):
            compact.select_lines(self.source)

    def test_multiline_source_is_not_silently_reflowed(self):
        self.source[0]['student_text'] += '\nAnother sentence.'
        with self.assertRaisesRegex(compact.Deferral, 'source_line_schema'):
            compact.select_lines(self.source)


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

    def test_empty_derivations_have_no_header(self):
        source = [line for line in self.source if line['kind'] != 'calculation']
        rendered = compact.render_target(source, 'B')
        self.assertEqual(rendered.target, 'Observations (1)\n1. The lamp is visible in frame 1.\nEnd of reasoning.\nB')
        self.assertTrue(self.validate(rendered, source_lines=source)['passed'])

    def test_derivation_citations_are_opt_in_and_derivations_only(self):
        rendered = compact.render_target(self.source, 'B', derivation_citations=True)
        self.assertIn('Uses observations 2, 3. [E1.L6]', rendered.target)
        self.assertEqual(rendered.target.count('['), 1)
        self.assertTrue(self.validate(rendered, derivation_citations=True)['passed'])

    def test_citation_ranges_are_lossless_and_sorted(self):
        citations = ['E2.L9', 'E1.L3', 'E1.L1', 'E1.L2', 'E2.L9', 'E2.L11']
        self.assertEqual(compact.citation_suffix(citations), ' [E1.L1-L3, E2.L9, E2.L11]')

    def test_reference_replacement_preserves_suffix_bytes(self):
        self.source[5]['student_text'] += ' Precision stays unchanged.'
        rendered = compact.render_target(self.source, 'B')
        self.assertIn('Uses observations 2, 3. Precision stays unchanged.', rendered.target)
        self.assertTrue(self.validate(rendered)['passed'])

    def test_utf8_text_remains_byte_identical(self):
        self.source[0]['student_text'] = 'The café’s lamp is visible in frame 1.'
        rendered = compact.render_target(self.source, 'B')
        self.assertEqual(rendered.target.split('\n')[1][3:].encode(), self.source[0]['student_text'].encode())
        self.assertTrue(self.validate(rendered)['passed'])

    def test_numeric_answer_is_copied_without_numeric_grounding_from_observations(self):
        self.source_checks['answer'] = '24'
        rendered = compact.render_target(self.source, '24')
        self.assertTrue(self.validate(rendered, answer='24')['passed'])
        self.assertTrue(rendered.target.endswith('End of reasoning.\n24'))

    def test_answer_whitespace_is_not_normalized(self):
        for answer in (' B', 'B ', 'B\n', 'Answer: B', ''):
            with self.subTest(answer=answer), self.assertRaisesRegex(compact.Deferral, 'answer_schema'):
                compact.render_target(self.source, answer)


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
        rendered = compact.render_target(source, 'B')
        self.rejects(rendered, 'no_selected_observations', source_lines=source)

    def test_default_inline_citations_fail(self):
        self.rejects(self.changed('1. The lamp is visible in frame 1.', '1. The lamp is visible in frame 1. [E1.L1]'), 'citation_policy_failed')

    def test_variant_does_not_allow_observation_citations(self):
        rendered = compact.render_target(self.source, 'B', derivation_citations=True)
        rendered = replace(rendered, target=rendered.target.replace('frame 1.', 'frame 1. [E1.L1]', 1))
        self.rejects(rendered, 'citation_policy_failed', derivation_citations=True)

    def test_variant_requires_exact_derivation_citations(self):
        rendered = compact.render_target(self.source, 'B', derivation_citations=True)
        rendered = replace(rendered, target=rendered.target.replace('[E1.L6]', '[E1.L7]'))
        self.rejects(rendered, 'citation_policy_failed', derivation_citations=True)

    def test_calculation_operands_must_match_typed_record(self):
        self.records['calculations_v2'][0]['operand_record_ids'] = ['M0001']
        self.source[5]['record_sha256'] = compact.digest_json(self.records['calculations_v2'][0])
        rendered = compact.render_target(self.source, 'B')
        self.rejects(rendered, 'source_tier_i_failed')

    def select_qualification(self):
        original = {'id': 'Q_SOURCE', 'scope': {'object': 'lamp'}, 'source_text': self.source[2]['student_text']}
        self.records['qualifications'] = [original]
        qualification = self.records['qualifications_v2'][0]
        qualification.update(source_qualification_id=original['id'], scope=copy.deepcopy(original['scope']),
                             source_text=original['source_text'], source_scope_sha256=compact.digest_json(original['scope']),
                             student_text=original['source_text'])
        self.source[2]['record_sha256'] = compact.digest_json(qualification)
        self.records['calculations_v2'][0]['operand_record_ids'] = ['Q0001']
        self.source[5]['record_sha256'] = compact.digest_json(self.records['calculations_v2'][0])
        self.source[5]['student_text'] = 'The distance is approximately 3.0 meters. Operands: Q0001.'
        return compact.render_target(self.source, 'B')

    def test_selected_qualification_preserves_original_scope(self):
        self.assertTrue(self.validate(self.select_qualification())['passed'])

    def test_selected_qualification_rejects_scope_drift(self):
        rendered = self.select_qualification()
        self.records['qualifications'][0]['scope']['object'] = 'desk'
        self.rejects(rendered, 'source_tier_i_failed')


class UtilityTests(unittest.TestCase):
    def test_configuration_hash_changes_with_citation_mode(self):
        base = compact.renderer_config('tokenizer', False)
        alternate = compact.renderer_config('tokenizer', True)
        self.assertNotEqual(compact.digest_json(base), compact.digest_json(alternate))
        self.assertEqual(base['max_tokens'], 1536)

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
        rendered = compact.render_target(source, checks['answer'])
        example = compact.safe_path(EXAMPLE).read_text(encoding='utf-8').splitlines()
        self.assertEqual(example[0], '# vsi590k_037500')
        self.assertEqual(example[-1], 'Answer: ' + checks['answer'])
        self.assertEqual(rendered.target, '\n'.join(example[1:-1] + [checks['answer']]))
        result = compact.admit(rendered, source, compact.load_json(RECOVERY / 'vsi590k_037500/records.json'),
                               checks, compact.load_json(RECOVERY / 'vsi590k_037500/evidence_index.json'),
                               checks['answer'], lambda text: len(text.split()))
        self.assertTrue(result['passed'], result)


if __name__ == '__main__':
    unittest.main()
