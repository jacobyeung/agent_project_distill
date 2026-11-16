"""Tests for tools/treegit/tree_commit.py on throwaway repositories under TMPDIR. Python 3.6 safe.

The build fixtures carry the trainer's own seal code (student_pilot/source_seal.py and p3_provenance.py),
copied from this repository's trainer/ when present, else from the read-only audit copy of tree b01ce449.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from tools.treegit import tree_commit as tc  # noqa: E402

SEAL_SOURCES = [os.path.join(REPO, 'trainer', 'student_pilot'),
                '/scratch/jjyeung/orch_n30/eff_audit/repo/sealed_tree_b01ce449/student_pilot']
SEAL_DIR = next((d for d in SEAL_SOURCES if os.path.isfile(os.path.join(d, 'source_seal.py'))), None)
SEAL_PY = os.environ.get('TREEGIT_SEAL_PYTHON', tc.DEFAULT_SEAL_PYTHON)
GIT_ENV = {'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@example.invalid', 'GIT_COMMITTER_NAME': 't',
           'GIT_COMMITTER_EMAIL': 't@example.invalid', 'GIT_CONFIG_NOSYSTEM': '1'}
os.environ.update(GIT_ENV)


def git(repo, *args):
    return subprocess.check_output(['git', '-C', repo] + list(args)).decode('utf-8').strip()


def write(root, rel, text, mode=0o644):
    p = os.path.join(root, rel)
    if not os.path.isdir(os.path.dirname(p)):
        os.makedirs(os.path.dirname(p))
    with open(p, 'w') as f:
        f.write(text)
    os.chmod(p, mode)


def tree_files(repo, rev, prefix=None):
    out = {}
    for line in git(repo, 'ls-tree', '-r', rev).split('\n'):
        meta, path = line.split('\t', 1)
        mode, typ, sha = meta.split(' ')
        if prefix is None or path.startswith(prefix + '/'):
            out[path] = (mode, sha)
    return out


@unittest.skipUnless(SEAL_DIR and os.path.exists(SEAL_PY), 'trainer seal code or trainer interpreter missing')
class TreeCommitTest(unittest.TestCase):

    def setUp(self):
        self.t = tempfile.mkdtemp(prefix='tc_')
        self.repo = os.path.join(self.t, 'repo')
        subprocess.check_call(['git', 'init', '-q', self.repo])
        write(self.repo, 'README.md', 'top\n')
        write(self.repo, 'other/keep.txt', 'keep\n')
        write(self.repo, '.gitignore', '*.png\nout/\n')
        git(self.repo, 'add', '-A')
        git(self.repo, 'commit', '-q', '-m', 'base')
        git(self.repo, 'checkout', '-q', '-b', 'eff/t')
        git(self.repo, 'branch', '-q', 'side')
        git(self.repo, 'checkout', '-q', 'side')  # eff/t is not checked out unless a test says so
        self.build = os.path.join(self.t, 'build')
        os.makedirs(os.path.join(self.build, 'student_pilot'))
        for n in ('source_seal.py', 'p3_provenance.py'):
            shutil.copyfile(os.path.join(SEAL_DIR, n), os.path.join(self.build, 'student_pilot', n))
        write(self.build, 'student_pilot/__init__.py', '')
        write(self.build, 'a.py', 'a = 1\n')
        write(self.build, 'sub/b.py', 'b = 2\n')
        write(self.build, 'run.sh', '#!/bin/sh\n', 0o755)
        write(self.build, 'x.png', 'not really a png\n')
        write(self.build, 'out/y.json', '{"y": 1}\n')
        write(self.build, 'artifacts/skip.bin', 'skipped by the seal\n')
        write(self.build, 'pkg/__pycache__/m.pyc', 'skipped by the seal\n')

    def seal(self, root):
        return tc.seal_of(SEAL_PY, root, root)[0]

    def commit(self, **kw):
        args = dict(repo=self.repo, branch='eff/t', build='b', tree=self.build, seal_python=SEAL_PY)
        args.update(kw)
        if 'expect_seal' not in args:
            args['expect_seal'] = self.seal(self.build)[:16]
        return tc.tree_commit(**args)

    def test_build_lands_with_ignored_names_and_skips_seal_dirs(self):
        before = git(self.repo, 'rev-parse', 'eff/t')
        rep = self.commit()
        self.assertEqual(git(self.repo, 'rev-parse', 'eff/t'), rep['commit'])
        self.assertEqual(rep['parent'], before)
        files = tree_files(self.repo, 'eff/t', 'trainer')
        self.assertIn('trainer/x.png', files)
        self.assertIn('trainer/out/y.json', files)
        self.assertEqual(files['trainer/run.sh'][0], '100755')
        self.assertEqual(files['trainer/a.py'][0], '100644')
        self.assertFalse([p for p in files if 'artifacts' in p or '__pycache__' in p])
        self.assertEqual(sorted(rep['seal_skipped_dirs']), ['artifacts/', 'pkg/__pycache__/'])
        self.assertEqual(git(self.repo, 'log', '-1', '--format=%s', 'eff/t'),
                         'trainer: b seal %s tar none' % rep['seal'])
        rows = [json.loads(x) for x in git(self.repo, 'show', 'eff/t:tools/treegit/SEALS.jsonl').split('\n')]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['seal'], rep['seal'])
        self.assertEqual(rows[0]['parent'], before)
        self.assertEqual(rep['verified_archive_seal'], rep['seal'])
        self.assertEqual(git(self.repo, 'symbolic-ref', 'HEAD'), 'refs/heads/side')

    def test_add_change_remove_mode_and_outside_paths_keep_blobs(self):
        self.commit(build='b1')
        outside_before = {p: v for p, v in tree_files(self.repo, 'eff/t').items()
                          if not p.startswith('trainer/') and p != 'tools/treegit/SEALS.jsonl'}
        write(self.build, 'a.py', 'a = 10\n')                 # changed
        os.rename(os.path.join(self.build, 'sub', 'b.py'), os.path.join(self.t, 'b.py'))  # removed
        write(self.build, 'c.py', 'c = 3\n')                  # added
        os.chmod(os.path.join(self.build, 'run.sh'), 0o644)   # mode change
        rep = self.commit(build='b2')
        files = tree_files(self.repo, 'eff/t', 'trainer')
        self.assertIn('trainer/c.py', files)
        self.assertNotIn('trainer/sub/b.py', files)
        self.assertEqual(files['trainer/run.sh'][0], '100644')
        self.assertEqual(git(self.repo, 'show', 'eff/t:trainer/a.py'), 'a = 10')
        outside_after = {p: v for p, v in tree_files(self.repo, 'eff/t').items()
                         if not p.startswith('trainer/') and p != 'tools/treegit/SEALS.jsonl'}
        self.assertEqual(outside_before, outside_after)
        diff = git(self.repo, 'diff', '--name-status', 'eff/t~1', 'eff/t').split('\n')
        self.assertEqual(sorted(diff), sorted(['M\ttools/treegit/SEALS.jsonl', 'M\ttrainer/a.py',
                                               'A\ttrainer/c.py', 'M\ttrainer/run.sh', 'D\ttrainer/sub/b.py']))
        self.assertEqual(len(git(self.repo, 'show', 'eff/t:tools/treegit/SEALS.jsonl').split('\n')), 2)
        self.assertEqual(rep['verified_archive_seal'], self.seal(self.build))

    def test_wrong_expect_seal_refuses(self):
        before = git(self.repo, 'rev-parse', 'eff/t')
        bad = 'f' * 16 if not self.seal(self.build).startswith('f') else '0' * 16
        with self.assertRaises(tc.Refused) as cm:
            self.commit(expect_seal=bad)
        self.assertIn('does not start with', str(cm.exception))
        self.assertEqual(git(self.repo, 'rev-parse', 'eff/t'), before)

    def test_branch_moved_between_read_and_update_ref_refuses(self):
        def move():
            tree = git(self.repo, 'rev-parse', 'eff/t^{tree}')
            c = subprocess.check_output(['git', '-C', self.repo, 'commit-tree', tree, '-p', 'eff/t', '-m', 'race'])
            git(self.repo, 'update-ref', 'refs/heads/eff/t', c.decode().strip())
        with self.assertRaises(tc.Refused) as cm:
            self.commit(before_update_ref=move)
        self.assertIn('moved', str(cm.exception))
        self.assertEqual(git(self.repo, 'log', '-1', '--format=%s', 'eff/t'), 'race')

    def test_link_refuses_and_names_member(self):
        seal = self.seal(self.build)
        os.symlink('b.py', os.path.join(self.build, 'sub', 'link.py'))
        with self.assertRaises(tc.Refused) as cm:
            self.commit(expect_seal=seal[:16])
        self.assertIn('sub/link.py', str(cm.exception))

    def test_tar_subdir_lists_left_out_members(self):
        tarp = os.path.join(self.t, 'build.tar')
        with tarfile.open(tarp, 'w') as tf:
            tf.add(self.build, arcname='tree_r1')
            data = b'kit\n'
            info = tarfile.TarInfo('build3/kits/k.json')
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
        rep = self.commit(tree=None, tar=tarp, subdir='tree_r1')
        self.assertEqual(rep['left_out'], ['build3/kits/k.json'])
        self.assertEqual(rep['seal'], self.seal(self.build))
        self.assertTrue(git(self.repo, 'log', '-1', '--format=%s', 'eff/t').endswith('tar ' + rep['tar_sha256']))

    def test_checked_out_branch_worktree_follows(self):
        git(self.repo, 'checkout', '-q', 'eff/t')
        rep = self.commit()
        self.assertTrue(rep.get('worktree_synced'))
        with open(os.path.join(self.repo, 'trainer', 'a.py')) as f:
            self.assertEqual(f.read(), 'a = 1\n')
        self.assertEqual(git(self.repo, 'status', '--porcelain'), '')


if __name__ == '__main__':
    unittest.main()
