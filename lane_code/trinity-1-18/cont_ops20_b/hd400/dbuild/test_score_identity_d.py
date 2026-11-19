"""D return identity regression tests; all fixtures stay in /dev/shm/c18e."""
import score_d as score

import os
import copy
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def identity_files(root, build, settings_sha):
    binding = build['export_binding']
    identity = dict(plan=build['plan_sha256'], operator_sha256=build['changed_members']['a/6.py']['after'],
        inputs='1'*64, cards=1, reads=[dict(arm='tower', modes=['none'], types=[3], expected=score.EXPECTED_COUNT,
        stage1_select_rule='candidates_argmax', save_own_depth=False, perception_memo='on',
        perception_memo_modules=['g3t'], perception_memo_verify_ids=[])], schedule=[[0,3]])
    pin = dict(score.EXPORTS[binding['step']], schema='h1-export-pins-v1',
        config_sha256=binding['config_sha256'],
        preparation={k:dict(sha256=v) for k,v in binding['preparation_sha256'].items()})
    dump(root/'metadata/IDENTITY.json', identity)
    dump(root/'metadata/EXPORT_PIN.json', pin)
    dump(root/'metadata/reads/0/metadata/READ_IDENTITY.json', dict(identity, read=0, settings_sha256=settings_sha))
    dump(root/'metadata/reads/0/metadata/IDENTITY.json', dict(plan=identity['plan'], inputs=identity['inputs'], settings_sha256=settings_sha))


def package_fixture(root, plan_path, delivery):
    plan = json.loads(plan_path.read_text())
    package = root/'package';package.mkdir()
    raw = plan_path.read_bytes()
    with tarfile.open(str(package/'0.tgz'), 'w:gz') as archive:
        entry = tarfile.TarInfo('9.json');entry.size = len(raw)
        archive.addfile(entry, io.BytesIO(raw))
    dump(package/'0.json', dict(token=plan['token'],
        plan_sha256=hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        payload_sha256=score.digest(package/'0.tgz')))
    (package/'a').mkdir();(package/'a/6.py').write_bytes((delivery/'a/6.py').read_bytes())
    return package


