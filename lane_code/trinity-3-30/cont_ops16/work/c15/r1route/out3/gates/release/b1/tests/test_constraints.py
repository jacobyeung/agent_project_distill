"""Offline production audit; these are not tests of a replacement package."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import unittest

ROOT = Path('/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/gates/lost/repin')
P = ROOT/'out/production'
sys.path.insert(0, str(P))
from orchard_h10.common import canonical, sha
from orchard_h10.job import check_inputs, verify_config


def load(path):
    return json.loads(Path(path).read_text())


def guard(path, message):
    tree = ast.parse((P/path).read_text())
    node = next(n for n in ast.walk(tree) if isinstance(n, ast.If)
                and any(isinstance(s, ast.Raise) and isinstance(s.exc, ast.Call)
                        and s.exc.args and isinstance(s.exc.args[0], ast.Constant)
                        and s.exc.args[0].value == message for s in n.body))
    return compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                   str(path), 'exec')


class ProductionConstraints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = {**load(P/'9.json'), **load(ROOT/'in/prod_pkg/0.json')}
        cls.inputs = load(ROOT/'in/prod_pkg/a/1.json')

    def test_production_identity_and_admission(self):
        self.assertEqual(sha(ROOT/'in/prod_pkg/0.tgz'),
                         '446a432306b8e68ebfa32228071259a61ffd2ec0dada3ec43a664ba342ca540e')
        self.assertEqual(canonical(load(P/'9.json')), self.cfg['plan_sha256'])
        self.assertEqual(sha(ROOT/'in/prod_pkg/a/1.json'),
                         load(ROOT/'in/prod_pkg/2.json')['inputs'])
        verify_config(self.cfg)
        self.assertEqual(check_inputs(self.inputs, self.cfg), self.inputs)

    def test_all_extracted_sources_unchanged(self):
        with tarfile.open(ROOT/'in/prod_pkg/0.tgz') as archive:
            for member in archive:
                self.assertTrue(member.isfile())
                raw = archive.extractfile(member).read()
                for folder in ('production',):
                    self.assertEqual(raw, (ROOT/'out'/folder/member.name).read_bytes())

    def test_all_production_payload_pins(self):
        for name, pin in self.cfg['payload_pins'].items():
            self.assertEqual(sha(P/name), pin['sha256'], name)
            self.assertEqual((P/name).stat().st_size, pin['bytes'], name)

    def test_camera_types_already_admit(self):
        value = copy.deepcopy(self.inputs)
        value['types'] = ['camera_displacement', 'camera_rotation',
                          'camera_movement_direction']
        self.assertEqual(check_inputs(value, self.cfg), value)

    def test_production_export_hashes_are_fixed(self):
        for name in ('artifact', 'heads', 'full_weights'):
            value = copy.deepcopy(self.inputs)
            value['files'][name]['sha256'] = '0'*64
            with self.assertRaisesRegex(ValueError, 'Registered dependency differs'):
                check_inputs(value, self.cfg)

    def test_production_export_bytes_are_not_fixed_at_metadata_admission(self):
        # Real bytes are checked by stage(); metadata admission only requires > 0.
        for name in ('artifact', 'heads', 'full_weights'):
            value = copy.deepcopy(self.inputs)
            value['files'][name]['bytes'] += 1
            self.assertEqual(check_inputs(value, self.cfg), value)

    def test_restore_rejects_a_different_config_identity(self):
        code = guard('b/parity_kit/stage_restore.py', 'export architecture or identity differs')
        receipt_path = P/'b/work/meta/x/fsw/ap/8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/prepared/s1_receipt.json'
        receipt = load(receipt_path)
        cfg = load(receipt_path.parent.parent/'config.json')
        artifact = dict(config_sha256=receipt['config_sha256'],
                        base_identity=cfg['base_identity'], frame_layout=cfg['frame_layout'],
                        geometry_online=False)
        env = dict(receipt=receipt, cfg=cfg, artifact=artifact)
        exec(code, env)
        artifact['config_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'export architecture or identity differs'):
            exec(code, env)

    def test_new_token_paths_conflict_with_fixed_policy_receipt(self):
        code = guard('orchard_h10/job.py', 'Policy receipt does not authorize these scripts')
        policy = dict(self.inputs['policy'], authorized=True)
        exec(code, dict(policy=policy, inputs=self.inputs))
        token = (Path('/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/gates/lost/reader/b1g/out/TOKEN')).read_text().strip()
        changed = json.loads(json.dumps(self.inputs).replace(self.cfg['token'], token))
        cfg = {**self.cfg, 'token': token, 'logical': '/scratch/jjyeung/'+token}
        check_inputs(changed, cfg)
        with self.assertRaisesRegex(ValueError, 'Policy receipt does not authorize'):
            exec(code, dict(policy=policy, inputs=changed))

    def test_launch_binding_always_says_sft_544(self):
        tree = ast.parse((P/'h1eval/h10/launch.py').read_text())
        call = next(n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'binding' for t in n.targets)
                    and isinstance(n.value, ast.Call))
        values = {k.arg: k.value for k in call.keywords}
        self.assertEqual(ast.literal_eval(values['step']), 544)
        self.assertEqual(ast.literal_eval(values['lineage']), 'SFT')


if __name__ == '__main__':
    unittest.main(verbosity=2)
