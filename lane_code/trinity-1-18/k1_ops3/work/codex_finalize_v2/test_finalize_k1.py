"""CPU-only tests using the real reader and immutable receipt snapshots in memory."""
import copy
from pathlib import Path
import unittest

import finalize_k1 as k1


class FinalizeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = k1.load_bundle()
        cls.tokens = k1.first_tokens(cls.bundle['data']['tokens'])
        cls.output = k1.finalize(cls.bundle)

    def test_real_receipts_and_timing_counts(self):
        self.assertTrue(self.output['production_ready'])
        self.assertTrue(self.output['frame_staging_authorized'])
        self.assertEqual(self.output['k1_finalize']['failed'], [])
        self.assertEqual(self.output['k1_finalize']['timing']['source_counts'],
                         {'d12_mp4': 138, 'frame_rates_07ca49df': 0, 'null': 162})
        self.assertEqual(self.output['k1_finalize']['timing']['failures'], {})
        self.assertEqual(len(self.output['k1_finalize']['timing']['arkit']['missing']), 75)

    def test_each_failed_receipt_keeps_both_flags_false(self):
        mutations = {
            'verify_mp4': lambda d: d.update(verify_mp4='{"checked": 138, "bad": ["bad"]}'),
            'wd': lambda d: d['wd'][0].update(error='planted decode error'),
            'wa': lambda d: d['wa'][0].update(misses=[12]),
            'parity': lambda d: d['parity'].update(pass_=False),
            'substitutions': lambda d: d['substitutions'][0].update(frames=[]),
            'accept': lambda d: d['accept'].update(anchors_ok=299),
        }
        for name, mutate in mutations.items():
            with self.subTest(receipt=name):
                bundle = copy.deepcopy(self.bundle)
                mutate(bundle['data'])
                output = k1.finalize(bundle)
                self.assertFalse(output['production_ready'])
                self.assertFalse(output['frame_staging_authorized'])
                self.assertIn(name, output['k1_finalize']['failed'])

    def test_missing_receipt_fails_closed(self):
        bundle = copy.deepcopy(self.bundle)
        bundle['data'].pop('wa')
        bundle['sources']['wa'].update(sha256=None, error='missing receipt')
        output = k1.finalize(bundle)
        self.assertFalse(output['production_ready'])
        self.assertFalse(output['frame_staging_authorized'])
        self.assertIn('wa', output['k1_finalize']['failed'])

    def test_duplicate_and_wrong_receipt_tokens_fail(self):
        for replacement in (self.bundle['data']['wd'][1]['s'], 'unselected_token'):
            with self.subTest(token=replacement):
                data = copy.deepcopy(self.bundle['data'])
                data['wd'][0]['s'] = replacement
                checks = k1.verify_receipts(self.bundle['manifest'], data,
                                           self.bundle['sources'], self.tokens)
                self.assertFalse(checks['wd']['passed'])

    def test_parity_uses_imported_json_digest_not_file_hash(self):
        receipt = self.output['k1_finalize']['receipts']['parity']
        self.assertEqual(receipt['details']['json_sha256'],
                         self.bundle['manifest']['k1a_frame_parity']['sha256'])
        self.assertNotEqual(receipt['sha256'], receipt['details']['json_sha256'])
        data = copy.deepcopy(self.bundle['data'])
        data['parity']['store_bytes'] += 1
        checks = k1.verify_receipts(self.bundle['manifest'], data,
                                   self.bundle['sources'], self.tokens)
        self.assertFalse(checks['parity']['passed'])

    def complete_rates_fixture(self):
        """Synthetic coverage exists only in memory; never publish these fixtures."""
        data = copy.deepcopy(self.bundle['data'])
        data['frame_rates']['missing_arkit_scenes'] = []
        for canonical, token in self.tokens.items():
            if canonical.startswith('arkitscenes/'):
                data['frame_rates']['by_scene']['d3/' + token] = 10.0
        return data

    def test_missing_one_arkit_token_clears_every_arkit_timing(self):
        data = self.complete_rates_fixture()
        manifest = copy.deepcopy(self.output)
        arkit = [c for c in manifest['captures'] if c['canonical'].startswith('arkitscenes/')]
        missing = arkit[-1]['canonical']
        data['frame_rates']['by_scene'].pop('d3/' + self.tokens[missing])
        # Seed stale non-null fields to verify that an all-or-none refusal clears them.
        for capture in arkit:
            capture['model_row']['student_input'].update(fps=10, timestamps=[1]*32, total_num_frames=999)
        result = k1.fill_timing(manifest, data, self.bundle['sources'], self.tokens)
        self.assertEqual(result['arkit']['missing'], [missing])
        for capture in arkit:
            self.assertEqual(capture['timing_source'], 'null')
            self.assertTrue(all(capture['model_row']['student_input'][key] is None for key in k1.TIMING_KEYS))

    def test_arkit_reader_refusal_is_atomic(self):
        data = self.complete_rates_fixture()
        manifest = copy.deepcopy(self.bundle['manifest'])
        arkit = [c for c in manifest['captures'] if c['canonical'].startswith('arkitscenes/')]
        data['frame_rates']['by_scene']['d3/' + self.tokens[arkit[-1]['canonical']]] = 0
        result = k1.fill_timing(manifest, data, self.bundle['sources'], self.tokens)
        self.assertFalse(result['arkit']['applied'])
        self.assertIn('frame rate', result['arkit']['reason'])
        self.assertTrue(all(c['timing_source'] == 'null' for c in arkit))
        self.assertTrue(all(c['model_row']['student_input'][key] is None
                            for c in arkit for key in k1.TIMING_KEYS))

    def test_bad_sealed_hash_clears_arkit_timing(self):
        manifest = copy.deepcopy(self.bundle['manifest'])
        sources = copy.deepcopy(self.bundle['sources'])
        sources['frame_rates']['sha256'] = '0' * 64
        result = k1.fill_timing(manifest, self.complete_rates_fixture(), sources, self.tokens)
        self.assertEqual(result['arkit']['reason'], 'Sealed frame-rate SHA256 mismatch')
        self.assertEqual(result['source_counts']['frame_rates_07ca49df'], 0)

    def test_complete_arkit_authority_uses_reader_and_marks_count_lower_bound(self):
        manifest = copy.deepcopy(self.bundle['manifest'])
        result = k1.fill_timing(manifest, self.complete_rates_fixture(),
                               self.bundle['sources'], self.tokens)
        self.assertTrue(result['arkit']['applied'])
        self.assertEqual(result['source_counts']['frame_rates_07ca49df'], 162)
        for canonical, proof in result['reader_results'].items():
            self.assertEqual(proof['total_num_frames_lower_bound'], canonical.startswith('arkitscenes/'))

    def test_planted_positive_wrong_fps_fails_reader_authority_check(self):
        capture = next(c for c in self.bundle['manifest']['captures'] if c['canonical'].startswith('scannet/'))
        token = self.tokens[capture['canonical']]
        original = k1.unique_rows(self.bundle['data']['d12'])[token]
        with self.assertRaisesRegex(ValueError, 'inconsistent with its native scene'):
            k1.resolve_timing(capture, token, original['fps'] * 2, original['n'], original['fps'])

    def test_planted_output_fps_fails_reader_timestamp_check(self):
        capture = next(c for c in self.output['captures'] if c['timing_source'] == 'd12_mp4')
        inputs = copy.deepcopy(capture['model_row']['student_input'])
        inputs['fps'] *= 2
        _, patch_times = k1.reader_functions()
        with self.assertRaisesRegex(ValueError, 'Original timestamps disagree'):
            patch_times(inputs)

    def test_source_identity_and_count_mismatches_leave_timing_null(self):
        capture = next(c for c in self.bundle['manifest']['captures'] if c['canonical'].startswith('scannet/'))
        token = self.tokens[capture['canonical']]
        for key, value in [('canonical', 'scannet/wrong_scene'), ('n', 1)]:
            with self.subTest(field=key):
                data = copy.deepcopy(self.bundle['data'])
                k1.unique_rows(data['d12'])[token][key] = value
                manifest = copy.deepcopy(self.bundle['manifest'])
                result = k1.fill_timing(manifest, data, self.bundle['sources'], self.tokens)
                self.assertIn(capture['canonical'], result['failures'])
                changed = next(c for c in manifest['captures'] if c['canonical'] == capture['canonical'])
                self.assertEqual(changed['timing_source'], 'null')

    def test_first_token_row_wins(self):
        self.assertEqual(k1.first_tokens([{'canonical': 'x', 's': 'first'},
                                         {'canonical': 'x', 's': 'second'}]), {'x': 'first'})

    def test_original_manifest_preserved_and_changes_are_bounded(self):
        self.assertEqual(k1.sha_bytes((k1.BASE / 'K1_MANIFEST.staged.json').read_bytes()), k1.MANIFEST_SHA)
        restored = copy.deepcopy(self.output)
        restored.pop('k1_finalize')
        restored['production_ready'] = self.bundle['manifest']['production_ready']
        restored['frame_staging_authorized'] = self.bundle['manifest']['frame_staging_authorized']
        for capture, original in zip(restored['captures'], self.bundle['manifest']['captures']):
            capture.pop('timing_source')
            for key in k1.TIMING_KEYS:
                capture['model_row']['student_input'][key] = original['model_row']['student_input'][key]
        self.assertEqual(restored, self.bundle['manifest'])

    def test_write_refuses_existing_file_and_outside_directory(self):
        with self.assertRaises(FileExistsError):
            k1.write_new(Path(__file__), {})
        with self.assertRaisesRegex(ValueError, 'inside codex_finalize_v2'):
            k1.write_new(k1.BASE / 'K1_MANIFEST.staged.json', {})


if __name__ == '__main__':
    unittest.main(verbosity=2)