class IdentityTests(unittest.TestCase):
    def mutate_rejected(self, path, keys, value):
        original = path.read_text();bad = json.loads(original);target = bad
        for key in keys[:-1]:target = target[key]
        target[keys[-1]] = value;dump(path, bad)
        try:
            with self.assertRaises((ValueError, KeyError, FileNotFoundError)):
                self.load()
        finally:
            path.write_text(original)

    def test_identity_and_pin_mutations(self):
        for name in ('plan', 'operator_sha256'):
            with self.subTest(identity=name):
                self.mutate_rejected(self.root/'metadata/IDENTITY.json', [name], 'f'*64)
        self.mutate_rejected(self.root/'metadata/IDENTITY.json', ['reads',0,'expected'], 636)
        self.mutate_rejected(self.root/'metadata/reads/0/metadata/READ_IDENTITY.json', ['plan'], 'f'*64)
        self.mutate_rejected(self.root/'metadata/reads/0/metadata/IDENTITY.json', ['plan'], 'f'*64)
        self.mutate_rejected(self.root/'metadata/reads/0/metadata/IDENTITY.json', ['settings_sha256'], 'f'*64)
        for name in ('run','step','member_directory','object','archive_sha256','config_sha256'):
            with self.subTest(pin=name):
                self.mutate_rejected(self.root/'metadata/EXPORT_PIN.json', [name], 'wrong')
        self.mutate_rejected(self.root/'metadata/EXPORT_PIN.json', ['preparation','config','sha256'], '0'*64)

    def test_zeroed_hash_return(self):
        for name in score.SERVING_KEYS + ('export_sha256','artifact_manifest_sha256'):
            with self.subTest(hash=name):
                self.mutate_rejected(self.env_path, ['binding',name], '0'*64)

    def test_valid_build(self):
        rows, report = self.load()
        self.assertTrue(rows)
        self.assertEqual(report['identity']['plan'], self.build['plan_sha256'])

    def setUp(self):
        self.work = Path(tempfile.mkdtemp(prefix='score_d_identity_', dir=os.environ['D_TEST_TMPDIR']))
        self.root = self.work/'return'
        self.package = HERE/'evidence/actual544/BUILD.json'
        self.build = score.read(self.package)['D']
        self.items_path = HERE/'evidence/items/dist580.json'
        self.manifest = score.read(self.items_path)
        settings = dict(stage1_select_rule='candidates_argmax', perception_memo='on', perception_memo_modules=['g3t'],
                        perception_memo_verify_ids=[], save_own_depth=False, types=['object_abs_distance'])
        binding = dict(settings, arms=['tower'], modes=[{'name':'none'}], lineage='SFT', fixture=False,
                       items_sha256=score.digest(self.items_path), item_set_sha256=self.manifest['item_set_sha256'],
                       step=544, settings_sha256=score.canonical(settings))
        for key in score.SERVING_KEYS + ('export_sha256','artifact_manifest_sha256'):binding[key] = '1'*64
        self.env_path = self.root/'metadata/reads/0/metadata/journals/3/0/environment.json'
        dump(self.env_path, dict(settings=settings, binding=binding))
        item = self.manifest['items'][0]
        row = dict(id=item['id'], room_key=item['room_key'], arm='tower', mode='none', type='object_abs_distance',
                   complete=True, output=dict(scores=dict(answer=.5)))
        (self.env_path.parent/'items.jsonl').write_text(json.dumps(row)+'\n')
        identity_files(self.root, self.build, binding['settings_sha256'])

    def load(self):
        return score.load_return(self.root, self.manifest, self.items_path, self.package)

    def test_both_d_exports(self):
        for step in (200,544):
            self.package = HERE/('evidence/actual%d/BUILD.json'%step)
            self.build = score.read(self.package)['D']
            env = score.read(self.env_path);env['binding']['step'] = step;dump(self.env_path, env)
            identity_files(self.root, self.build, env['binding']['settings_sha256'])
            self.assertEqual(self.load()[1]['step'], step)

    def test_400_and_544_comparison(self):
        original_package = self.package
        original_rows = self.load()[0]
        binding = score.read(HERE/'bind_D400.json')
        self.build = copy.deepcopy(self.build)
        self.build['export_binding'] = {k:binding[k] for k in self.build['export_binding']}
        self.build['plan_sha256'] = '4'*64  # Synthetic package identity, not a build receipt.
        self.package = self.work/'BUILD400.json'
        dump(self.package, {'D':self.build})
        with self.assertRaises(ValueError):self.load()  # A 544 return cannot authenticate as 400.
        env = score.read(self.env_path);env['binding']['step'] = 400;dump(self.env_path, env)
        identity_files(self.root, self.build, env['binding']['settings_sha256'])
        rows, meta = self.load()
        self.assertEqual(meta['step'], 400)
        self.assertTrue(score.comparison(rows, original_rows, self.manifest))
        for key in ('run','step','member_directory','object','archive_sha256','config_sha256'):
            self.mutate_rejected(self.root/'metadata/EXPORT_PIN.json', [key], 'wrong')
        self.mutate_rejected(self.root/'metadata/EXPORT_PIN.json', ['preparation','config','sha256'], '0'*64)
        self.package = original_package
        with self.assertRaises(ValueError):self.load()

    def test_package_directory(self):
        self.package = package_fixture(self.work, HERE/'evidence/actual544/payload/9.json', HERE/'evidence/actual544/delivery')
        self.assertEqual(score.package_identity(self.package)['plan'], self.build['plan_sha256'])
        self.load()

    def test_a4_rejected(self):
        root = os.environ['D_TEST_A4_RETURN']
        with self.assertRaisesRegex(ValueError, 'Return plan/operator differs'):
            score.load_return(root, self.manifest, self.items_path, self.package)

    def test_wrong_d_build_rejected(self):
        self.package = HERE/'evidence/actual200/BUILD.json'
        with self.assertRaisesRegex(ValueError, 'Return plan/operator differs'):
            self.load()

    def test_step_must_match_build(self):
        self.mutate_rejected(self.env_path, ['binding','step'], 200)


if __name__ == '__main__':unittest.main()
