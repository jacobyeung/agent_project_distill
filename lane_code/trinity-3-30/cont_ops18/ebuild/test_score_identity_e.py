"""Identity regression tests; synthetic E returns are not serving results."""
import score_e as score

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
        self.work = Path(tempfile.mkdtemp(prefix='score_e_identity_', dir='/dev/shm/c18e'))
        self.root = self.work/'return'
        self.package = HERE/'evidence/E/BUILD.json'
        self.build = score.read(self.package)['E']
        self.value, self.items = score.manifest(HERE/'evidence/scoring/items/devs1_routed.json')
        src = HERE/'evidence/A4_return/metadata/reads/0/metadata/journals/3/0'
        env = score.read(src/'environment.json')
        self.reference = copy.deepcopy(env['binding'])
        other = score.read(HERE/'evidence/step544_return/metadata/reads/1/metadata/journals/3/0/environment.json')['binding']
        self.assertEqual({k:other[k] for k in score.SERVING_KEYS}, {k:self.reference[k] for k in score.SERVING_KEYS})
        self.env_path = self.root/'metadata/reads/0/metadata/journals/3/0/environment.json'
        dump(self.env_path, env)
        source = src/'items.jsonl'
        if not source.exists():
            import gzip
            raw = gzip.decompress((src/'items.jsonl.gz').read_bytes())
        else:raw = source.read_bytes()
        (self.env_path.parent/'items.jsonl').write_bytes(raw)
        identity_files(self.root, self.build, env['binding']['settings_sha256'])

    def load(self):
        return score.load_return(self.root, self.value, self.items, self.package, self.reference)

    def test_a4_rejected(self):
        # A4 has valid journals and the same step, but a different plan/operator/export.
        with self.assertRaisesRegex(ValueError, 'Return plan/operator differs'):
            score.load_return(score.A4, self.value, self.items, self.package, self.reference)

    def test_each_serving_pin_matches_baselines(self):
        for name in score.SERVING_KEYS:
            with self.subTest(hash=name):
                self.mutate_rejected(self.env_path, ['binding',name], 'f'*64)

    def test_package_directory(self):
        self.package = package_fixture(self.work, HERE/'evidence/E/payload/9.json', HERE/'evidence/E/delivery')
        self.assertEqual(score.package_identity(self.package)['plan'], self.build['plan_sha256'])
        self.load()

    def test_other_build_token_rejected(self):
        build = copy.deepcopy(self.build);build['plan_sha256'] = 'a'*64
        self.package = self.work/'other_BUILD.json';dump(self.package, {'E':build})
        with self.assertRaisesRegex(ValueError, 'Return plan/operator differs'):
            self.load()

    def test_a4_submission_guards_retained(self):
        old = Path('/scratch/jjyeung/orch_n30/cont_ops17/work/o_sub_A4.sh').read_text()
        new = (HERE/'o_sub_E.sh').read_text()
        old_cpu = old.split("<<'PYCODE'\n")[1].split('\nPYCODE',1)[0]
        new_cpu = new.split("<<'PYCODE'\n")[1].split('\nPYCODE',1)[0]
        self.assertNotIn('full_reader', old.lower())
        self.assertNotIn('FULL_READER', old)
        for line in old_cpu.splitlines():
            self.assertIn(line, new_cpu)
        for line in old.splitlines():
            if line.startswith(('test ', '[[ ', 'set ', 'umask ', 'squeue ')):
                self.assertIn(line, new)
        for fragment in ("os.path.islink(p)", "total>75000000", '3.py check --gpus 1 --time', '3.py submit --gpus 1 --time'):
            self.assertIn(fragment, new)


if __name__ == '__main__':unittest.main()
