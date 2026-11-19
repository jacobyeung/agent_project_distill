"""Differential CPU tests; synthetic fixtures establish behavior, never admission."""
from copy import deepcopy
import importlib, itertools, json, os, sys, tempfile, types, unittest
from pathlib import Path
from unittest.mock import patch
from student_pilot import r1_coverage as C, r1_population as P, r1_routing as R
from student_pilot.p3_provenance import file_pin, load, digest

ROOT = Path(__file__).resolve().parents[2]
REF = types.ModuleType('patch_a2_reference')
REF.__path__ = [str(ROOT/'work/base/student_pilot')]
sys.modules[REF.__name__] = REF
BC = importlib.import_module(REF.__name__+'.r1_coverage')
BP = importlib.import_module(REF.__name__+'.r1_population')
BR = importlib.import_module(REF.__name__+'.r1_routing')
FAMILIES = ('absolute_distance','units','coverage_distance','coverage_units','recovery','camera_wording')
DETAILS = []

def outcome(fn):
    try:
        value = fn()
        if isinstance(value, (P.Membership, BP.Membership)):
            return ('OK', value.sources, value.rows, value.minimal)
        return ('OK', value)
    except Exception as e:
        return (type(e).__name__, str(e))

class Differential(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='patch_a2_diff_', dir=os.environ['TMPDIR']))
        self.serial = 0

    def pin(self, value):
        self.serial += 1
        p = self.root/(str(self.serial)+'.json')
        p.write_text(json.dumps(value)); return file_pin(p)

    def test_1280_legacy_source_names_cases(self):
        # Explicit reconstructed matrix: 256 source subsets x five undeclared configs.
        keys = FAMILIES+('room','room_programs_excluded')
        configs = [None, {}, {'r1_training':{}},
            {'r1_training':{'routing_slices':'deferred_first_boundary'}},
            {'r1_training':{'routing_slices':'invalid'}}]
        count = 0
        for bits in itertools.product((False,True), repeat=len(keys)):
            sources = {k:{} for k,b in zip(keys,bits) if b}
            for index,cfg in enumerate(configs):
                old = outcome(lambda:BC.source_names(sources,cfg))
                new = outcome(lambda:C.source_names(sources,cfg))
                with self.subTest(sources=tuple(sources), cfg=index): self.assertEqual(old,new)
                count += 1
        self.assertEqual(count, 1280)
        DETAILS.append(dict(check='legacy_source_names', cases=count, matrix='256 subsets of six families and two room audit keys x None, empty config, empty training, deferred, invalid routing_slices'))

    def test_legacy_validate_binding_cases(self):
        source = self.pin({})
        count = 0
        for bits in itertools.product((False,True), repeat=6):
            specs = {k:dict(source=source) for k,b in zip(FAMILIES,bits) if b}
            for mode in ('full','deferred','invalid'):
                cfg = dict(r1_training=dict(row_sources=self.pin(specs)))
                if mode != 'full': cfg['r1_training']['routing_slices'] = 'deferred_first_boundary' if mode=='deferred' else 'invalid'
                a = outcome(lambda:BC.validate_binding(cfg)); b = outcome(lambda:C.validate_binding(cfg))
                with self.subTest(sources=tuple(specs), mode=mode): self.assertEqual(a,b)
                count += 1
        DETAILS.append(dict(check='legacy_validate_binding', cases=count, scope='unchanged legacy behavior; source pins use a small invalid fixture so intentional camera pin replacement is tested separately'))

    def test_legacy_membership_cases(self):
        source = self.pin({}); count = 0
        for bits in itertools.product((False,True), repeat=6):
            sources = {k:dict(source=source, rows={k:digest({'fixture':k})}) for k,b in zip(FAMILIES,bits) if b}
            for minimal in (False,True):
                pin = self.pin(dict(schema='r1-source-membership-v1',sources=sources))
                a = outcome(lambda:BP.Membership(pin,minimal=minimal)); b = outcome(lambda:P.Membership(pin,minimal=minimal))
                with self.subTest(sources=tuple(sources), minimal=minimal): self.assertEqual(a,b)
                count += 1
        for name, value in (
            ('schema',dict(schema='wrong',sources={})),
            ('foreign',dict(schema='r1-source-membership-v1',sources={'foreign':dict(source=source,rows={})})),
            ('overlap',dict(schema='r1-source-membership-v1',sources={k:dict(source=source,rows={'duplicate':'0'*64}) for k in ('recovery','units')})),
            ('pin',dict(schema='r1-source-membership-v1',sources={'recovery':dict(source={**source,'sha256':'0'*64},rows={})}))):
            pin=self.pin(value)
            with self.subTest(case=name): self.assertEqual(outcome(lambda:BP.Membership(pin)),outcome(lambda:P.Membership(pin)))
            count += 1
        row = dict(qid='fixture',question_type='camera_displacement')
        for kind in FAMILIES:
            marked = dict(row,r1_source=dict(family=kind,sha256=source['sha256']))
            pin = self.pin(dict(schema='r1-source-membership-v1',sources={k:dict(source=source,rows={'fixture':digest(marked)} if k==kind else {}) for k in FAMILIES}))
            a,b = BP.Membership(pin),P.Membership(pin)
            for stream in ('routing','vqa','spatial'):
                for candidate in (marked,row,dict(marked,question_type='object_abs_distance'),dict(marked,qid='other')):
                    self.assertEqual(outcome(lambda:a.cell(candidate,stream)),outcome(lambda:b.cell(candidate,stream)))
                    count += 1
        DETAILS.append(dict(check='legacy_membership_and_cell',cases=count))

    def test_native_refusal_event_order_matches_base(self):
        src=self.pin({})
        cases=[('deferred',dict(r1_training=dict(routing_slices='deferred_first_boundary',row_sources=self.pin({}),source_membership=self.pin(dict(sources={}))))),
            ('no_routing_inputs',dict(r1_training=dict(row_sources=self.pin({k:dict(source=src) for k in ('recovery','absolute_distance','units')}),source_membership=self.pin(dict(schema='r1-source-catalog-v1',sources={}))))) ]
        for name,cfg in cases:
            records=[]
            for module,which in ((BR,'base'),(R,'candidate')):
                events=[]; output=self.root/(name+'_'+which)
                original_load=module.load
                def traced(path):
                    events.append(('load',str(path))); return original_load(path)
                with patch.object(module,'load',side_effect=traced),patch.object(module,'compose',wraps=module.compose) as compose:
                    result=outcome(lambda:module.compose_native(deepcopy(cfg),{},output))
                    records.append(dict(result=result,events=events,compose_called=compose.called,output_exists=output.exists(),files=[str(p.relative_to(output)) for p in output.rglob('*')] if output.exists() else []))
            DETAILS.append(dict(check='native_refusal',case=name,base=records[0],candidate=records[1]))
            with self.subTest(case=name): self.assertEqual(records[0],records[1])

    def test_deferred_native_cannot_drop_base_rows_and_publish(self):
        # Reuse PATCH_A's explicitly synthetic base/exclusion fixture. All rows
        # below belong to replaced base cells, so no frame or reader stub is used.
        import sqlite3
        from test_r1_subset import Subsets
        fixture=Subsets(); fixture.root=self.root; fixture.serial=0
        cfg=dict(r1_training=dict(routing_slices='deferred_first_boundary',
            row_sources=self.pin({}), source_membership=self.pin(dict(schema='r1-source-catalog-v1',sources={}))))
        fixture.serial=self.serial
        base=fixture.tiny_base(cfg)
        db=sqlite3.connect(':memory:');db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
        for i,(qid,typ) in enumerate((('a0_recovery_fixture','camera_displacement'),('a0_units_fixture','camera_displacement'),('distance_fixture','object_abs_distance'))):
            db.execute('INSERT INTO rows VALUES(?,?,?)',(i,json.dumps(dict(qid=qid,question_type=typ)),'{}'))
        db.commit();(self.root/'base.sqlite').write_bytes(db.serialize());db.close()
        receipt=load(base['path']);receipt.update(database=file_pin(self.root/'base.sqlite'),count=3)
        self.serial=fixture.serial;base=self.pin(receipt)
        output=self.root/'actual_native'
        result=outcome(lambda:R.compose_native(cfg,base,output))
        files=sorted(str(p.relative_to(output)) for p in output.rglob('*') if p.is_file()) if output.exists() else []
        DETAILS.append(dict(check='native_deferred_real_sqlite',outcome=result,files=files,output_exists=output.exists(),base_replaced_rows=3,scope='Synthetic CPU behavior regression; unmodified compose_native, SQLite, filters and reader'))
        self.assertEqual(result,('KeyError',"'recovery'"))
        self.assertFalse(output.exists())

    def test_projection_keeps_only_bound_families_and_room_audits(self):
        raw=load(ROOT.parent/'ro/orch_n30/fb_pack/route/out/config/LOCALIZED_ROW_SOURCES.json')
        bound=FAMILIES[:4]
        cfg=dict(r1_training=dict(routing_slice_declaration=self.pin(dict(schema='r1-routing-slices-v1',bound=list(bound),deferred={k:'Not selected for this unit test' for k in FAMILIES if k not in bound}))))
        with self.assertRaisesRegex(ValueError,'R1_ROUTING_FAMILY_UNDECLARED:'):
            C.source_names(raw,cfg)
        projected={k:v for k,v in raw.items() if k in set(bound)|{'room','room_programs_excluded'}}
        self.assertEqual(C.source_names(projected,cfg),bound)
        self.assertNotIn('command',projected);self.assertNotIn('inputs',projected)
        for name in bound:self.assertEqual(projected[name],raw[name])

