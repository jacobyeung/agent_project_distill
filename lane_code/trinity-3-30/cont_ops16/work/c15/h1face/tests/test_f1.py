"""Facing populations, payload invariance, and the unchanged step-544 gate."""
import offline_guard
import copy
import json
from pathlib import Path
import sys
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'kit/launcher'), str(ROOT)]
import orchard_launcher as L
from tools.verify_f1 import payload


def folder():
    root = ROOT/'evidence'/('test_f1_'+uuid.uuid4().hex)
    root.mkdir()
    return root


class FacingTests(unittest.TestCase):
    def test_direct_keeps_all_direction_twins(self):
        inventory = json.loads((ROOT/'kit/reader/e193_items.json').read_text())['families']
        counts = {'object_rel_direction_'+level:50 for level in ('easy','medium','hard')}
        for family in ('away','forward'):
            rows = [dict(question_type=t) for t in inventory[family]['items'].values()]
            direct = L.F.population(rows, dict(types='direct'))
            self.assertEqual(direct, L.F.population(rows, {}))
            self.assertEqual(direct, dict(items=150, types=counts, excluded={}, rooms_with_items=None))

    def test_facing_payload_bytes_and_pins_equal_main_a7(self):
        root = folder()
        token = 'a'+uuid.uuid4().hex[:10]
        old = L.prepare(token, root/'main_a7', 200, run='673bc60f', families=['main','a7'], types='direct')
        for index, families in enumerate((['away'],['forward'],['away','forward'],['main','a7','away','forward'])):
            dest = root/str(index)
            cfg = L.prepare(token, dest, 200, run='673bc60f', families=families, types='direct')
            raw = payload(dest)
            self.assertEqual(raw, payload(root/'main_a7'))
            self.assertEqual(cfg['payload_pins'], old['payload_pins'])
            L.validate_request(cfg); L.validate_payload(raw, cfg)
            L.validate_batch((dest/'BATCH.sh').read_text(), cfg)

    def test_step_544_refuses_every_non_a7_family(self):
        for types in (None, 'direct'):
            root = folder()
            cfg = L.prepare('a000000001', root/'accepted', 544, run='469ddece',
                            generation='mstop', families=['a7'], types=types)
            for families in (['main'], ['away'], ['forward'], ['a7','away'],
                             ['main','a7','away','forward'], ['unknown'], []):
                dest = root/('refused_'+str(len(families))+'_'+str(families))
                with self.assertRaises(ValueError):
                    L.prepare('a000000001', dest, 544, run='469ddece',
                              generation='mstop', families=families, types=types)
                self.assertFalse(dest.exists())
                bad = copy.deepcopy(cfg)
                bad['families'] = bad['spec']['families'] = families
                bad['plan_sha256'] = L.canonical(bad['spec'])
                with self.assertRaises(ValueError): L.validate_request(bad)


if __name__ == '__main__':
    unittest.main()
