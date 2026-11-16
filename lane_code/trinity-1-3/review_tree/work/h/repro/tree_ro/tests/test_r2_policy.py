"""Synthetic evidence tests exercise real record and bank readers."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from student_pilot import r2_policy as P
from student_pilot.p3_provenance import file_pin, digest, write
from tests.test_r2_data_path import directory, fixture, manifest, LANE
from student_pilot.r2_withheld import Withheld, SHA256, shape
from student_pilot.r2_intake import intake, text_report


def evidence(root, phase='training'):
    root.mkdir(exist_ok=True)
    source = root/'input.json'
    write(source, dict(synthetic=True))
    registry = P.slots()
    for i, (name, slot) in enumerate(registry.items()):
        record = dict(schema=slot['expected_schema'], component=name, component_class=slot['component_class'],
                      phase=slot['phase'], inputs=[file_pin(source)], synthetic=True,
                      verdict='PROVEN_CLEAN', exclusions_complete=True)
        if name in P.LINEAGE:
            record.update(verdict='OVERLAP_FOUND', checked_banks=list(P.SCOPE),
                          overlaps=[dict(bank='STI-Bench'), dict(bank='VSI-Bench', venue='381879')])
        if name in P.EXTERNAL:
            record.update(verdict='EXEMPT_FROZEN', frozen=True)
        path=root/f'{i}.json'; write(path, record); slot['record']=file_pin(path)
    path=root/'registry.json'; write(path, registry)
    return file_pin(path)


class Policy(unittest.TestCase):
    def setUp(self):
        self.root=directory()
        self.registry=evidence(self.root/'e')
        self.prereg=file_pin(LANE/'work/records/design/REFREEZE_PREREGISTRATION_20261115.json')
        write(self.root/'freeze.json', dict(schema='r2-dated-freeze-v1', date='2026-11-15',
              prereg_sha256=self.prereg['sha256'], decisions={k:'fixture' for k in ['C1','C2','C3','C4','D1','D2']},
              evidence=[self.prereg]))
        self.freeze=file_pin(self.root/'freeze.json')

    def bank(self, banks=('VSI-Bench',), venue='381879', kind='object_abs_distance'):
        items=[dict(id='synthetic', question_type=kind)]
        path=self.root/'bank.json'; path.write_text(json.dumps(items))
        catalog=dict(schema='r2-bank-catalog-v1', reader_sha256=P.reader_hash(),
                     items={digest(items[0]):dict(banks=list(banks), venue=venue)})
        cp=self.root/'catalog.json'; cp.write_text(json.dumps(catalog))
        return file_pin(path), file_pin(cp)

    def read(self, bank, **kwargs):
        return P.read_bank(*bank, registry_pin=self.registry, prereg_pin=self.prereg, **kwargs)

    def test_phase_registry_and_missing_records(self):
        self.assertEqual(len(P.components(self.registry, 'training')),9)
        self.assertEqual(len(P.components(self.registry, 'native_evaluation')),14)
        original=json.loads(Path(self.registry['path']).read_text())
        for name in original:
            changed=deepcopy(original); changed[name]['record']=None
            path=self.root/'changed.json'; path.write_text(json.dumps(changed)); pin=file_pin(path)
            if name in P.CHOICES:
                P.components(pin,'training')
            with self.assertRaises(ValueError): P.components(pin,'native_evaluation')
        changed=deepcopy(original); changed['init_m544']['component_class']='external_frozen'
        path.write_text(json.dumps(changed))
        with self.assertRaises(ValueError): P.components(file_pin(path),'training')
        path.write_text('{}')
        with self.assertRaises(ValueError): P.components(file_pin(path),'training')
        with self.assertRaises(ValueError): P.components(self.registry,'other')

    def test_record_schema_overlap_and_pins(self):
        registry=json.loads(Path(self.registry['path']).read_text())
        slot=registry['init_m544']; original=json.loads(Path(slot['record']['path']).read_text())
        for changes in [dict(schema='foreign'), dict(component='foreign'), dict(phase='other'), dict(inputs=[]),
                        dict(verdict='UNKNOWN'), dict(overlaps=None), dict(checked_banks=[]),
                        dict(overlaps=[dict(bank='VSTI', venue='other')])]:
            path=self.root/'bad.json'; path.write_text(json.dumps({**original,**changes}))
            with self.assertRaises(ValueError): P.record({**slot,'record':file_pin(path)})
        for name, changes in [('geometry_tower', dict(frozen=False)), ('data_rows_r2',dict(exclusions_complete=False))]:
            slot=registry[name]; data=json.loads(Path(slot['record']['path']).read_text()); data.update(changes)
            path.write_text(json.dumps(data))
            with self.assertRaises(ValueError): P.record({**slot,'record':file_pin(path)})
        with self.assertRaises(ValueError): P.record({**slot,'record':dict(path=str(path),sha256='0'*64)})

    def test_actual_bank_identity_and_scope(self):
        bank=self.bank()
        _, receipt=self.read(bank, freeze_pin=self.freeze)
        self.assertEqual(receipt['required_scores'],['all','without_venue_381879'])
        P.require_scores(receipt, dict(all=0,without_venue_381879=0))
        with self.assertRaises(ValueError): P.require_scores(receipt, dict(all=0))
        for denied in ['STI-Bench','ReSTI','MindCube','unknown']:
            with self.assertRaisesRegex(ValueError,'outside'):
                self.read(self.bank((denied,)),declared_label='development',freeze_pin=self.freeze)
        _, receipt=self.read(self.bank(('dev-S1',)))
        self.assertEqual(receipt['label'],'paired-comparison only')
        for change in ['reader','identity','empty','duplicate']:
            bank=self.bank(); path=Path(bank[0]['path']); cp=Path(bank[1]['path'])
            data=json.loads(cp.read_text())
            if change=='reader': data['reader_sha256']='0'*64
            if change=='identity': data['items']={}
            if change=='empty': path.write_text('[]')
            if change=='duplicate': path.write_text(json.dumps(json.loads(path.read_text())*2))
            cp.write_text(json.dumps(data))
            with self.assertRaises(ValueError): self.read((file_pin(path),file_pin(cp)),freeze_pin=self.freeze)

    def test_selector_and_freeze(self):
        for bank in ['ReVSI','VSTI']:
            with self.assertRaisesRegex(ValueError,'selector'):
                self.read(self.bank((bank,)), choices=['grounding_selector_deployed'],freeze_pin=self.freeze)
        with self.assertRaisesRegex(ValueError,'freeze'): self.read(self.bank(),choices=['box_policy'])
        with self.assertRaisesRegex(ValueError,'Unknown program'): self.read(self.bank(), choices=['other'])
        self.read(self.bank(),choices=list(P.CHOICES),freeze_pin=self.freeze)
        self.read(self.bank(('VSTI',),kind='camera_displacement'), camera_routing=True)
        with self.assertRaises(ValueError): self.read(self.bank(('VSTI',)), camera_routing=True)
        path=Path(self.freeze['path']); frozen=json.loads(path.read_text())
        for change in [dict(schema='bad'),dict(date='bad'),dict(date='2026-11-14'),dict(prereg_sha256='a'*64),dict(decisions={}),dict(evidence=[])]:
            path.write_text(json.dumps({**frozen,**change}))
            with self.assertRaises(ValueError): P.freeze_check(file_pin(path), self.prereg)

    def test_shared_withheld_and_alias_intake(self):
        source=LANE/'work/shared/WITHHELD_ROOMS_80.json'
        room_list=json.loads(source.read_text())
        rule=Withheld(file_pin(source))
        self.assertEqual(rule.rooms_sha256,room_list['rooms_sha256'])
        row=fixture(self.root)
        alias=room_list['aliases'][room_list['rooms'][0]][0]
        row['provenance']['alias']=alias
        admitted, report=intake(manifest(self.root/'m',[row],family='alias_only'))
        self.assertEqual(admitted,[]); self.assertEqual(report['rows_withheld'],1)
        self.assertIn('alias_only: rows withheld=1',text_report(report))
        row['provenance']['alias']=next(x for x in room_list['aliases'][room_list['rooms'][0]] if x.startswith('d1/v'))
        self.assertTrue(rule.touches(row,dict(names=[])))
        row['provenance']['alias']='d1/fixture_clean'
        self.assertFalse(rule.touches(row,dict(names=[])))
        for changed in [{**room_list,'seed':0},{**room_list,'rooms':room_list['rooms'][:-1]},dict(rooms=[])]:
            path=self.root/'foreign.json';path.write_text(json.dumps(changed))
            with self.assertRaises(ValueError): Withheld(file_pin(path))
            with self.assertRaises(ValueError): shape(changed)
        with self.assertRaises(ValueError): Withheld(dict(path=str(source),sha256='0'*64))