class Camera(unittest.TestCase):
    def test_final_and_standin_in_declared_and_legacy_six_family_configs(self):
        from real_route_tests import RealRoute
        from student_pilot.r1_persisted import scope
        RealRoute.setUpClass()
        final = file_pin(ROOT.parent/'ro/orch_n30/fb_pack/cam/out/rows/camera_wording.jsonl')
        standin = file_pin(ROOT.parent/'ro/orch_n30/fb_pack/route/out/rows/camera_wording.jsonl')
        root=Path(tempfile.mkdtemp(prefix='camera_a2_',dir=os.environ['TMPDIR']))
        counter=itertools.count()
        def pin(value):
            p=root/(str(next(counter))+'.json');p.write_text(json.dumps(value));return file_pin(p)
        with scope(RealRoute.maps):
            for declared in (False,True):
                for which,camera in (('final',final),('standin',standin),('forged_final',dict(path=standin['path'],sha256=final['sha256']))):
                    specs={k:deepcopy(RealRoute.specs[k]) for k in FAMILIES}
                    specs['camera_wording']['source']=camera
                    cfg=dict(r1_training=dict(row_sources=pin(specs),wording_exclusion=RealRoute.original['r1_training']['wording_exclusion']))
                    if declared:cfg['r1_training']['routing_slice_declaration']=pin(dict(schema='r1-routing-slices-v1',bound=list(FAMILIES),deferred={}))
                    authenticated=[]; original=C.pinned
                    def capture(p):
                        # Unit isolation only: the read-only kit omits these two
                        # coverage files. Do not replace or bypass any camera read.
                        if p['sha256'] in C.PINS.values():
                            return Path(p['path'])
                        result=original(p); authenticated.append(p['sha256']);return result
                    with patch.object(C,'pinned',side_effect=capture): result=outcome(lambda:C.validate_binding(cfg))
                    DETAILS.append(dict(check='camera_authentication',declared=declared,file=which,outcome=result,authenticated=authenticated,scope='UNIT: only coverage-file pinned() calls isolated; camera pinned() and source constants unchanged; no production admission'))
                    with self.subTest(declared=declared,file=which):
                        if which=='final':
                            self.assertEqual(result,('ValueError','R1_CAMERA_WORDING_REQUIRED'))
                            self.assertIn(final['sha256'],authenticated)
                        elif which=='standin':
                            self.assertEqual(result,('ValueError','R1_CAMERA_SOURCE_PIN'))
                            self.assertNotIn(standin['sha256'],authenticated)
                        else:
                            self.assertEqual(result,('ValueError','Missing or changed pinned input: '+standin['path']))
        self.assertEqual(final['sha256'],'e8cbda99f794540c9c0f716d1ae8ce451fd84e473598795c67237fe051acd2d0')

    def test_camera_only_source_authentication_without_mocks(self):
        root=Path(tempfile.mkdtemp(prefix='camera_unmocked_',dir=os.environ['TMPDIR']))
        for name,path in (('final',ROOT.parent/'ro/orch_n30/fb_pack/cam/out/rows/camera_wording.jsonl'),
                          ('standin',ROOT.parent/'ro/orch_n30/fb_pack/route/out/rows/camera_wording.jsonl')):
            spec=root/(name+'.json'); spec.write_text(json.dumps(dict(camera_wording=dict(source=file_pin(path)))))
            cfg=dict(r1_training=dict(row_sources=file_pin(spec)))
            expected='R1_CAMERA_WORDING_REQUIRED' if name=='final' else 'R1_CAMERA_SOURCE_PIN'
            with self.subTest(file=name): self.assertEqual(outcome(lambda:C.validate_binding(cfg)),('ValueError',expected))
