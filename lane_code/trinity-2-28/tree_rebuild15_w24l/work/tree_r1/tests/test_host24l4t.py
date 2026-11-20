"""Pointing scenes fail closed; differential checks retain native refusals."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import random
import unittest
from unittest.mock import patch

from tests.test_host24l4r import ProtectedRooms
from student_pilot import r1_rooms as rooms
from student_pilot.r2_withheld import Withheld


class PointingResolution(ProtectedRooms):
    def unresolved_clean(self, scene):
        row = dict(self.good, qid='shared', canonical='scannet/scene9000_00',
                   provenance=dict(canonical_scene=scene))
        self.assertEqual(rooms.Rooms(self.pins).status(row)[0], 'ok')
        with self.assertRaisesRegex(ValueError, '^R1_PROTECTED_ROOM_UNRESOLVED:pointing$'):
            self.call([row], [row])
        with self.assertRaisesRegex(ValueError, '^R1_PROTECTED_ROOM_UNRESOLVED:pointing$'):
            self.call([row], [], [self.role()])

    def test_uppercase_scene_with_clean_ordinary_room_refuses(self):
        self.unresolved_clean('ScanNet/scene0001_02')

    def test_empty_capture_with_clean_ordinary_room_refuses(self):
        self.unresolved_clean('scannet/')

    def test_opaque_scene_with_clean_ordinary_room_refuses(self):
        self.unresolved_clean('d1/opaque')

    def test_unknown_scene_with_clean_ordinary_room_refuses(self):
        self.unresolved_clean('unknown/token')

    def test_listed_protected_ordinary_room_does_not_resolve_bad_scene(self):
        role = self.role()
        for scene in ('ScanNet/scene0001_02', 'scannet/', 'd1/opaque', 'unknown/token', '', 7, [], {}):
            for canonical in ('scannet/scene0001_02', 'scannet/scene0800_00', 'scannet/scene1001_00'):
                row = dict(qid='shared', canonical=canonical, provenance=dict(canonical_scene=scene))
                with self.subTest(scene=scene, canonical=canonical):
                    with self.assertRaisesRegex(ValueError, '^R1_PROTECTED_ROOM_UNRESOLVED:pointing$'):
                        self.call([row], [], [role])
                    with self.assertRaisesRegex(ValueError, '^R1_PROTECTED_ROOM_UNRESOLVED:pointing$'):
                        self.call([row], [row])

    def test_withheld_hit_keeps_native_opaque_alias_protection(self):
        withheld = Withheld()
        authority = rooms.Rooms(self.pins)
        opaque = []
        for alias in sorted(withheld.aliases):
            try:
                authority.room(alias)
            except (AttributeError, TypeError, ValueError):
                opaque.append(alias)
        self.assertTrue(opaque)
        role = self.role()
        for scene in (opaque[0], 'unknown/token'):
            row = dict(self.good, qid='shared', provenance=dict(canonical_scene=scene, alias=opaque[0]))
            with self.subTest(scene=scene):
                with self.assertRaisesRegex(ValueError, '^R1_PROTECTED_ROOM_ROWS:pointing$'):
                    self.call([row], [row])
                self.assertEqual(self.call([row], [], [role])['checked_keys'], 1)

    def test_absent_scene_and_other_streams_keep_native_resolution(self):
        for provenance in ({}, dict(canonical_scene=None)):
            row = dict(self.good, provenance=provenance)
            self.assertEqual(self.call([row], [row])['admitted_rows'], 1)
        for stream in ('pose', 'routing', 'vqa'):
            row = dict(self.good, provenance=dict(canonical_scene='unknown/token'))
            self.assertEqual(self.call([row], [row], stream=stream)['admitted_rows'], 1)

    def test_random_rows_never_admit_a_baseline_refusal(self):
        # Compare the actual sealed implementations, with the same native authority
        # objects. Like the reviewer's fuzz, VQA uses strict Rooms (twins disabled).
        baseline_root = Path(os.environ.get('HOST24L4T_BASE_ROOT', Path(__file__).resolve().parents[2]))
        functions = {'24l4t': rooms.check_protected_rooms}
        authority = rooms.Rooms(self.pins)
        withheld = Withheld()
        for version in ('24l4r', '24l4s'):
            source = baseline_root/('tree_r1_'+version)/'student_pilot/r1_rooms.py'
            self.assertTrue(source.is_file(), str(source))
            spec = importlib.util.spec_from_file_location('student_pilot._compare_'+version, source)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.stack.enter_context(patch.object(module, 'Rooms', return_value=authority))
            functions[version] = module.check_protected_rooms
        self.stack.enter_context(patch.object(rooms, 'Rooms', return_value=authority))
        self.stack.enter_context(patch('student_pilot.r2_withheld.Withheld', return_value=withheld))
        rng = random.Random(24420)
        values = [None, '', 'scannet/scene9000_00', 'scannet/scene0001_02',
                  'scannet/scene0800_00', 'scannet/scene1001_00', 'ScanNet/scene0001_02',
                  'scannet/', 'd1/opaque', 'unknown/token', 'bad', 7, [], {},
                  'arkitscenes/123', 'scannetpp/abcdef0123', sorted(withheld.aliases)[0]]
        samples = []
        for i in range(2500):
            row = dict(qid='random-'+str(i))
            if rng.random() < .8:
                row.update(dataset=rng.choice(('scannet', 'd1', 'scannetpp', 'd2', 'arkitscenes', 'unknown')),
                           scene=rng.choice(('scene9000_00', 'scene0001_02', 'scene0800_00', 'scene1001_00',
                                             'alias', 'opaque', '', '123', 'abcdef0123')))
            if rng.random() < .65:
                row['canonical'] = copy.deepcopy(rng.choice(values))
            for field in ('provenance', 'ground_record', 'gt_authority', 'routing'):
                nested = {}
                if rng.random() < .3:
                    nested['canonical'] = copy.deepcopy(rng.choice(values))
                if field == 'provenance':
                    if rng.random() < .8:
                        nested['canonical_scene'] = copy.deepcopy(rng.choice(values))
                    if rng.random() < .15:
                        nested['alias'] = rng.choice(('unknown/token', sorted(withheld.aliases)[0]))
                if nested:
                    row[field] = nested
            samples.append(row)
        counts = {}
        for stream in ('pose', 'vqa', 'routing', 'pointing'):
            tally = {v: dict(admitted=0, refused=0) for v in functions}
            for row in samples:
                outcomes = {}
                for version, function in functions.items():
                    try:
                        function(self.cfg0, stream, iter([row]), iter([row]))
                    except (ValueError, TypeError, AttributeError) as error:
                        outcomes[version] = str(error)
                        tally[version]['refused'] += 1
                    else:
                        outcomes[version] = None
                        tally[version]['admitted'] += 1
                if outcomes['24l4t'] is None:
                    self.assertIsNone(outcomes['24l4r'], (stream, row, outcomes))
                    self.assertIsNone(outcomes['24l4s'], (stream, row, outcomes))
            self.assertGreater(tally['24l4t']['admitted'], 0)
            self.assertGreater(tally['24l4t']['refused'], 0)
            counts[stream] = tally
        output = Path(os.environ.get('LANE_TEST_OUTPUT', str(self.root)))/'fuzz24l4t.json'
        output.write_text(json.dumps(dict(seed=24420, rows_per_stream=2500, twins=False,
                                         counts=counts), indent=2)+'\n')


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(PointingResolution(name) for name in sorted(PointingResolution.__dict__)
                              if name.startswith('test_'))
