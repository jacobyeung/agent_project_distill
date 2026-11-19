"""Pinned routing subsets; tiny fixtures do not establish production admission."""
from copy import deepcopy
import itertools
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from student_pilot import r1_coverage as C, r1_routing as R
from student_pilot.p3_provenance import file_pin, load
from student_pilot.r1_population import Membership

FAMILIES = ('absolute_distance', 'units', 'coverage_distance', 'coverage_units', 'recovery', 'camera_wording')

class Subsets(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='r1_subset_', dir=os.environ['TMPDIR']))
        self.serial = 0

    def write(self, value):
        self.serial += 1
        path = self.root / (str(self.serial)+'.json')
        path.write_text(json.dumps(value))
        return file_pin(path)

    def config(self, names):
        declaration = dict(schema='r1-routing-slices-v1', bound=list(names),
            deferred={k:'Awaiting independently validated rows' for k in FAMILIES if k not in names})
        return dict(r1_training=dict(routing_slice_declaration=self.write(declaration)))

    def test_every_subset(self):
        for n in range(7):
            for names in itertools.combinations(FAMILIES, n):
                with self.subTest(names=names):
                    self.assertEqual(C.source_names(dict.fromkeys(names), self.config(names)), names)

    def test_undeclared_source_refuses_by_name(self):
        for name in ('recovery', 'foreign'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'R1_ROUTING_FAMILY_UNDECLARED:'+name):
                C.source_names({**dict.fromkeys(FAMILIES[:4]), name:{}}, self.config(FAMILIES[:4]))

    def test_missing_source_refuses_by_name(self):
        with self.assertRaisesRegex(ValueError, 'R1_ROUTING_SOURCE_MISSING:recovery'):
            C.source_names(dict.fromkeys(FAMILIES[:4]), self.config(FAMILIES[:5]))

    def test_declaration_requires_all_reasons_and_valid_pin(self):
        cfg = self.config(FAMILIES[:4])
        pin = cfg['r1_training']['routing_slice_declaration']
        value = load(pin['path'])
        for change in ('missing', 'empty', 'overlap', 'duplicate', 'unknown', 'changed_pin'):
            bad = deepcopy(value)
            if change == 'missing': bad['deferred'].pop('recovery')
            elif change == 'empty': bad['deferred']['recovery'] = ' '
            elif change == 'overlap': bad['bound'].append('recovery')
            elif change == 'duplicate': bad['bound'].append('units')
            elif change == 'unknown': bad['bound'].append('foreign')
            new = self.write(bad)
            if change == 'changed_pin': new['sha256'] = '0'*64
            with self.subTest(change=change), self.assertRaises(ValueError):
                C.source_names(dict.fromkeys(FAMILIES[:4]), dict(r1_training=dict(routing_slice_declaration=new)))

    def test_legacy_deferred_unchanged(self):
        cfg = dict(r1_training=dict(routing_slices='deferred_first_boundary'))
        self.assertEqual(C.source_names({}, cfg), ())
        self.assertTrue(C.deferred(cfg))
        for name in FAMILIES:
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'R1_MINIMAL_SLICE_BOUND:.*'+name):
                C.source_names({name:{}}, cfg)

    def test_deferred_and_subset_declarations_cannot_mix(self):
        cfg = dict(r1_training=dict(routing_slices='deferred_first_boundary'))
        cfg['r1_training']['routing_slice_declaration'] = self.config(())['r1_training']['routing_slice_declaration']
        with self.assertRaisesRegex(ValueError, 'R1_ROUTING_DECLARATION_WITH_DEFERRED'):
            C.source_names({}, cfg)

    def tiny_base(self, cfg):
        from student_pilot.carrier_c1_routing import ROUTING_SCHEMA
        db = sqlite3.connect(':memory:')
        db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
        db.commit()
        (self.root/'base.sqlite').write_bytes(db.serialize()); db.close()
        division = self.write(dict(train_scenes=['d1/fixture_clean'], heldout_scenes=['d1/held']))
        cfg.update(dev_scene_exclusions=self.write(dict(schema='dev_s1_withhold_v1',
            natives=['d1/dev'], rooms=['d1/dev'], physical_groups=['scannet/dev'],
            canonical={'d1/dev':['scannet/dev']}, aliases={'d1/dev':['d1/vdev']})),
            benchmark_scene_exclusions=self.write(dict(schema='benchmark_scene_exclusions_v1', scenes=['d1/benchmark'])))
        return self.write(dict(schema=ROUTING_SCHEMA, stream='routing', database=file_pin(self.root/'base.sqlite'),
            count=0, division=division, scene_role='train', heldout_overlap=0))

    def test_composition_records_deferred_reasons_and_membership(self):
        for names in (FAMILIES[:4], FAMILIES[:5], ('coverage_units',), ()):
            with self.subTest(names=names):
                cfg = self.config(names); base = self.tiny_base(cfg)
                source = self.write({})
                sources = dict.fromkeys(names, source)
                row = dict(dataset='d1', scene='fixture_clean', question_type='camera_displacement',
                    target='<think>The camera moves right between the shown frames.</think><answer>right</answer>')
                batches = [(k, source, [dict(row=dict(row, qid='fixture_'+k))], source) for k in names]
                result = R.compose(base, sources, batches, cfg, self.root/('compose_'+str(self.serial)))
                self.assertEqual(result['count'], len(names))
                self.assertEqual(result['per_source'], dict.fromkeys(names, 1))
                declared = cfg['r1_training']['routing_slice_declaration']
                self.assertEqual(result['routing_slice_declaration'], declared)
                self.assertEqual(result['deferred'], load(declared['path'])['deferred'])
                member = Membership(result['source_membership'], cfg=cfg)
                self.assertEqual(set(member.sources), set(names))
                self.assertEqual(set(Membership(result['source_membership']).sources), set(names))
                relocated = deepcopy(cfg)
                relocated['r1_training']['routing_slice_declaration'] = self.write(load(declared['path']))
                self.assertEqual(set(Membership(result['source_membership'], cfg=relocated).sources), set(names))
                bad = load(result['source_membership']['path']); bad['deferred'] = {}
                if names != FAMILIES:
                    with self.assertRaisesRegex(ValueError, 'MEMBERSHIP_DEFERRED_DIFFERS'):
                        Membership(self.write(bad), cfg=cfg)

    def test_native_missing_and_undeclared_envelopes(self):
        # All source bytes are tiny test fixtures; no intake admission is claimed.
        names = ('absolute_distance', 'units')
        cfg = self.config(names); source = self.write({})
        cfg['r1_training']['row_sources'] = self.write({k:dict(source=source) for k in names})
        cfg['r1_training']['routing_inputs'] = {'absolute_distance':source}
        with self.assertRaisesRegex(ValueError, 'R1_ROUTING_ENVELOPE_MISSING:units'):
            R.compose_native(cfg, {}, self.root/'missing')
        cfg['r1_training']['routing_inputs']['units'] = dict(path=str(self.root/'MISSING.json'), sha256='0'*64)
        with self.assertRaisesRegex(ValueError, 'R1_ROUTING_ENVELOPE_MISSING_OR_CHANGED:units'):
            R.compose_native(cfg, {}, self.root/'absent')
        cfg['r1_training']['routing_inputs'] = {**dict.fromkeys(names, source), 'recovery':source}
        with self.assertRaisesRegex(ValueError, 'R1_ROUTING_FAMILY_UNDECLARED:recovery:envelope'):
            R.compose_native(cfg, {}, self.root/'undeclared')

    def test_alias_registered_and_guard_obligations(self):
        from student_pilot.job_env import ALIASES
        from launch_r2 import runtime
        self.assertEqual(ALIASES.get('STUDENT_R2_FRAME_HOST'), 'Q_E7')
        with patch.object(runtime.inspect, 'getsourcelines', return_value=(['def intake(): pass\n'], 1)):
            with self.assertRaisesRegex(ValueError, 'ambiguous or absent'):
                runtime.obligations()

    def test_camera_pin_is_tree_constant(self):
        self.assertEqual(C.EXTRA_PINS['camera_wording'], C.CAMERA_SOURCE_SHA256)
        source = Path(C.__file__).read_text()
        self.assertNotIn('environ', source)

if __name__ == '__main__': unittest.main()
