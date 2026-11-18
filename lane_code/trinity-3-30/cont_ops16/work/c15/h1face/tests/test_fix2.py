"""Deployment migration must reach prepared jobs and reject stale receipts."""
import offline_guard
import base64
import copy
import io
import json
from pathlib import Path
import re
import sys
import tarfile
import unittest
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'kit/launcher'))
import binding as B
import orchard_launcher as L
import export_stage as E


class Deployment(unittest.TestCase):
    def test_exact_roots_for_milestones_and_all_stops(self):
        root = '/project/community/jjyeung/okh7/'
        for step, generation in [(100, None), (200, None)] + [(137, g) for g in B.STOPS]:
            with self.subTest(step=step, generation=generation):
                value = B.expected('17c4ffa4', step, generation)
                self.assertEqual(value['done'], root+f'x_3fdda0fb/o/gcs_17c4ffa4_m{step}.done')
                self.assertEqual(value['claim'], root+f'x_3fdda0fb/o/gcs_17c4ffa4_{generation}.claim' if generation else None)
                for field in ('done', 'claim'):
                    if value[field] is None:
                        continue
                    stale = dict(value)
                    stale[field] = stale[field].replace('x_3fdda0fb', 'x_4b3114cf')
                    with self.assertRaisesRegex(ValueError, 'Export binding differs'):
                        B.validate(stale)

    def test_d0_binding_bytes_unchanged(self):
        for step in (100, 200):
            wanted = dict(run='359fcc3c', step=step, namespace='8865619b', generation=f'm{step}',
                          object=f'q8/8865619b/359fcc3c_m{step}.tar',
                          done=f'/project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m{step}.done', claim=None)
            self.assertEqual(json.dumps(B.expected('359fcc3c', step)).encode(), json.dumps(wanted).encode())

    def test_prepared_bootstrap_pins_new_binding_and_refuses_old_root(self):
        for step, generation in [(100, None), (200, None), (137, 'mstopC')]:
            dest = ROOT/'evidence'/('test_'+uuid.uuid4().hex)/'prepared'
            cfg = L.prepare('a000000001', dest, step, run='17c4ffa4', generation=generation, families=['a7'])
            L.validate_request(cfg)
            L.validate_batch((dest/'BATCH.sh').read_text(), cfg)
            encoded = re.search(r"raw=base64.b64decode\('([^']+)'", (dest/'BATCH.sh').read_text())[1]
            with tarfile.open(fileobj=io.BytesIO(base64.b64decode(encoded))) as archive:
                source = archive.extractfile('bootstrap/binding.py').read()
                packaged = json.loads(archive.extractfile('bootstrap/CONFIG.json').read())
            self.assertEqual(source, (ROOT/'kit/launcher/binding.py').read_bytes())
            self.assertIn(b'x_3fdda0fb', source)
            self.assertNotIn(b'x_4b3114cf', source)
            self.assertEqual(packaged['spec']['export_binding'], B.expected('17c4ffa4', step, generation))
            stale = copy.deepcopy(cfg)
            for field in ('done', 'claim'):
                value = stale['spec']['export_binding'][field]
                if value:
                    stale['spec']['export_binding'][field] = value.replace('x_3fdda0fb', 'x_4b3114cf')
            stale['plan_sha256'] = L.canonical(stale['spec'])
            with self.assertRaisesRegex(ValueError, 'Export binding differs'):
                L.validate_request(stale)
            with patch.object(E.S, 'process_stream') as remote, patch.object(Path, 'read_bytes') as read:
                with self.assertRaisesRegex(ValueError, 'Export binding differs'):
                    E.fetch_and_stage(dest, stale)
                read.assert_not_called()
                remote.assert_not_called()


if __name__ == '__main__':
    unittest.main()
