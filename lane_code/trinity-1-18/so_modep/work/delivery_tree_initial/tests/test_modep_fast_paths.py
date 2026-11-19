"""Byte parity and unchanged filesystem checks for the opt-in path arithmetic."""
import json
import os
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from student_pilot import orchard_paths as paths
from student_pilot.p3_provenance import file_pin
from student_pilot.s1_admission import FrameAudit, verify_frames


class FastPaths(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='modep_paths_', dir=os.environ['TMPDIR']))
        self.project = self.root / 'project'
        self.frames = self.project / 'data2root/frames'
        self.frames.mkdir(parents=True)
        self.mapping = json.dumps({'/data2': str(self.project/'data2root')})
        self.scope = patch.object(paths, 'PROJECT', self.project)
        self.scope.start()
        self.env = patch.dict(os.environ, {'STUDENT_ORCHARD': '1', 'Q_E1': '1',
            'STUDENT_FRAME_ROOT_MAP': self.mapping, 'Q_E4': self.mapping})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(self.scope.stop)

    def call(self, flag, value, mapping=None):
        with patch.dict(os.environ, S1_PREP_FAST_PATHS=flag,
                        Q_E4=self.mapping if mapping is None else mapping):
            try:
                return ('value', str(paths.resolve_read(value)))
            except Exception as error:
                return (type(error).__name__, str(error))

    def test_lexical_containment_matches_pathlib(self):
        rng = random.Random(17)
        values = ['', '.', '..', '/', '//', '/a', '/a/b', '/a/../b', 'a/b', 'a/../b']
        for _ in range(150):
            values.append(rng.choice(['', '/', '//'])+'/'.join(rng.choices(['a', 'b', '.', '..'], k=5)))
        with patch.dict(os.environ, S1_PREP_FAST_PATHS='1'):
            for path in map(Path, values):
                for root in map(Path, values):
                    self.assertEqual(paths._within(path, root), path.is_relative_to(root), (path, root))

    def test_mappings_aliases_and_refusals_match(self):
        source = self.frames/'one';source.write_bytes(b'one')
        outside = self.root/'outside';outside.write_bytes(b'outside')
        (self.frames/'escape').symlink_to(outside)
        (self.frames/'inside').symlink_to(source)
        candidates = ['/data2/frames/one', '/data2/frames/missing', '/data2/frames/inside',
                      '/data2/frames/escape', '/data2/../outside', '/other/file']
        mappings = [self.mapping, '/data2='+str(self.project/'data2root'),
                    json.dumps({'/unsupported': str(self.frames)}),
                    json.dumps({'/data2': str(self.root/'outside')}),
                    json.dumps({'/data2': str(self.project/'data2root'), '/ignored': None}),
                    json.dumps({'/data2': str(self.project/'data2root/../data2root')}), '{broken']
        for mapping in mappings:
            for value in candidates:
                self.assertEqual(self.call('0', value, mapping), self.call('1', value, mapping))

    def test_every_resolution_is_repeated_and_mapping_changes_are_seen(self):
        p = self.frames/'one';p.write_bytes(b'one')
        sequences = []
        real = Path.resolve
        for flag in ('0', '1'):
            calls = []
            def resolve(path, **kw):
                calls.append(str(path));return real(path, **kw)
            with patch.dict(os.environ, S1_PREP_FAST_PATHS=flag), patch.object(Path, 'resolve', resolve):
                paths.resolve_read('/data2/frames/one')
                paths.resolve_read('/data2/frames/one')
            sequences.append(calls)
        self.assertEqual(sequences[0], sequences[1])
        self.assertEqual(len(sequences[1]), 6)
        self.assertEqual(self.call('1', '/data2/frames/one', '{"/bad":"/tmp/jjyeung/x"}')[0], 'ValueError')

    def test_database_and_samples_are_byte_identical(self):
        pins = []
        for i in range(37):
            p = self.frames/str(i);p.write_bytes(str(i).encode()*11)
            pins.append(dict(path='/data2/frames/'+str(i), sha256=file_pin(p)['sha256']))
        results = []
        for flag in ('0', '1'):
            out = self.root/('audit'+flag);out.mkdir()
            with patch.dict(os.environ, S1_PREP_FAST_PATHS=flag):
                audit = FrameAudit(out, [self.frames], sample_size=11)
                try:
                    for i in range(93):
                        audit.keep(dict(student_input=dict(frames=[pins[(i+j)%37] for j in range(32)])), 's'+str(i%3))
                    report = audit.finish()
                finally:
                    audit.close()
                verify_frames(report)
            results.append(report)
        self.assertEqual((self.root/'audit0/frame_inventory.sqlite').read_bytes(),
                         (self.root/'audit1/frame_inventory.sqlite').read_bytes())
        for result in results:result['inventory']['path'] = 'same-inventory-path'
        self.assertEqual(results[0], results[1])

    def test_changed_symlink_and_missing_frame_still_refuse(self):
        p = self.frames/'one';p.write_bytes(b'one')
        pin = dict(path='/data2/frames/link', sha256=file_pin(p)['sha256'])
        for flag in ('0', '1'):
            link = self.frames/('link'+flag);link.symlink_to(p)
            out = self.root/('mutation'+flag);out.mkdir()
            with patch.dict(os.environ, S1_PREP_FAST_PATHS=flag):
                audit = FrameAudit(out, [self.frames])
                try:
                    actual = dict(pin, path='/data2/frames/link'+flag)
                    audit.keep(dict(student_input=dict(frames=[actual])), 'vqa')
                    link.rename(self.frames/('retained-link'+flag))
                    link.symlink_to(self.root/'absent')
                    with self.assertRaises(ValueError):audit.keep(dict(student_input=dict(frames=[actual])), 'vqa')
                finally:audit.close()


if __name__ == '__main__':unittest.main()
