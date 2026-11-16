"""Tests for orchkit.anon: names, bytes, nested tar members, job parts, and the shipped helpers."""
import gzip
import io
import os
import sys
import tarfile
import tempfile
import unittest

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, TOOLS)
from orchkit import anon  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def tar_bytes(files, compress=False):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode='w') as archive:
        for name, data in sorted(files.items()):
            item = tarfile.TarInfo(name)
            item.size = len(data)
            archive.addfile(item, io.BytesIO(data))
    data = raw.getvalue()
    return gzip.compress(data) if compress else data


class AnonTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='orchkit_anon_')
        self.words = os.path.join(self.tmp, 'W.txt')
        with open(self.words, 'w') as handle:
            handle.write('# test list\nname plum\ntext walnut\ntextre (?<![\\w/])/secret/\n')
        self.rules = anon.load_rules(self.words)

    def write(self, rel, data):
        path = os.path.join(self.tmp, 'kit', rel)
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, 'wb') as handle:
            handle.write(data)
        return path

    def test_clean_tree_has_no_hits(self):
        self.write('a.py', b'print("plum is only a name rule")\n')
        self.assertEqual(anon.scan_tree(os.path.join(self.tmp, 'kit'), self.rules), [])

    def test_name_rule_hits_file_names_only(self):
        self.write('PLUM/x.py', b'ok\n')
        hits = anon.scan_tree(os.path.join(self.tmp, 'kit'), self.rules)
        self.assertTrue(hits)
        self.assertTrue(all(h['scope'] == 'name' for h in hits))

    def test_word_in_nested_tar_member_is_found(self):
        inner = tar_bytes({'deep/notes.txt': b'a Walnut tree\n'})
        middle = tar_bytes({'inner.tar': inner}, compress=True)
        self.write('payload.tar.gz', tar_bytes({'m/middle.tgz': middle}, compress=True))
        hits = anon.scan_tree(os.path.join(self.tmp, 'kit'), self.rules)
        self.assertEqual([h['where'] for h in hits],
                         ['payload.tar.gz!/m/middle.tgz!/inner.tar!/deep/notes.txt'])

    def test_member_name_and_regex_rule(self):
        self.write('p.tar', tar_bytes({'plum.txt': b'x', 'b.txt': b'see /secret/x'}))
        where = sorted(h['where'] for h in anon.scan_tree(os.path.join(self.tmp, 'kit'), self.rules))
        self.assertEqual(where, ['p.tar!/b.txt', 'p.tar!/plum.txt'])

    def test_symlink_target_is_checked(self):
        os.makedirs(os.path.join(self.tmp, 'kit'))
        os.symlink('/secret/plum', os.path.join(self.tmp, 'kit', 'link'))
        self.assertTrue(anon.scan_tree(os.path.join(self.tmp, 'kit'), self.rules))

    def test_job_parts(self):
        good = 'a15_cot_ap0123456789abcdef'
        self.assertEqual(anon.scan_job(self.rules, good, '#!/bin/bash\n', ['x'], {'A': 'b'}), [])
        self.assertTrue(anon.scan_job(self.rules, 'a15_cot_ap0123'))
        self.assertTrue(anon.scan_job(self.rules, good, argv=['--plum']))
        self.assertTrue(anon.scan_job(self.rules, good, env={'PLUM_DIR': '1'}))
        self.assertTrue(anon.scan_job(self.rules, good, env={'X': '/secret/y'}))
        self.assertTrue(anon.scan_job(self.rules, good, script='#SBATCH --comment=plum\n'))

    def test_missing_or_empty_word_list_is_an_error(self):
        with self.assertRaises((IOError, OSError)):
            anon.load_rules(os.path.join(self.tmp, 'absent.txt'))
        empty = os.path.join(self.tmp, 'empty.txt')
        with open(empty, 'w') as handle:
            handle.write('# nothing\n')
        with self.assertRaises(ValueError):
            anon.load_rules(empty)

    def test_shipped_job_side_modules_pass_the_real_list(self):
        rules = anon.load_rules()
        for name in ('util.py', 'stage.py', 'ret.py'):
            path = os.path.join(HERE, name)
            if os.path.exists(path):
                self.assertEqual(anon.scan_tree(path, rules), [], name)

    def test_real_list_catches_cluster_paths(self):
        rules = anon.load_rules()
        self.assertTrue(anon.scan_text('x', 'cd /scratch/jjyeung/foo', rules))
        self.assertTrue(anon.scan_text('x', 'open("/data2/x")', rules))
        self.assertEqual(anon.scan_text('x', '/project/community/u/data/x', rules), [])


if __name__ == '__main__':
    unittest.main()
