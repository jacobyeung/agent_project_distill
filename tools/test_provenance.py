"""Exercise admission against real Git repositories; preserve all fixtures."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        base = Path(os.environ.get('PROVENANCE_TEST_OUTPUT', Path(__file__).resolve().parents[1] / 'out'))
        base.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix='provenance-', dir=base))
        self.env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        self.env['PYTHONDONTWRITEBYTECODE'] = '1'
        (self.root / 'tools').mkdir()
        self.tool = self.root / 'tools/provenance.py'
        shutil.copy2(Path(__file__).with_name('provenance.py'), self.tool)
        self.config = self.root / 'config.json'
        self.config.write_text('{"epoch": 1}\n')
        (self.root / '.gitignore').write_text('out/\n')
        self.git('init', '--initial-branch=main')
        self.git('config', 'user.name', 'Provenance Test')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('add', '.')
        self.git('commit', '-m', 'Create provenance fixture')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], env=self.env, text=True, stderr=subprocess.PIPE).strip()

    def run_tool(self, config=None, cwd=None, env=None):
        return subprocess.run([sys.executable, '-B', str(self.tool), str(config or self.config)],
                              cwd=cwd or self.root, env=env or self.env, text=True, capture_output=True)

    def test_clean_and_exact_config_hash_from_foreign_directory(self):
        result = self.run_tool(cwd=self.root.parent)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {'repo_commit': self.git('rev-parse', 'HEAD'),
            'dirty': False, 'config_sha256': hashlib.sha256(self.config.read_bytes()).hexdigest()})

    def test_tracked_and_staged_changes_refuse(self):
        self.config.write_text('{"epoch": 2}\n')
        for staged in (False, True):
            if staged:
                self.git('add', 'config.json')
            result = self.run_tool()
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertTrue(json.loads(result.stdout)['dirty'])
            self.assertEqual(json.loads(result.stdout)['config_sha256'], hashlib.sha256(self.config.read_bytes()).hexdigest())

    def test_untracked_file_refuses(self):
        (self.root / 'untracked.txt').write_text('new code\n')
        self.assertEqual(self.run_tool().returncode, 1)

    def test_ignored_outputs_do_not_refuse(self):
        (self.root / 'out').mkdir()
        (self.root / 'out/log.txt').write_text('output\n')
        self.assertEqual(self.run_tool().returncode, 0)

    def test_missing_config_refuses(self):
        self.assertEqual(self.run_tool(self.root / 'missing.json').returncode, 2)

    def test_inherited_git_directory_cannot_redirect_identity(self):
        env = dict(self.env, GIT_DIR=str(self.root / 'missing.git'), GIT_WORK_TREE=str(self.root.parent))
        self.assertEqual(self.run_tool(env=env).returncode, 0)

    def test_unborn_repository_refuses(self):
        root = self.root / 'out/unborn'
        (root / 'tools').mkdir(parents=True)
        shutil.copy2(self.tool, root / 'tools/provenance.py')
        subprocess.run(['git', 'init', str(root)], env=self.env, capture_output=True, check=True)
        result = subprocess.run([sys.executable, '-B', str(root / 'tools/provenance.py'), str(self.config)], env=self.env, capture_output=True)
        self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
