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
        items=[dict(id='synthetic', question_type=kind, venue=venue)]
        path=self.root/'bank.json'; path.write_text(json.dumps(items))
        catalog=dict(schema='r2-bank-catalog-v1', reader_sha256=P.reader_hash(),
                     items={digest(items[0]):dict(banks=list(banks), venue=venue)},
                     files={file_pin(path)['sha256']:dict(banks=list(banks),items=[digest(items[0])])})
        cp=self.root/'catalog.json'; cp.write_text(json.dumps(catalog))
        return file_pin(path), file_pin(cp)

    def read(self, bank, **kwargs):
        from launch_r2 import build as B
        root=directory();(root/'b').mkdir();(root/'k').mkdir()
        (root/'b/wh.json').write_bytes((B.TREE/'launch_s1/b/wh.json').read_bytes())
        (root/'job.sh').write_text('#!/bin/bash\nexit 2\n')
        def save(value):
            raw=B.capsule_json(value);h=__import__('hashlib').sha256(raw).hexdigest()
            p=root/'k'/(h+'.json');p.write_bytes(raw)
            return dict(path='k/'+p.name,sha256=h)
        def transport(pin):
            value=load(pin['path'])
            def walk(v):
                if isinstance(v,dict):
                    if set(v)=={'path','sha256'}:return transport(v)
                    return {k:walk(x) for k,x in v.items()}
                if isinstance(v,list):return [walk(x) for x in v]
                return v
            return save(walk(value))
        from student_pilot.p3_provenance import load
        prereg=save(load(self.prereg['path']))
        frozen=None
        if kwargs.get('freeze_pin'):
            v=load(kwargs['freeze_pin']['path']);v['prereg_sha256']=prereg['sha256']
            v['evidence']=[prereg];frozen=save(v)
        cfg=dict(r2_build2=dict(registry=transport(self.registry)),r2_evaluation=dict(
            catalog=save(load(bank[1]['path'])),prereg=prereg,freeze=frozen,
            choices=kwargs.get('choices',()),camera_routing=kwargs.get('camera_routing',False)))
        pin=save(cfg)
        (root/'k/launch.json').write_bytes(B.capsule_json(dict(config=dict(file=pin['path'],sha256=pin['sha256']))))
        (root/'k/0.json').write_bytes(B.capsule_json(dict(commit='a'*40,trainer=dict(file=pin['path'],sha256=pin['sha256']),
            record=dict(file=pin['path'],sha256=pin['sha256']))))
        files=[root/'job.sh',*list((root/'b').rglob('*')),*list((root/'k').rglob('*'))]
        (root/'SHA256SUMS.txt').write_text(''.join(file_pin(p)['sha256']+'  '+str(p.relative_to(root))+'\n' for p in files if p.is_file()))
        (root/'ANON_OK.json').write_text(json.dumps(dict(status='CLEAN',hits=0,manifest_sha256=file_pin(root/'SHA256SUMS.txt')['sha256'])))
        return P.read_bank(bank[0],catalog_pin=kwargs.get('caller_catalog_pin'),kit_root=root,choices=(),camera_routing=False)

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
        with self.assertRaisesRegex(ValueError,'Caller catalog differs'):
            self.read(bank,caller_catalog_pin=bank[1])
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
