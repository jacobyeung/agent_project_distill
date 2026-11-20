"""Post-condition room authorities, using native parsers and authenticated fixtures."""
import copy
import json
import sqlite3
import unittest
from unittest.mock import patch
from tests.test_host24l4r import Fixture, ProtectedRooms
from student_pilot import r1_rooms as rooms, r1_direction_twins as twins
from student_pilot.p3_provenance import file_pin, write
from student_pilot.r2_withheld import Withheld


class RoomResolution(ProtectedRooms):

    def pointing_rows(self):
        for canonical in ('scannet/scene0001_02', 'scannet/scene0800_00', 'scannet/scene1001_00'):
            for field in ('canonical', 'provenance.canonical', 'dataset_scene'):
                row = dict(qid='shared', provenance=dict(canonical_scene='scannet/scene9000_00'))
                if field == 'canonical':
                    row['canonical'] = canonical
                elif field == 'provenance.canonical':
                    row['provenance']['canonical'] = canonical
                else:
                    row['dataset'], row['scene'] = canonical.split('/')
                yield field, row

    def test_pointing_clean_canonical_scene_cannot_hide_native_protected_room(self):
        authority = rooms.Rooms(self.pins)
        for field, row in self.pointing_rows():
            with self.subTest(field=field, row=row):
                self.assertIn(authority.status(row)[0], ('k1_heldout', 'r0'))
                with self.assertRaisesRegex(ValueError, '^R1_PROTECTED_ROOM_ROWS:pointing$'):
                    self.call([row], [row])

    def test_pointing_list_accepts_native_protected_room_with_clean_canonical_scene(self):
        role = self.role()
        for field, row in self.pointing_rows():
            with self.subTest(field=field, row=row):
                self.assertEqual(self.call([row, self.good], [self.good], [role])['checked_keys'], 1)

    def test_pointing_unresolved_canonical_scene_cannot_hide_protected_room(self):
        for canonical in ('unknown/token', 'bad'):
            row = dict(qid='shared', canonical='scannet/scene0001_02',
                       provenance=dict(canonical_scene=canonical))
            with self.subTest(canonical=canonical):
                with self.assertRaisesRegex(ValueError, '^R1_PROTECTED_ROOM_UNRESOLVED:pointing$'):
                    self.call([row], [row])
                with self.assertRaisesRegex(ValueError, '^R1_PROTECTED_ROOM_UNRESOLVED:pointing$'):
                    self.call([row], [], [self.role()])

    def test_pointing_clean_and_withheld_fields_keep_native_behavior(self):
        clean = dict(self.good, canonical='scannet/scene9001_00',
                     provenance=dict(canonical_scene='scannet/scene9002_00'))
        self.assertEqual(self.call([clean], [clean])['admitted_rows'], 1)
        alias = sorted(Withheld().aliases)[0]
        for field in ('canonical', 'alias'):
            row = copy.deepcopy(clean); row['provenance'][field] = alias
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, '^R1_PROTECTED_ROOM_ROWS:pointing$'):
                    self.call([row], [row])
                row['qid'] = 'shared'
                self.assertEqual(self.call([row], [], [self.role()])['checked_keys'], 1)

    def vqa_authority(self):
        # Only pinned hash/count constants change. Binding construction, byte checks,
        # strict/tiered resolution, SQLite reads and the withheld file run natively.
        withheld = next(x for x in sorted(Withheld().aliases) if x.startswith('scannet/scene'))
        mapping = dict(clean='scannet/scene9000_00', heldout='scannet/scene0001_02',
                       reserve='scannet/scene1001_00', r0='scannet/scene0800_00', withheld=withheld)
        aliases = {'d1/opaque_'+key: dict(canonical=value) for key, value in mapping.items()}
        path = self.root/'tiered.json'
        write(path, dict(complete=True, conflicts=[], quarantined_tokens=[], aliases=aliases))
        rows = self.jsonl('twins.jsonl', [])
        binding = self.jsonl('binding.jsonl', [dict(twin_key='twin', source_key='source')])
        union = self.jsonl('union.jsonl', [dict(row_key='union'+str(i)) for i in range(4959)])
        db = self.root/'vqa.sqlite'
        source = dict(qid='source', dataset='d1', scene='opaque_clean')
        with sqlite3.connect(db) as conn:
            conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT)')
            conn.execute('INSERT INTO rows VALUES(0,?)', (json.dumps(source),))
        spec = dict(rows=rows, binding=binding, aliases=file_pin(path), source_database=file_pin(db))
        self.cfg0['r1_training'].update(direction_twins=spec, v7_k1_removal=union)
        for name, pin in [('ROWS', rows), ('BINDING', binding), ('ALIASES', spec['aliases']), ('UNION', union)]:
            self.stack.enter_context(patch.object(twins, name, pin['sha256']))
        self.stack.enter_context(patch.object(twins, 'COUNT', 1))
        self.stack.enter_context(patch.object(rooms, 'STORE', spec['source_database']['sha256']))
        return mapping, source

    def test_vqa_native_tiered_clean_alias_passes(self):
        _, source = self.vqa_authority()
        self.assertEqual(rooms.Rooms(self.pins).status(source)[0], 'unresolved')
        self.assertEqual(twins.Binding(self.cfg0).room(source), 'scannet/scene9000')
        self.assertEqual(self.call([source], [source], stream='vqa')['admitted_rows'], 1)

    def test_vqa_native_tiered_protected_aliases_refuse(self):
        mapping, _ = self.vqa_authority()
        for key in mapping.keys() - {'clean'}:
            row = dict(qid='shared', dataset='d1', scene='opaque_'+key)
            with self.subTest(key=key):
                self.assertEqual(rooms.Rooms(self.pins).status(row)[0], 'unresolved')
                with self.assertRaisesRegex(ValueError, '^R1_PROTECTED_ROOM_ROWS:vqa$'):
                    self.call([row], [row], stream='vqa')

    def test_vqa_list_accepts_native_tiered_protected_aliases(self):
        mapping, source = self.vqa_authority()
        role = self.role('vqa')
        for key in mapping.keys() - {'clean'}:
            row = dict(qid='shared', dataset='d1', scene='opaque_'+key)
            with self.subTest(key=key):
                self.assertEqual(self.call([row, source], [source], [role], 'vqa')['checked_keys'], 1)

    def test_vqa_tiered_clean_list_key_refuses(self):
        _, source = self.vqa_authority(); source['qid'] = 'shared'
        with self.assertRaisesRegex(ValueError, '^R1_PROTECTED_LIST_KEY_NOT_PROTECTED:vqa$'):
            self.call([source], [], [self.role('vqa')], 'vqa')

    def test_vqa_native_unknown_alias_still_refuses(self):
        self.vqa_authority()
        row = dict(qid='shared', dataset='d1', scene='absent')
        with self.assertRaisesRegex(ValueError, '^R1_TWIN_ROOM_UNRESOLVED$'):
            twins.Binding(self.cfg0).room(row)
        with self.assertRaisesRegex(ValueError, '^R1_PROTECTED_ROOM_UNRESOLVED:vqa$'):
            self.call([row], [row], stream='vqa')
        with self.assertRaisesRegex(ValueError, '^R1_PROTECTED_ROOM_UNRESOLVED:vqa$'):
            self.call([row], [], [self.role('vqa')], 'vqa')

    def test_vqa_authority_bytes_remain_authenticated(self):
        self.vqa_authority()
        from pathlib import Path
        Path(self.cfg0['r1_training']['direction_twins']['aliases']['path']).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Missing or changed pinned input'):
            self.call([self.good], [self.good], stream='vqa')

    def test_non_vqa_streams_do_not_use_tiered_aliases(self):
        _, source = self.vqa_authority()
        for stream in ('pose', 'routing', 'pointing'):
            with self.subTest(stream=stream):
                with self.assertRaisesRegex(ValueError, '^R1_PROTECTED_ROOM_UNRESOLVED:'+stream+'$'):
                    self.call([source], [source], stream=stream)

    def test_vqa_census_and_postcondition_use_same_native_authority(self):
        _, source = self.vqa_authority()
        cfg = copy.deepcopy(self.cfg0)
        write(self.root/'sources.json', {})
        write(self.root/'store.json', dict(database=cfg['r1_training']['direction_twins']['source_database']))
        cfg['r1_training']['row_sources'] = file_pin(self.root/'sources.json')
        cfg['streams'] = dict(vqa=file_pin(self.root/'store.json'))
        self.jsonl('empty.jsonl', [])
        write(self.root/'naming.json', dict(rows=[dict(qid='n'+str(i)) for i in range(109)]))
        with patch('student_pilot.r1_coverage.deferred'), \
                patch('student_pilot.r1_coverage.validate_binding', return_value=None), \
                patch('student_pilot.r1_coverage.source_names', return_value=()), \
                patch('student_pilot.row_removals.pinned', return_value=self.root/'empty.jsonl'):
            audit, _ = rooms.census(cfg)
        result = rooms.check_protected_rooms(cfg, 'vqa', [source], [source])
        self.assertEqual(audit['store']['unresolved'], 0)
        self.assertEqual(audit['store']['canonical_from'], dict(pinned_tiered_room=1))
        self.assertEqual(audit['store']['ok'], result['admitted_rows'])


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(RoomResolution(name) for name in sorted(RoomResolution.__dict__)
                              if name.startswith('test_'))
