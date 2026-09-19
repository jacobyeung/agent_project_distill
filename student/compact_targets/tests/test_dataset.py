import copy
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from student.compact_targets import compact_counted_v1 as compact
from student.compact_targets.tests.test_compact_counted_v1 import fixture


OLD_COMMIT = 'a' * 40
NEW_COMMIT = 'b' * 40


class DatasetTests(unittest.TestCase):
    def setUp(self):
        parent = Path(os.environ.get('COMPACT_TEST_OUTPUT', '/data2/jjyeung/agent_project_data/devin_lane_out/converter_compact_v1_20260919_out/tests'))
        parent.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix=self._testMethodName + '_', dir=parent))
        self.reviewed = self.root / 'reviewed'
        self.recovery = self.root / 'recovery'
        self.output = self.root / 'compact'
        self.entries = []
        self.config = compact.renderer_config('synthetic-tokenizer')
        self.config['source_index'] = 'synthetic-fixture'

    def add_source(self, number, mutate=None):
        lines, records, checks, evidence = fixture()
        qid = f'vsi590k_{number:06d}'
        if mutate:
            mutate(lines, records, checks, evidence)
        checks.update(qid=qid, artifacts={})
        for name, value in (('rendered_lines', lines), ('records', records), ('evidence_index', evidence)):
            checks['artifacts'][name] = compact.save(self.recovery / qid / (name + '.json'), value)
        compact.save(self.recovery / qid / 'checks.json', checks)
        inputs = {'question': 'Synthetic input only.', 'options': ['First', 'Second'],
                  'frames': [{'path': f'/synthetic/frame_{index}.png', 'sha256': 'd' * 64} for index in range(32)],
                  'frame_indices': list(range(32)), 'timestamps': list(range(32)), 'fps': 1.0, 'total_num_frames': 32}
        row = {'qid': qid, 'category': 'synthetic', 'dataset': 'synthetic', 'scene': f'scene{number}',
               'generation_commit': OLD_COMMIT, 'validation_commit': OLD_COMMIT, 'config_sha256': 'c' * 64,
               'student_input': inputs, 'target': 'Observations\nA0001. Source prose.\nB',
               'native_answer_archive': {'native_final': '<ANSWER>B</ANSWER>'}, 'other_metadata': {'preserve': True}}
        row_pin = compact.save(self.reviewed / 'targets' / qid / 'row.json', row)
        target_pin = compact.save(self.reviewed / 'targets' / qid / 'target.txt', row['target'].encode())
        entry = {'qid': qid, 'question_type': 'synthetic', 'dataset': 'synthetic', 'scene': row['scene'],
                 'pool': 'clean_vsi590k', 'answer': 'B', 'generation_commit': OLD_COMMIT, 'validation_commit': OLD_COMMIT,
                 'config_sha256': 'c' * 64, 'postprocess': 'strip_calculations_v1', 'source_index_sha256': 'e' * 64,
                 'row_path': row_pin['path'], 'row_sha256': row_pin['sha256'],
                 'target_path': target_pin['path'], 'sha256': target_pin['sha256'], 'tier_i': checks['tier_i']}
        self.entries.append(entry)
        return entry, row

    def index(self):
        path = self.reviewed / 'candidate_index.jsonl'
        compact.save(path, ''.join(json.dumps(row, sort_keys=True) + '\n' for row in self.entries).encode())
        return path

    def build(self, count_tokens=lambda text: 100, **kwargs):
        return compact.build_dataset(self.index(), self.recovery, self.output, self.config, NEW_COMMIT, count_tokens, **kwargs)

    def test_roundtrip_preserves_rows_and_exact_index_schema(self):
        original_entry, original_row = self.add_source(1)
        result = self.build()
        candidates = compact.load_jsonl(self.output / 'candidate_index.jsonl')
        self.assertEqual(result['candidate_count'], 1)
        self.assertEqual(result['deferred_count'], 0)
        entry = candidates[0]
        row = compact.load_json(entry['row_path'])
        self.assertEqual(row, {**original_row, 'target': row['target'], 'generation_commit': NEW_COMMIT,
                               'config_sha256': compact.digest_json(self.config),
                               'source_generation_commit': OLD_COMMIT, 'source_config_sha256': 'c' * 64})
        self.assertEqual(set(entry), set(original_entry))
        self.assertEqual(entry['generation_commit'], NEW_COMMIT)
        self.assertEqual(row['generation_commit'], NEW_COMMIT)
        self.assertEqual(entry['config_sha256'], compact.digest_json(self.config))
        self.assertEqual(compact.binding(entry['row_path'])['sha256'], entry['row_sha256'])
        self.assertEqual(compact.binding(entry['target_path'])['sha256'], entry['sha256'])
        self.assertEqual(compact.verify_dataset(self.output, lambda text: 100)['status'], 'VERIFIED')

    def test_row_agrees_with_its_candidate_on_every_trainer_compared_field(self):
        _, original_row = self.add_source(1)
        self.build()
        entry = compact.load_jsonl(self.output / 'candidate_index.jsonl')[0]
        row = compact.load_json(entry['row_path'])
        for row_key, index_key in compact.ROW_ALIGNED_FIELDS:
            with self.subTest(field=row_key):
                self.assertEqual(row[row_key], entry[index_key])
        self.assertEqual(row['generation_commit'], NEW_COMMIT)
        self.assertEqual(row['source_generation_commit'], original_row['generation_commit'])
        self.assertEqual(row['source_config_sha256'], original_row['config_sha256'])
        self.assertNotIn('source_validation_commit', row)
        self.assertEqual(compact.verify_dataset(self.output, lambda text: 100)['status'], 'VERIFIED')

    def test_aligned_row_keeps_the_reviewed_values_and_refuses_a_conflicting_key(self):
        identity = {'qid': 'q', 'scene': 's', 'question_type': 'c', 'dataset': 'd', 'generation_commit': NEW_COMMIT,
                    'validation_commit': NEW_COMMIT, 'config_sha256': 'f' * 64}
        source = {'qid': 'q', 'scene': 's', 'category': 'c', 'dataset': 'd', 'generation_commit': OLD_COMMIT,
                  'validation_commit': OLD_COMMIT, 'config_sha256': 'c' * 64, 'target': 'old', 'keep': 1}
        self.assertEqual(compact.aligned_row(source, identity, 'new'),
                         {**source, 'target': 'new', 'generation_commit': NEW_COMMIT, 'validation_commit': NEW_COMMIT,
                          'config_sha256': 'f' * 64, 'source_generation_commit': OLD_COMMIT,
                          'source_validation_commit': OLD_COMMIT, 'source_config_sha256': 'c' * 64})
        with self.assertRaisesRegex(compact.Deferral, 'source_provenance_key_conflict'):
            compact.aligned_row({**source, 'source_generation_commit': 'kept'}, identity, 'new')
        with self.assertRaisesRegex(compact.Deferral, 'candidate_field_missing'):
            compact.aligned_row(source, {key: value for key, value in identity.items() if key != 'dataset'}, 'new')

    def test_verifier_rejects_row_provenance_drift(self):
        self.add_source(1)
        self.build()
        entry = compact.load_jsonl(self.output / 'candidate_index.jsonl')[0]
        row_path = Path(entry['row_path'])
        row = compact.load_json(row_path)
        row['generation_commit'] = OLD_COMMIT
        row_path.write_bytes(compact.canonical_bytes(row))
        with self.assertRaisesRegex(compact.Deferral, 'source_hash_mismatch'):
            compact.verify_dataset(self.output, lambda text: 100)

    def test_failed_sources_stay_in_denominator_and_do_not_block_good_sources(self):
        self.add_source(1)
        self.add_source(2, lambda lines, records, checks, evidence: lines[0].update(student_text='LONG source text.'))
        self.add_source(3, lambda lines, records, checks, evidence: lines.__setitem__(slice(None), [lines[1]]))
        self.add_source(4, lambda lines, records, checks, evidence: checks['tier_i']['checks'].update(artifact_lint='defect'))
        result = self.build(count_tokens=lambda text: 1537 if 'LONG' in text else 100)
        self.assertEqual(result['candidate_count'], 1)
        self.assertEqual(result['deferred_count'], 3)
        membership = compact.load_json(self.output / 'MEMBERSHIP.json')
        self.assertEqual(membership['intersection_count'], 4)
        reasons = {entry['qid']: entry['reason_codes'] for entry in compact.load_jsonl(self.output / 'DEFERRED.jsonl')}
        self.assertEqual(reasons['vsi590k_000002'], ['over_budget'])
        self.assertEqual(reasons['vsi590k_000003'], ['no_selected_observations'])
        self.assertIn('source_tier_i_failed', reasons['vsi590k_000004'])

    def test_recovery_only_qid_is_not_in_denominator(self):
        self.add_source(1)
        (self.recovery / 'vsi590k_000099').mkdir()
        result = self.build()
        membership = compact.load_json(result['membership']['path'])
        self.assertEqual(membership['recovery_count'], 2)
        self.assertEqual(membership['intersection_count'], 1)
        self.assertEqual(membership['recovery_not_reviewed'], ['vsi590k_000099'])

    def test_missing_source_file_defers_only_that_qid(self):
        self.add_source(1)
        entry, _ = self.add_source(2)
        (self.recovery / entry['qid'] / 'records.json').rename(self.recovery / entry['qid'] / 'records.retained.json')
        result = self.build()
        self.assertEqual(result['candidate_count'], 1)
        self.assertEqual(result['deferred_count'], 1)
        self.assertIn('source_load_error', result['dispositions'][1]['reason_codes'])

    def test_source_hash_drift_defers(self):
        entry, _ = self.add_source(1)
        path = self.recovery / entry['qid'] / 'rendered_lines.json'
        path.write_bytes(path.read_bytes() + b'\n')
        result = self.build()
        self.assertEqual(result['candidate_count'], 0)
        self.assertEqual(result['dispositions'][0]['reason_codes'], ['source_hash_mismatch'])

    def test_input_target_hash_drift_defers(self):
        entry, _ = self.add_source(1)
        Path(entry['target_path']).write_text('Changed target\nB')
        result = self.build()
        self.assertEqual(result['dispositions'][0]['reason_codes'], ['source_hash_mismatch'])

    def test_source_answer_mismatch_defers(self):
        self.add_source(1)
        self.entries[0]['answer'] = 'A'
        result = self.build()
        self.assertEqual(result['dispositions'][0]['reason_codes'], ['source_answer_mismatch'])

    def test_source_identity_mismatch_defers(self):
        self.add_source(1)
        self.entries[0]['scene'] = 'foreign-scene'
        result = self.build()
        self.assertEqual(result['dispositions'][0]['reason_codes'], ['source_identity_mismatch'])

    def test_duplicate_index_qid_refuses_before_output(self):
        entry, _ = self.add_source(1)
        self.entries.append(copy.deepcopy(entry))
        with self.assertRaisesRegex(compact.Deferral, 'duplicate_candidate_qid'):
            self.build()
        self.assertFalse(self.output.exists())

    def test_output_is_immutable_and_files_remain(self):
        self.add_source(1)
        self.build()
        before = compact.binding(self.output / 'candidate_index.jsonl')
        with self.assertRaisesRegex(compact.Deferral, 'immutable_output_exists'):
            self.build()
        self.assertEqual(compact.binding(self.output / 'candidate_index.jsonl'), before)

    def test_omitted_lines_are_retained_in_checks_sidecar(self):
        self.add_source(1)
        self.build()
        checks = compact.load_json(self.output / 'targets/vsi590k_000001/checks.json')
        self.assertEqual([line['id'] for line in checks['omitted_lines']], ['Q0001', 'M0003', 'V0001'])
        self.assertTrue(all('student_text' in line and 'record_sha256' in line for line in checks['omitted_lines']))

    def test_pilot_writes_both_variants_and_budget_failures_are_visible(self):
        self.add_source(1)
        self.build(count_tokens=lambda text: 2000 if '[E' in text else 100)
        sample = compact.load_json(self.output / 'PILOT_SAMPLE_16.json')
        self.assertEqual(sample['seed'], 17)
        self.assertEqual(sample['count'], 1)
        item = sample['samples'][0]
        self.assertTrue(item['default']['passed'])
        self.assertFalse(item['derivation_citations']['passed'])
        self.assertEqual(item['derivation_citations']['reason_codes'], ['over_budget'])
        for variant in ('default', 'derivation_citations'):
            self.assertTrue(Path(item[variant]['artifacts']['target']['path']).is_file())
        self.assertEqual(compact.load_jsonl(self.root / 'pilot_variant_derivation_citations/candidate_index.jsonl'), [])

    def test_verifier_detects_changed_target_bytes(self):
        self.add_source(1)
        self.build()
        target = self.output / 'targets/vsi590k_000001/target.txt'
        target.write_bytes(target.read_bytes() + b'\n')
        with self.assertRaisesRegex(compact.Deferral, 'source_hash_mismatch'):
            compact.verify_dataset(self.output, lambda text: 100)

    def test_json_loader_rejects_duplicates_and_nonfinite_numbers(self):
        for payload in (b'{"qid": "x", "qid": "y"}', b'{"value": NaN}', b'{"value": Infinity}'):
            with self.subTest(payload=payload), self.assertRaises(compact.Deferral):
                compact.decode_json(payload)

    def test_saved_json_uses_source_record_canonical_hash_convention(self):
        value = {'z': 'café', 'a': 1}
        pin = compact.save(self.root / 'canonical.json', value)
        self.assertEqual(pin['sha256'], compact.digest_json(value))
        self.assertEqual(Path(pin['path']).read_bytes(), b'{\n  "a": 1,\n  "z": "caf\xc3\xa9"\n}\n')

    def test_missing_source_pin_defers(self):
        entry, _ = self.add_source(1)
        path = self.recovery / entry['qid'] / 'checks.json'
        checks = compact.load_json(path)
        checks['artifacts']['records'].pop('sha256')
        path.write_bytes(compact.canonical_bytes(checks))
        result = self.build()
        self.assertEqual(result['dispositions'][0]['reason_codes'], ['source_pin_missing'])

    def test_verifier_replays_deferred_and_pilot_budget_checks(self):
        self.add_source(1)
        self.add_source(2, lambda lines, records, checks, evidence: lines[0].update(student_text='LONG source text.'))
        counter = lambda text: 2000 if 'LONG' in text or '[E' in text else 100
        self.build(count_tokens=counter)
        receipt = compact.verify_dataset(self.output, counter)
        self.assertEqual((receipt['candidates'], receipt['deferred'], receipt['pilot_variants']), (1, 1, 1))
        self.assertTrue(receipt['all_rendered_admission_checks_replayed'])

    def test_verifier_authenticates_pilot_sample(self):
        self.add_source(1)
        self.build()
        path = self.output / 'PILOT_SAMPLE_16.json'
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(compact.Deferral, 'source_hash_mismatch'):
            compact.verify_dataset(self.output, lambda text: 100)

    def test_verifier_rejects_rehashed_index_metadata_drift(self):
        self.add_source(1)
        self.build()
        path = self.output / 'candidate_index.jsonl'
        entries = compact.load_jsonl(path)
        entries[0]['pool'] = 'foreign_pool'
        path.write_text(json.dumps(entries[0]) + '\n')
        manifest_path = self.output / 'MANIFEST.json'
        manifest = compact.load_json(manifest_path)
        manifest['candidate_index'] = compact.binding(path)
        manifest_path.write_bytes(compact.canonical_bytes(manifest))
        with self.assertRaisesRegex(compact.Deferral, 'candidate_index_changed'):
            compact.verify_dataset(self.output, lambda text: 100)

    def test_citation_cli_requires_a_bounded_pilot(self):
        self.add_source(1)
        arguments = ['render', '--candidate-index', str(self.index()), '--recovery-root', str(self.recovery),
                     '--output', str(self.output), '--derivation-citations']
        with patch.object(compact, 'tokenizer_counter', return_value=(lambda text: 100, {})), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as missing:
                compact.main(arguments)
            self.assertEqual(missing.exception.code, 2)
            sample = self.root / 'oversized_pilot.json'
            compact.save(sample, {'samples': [{'qid': f'vsi590k_{number:06d}'} for number in range(17)]})
            with self.assertRaises(SystemExit) as oversized:
                compact.main(arguments + ['--pilot-sample', str(sample)])
            self.assertEqual(oversized.exception.code, 2)
        self.assertFalse(self.output.exists())

    def test_sidecar_suffix_keeps_a_rerender_beside_the_first_set(self):
        entry, _ = self.add_source(1)
        arguments = ['render', '--candidate-index', str(self.index()), '--recovery-root', str(self.recovery),
                     '--tokenizer', str(self.root / 'synthetic-tokenizer')]
        provenance = lambda config: {'repo_commit': NEW_COMMIT, 'dirty': False, 'config_sha256': compact.binding(config)['sha256']}
        with patch.object(compact, 'tokenizer_counter', return_value=(lambda text: 100, {})), \
                patch('tools.provenance.provenance', side_effect=provenance), redirect_stdout(io.StringIO()):
            self.assertEqual(compact.main(arguments + ['--output', str(self.output)]), 0)
            self.assertEqual(compact.main(arguments + ['--output', str(self.root / 'compact_v1b'),
                                                       '--sidecar-suffix', '_v1b']), 0)
        for name in ('CONFIG_compact.json', 'CONFIG_compact_v1b.json', 'PROVENANCE_compact.json',
                     'PROVENANCE_compact_v1b.json', 'pilot_variant_derivation_citations/CONFIG.json',
                     'pilot_variant_derivation_citations_v1b/CONFIG.json'):
            self.assertTrue((self.root / name).is_file(), name)
        self.assertEqual([row['qid'] for row in compact.load_jsonl(self.root / 'compact_v1b/candidate_index.jsonl')],
                         [entry['qid']])
        self.assertEqual(compact.verify_dataset(self.root / 'compact_v1b', lambda text: 100)['status'], 'VERIFIED')

    def test_citation_cli_renders_only_selected_pilot(self):
        entry, _ = self.add_source(1)
        self.add_source(2)
        sample = self.root / 'pilot.json'
        compact.save(sample, {'samples': [{'qid': entry['qid']}]})
        arguments = ['render', '--candidate-index', str(self.index()), '--recovery-root', str(self.recovery),
                     '--output', str(self.output), '--tokenizer', str(self.root / 'synthetic-tokenizer'),
                     '--derivation-citations', '--pilot-sample', str(sample)]
        provenance = lambda config: {'repo_commit': NEW_COMMIT, 'dirty': False, 'config_sha256': compact.binding(config)['sha256']}
        with patch.object(compact, 'tokenizer_counter', return_value=(lambda text: 100, {})), \
                patch('tools.provenance.provenance', side_effect=provenance), redirect_stdout(io.StringIO()):
            self.assertEqual(compact.main(arguments), 0)
        entries = compact.load_jsonl(self.output / 'candidate_index.jsonl')
        self.assertEqual([item['qid'] for item in entries], [entry['qid']])
        target = Path(entries[0]['target_path']).read_text()
        self.assertEqual(target.count('[E'), 1)
        self.assertEqual(compact.verify_dataset(self.output, lambda text: 100)['status'], 'VERIFIED')


if __name__ == '__main__':
    unittest.main()
