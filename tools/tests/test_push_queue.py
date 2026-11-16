"""Tests for the push-queue step of tools/lane_code_sync.sh (run with --queue-only).

Every repository lives in a fresh directory under TMPDIR: a bare "origin", the Git owner's clone and
builder clones in lane folders. No path or remote outside that directory is named; GitHub is never used.
Python 3.6 safe.
"""
import os
import socket
import subprocess
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SYNC = os.path.join(REPO, 'tools', 'lane_code_sync.sh')
SCAN = os.path.join(REPO, 'tools', 'lane_code_scan.py')
FAKE_KEY = 'AKIA' + 'ABCDEFGHIJKLMNOP'  # matches the scanner's aws_akia pattern; split so this file stays clean

GIT_ENV = {'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@example.invalid', 'GIT_COMMITTER_NAME': 't',
           'GIT_COMMITTER_EMAIL': 't@example.invalid', 'GIT_CONFIG_NOSYSTEM': '1',
           'GIT_TERMINAL_PROMPT': '0'}


def run(args, cwd=None, env=None, check=True):
    e = dict(os.environ)
    e.update(GIT_ENV)
    if env:
        e.update(env)
    p = subprocess.Popen(args, cwd=cwd, env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         universal_newlines=True)
    out = p.communicate()[0]
    if check and p.returncode != 0:
        raise AssertionError('%s failed rc=%d:\n%s' % (args, p.returncode, out))
    return p.returncode, out


def git(repo, *args, **kw):
    return run(['git', '-C', repo] + list(args), **kw)[1].strip()


@unittest.skipUnless(socket.gethostname().split('.')[0] == 'trinity-3-30',
                     'the sync script runs on trinity-3-30 only')
