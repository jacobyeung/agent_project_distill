import copy
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from fixture_attestation import capture_fixture_attestation
sys.path.insert(0, str(ROOT.parent / 'tree_s1_admissionfix_168872'))
import student_pilot
student_pilot.__path__.insert(0, str(ROOT / 'student_pilot'))
from student_pilot import carrier_c1_run as run


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


base = module('test_warm_start', ROOT / 'test_warm_start.py')
base.ROOT = ROOT
student_pilot.__path__.insert(0, str(ROOT / 'student_pilot'))
from student_pilot import s1_warm_start as warm, s1_warm_data_identity as guard, s1_row_order
from student_pilot.p3_provenance import digest, file_pin, load, write
import torch


class GuardedRebind(unittest.TestCase):
    def save(self, name, value):
        path = self.root / name
        write(path, value)
        return file_pin(path)

    def setUp(self):
        self.root, cfg, donor, receipt, self.model = base.fixture()
        self.donor = copy.deepcopy(donor)
        self.before = {k: copy.deepcopy(v) for k, v in receipt.items() if k not in ('init_artifact', 'warm_start')}
        self.source = {}
        for name, value in self.before['streams'].items():
            self.source[name] = dict(schema='fixture-stream-v1', stream=name, count=value['count'],
                database=value['database'], camera={'weight_focal': 1.}, depth={'num_points_per_frame': 64},
                model={'path': '/fixed/model.json', 'sha256': 'a'*64},
                division={'path': '/fixed/division.json', 'sha256': 'b'*64}, supervision='fixed')
            pin = self.save(name + '_donor_receipt.json', self.source[name])
            self.donor['streams'][name] = pin
            value['receipt'] = pin
        self.before['config_sha256'] = run.identity(self.donor)
        binding = self.before['source_seal']
        binding['config_sha256'] = self.before['config_sha256']
        binding['sha256'] = digest({key: part for key, part in binding.items() if key != 'sha256'})
        self.donor['preparation'] = self.save('guard_donor_preparation.json', self.before)
        donor_pin = self.save('guard_donor_config.json', self.donor)
        artifact = load(cfg['init_artifact']['artifact']['path'])
        artifact.update(config_sha256=self.before['config_sha256'], source_seal=binding,
                        training_source_seal=binding)
        self.cfg = copy.deepcopy(cfg)
        self.cfg['streams'] = copy.deepcopy(self.donor['streams'])
        self.cfg['warm_start']['donor_config'] = donor_pin
        self.cfg['init_artifact']['artifact'] = self.save('guard_artifact.json', artifact)
        self.receipt = {**copy.deepcopy(self.before), 'init_artifact': self.cfg['init_artifact']}

    def moved(self, name='vqa', data=None):
        cfg, receipt = copy.deepcopy(self.cfg), copy.deepcopy(self.receipt)
        pin = self.save(name + '_moved_' + str(len(list(self.root.iterdir()))) + '.json',
                        self.source[name] if data is None else data)
        cfg['streams'][name] = pin
        receipt['streams'][name]['receipt'] = pin
        return cfg, receipt

    def test_pure_receipt_path_change_accepts_and_strict_baseline_refuses(self):
        cfg, receipt = self.moved()
        strict = module('student_pilot.s1_strict_review_baseline',
                        ROOT.parent / 'warm_start_reviewfix_07ca49df/student_pilot/s1_warm_start.py')
        with self.assertRaisesRegex(ValueError, 'training/data policy'):
            strict.bind(cfg, receipt)
        lineage = warm.bind(cfg, receipt)
        self.assertEqual(lineage['step'], 200)
        self.assertEqual(lineage['row_identity_method'], 'native-file-pins-v1')

    def test_reviewer_f1_differing_effective_settings_still_refuses(self):
        for field, value in (('camera', {'weight_focal': 99.}), ('depth', {'num_points_per_frame': 1}),
                             ('model', {'path': '/fixed/model.json', 'sha256': 'c'*64}),
                             ('division', {'path': '/fixed/division.json', 'sha256': 'd'*64})):
            cfg, receipt = self.moved()
            receipt[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'preparation settings'):
                warm.bind(cfg, receipt)

    def test_every_stream_receipt_setting_and_unknown_field_are_bound(self):
        for name in self.source:
            for field, value in (('camera', {'weight_focal': 99.}),
                                 ('depth', {'num_points_per_frame': 1}),
                                 ('model', {'path': '/fixed/model.json', 'sha256': 'c'*64}),
                                 ('division', {'path': '/fixed/division.json', 'sha256': 'd'*64}),
                                 ('supervision', 'changed'), ('unknown_field', True)):
                changed = {**self.source[name], field: value}
                cfg, receipt = self.moved(name, changed)
                with self.subTest(stream=name, field=field), self.assertRaisesRegex(ValueError, 'preparation settings'):
                    warm.bind(cfg, receipt)

    def test_rebuilt_path_embedded_in_receipt_can_change_its_content_pin(self):
        cfg, receipt = self.moved()
        old = Path(receipt['streams']['vqa']['database']['path'])
        new = self.root / 'same_database_new_path.sqlite'
        with new.open('xb') as stream:
            stream.write(old.read_bytes())
        receipt['streams']['vqa']['database'] = file_pin(new)
        source = {**self.source['vqa'], 'database': file_pin(new)}
        cfg['streams']['vqa'] = self.save('receipt_with_moved_database.json', source)
        receipt['streams']['vqa']['receipt'] = cfg['streams']['vqa']
        self.assertNotEqual(cfg['streams']['vqa']['sha256'], self.donor['streams']['vqa']['sha256'])
        self.assertEqual(warm.bind(cfg, receipt)['step'], 200)

    def rebuild(self, swap=False):
        cfg, receipt = copy.deepcopy(self.cfg), copy.deepcopy(self.receipt)
        path = self.root / ('rebuilt_swap.sqlite' if swap else 'rebuilt.sqlite')
        original = receipt['streams']['vqa']['database']
        source = sqlite3.connect(Path(original['path']).as_uri() + '?mode=ro&immutable=1', uri=True)
        try:
            values = list(source.execute('SELECT i,row,target FROM rows ORDER BY i'))
        finally:
            source.close()
        if swap:
            values[0], values[1] = (0, *values[1][1:]), (1, *values[0][1:])
        conn = sqlite3.connect(path)
        try:
            conn.execute('PRAGMA page_size=8192')
            conn.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT, target TEXT)')
            conn.executemany('INSERT INTO rows VALUES (?,?,?)', values)
            conn.commit()
        finally:
            conn.close()
        pin = file_pin(path)
        receipt['streams']['vqa']['database'] = pin
        cfg['streams']['vqa'] = self.save('rebuilt_swap_receipt.json' if swap else 'rebuilt_receipt.json',
                                         {**self.source['vqa'], 'database': pin})
        receipt['streams']['vqa']['receipt'] = cfg['streams']['vqa']
        return cfg, receipt

    def test_attestation_allows_only_equal_ordered_content(self):
        pin = self.save('row_attestation.json', capture_fixture_attestation(self.cfg['warm_start']['donor_config']))
        cfg, receipt = self.rebuild()
        with self.assertRaisesRegex(ValueError, 'row content/order'):
            warm.bind(cfg, receipt)
        cfg['warm_start']['donor_row_order'] = pin
        self.assertEqual(warm.bind(cfg, receipt)['row_identity_method'], s1_row_order.SCHEMA)
        cfg, receipt = self.rebuild(swap=True)
        cfg['warm_start']['donor_row_order'] = pin
        with self.assertRaisesRegex(ValueError, 'row content'):
            warm.bind(cfg, receipt)

    def test_unknown_preparation_fields_counts_stream_order_and_policy_refuse(self):
        for changed in (
                {**self.receipt, 'unlisted_setting': 'changed'},
                {**self.receipt, 'streams': dict(reversed(list(self.receipt['streams'].items())))}):
            with self.assertRaisesRegex(ValueError, 'preparation settings'):
                warm.bind(self.cfg, changed)
        for name in self.receipt['streams']:
            changed = copy.deepcopy(self.receipt)
            changed['streams'][name]['count'] += 1
            with self.assertRaisesRegex(ValueError, 'preparation settings'):
                warm.bind(self.cfg, changed)
        cfg = copy.deepcopy(self.cfg)
        cfg['scheduled_sampling']['seed'] += 1
        with self.assertRaises(ValueError):
            warm.bind(cfg, self.receipt)

    def test_reviewer_f2_stray_export_key_still_refuses(self):
        state = dict(self.model.auxiliary_heads.state_dict())
        state['stray_head.weight'] = torch.zeros(3)
        path = self.root / 'extra_heads.pt'
        torch.save(state, path)
        artifact = load(self.cfg['init_artifact']['artifact']['path'])
        artifact['heads'] = file_pin(path)
        cfg = copy.deepcopy(self.cfg)
        cfg['init_artifact']['artifact'] = self.save('extra_artifact.json', artifact)
        receipt = {**self.receipt, 'init_artifact': cfg['init_artifact']}
        receipt['warm_start'] = warm.bind(cfg, receipt)
        with self.assertRaisesRegex(ValueError, 'export key'):
            base.load_fixture(self.root, receipt, base.Tiny())

    def test_explicit_allowlist_covers_production_rebuilt_pin_locations_only(self):
        p = Path('/scratch/jjyeung/orch_cd/orchard_cp2/out/admission_preparation_169097/'
                 'prepare_dd26bb95f37a43789206c6e4d4cd94bd')
        documents = [('prepared/s1_receipt.json', guard.preparation_allowlist())]
        documents += [(name + '/receipt.json', guard.stream_allowlist(name)) for name in ('pointing', 'routing', 'vqa')]
        for relative, allowed in documents:
            before = load(p / relative)
            after = copy.deepcopy(before)

            def relocate(value):
                if isinstance(value, dict):
                    if set(value) == {'path', 'sha256'} and '/runs/469ddece/inputs/' in value['path']:
                        value['path'] = value['path'].replace('/runs/469ddece/', '/runs/fedcba98/')
                        value['sha256'] = 'd'*64
                    else:
                        for part in value.values():
                            relocate(part)
                elif isinstance(value, list):
                    for part in value:
                        relocate(part)

            relocate(after)
            guard.compare(before, after, allowed, relative)
            after['unknown_field'] = True
            with self.assertRaisesRegex(ValueError, 'fields'):
                guard.compare(before, after, allowed, relative)


if __name__ == '__main__':
    unittest.main()
