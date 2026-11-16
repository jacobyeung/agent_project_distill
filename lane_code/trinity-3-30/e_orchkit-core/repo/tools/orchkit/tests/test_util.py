"""Tests for orchkit.util. unittest style, so both the system Python 3.6 and pytest run them."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, TOOLS)
from orchkit import util  # noqa: E402


class UtilTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='orchkit_util_')

    def path(self, name):
        return os.path.join(self.tmp, name)

    def test_sha256_file_matches_hashlib_and_counts_bytes(self):
        data = os.urandom(3 * util.CHUNK + 17)
        with open(self.path('blob'), 'wb') as handle:
            handle.write(data)
        digest, count = util.sha256_file(self.path('blob'))
        self.assertEqual(digest, hashlib.sha256(data).hexdigest())
        self.assertEqual(count, len(data))

    def test_canonical_json_is_order_independent(self):
        left = util.canonical_json({'b': [1, 2], 'a': {'y': None, 'x': u'é'}})
        right = util.canonical_json({'a': {'x': u'é', 'y': None}, 'b': [1, 2]})
        self.assertEqual(left, right)
        self.assertEqual(left, u'{"a":{"x":"é","y":null},"b":[1,2]}'.encode('utf-8'))
        self.assertEqual(util.canonical_sha256({'a': 1}), hashlib.sha256(b'{"a":1}').hexdigest())

    def test_canonical_json_refuses_nan(self):
        with self.assertRaises(ValueError):
            util.canonical_json({'x': float('nan')})

    def test_write_json_round_trip_leaves_no_temporary_file(self):
        util.write_json(self.path('o.json'), {'k': [1, {'z': 2}]})
        self.assertEqual(util.read_json(self.path('o.json')), {'k': [1, {'z': 2}]})
        self.assertEqual(os.listdir(self.tmp), ['o.json'])
        with open(self.path('o.json'), 'rb') as handle:
            self.assertTrue(handle.read().endswith(b'\n'))

    def test_atomic_write_replaces_whole_file(self):
        util.atomic_write(self.path('f'), b'first version, longer')
        util.atomic_write(self.path('f'), b'second')
        with open(self.path('f'), 'rb') as handle:
            self.assertEqual(handle.read(), b'second')

    def test_stamps(self):
        self.assertEqual(util.utc_stamp(0), '19700101T000000Z')
        self.assertEqual(util.utc_iso(0), '1970-01-01T00:00:00Z')

    def test_proc_identity_of_self_and_of_a_dead_pid(self):
        me = util.proc_identity(os.getpid())
        self.assertEqual(me['pid'], os.getpid())
        self.assertIn(me['state'], ('R', 'S'))
        self.assertGreater(me['starttime'], 0)
        child = subprocess.Popen([sys.executable, '-c', 'pass'])
        child.wait()
        self.assertIsNone(util.proc_identity(child.pid))

    def test_proc_identity_keeps_a_comm_with_spaces_and_parentheses(self):
        script = self.path('a (b) c')
        with open(script, 'w') as handle:
            handle.write('#!/bin/sh\nsleep 30\n')
        os.chmod(script, 0o755)
        child = subprocess.Popen([script])
        try:
            seen = None
            for _ in range(300):
                seen = util.proc_identity(child.pid)['comm']
                if seen == 'a (b) c':
                    break
                time.sleep(0.01)
            self.assertEqual(seen, 'a (b) c')
        finally:
            child.kill()
            child.wait()

    def test_append_jsonl_locked_keeps_every_line_from_parallel_writers(self):
        target = self.path('ledger.jsonl')
        code = ('import sys; sys.path.insert(0, %r); from orchkit import util\n'
                'for i in range(50): util.append_jsonl_locked(%r, {"w": int(sys.argv[1]), "i": i})\n'
                % (TOOLS, target))
        writers = [subprocess.Popen([sys.executable, '-c', code, str(n)]) for n in range(4)]
        for writer in writers:
            self.assertEqual(writer.wait(), 0)
        with open(target) as handle:
            rows = [json.loads(line) for line in handle]
        self.assertEqual(len(rows), 200)
        self.assertEqual(len({(row['w'], row['i']) for row in rows}), 200)

    def test_append_jsonl_locked_refuses_an_oversize_row(self):
        with self.assertRaises(ValueError):
            util.append_jsonl_locked(self.path('l.jsonl'), {'x': 'y' * 2000})
        self.assertFalse(os.path.exists(self.path('l.jsonl')))


if __name__ == '__main__':
    unittest.main()