class PushQueueTest(unittest.TestCase):

    def setUp(self):
        self.t = tempfile.mkdtemp(prefix='pq_')
        self.origin = os.path.join(self.t, 'origin.git')
        self.owner = os.path.join(self.t, 'S', 'repo')
        self.S = os.path.join(self.t, 'S')
        self.lanes = os.path.join(self.t, 'lanes')
        self.ev = os.path.join(self.t, 'ev')
        for d in (self.lanes, self.ev, self.S):
            os.makedirs(d)
        run(['git', 'init', '-q', '--bare', self.origin])
        seed = os.path.join(self.t, 'seed')
        run(['git', 'init', '-q', seed])
        self.write(seed, 'README.md', 'main\n')
        git(seed, 'add', 'README.md')
        git(seed, 'commit', '-q', '-m', 'main')
        git(seed, 'push', '-q', self.origin, 'HEAD:refs/heads/main')
        run(['git', 'clone', '-q', self.origin, self.owner])
        self.main_sha = git(self.owner, 'rev-parse', 'refs/remotes/origin/main')
        self.owner_head = git(self.owner, 'symbolic-ref', 'HEAD')

    @staticmethod
    def write(repo, rel, text):
        p = os.path.join(repo, rel)
        if not os.path.isdir(os.path.dirname(p)):
            os.makedirs(os.path.dirname(p))
        with open(p, 'w') as f:
            f.write(text)

    def lane(self, name, branch='eff/test', sub='clone'):
        lane = os.path.join(self.lanes, name)
        clone = os.path.join(lane, sub)
        run(['git', 'clone', '-q', self.origin, clone])
        git(clone, 'checkout', '-q', '-b', branch)
        return lane, clone

    def commit(self, clone, rel, text):
        self.write(clone, rel, text)
        git(clone, 'add', rel)
        git(clone, 'commit', '-q', '-m', 'c ' + rel)
        return git(clone, 'rev-parse', 'HEAD')

    def queue(self, lane, *lines):
        with open(os.path.join(lane, 'PUSH_QUEUE.txt'), 'a') as f:
            for x in lines:
                f.write(x + '\n')

    def sync(self):
        rc, out = run(['bash', SYNC, '--queue-only'], check=False,
                      env={'LCS_B': os.path.join(self.t, 'B'), 'LCS_S': self.S, 'LCS_R': self.owner,
                           'LCS_EV': self.ev, 'LCS_SCAN': SCAN, 'LCS_LANES_ROOT': self.lanes})
        return rc, out

    def remote(self, branch):
        return git(self.origin, 'for-each-ref', '--format=%(objectname)', 'refs/heads/' + branch)

    def blockers(self):
        return sorted(x for x in os.listdir(self.ev) if 'BLOCKER_push_queue' in x)

    def test_refuses_main(self):
        lane, clone = self.lane('e_a', branch='main')
        sha = self.commit(clone, 'a.py', 'x = 1\n')
        self.queue(lane, '2026-11-16T00:00:00Z main ' + sha)
        rc, out = self.sync()
        self.assertIn('REFUSED main', out)
        self.assertEqual(self.remote('main'), self.main_sha)

    def test_refuses_branch_outside_eff(self):
        lane, clone = self.lane('e_a', branch='feature/x')
        sha = self.commit(clone, 'a.py', 'x = 1\n')
        self.queue(lane, '2026-11-16T00:00:00Z feature/x ' + sha, '2026-11-16T00:00:01Z eff/Bad_Name ' + sha)
        rc, out = self.sync()
        self.assertIn('REFUSED feature/x', out)
        self.assertIn('REFUSED eff/Bad_Name', out)
        self.assertEqual(self.remote('feature/x'), '')
        self.assertEqual(self.remote('eff/Bad_Name'), '')

    def test_refuses_clone_outside_pattern(self):
        lane, clone = self.lane('e_a')
        s1 = self.commit(clone, 'a.py', 'x = 1\n')
        s2 = self.commit(clone, 'b.py', 'x = 2\n')
        s3 = self.commit(clone, 'c.py', 'x = 3\n')
        other = os.path.join(self.t, 'elsewhere')
        run(['git', 'clone', '-q', clone, other])
        os.symlink(clone, os.path.join(lane, 'link'))
        self.queue(lane, '2026-11-16T00:00:00Z eff/test %s %s' % (s1, other),
                   '2026-11-16T00:00:01Z eff/test %s %s/../e_a/clone' % (s2, lane),
                   '2026-11-16T00:00:02Z eff/test %s %s/link' % (s3, lane))
        rc, out = self.sync()
        self.assertEqual(out.count('is not <lane>/clone'), 3, out)
        self.assertEqual(self.remote('eff/test'), '')
        # A lane folder outside (e|eff)_<name> is not even read.
        bad, bclone = self.lane('zz_b')
        self.queue(bad, '2026-11-16T00:00:00Z eff/test ' + self.commit(bclone, 'b.py', 'y = 2\n'))
        rc, out = self.sync()
        self.assertIn('QUEUE done: 0 new lines', out)
        self.assertEqual(self.remote('eff/test'), '')

    def test_clone_link_inside_lane_is_accepted_link_outside_refused(self):
        lane, repo = self.lane('e_a', sub='repo')
        os.symlink('repo', os.path.join(lane, 'clone'))
        s1 = self.commit(repo, 'a.py', 'x = 1\n')
        self.queue(lane, '2026-11-16T00:00:00Z eff/test ' + s1)
        rc, out = self.sync()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.remote('eff/test'), s1)
        lane2, real2 = self.lane('e_b', branch='eff/other', sub='real')
        os.symlink(os.path.join(self.lanes, 'e_a', 'repo'), os.path.join(lane2, 'clone'))
        self.queue(lane2, '2026-11-16T00:00:01Z eff/other ' + self.commit(real2, 'b.py', 'y = 2\n'))
        rc, out = self.sync()
        self.assertIn('is not <lane>/clone', out)
        self.assertEqual(self.remote('eff/other'), '')

    def test_publishes_fast_forward_and_repeat_is_done(self):
        lane, clone = self.lane('e_a', sub='repo')
        s1 = self.commit(clone, 'a.py', 'x = 1\n')
        s2 = self.commit(clone, 'b.py', 'y = 2\n')
        self.queue(lane, '2026-11-16T00:00:00Z eff/test ' + s1)
        rc, out = self.sync()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.remote('eff/test'), s1)
        self.queue(lane, '2026-11-16T00:00:01Z eff/test ' + s2, '2026-11-16T00:00:02Z eff/test ' + s2)
        rc, out = self.sync()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.remote('eff/test'), s2)
        self.assertEqual(out.count('pushed eff/test'), 1, out)
        rc, out = self.sync()
        self.assertIn('QUEUE done: 0 new lines', out)
        with open(os.path.join(self.S, 'PUSH_DONE.txt')) as f:
            done = f.read()
        self.assertIn('eff/test %s pushed' % s1, done)
        self.assertIn('eff/test %s pushed' % s2, done)
        self.assertEqual(git(self.owner, 'symbolic-ref', 'HEAD'), self.owner_head)
        self.assertEqual(self.remote('main'), self.main_sha)

    def test_reports_non_fast_forward_without_force(self):
        lane, clone = self.lane('e_a')
        s1 = self.commit(clone, 'a.py', 'x = 1\n')
        self.queue(lane, '2026-11-16T00:00:00Z eff/test ' + s1)
        self.assertEqual(self.sync()[0], 0)
        lane2, clone2 = self.lane('e_b')  # same branch name, unrelated history
        s2 = self.commit(clone2, 'c.py', 'z = 3\n')
        self.queue(lane2, '2026-11-16T00:00:01Z eff/test ' + s2)
        rc, out = self.sync()
        self.assertIn('non-fast-forward', out)
        self.assertEqual(self.remote('eff/test'), s1)
        self.assertEqual(len(self.blockers()), 1)

    def test_head_must_descend_from_queued_sha(self):
        lane, clone = self.lane('e_a')
        s1 = self.commit(clone, 'a.py', 'x = 1\n')
        git(clone, 'checkout', '-q', '-B', 'eff/test', self.main_sha)
        self.commit(clone, 'b.py', 'y = 2\n')
        self.queue(lane, '2026-11-16T00:00:00Z eff/test ' + s1)
        rc, out = self.sync()
        self.assertIn('neither equals nor descends', out)
        self.assertEqual(self.remote('eff/test'), '')

    def test_secret_blocks_branch_and_names_file(self):
        lane, clone = self.lane('e_a')
        self.commit(clone, 'ok.py', 'x = 1\n')
        sha = self.commit(clone, 'pkg/leak.py', 'KEY = "%s"\n' % FAKE_KEY)
        self.queue(lane, '2026-11-16T00:00:00Z eff/test ' + sha)
        rc, out = self.sync()
        self.assertIn('pkg/leak.py', out)
        self.assertEqual(self.remote('eff/test'), '')
        b = self.blockers()
        self.assertEqual(len(b), 1)
        with open(os.path.join(self.ev, b[0])) as f:
            self.assertIn('pkg/leak.py', f.read())
        rc, out = self.sync()  # a blocked line is never retried
        self.assertIn('QUEUE done: 0 new lines', out)


if __name__ == '__main__':
    unittest.main()
