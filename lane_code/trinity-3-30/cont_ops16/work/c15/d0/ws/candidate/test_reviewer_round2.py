import copy
import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import test_warm_start as base
import reviewer_round2_original as original
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('accept_scan_current', ROOT / 'accept_scan.py')
accept = importlib.util.module_from_spec(spec)
spec.loader.exec_module(accept)
original.accept = accept
original.SCANNER_DIR = ROOT.parent / 'donor_row_scanner_07ca49df'
from student_pilot import s1_warm_start as warm, s1_row_order as rows
from student_pilot.p3_provenance import file_pin, load


Round1Regression = original.Round1Regression


class RowGate(original.RowGate):
    def test_limit_attestation_does_not_carry_scanner_provenance(self):
        with self.assertRaisesRegex(ValueError, 'approved scanner provenance'):
            super().test_limit_attestation_does_not_carry_scanner_provenance()

    def test_source_provenance_is_preserved_required_and_recorded(self):
        envelope = load(self.attestation['path'])
        self.assertEqual(envelope['scanner_source_sha256'], rows.SCANNER_SOURCE_SHA256)
        lineage = warm.bind(self.with_attestation(self.cfg), self.receipt)
        self.assertEqual(lineage['row_identity_scanner_source_sha256'], rows.SCANNER_SOURCE_SHA256)
        self.assertIsNone(warm.bind(self.cfg, self.receipt)['row_identity_scanner_source_sha256'])
        for name, source in (('missing', None), ('wrong', '0'*64)):
            value = copy.deepcopy(envelope)
            if source is None:
                value.pop('scanner_source_sha256')
            else:
                value['scanner_source_sha256'] = source
            pin = self.save('source_' + name + '.json', value)
            with self.subTest(source=name), self.assertRaisesRegex(ValueError, 'approved scanner provenance'):
                warm.bind(self.with_attestation(self.cfg, pin), self.receipt)

    def test_acceptor_refuses_unapproved_producer_even_when_caller_names_it(self):
        output = copy.deepcopy(self.scanner_output)
        output['scanner']['source_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'Scanner identity'):
            accept.accept(output, '0'*64, self.donor_pin, self.donor['preparation'], self.counts)

    def test_configuration_and_preparation_content_aliases_pass(self):
        envelope = load(self.attestation['path'])
        envelope['config']['path'] = '/another/inputs/config.json'
        envelope['preparation']['path'] = '/another/inputs/preparation.json'
        pin = self.save('alias_attestation.json', envelope)
        lineage = warm.bind(self.with_attestation(self.cfg, pin), self.receipt)
        self.assertEqual(lineage['row_identity_method'], rows.SCHEMA)
        mirror = self.root / 'mirrored_donor_config.json'
        with mirror.open('xb') as target:
            target.write(Path(self.donor_pin['path']).read_bytes())
        cfg = self.with_attestation(self.cfg, pin)
        cfg['warm_start']['donor_config'] = file_pin(mirror)
        self.assertEqual(warm.bind(cfg, self.receipt)['step'], 200)

    def test_aliases_do_not_allow_content_changes_or_malformed_pins(self):
        envelope = load(self.attestation['path'])
        for field in ('config', 'preparation'):
            for name, replacement in (('changed_sha', {'path': '/alias', 'sha256': 'f'*64}),
                                      ('relative_path', {'path': 'alias', 'sha256': envelope[field]['sha256']}),
                                      ('extra_field', {**envelope[field], 'extra': True})):
                value = copy.deepcopy(envelope)
                value[field] = replacement
                pin = self.save(field + '_' + name + '.json', value)
                with self.subTest(field=field, case=name), self.assertRaises(ValueError):
                    warm.bind(self.with_attestation(self.cfg, pin), self.receipt)


if __name__ == '__main__':
    unittest.main()
