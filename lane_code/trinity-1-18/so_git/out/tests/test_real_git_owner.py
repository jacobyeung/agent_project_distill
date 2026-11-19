"""Opt-in real Git proof using two local bare remotes and a throwaway clone."""
import hashlib
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get('LCS_RUN_REAL_GIT_TESTS') == '1',
                     'owner must explicitly enable real Git in a throwaway directory')
class RealGitOwnerTests(unittest.TestCase):
    def setUp(self):
        parent = Path(os.environ['LCS_REAL_GIT_WORK']).resolve(strict=True)
        self.assertTrue(str(parent).startswith('/scratch/'))
        root = Path(tempfile.mkdtemp(prefix='real_git_', dir=parent))
        state = root / 'state'
        state.mkdir()
        origin, home, seed, repo = (root / 'origin.git', root / 'home.git', root / 'seed', state / 'repo')
        env = dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1',
                   GIT_ALLOW_PROTOCOL='file',
                   GIT_TERMINAL_PROMPT='0', GIT_AUTHOR_NAME='Owner tool test', GIT_AUTHOR_EMAIL='owner-test@invalid',
                   GIT_COMMITTER_NAME='Owner tool test', GIT_COMMITTER_EMAIL='owner-test@invalid')
        # Ignore inherited repository/worktree selectors, so no command can target a production repo.
        for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR', 'GIT_OBJECT_DIRECTORY',
                    'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_CONFIG', 'GIT_CONFIG_COUNT'):
            env.pop(key, None)

        def run(*args, cwd=None, extra=None, expected=0):
            result = subprocess.run(args, cwd=cwd, env=dict(env, **(extra or {})),
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=30)
            self.assertEqual(result.returncode, expected, f'{args}: {result.stdout}\n{result.stderr}')
            return (result.stdout + (result.stderr if expected else '')).strip()

        def git(*args):
            return run('git', '-C', str(repo), *args)

        run('git', 'init', '--bare', str(origin))
        run('git', 'init', '--bare', str(home))
        run('git', 'init', '-b', 'lane-code', str(seed))
        (seed / 'lane_code' / 'fake_node').mkdir(parents=True)
        (seed / 'lane_code' / 'fake_node' / 'module.py').write_text('old = 1\n')
        (seed / 'lane_code' / 'fake_node' / 'move_me.py').write_text('move = 1\n')
        (seed / 'tools').mkdir()
        for name in ('lane_code_sync.sh', 'lane_code_filter.py', 'lane_code_scan.py'):
            (seed / 'tools' / name).write_text('# staged fixture\n')
        run('git', '-C', str(seed), 'add', '--', 'lane_code', 'tools')
        run('git', '-C', str(seed), 'commit', '-q', '-m', 'Seed local owner fixture')
        run('git', '-C', str(seed), 'push', '-q', str(origin), 'lane-code:refs/heads/lane-code')
        run('git', '-C', str(seed), 'push', '-q', str(home), 'lane-code:refs/heads/lane-code')
        run('git', 'clone', '-q', '--branch', 'lane-code', str(origin), str(repo))
        git('remote', 'add', 'home', str(home))
        kitfile = root / 'kit.tar'
        with tarfile.open(kitfile, 'w') as tf:
            data = b'PROBE = True\n'
            info = tarfile.TarInfo('probe.py')
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
        sha = hashlib.sha256(kitfile.read_bytes()).hexdigest()
        review = root / 'review.md'
        review.write_text('VERDICT: GO\n')
        extra = dict(LCS_ENABLE_KIT_LANDING='1', LCS_TEST_ROOT=str(root), LCS_S=str(state), LCS_R=str(repo),
                     LCS_EV=str(root / 'events'),
                     LCS_FILTER=str(BASE / 'tools' / 'lane_code_filter.py'),
                     LCS_SCAN=str(BASE / 'tools' / 'lane_code_scan.py'), LCS_PYTHON=sys.executable)
        self.command = ('bash', str(BASE / 'tools' / 'land_kit.sh'), str(kitfile), 'probe-seal', sha,
                        str(review), '_probe', '--builder', 'test_builder', '--reviewer', 'test_reviewer',
                        '--bind-sha', sha)
        self.run_command, self.git, self.extra = run, git, extra
        self.root, self.state, self.repo = root, state, repo
        self.origin, self.home = origin, home
        print('\nREAL_GIT_ROOT', root)

    def land(self, expected=0):
        return self.run_command(*self.command, extra=self.extra, expected=expected)

    def test_land_probe_and_hourly_pathspec_preserves_kits(self):
        root, state, repo, origin, home = self.root, self.state, self.repo, self.origin, self.home
        run, git = self.run_command, self.git
        output = self.land()
        print(output)
        head = git('rev-parse', 'HEAD')
        print('COMMIT\n' + git('show', '--no-patch', '--format=fuller', head))
        print('TREE\n' + git('ls-tree', '-r', '--name-only', head))
        for remote in ('origin', 'home'):
            observed = git('ls-remote', remote, 'refs/heads/lane-code')
            print(f'LS_REMOTE {remote}\n{observed}')
            self.assertEqual(observed, head + '\trefs/heads/lane-code')
        before = git('rev-parse', 'HEAD:kits')
        metadata = json.loads((repo / 'kits' / '_probe' / 'KIT.json').read_text())
        self.assertEqual(metadata['binding']['methods'], ['owner_bind_sha256'])
        self.assertIn('commit=' + head, (state / 'KITS_LANDED.txt').read_text())
        receipt, = (root / 'events').glob('*_RESULT_kit__probe_landed.md')
        self.assertIn('commit=' + head, receipt.read_text())
        # Deliberately dirty kits: a broad -A . pathspec would stage both changes.
        (repo / 'kits' / '_probe' / 'probe.py').rename(root / 'saved_probe.py')
        changed_metadata = dict(metadata, reviewer='unstaged local edit')
        (repo / 'kits' / '_probe' / 'KIT.json').write_text(json.dumps(changed_metadata))
        self.assertEqual(set(git('diff', '--name-only', '--', 'kits').splitlines()),
                         {'kits/_probe/probe.py', 'kits/_probe/KIT.json'})
        (repo / 'lane_code' / 'fake_node' / 'module.py').write_text('new = 2\n')
        # Move out a tracked lane file to exercise the -A removal case without a deletion command.
        (repo / 'lane_code' / 'fake_node' / 'move_me.py').rename(root / 'saved_move_me.py')
        source = Path(__file__).parent / 'fixtures' / 'lane_code_sync.sh'
        line, = [line for line in source.read_text().splitlines() if line.startswith('git -C "$R" add ')]
        command = shlex.split(line.split(' || ')[0])
        self.assertEqual(command[:4], ['git', '-C', '$R', 'add'])
        command[2] = str(repo)
        run(*command)
        staged = git('diff', '--cached', '--name-only').splitlines()
        self.assertTrue(staged)
        self.assertFalse(any(p.startswith('kits/') for p in staged))
        git('commit', '-q', '-m', 'Exercise unchanged hourly add pathspec')
        after = git('rev-parse', 'HEAD:kits')
        self.assertEqual(before, after)
        print(f'HOURLY_KITS_TREE before={before} after={after} unchanged=true')
        print('HOURLY_UNSTAGED_KITS\n' + git('diff', '--name-only', '--', 'kits'))
        # Publish the fixture's simulated hourly commit, using the same two isolated bare remotes.
        for remote in ('origin', 'home'):
            git('push', '-q', remote, 'HEAD:refs/heads/lane-code')
            self.assertEqual(git('ls-remote', remote, 'refs/heads/lane-code').split()[0], git('rev-parse', 'HEAD'))
        for remote in (origin, home):
            self.assertEqual(run('git', '--git-dir=' + str(remote), 'for-each-ref', '--format=%(refname)', 'refs/heads'),
                             'refs/heads/lane-code')
        self.assertEqual(metadata['file_count'], 1)

    @unittest.skipUnless(os.environ.get('LCS_REVIEW2_FIXES') == '1', 'requires LCS_REVIEW2_FIXES=1')
    def test_failed_commit_clears_staging_without_moving_head(self):
        hooks = self.root / 'commit_hooks'
        hooks.mkdir()
        hook = hooks / 'pre-commit'
        hook.write_text('#!/bin/sh\nexit 1\n')
        hook.chmod(0o755)
        self.git('config', 'core.hooksPath', str(hooks))
        head = self.git('rev-parse', 'HEAD')
        output = self.land(expected=2)
        self.assertIn('kit staging cleared', output)
        self.git('diff', '--cached', '--quiet')
        self.assertEqual(self.git('rev-parse', 'HEAD'), head)
        self.assertEqual(self.git('ls-files', '--', 'kits/_probe'), '')
        self.assertEqual(set(self.git('ls-files', '--others', '--exclude-standard', '--', 'kits/_probe').splitlines()),
                         {'kits/_probe/KIT.json', 'kits/_probe/probe.py'})
        self.assertIn('not fully tracked', self.land(expected=2))
        self.assertFalse((self.state / 'KITS_LANDED.txt').exists())
        self.assertEqual(list((self.root / 'events').glob('*RESULT*')), [])
        print('FAILED_COMMIT staging_cleared=true head_unchanged=true kit_untracked=true rerun_refused=true')

    @unittest.skipUnless(os.environ.get('LCS_REVIEW2_FIXES') == '1', 'requires LCS_REVIEW2_FIXES=1')
    def test_origin_rejection_stops_before_home_and_receipts(self):
        hook = self.origin / 'hooks/pre-receive'
        hook.write_text('#!/bin/sh\nexit 1\n')
        hook.chmod(0o755)
        before = {r: self.git('ls-remote', r, 'refs/heads/lane-code') for r in ('origin', 'home')}
        head = self.git('rev-parse', 'HEAD')
        output = self.land(expected=2)
        self.assertIn('STOP: origin push failed', output)
        self.assertIn('contact the user before the next hourly run', output)
        self.assertNotEqual(self.git('rev-parse', 'HEAD'), head)
        for remote in ('origin', 'home'):
            self.assertEqual(self.git('ls-remote', remote, 'refs/heads/lane-code'), before[remote])
        self.assertFalse((self.state / 'KITS_LANDED.txt').exists())
        self.assertEqual(list((self.root / 'events').glob('*RESULT*')), [])
        print('ORIGIN_REJECTION stop=true home_unchanged=true origin_unchanged=true receipt_absent=true')


if __name__ == '__main__':
    unittest.main()
