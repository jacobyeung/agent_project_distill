"""Tests for orchkit.anon: names, bytes, nested tar members, job parts, and the shipped helpers."""
import bz2
import gzip
import io
import json
import lzma
import os
import sys
import tarfile
import tempfile
import unittest
import zipfile
import zlib

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
        self.assertIn('payload.tar.gz!gz!/m/middle.tgz!gz!/inner.tar!/deep/notes.txt',
                      [h['where'] for h in hits])

    def test_member_name_and_regex_rule(self):
        self.write('p.tar', tar_bytes({'plum.txt': b'x', 'b.txt': b'see /secret/x'}))
        where = sorted(h['where'] for h in anon.scan_tree(os.path.join(self.tmp, 'kit'), self.rules))
        self.assertTrue({'p.tar!/b.txt', 'p.tar!/plum.txt'} <= set(where), where)

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

    def test_review_oc01_hidden_bytes_are_found_or_fail_closed(self):
        rules = anon.load_rules()

        def tar(name, data, uname='', kind=tarfile.REGTYPE):
            raw = io.BytesIO()
            with tarfile.open(fileobj=raw, mode='w') as archive:
                item = tarfile.TarInfo(name)
                item.size = len(data)
                item.uname = uname
                item.type = kind
                archive.addfile(item, io.BytesIO(data))
            return raw.getvalue()

        deep = gzip.compress(tar('x', b'qwen'))
        for _ in range(4):
            deep = gzip.compress(tar('a.tgz', deep))
        cases = {'a.bin': gzip.compress(tar('x', b'qwen')), 'deep.tgz': deep,
                 'u.tar': tar('x', b'ok', uname='qwen'),
                 'f.tar': tar('x', b'qwen', kind=tarfile.FIFOTYPE),
                 'w.txt': 'qwen'.encode('utf-16'), 'b.bin': bz2.compress(b'qwen'),
                 'x.bin': lzma.compress(b'qwen')}
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, 'w') as archive:
            archive.writestr('m.txt', 'qwen')
        cases['z.npz'] = raw.getvalue()
        for name, data in sorted(cases.items()):
            path = self.write(name, data)
            self.assertTrue(anon.scan_tree(path, rules), name)
        self.assertTrue(any(hit['rule'] == 'too-deep'
                            for hit in anon.scan_tree(os.path.join(self.tmp, 'kit', 'deep.tgz'), rules)))
        named = io.BytesIO()
        with gzip.GzipFile(filename='qwen.txt', fileobj=named, mode='wb', mtime=0) as handle:
            handle.write(b'ok')
        trailers = {'n.gz': named.getvalue(), 't.bz2': bz2.compress(b'ok') + b'qwen',
                    't.xz': lzma.compress(b'ok') + b'qwen',
                    'h.bz2': bz2.compress(b'ok') + bz2.compress(b'qwen')}
        for name, data in sorted(trailers.items()):
            self.assertTrue(anon.scan_tree(self.write(name, data), rules), name)
        broken = self.write('c.gz', b'\x1f\x8b' + b'not gzip')
        self.assertEqual(anon.scan_tree(broken, rules)[0]['rule'], 'undecodable')

    def test_review_oc03_lane_case_and_format_id_prefix(self):
        rules = anon.load_rules()
        for text in ('ORCH_N30', 'Native_R4', 'orchkit-pins-v1-private', 'orchkit', 'ORCHKIT_X'):
            self.assertTrue(anon.scan_text('x', text, rules, 'text'), text)
        for text in ('"orchkit-pins-v1"', '"orchkit-config-v1",'):
            self.assertEqual(anon.scan_text('x', text, rules, 'name'), [], text)

    def test_review_oc02_config_strings_are_names(self):
        rules = anon.load_rules()
        path = self.write('CONFIG.json', json.dumps({'schema': 'orchkit-config-v1',
                                                     'job': {'root_parent': '/tmp/split'}}).encode())
        self.assertTrue(anon.scan_tree(os.path.dirname(path), rules))
        self.write('code.py', b'x = "a b".split()\n')
        os.rename(path, path + '.moved')
        self.assertEqual(anon.scan_tree(os.path.join(self.tmp, 'kit', 'code.py'), rules), [])
        self.assertEqual(anon.scan_job(rules, 'a15_cot_ap0123456789abcdef\n')[0]['rule'],
                         'job-name-format')

    def test_review_oc13_prefixed_zip_is_opened(self):
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('x', b'qwen')
        path = self.write('run.pyz', b'#!/usr/bin/env python3\n' + raw.getvalue())
        self.assertIn('run.pyz!/x', [hit['where'] for hit in anon.scan_tree(path, anon.load_rules())])

    def test_review_oc15_every_container_reading_is_inspected(self):
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode='w') as archive:
            blob = gzip.compress(b'qwen')
            item = tarfile.TarInfo('x.gz')
            item.size = len(blob)
            archive.addfile(item, io.BytesIO(blob))
        empty = io.BytesIO()
        with zipfile.ZipFile(empty, 'w'):
            pass
        path = self.write('a.bin', raw.getvalue() + empty.getvalue())
        self.assertIn('a.bin!/x.gz!gz', [hit['where'] for hit in anon.scan_tree(path, anon.load_rules())])
        path = self.write('b.bin', b'7z\xbc\xaf\x27\x1c' + b'\x00' * 40)
        self.assertEqual(anon.scan_tree(path, anon.load_rules())[0]['rule'], 'unsupported-container')

    def test_v7_tar_with_a_trailing_zip_and_json_escapes(self):
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode='w', format=tarfile.USTAR_FORMAT) as archive:
            blob = gzip.compress(b'qwen')
            item = tarfile.TarInfo('x.gz')
            item.size = len(blob)
            archive.addfile(item, io.BytesIO(blob))
        data = bytearray(raw.getvalue())
        data[257:265] = b'\x00' * 8
        data[148:156] = b' ' * 8
        data[148:156] = ('%06o\x00 ' % sum(data[:512])).encode('ascii')
        empty = io.BytesIO()
        with zipfile.ZipFile(empty, 'w'):
            pass
        path = self.write('v7.bin', bytes(data) + empty.getvalue())
        hits = anon.scan_tree(path, anon.load_rules())
        self.assertTrue(hits)
        path = self.write('d.json', b'{"m": "q\\u0077en"}')
        self.assertTrue(anon.scan_tree(path, anon.load_rules()))

    def test_review_oc18_escapes_in_any_encoding_or_layer(self):
        plain = b'{"m": "q\\u0077en"}'
        cases = {'a16.json': plain.decode().encode('utf-16'), 'a32.json': plain.decode().encode('utf-32'),
                 'a16le.json': plain.decode().encode('utf-16-le'), 'c.json.gz': gzip.compress(plain),
                 'noext.bin': plain, 'py.txt': b"x = 'q\\x77en'\n"}
        for name, data in sorted(cases.items()):
            self.assertTrue(anon.scan_tree(self.write(name, data), anon.load_rules()), name)

    def test_review_oc19_damaged_zip_fails_closed(self):
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('x', b'qwen')
        path = self.write('a.zip', raw.getvalue()[:-22])
        self.assertEqual(anon.scan_tree(path, anon.load_rules())[0]['rule'], 'unsupported-container')

    def test_review_oc23_octal_named_and_slash_escapes(self):
        cases = {'o.py': b'x = "q\\167en"\n', 'n.py': b'x = "q\\N{LATIN SMALL LETTER W}en"\n',
                 's.json': b'{"p": "\\/data2\\/secret"}'}
        for name, data in sorted(cases.items()):
            self.assertTrue(anon.scan_tree(self.write(name, data), anon.load_rules()), name)

    def test_review_oc24_damaged_prefixed_zip_and_bad_checksum_tar(self):
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('x', b'qwen')
        path = self.write('p.zip', b'#!/usr/bin/env python3\n' + raw.getvalue()[:-22])
        self.assertEqual(anon.scan_tree(path, anon.load_rules())[0]['rule'], 'unsupported-container')
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode='w', format=tarfile.USTAR_FORMAT) as archive:
            blob = gzip.compress(b'qwen')
            item = tarfile.TarInfo('x.gz')
            item.size = len(blob)
            archive.addfile(item, io.BytesIO(blob))
        data = bytearray(raw.getvalue())
        data[257:265] = b'\x00' * 8
        data[148:156] = b'0000000\x00'
        path = self.write('t.tar', bytes(data))
        self.assertEqual(anon.scan_tree(path, anon.load_rules())[0]['rule'], 'unsupported-container')

    def test_review_oc27_to_oc31(self):
        rules = anon.load_rules()
        named = io.BytesIO()
        with gzip.GzipFile(filename='split.txt', fileobj=named, mode='wb', mtime=0) as handle:
            handle.write(b'ok')
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode='w', format=tarfile.USTAR_FORMAT) as archive:
            item = tarfile.TarInfo('\u00e9t\u00e9.gz')
            blob = gzip.compress(b'qwen')
            item.size = len(blob)
            archive.addfile(item, io.BytesIO(blob))
        bad = bytearray(raw.getvalue())
        bad[257:265] = b'\x00' * 8
        bad[148:156] = b'0000000\x00'
        cases = {'c.py': b'x = "q\\\nwen"\n', 'g.gz': named.getvalue(), 'u.tar': bytes(bad),
                 'a.lzma': lzma.compress(b'qwen', format=lzma.FORMAT_ALONE),
                 'z.bin': zlib.compress(b'qwen')}
        for name, data in sorted(cases.items()):
            self.assertTrue(anon.scan_tree(self.write(name, data), rules), name)
        for text in ('/data2', '//data2/secret', '//scratch//jjyeung/x', '/home//jjyeung/agent_x'):
            self.assertTrue(anon.scan_text('x', text, rules, 'name'), text)
        for text in ('/project/u/data/x', 'metadata/x', '/x/data_out'):
            self.assertEqual(anon.scan_text('x', text, rules, 'name'), [], text)


if __name__ == '__main__':
    unittest.main()
