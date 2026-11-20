"""Protected-list order, authenticated room checks and stream isolation fixtures."""
import ast
import copy
import io
import json
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from student_pilot import r1_launch22 as launch, r1_rooms as rooms
from student_pilot.p3_provenance import file_pin, pinned, write
from student_pilot.row_removals import Removals


class Fixture(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='protected24l4r_'))

    def jsonl(self, name, rows):
        p = self.root/name
        p.write_text(''.join(json.dumps(row, sort_keys=True)+'\n' for row in rows))
        return file_pin(p)

    def role(self, stream='pointing', keys=('shared',), name='role.jsonl'):
        return dict(self.jsonl(name, [dict(row_key=k) for k in keys]), role='protected_rooms', stream=stream)

    def cfg(self, extras=()):
        files = [dict(path=str(self.root/str(i)), sha256=h) for i,h in enumerate(launch.REMOVAL_ORDER)]
        files[11:11] = extras
        return dict(remove_files=files, r1_training=dict(launch22=dict(removal_order=[p['sha256'] for p in files])))

    def sync(self, cfg):
        cfg['r1_training']['launch22']['removal_order'] = [p['sha256'] for p in cfg['remove_files']]
        return cfg

    def naming_stub(self):
        # Production naming bytes are unavailable. Every other pin uses the native byte check.
        return patch('student_pilot.p3_provenance.pinned', side_effect=lambda p:
                     self.root/'naming.json' if p['sha256'] == launch.NAMING_REMOVE else pinned(p))


class RemovalOrder(Fixture):
    def refuses(self, cfg):
        with self.assertRaisesRegex(ValueError, '^R1_NAMING_REMOVAL_ORDER$'):
            launch.validate_removals(cfg)

    def test_twelve_pass_and_naming_remains_last(self):
        cfg = self.cfg()
        with self.naming_stub():
            launch.validate_removals(cfg)
        self.assertEqual(cfg['remove_files'][-1]['sha256'], launch.NAMING_REMOVE)
        self.assertEqual(len(launch.REMOVAL_ORDER), 12)

    def test_one_and_two_and_same_stream_multiple_lists(self):
        one = self.role()
        two = self.role('pose', ('pose-key',), 'pose.jsonl')
        three = self.role('pointing', ('other',), 'other.jsonl')
        with self.naming_stub():
            for extra in ([one], [one,two], [one,two,three]):
                launch.validate_removals(self.cfg(extra))

    def test_role_at_every_wrong_position_refuses(self):
        role = self.role()
        for i in (*range(11), 12):
            cfg = self.cfg(); cfg['remove_files'].insert(i, role)
            with self.subTest(i=i):
                self.refuses(self.sync(cfg))

    def test_unknown_missing_role_or_stream_refuses(self):
        p = self.role()
        for field, value in [('role','other'), ('role',None), ('stream','mdg'), ('stream',None), ('stream','')]:
            q = dict(p)
            if value is None:q.pop(field)
            else:q[field] = value
            with self.subTest(field=field,value=value):self.refuses(self.cfg([q]))
        self.refuses(self.cfg([{k:v for k,v in p.items() if k not in ('role','stream')}]))

    def test_roles_on_pinned_entries_refuse(self):
        for i in range(12):
            cfg = self.cfg(); cfg['remove_files'][i].update(role='protected_rooms', stream='vqa')
            self.refuses(cfg)

    def test_duplicates_refuse_except_sealed_empty_pair(self):
        p = self.role()
        self.refuses(self.cfg([p,p]))
        self.refuses(self.cfg([p,dict(p,stream='pose')]))
        for h in launch.REMOVAL_ORDER:
            self.refuses(self.cfg([dict(p,sha256=h)]))

    def test_spec_mismatch_missing_changed_naming_and_prefix_refuse(self):
        cfg = self.cfg([self.role()]); cfg['r1_training']['launch22']['removal_order'] = list(launch.REMOVAL_ORDER)
        self.refuses(cfg)
        for i in (0,10,11):
            cfg = self.cfg(); cfg['remove_files'][i]['sha256'] = 'f'*64
            self.refuses(self.sync(cfg))
        cfg = self.cfg();cfg['remove_files'].pop();self.refuses(self.sync(cfg))

    def test_bad_sha_and_defects_refuse(self):
        p = self.role()
        for h in (None, '', 'F'*64, 'f'*63):self.refuses(self.cfg([dict(p,sha256=h)]))
        self.refuses(self.cfg([dict(p,defects=['extent'])]))
        self.refuses(dict(remove_files=[p]))

    def test_added_list_bytes_and_naming_bytes_are_checked(self):
        p = self.role();Path(p['path']).write_text('{}\n')
        with self.naming_stub(), self.assertRaisesRegex(ValueError,'Missing or changed pinned input'):
            launch.validate_removals(self.cfg([p]))
        cfg = self.cfg();Path(cfg['remove_files'][-1]['path']).write_text('{}')
        with self.assertRaisesRegex(ValueError,'Missing or changed pinned input'):
            launch.validate_removals(cfg)

    def test_identity_digests_role_and_stream(self):
        from student_pilot.carrier_c1_run import identity
        cfg = self.cfg([self.role()]); before = identity(cfg)
        for field,value in [('role','different'), ('stream','pose')]:
            other = copy.deepcopy(cfg);other['remove_files'][11][field] = value
            self.assertNotEqual(identity(other), before)


class ProtectedRooms(Fixture):
    def setUp(self):
        super().setUp()
        values = dict(split=dict(teacher_k1=dict(sha256=rooms.TEACHER,
            captures=[dict(room='scannet/scene%04d'%i,k1_split='heldout') for i in range(50)]),
            r0_scenes=dict(captures={'r':dict(room='scannet/scene0800')})),
            aliases={'d1/alias':'scannet/scene0001_02'}, build={})
        self.pins = {}
        for key,value in values.items():
            path=self.root/(key+'.json');write(path,value);self.pins[key]=file_pin(path)
        path=self.root/'reserve.txt';path.write_text(''.join('scannet/scene%04d\n'%i for i in range(1000,1372)))
        self.pins['reserve']=file_pin(path)
        path=self.root/'visits.csv';path.write_text('video_id,visit_id\n123,44\n')
        self.pins['visits']=file_pin(path)
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(rooms,'AUTHORITY',{k:p['sha256'] for k,p in self.pins.items()}))
        self.stack.enter_context(self.naming_stub())
        self.cfg0=self.cfg();self.cfg0['r1_training']['room_authority']=self.pins
        self.good=dict(qid='good',dataset='scannet',scene='scene9000_00')
        self.bad=dict(qid='shared',provenance=dict(canonical_scene='scannet/scene0001_02'))

    def call(self, sources, admitted, extra=(), stream='pointing'):
        cfg=copy.deepcopy(self.cfg0);cfg['remove_files'][11:11]=extra;self.sync(cfg)
        return rooms.check_protected_rooms(cfg,stream,iter(sources),iter(admitted))

    def test_clean_stream_and_valid_list_pass(self):
        p=self.role()
        result=self.call([self.bad,self.good],[self.good],[p])
        self.assertEqual(result,dict(stream='pointing',source_rows=2,admitted_rows=1,
            protected_lists=1,listed_keys=1,checked_keys=1,protected_rows=0))
        self.assertEqual(self.call([self.good],[self.good])['protected_lists'],0)

    def test_pointing_canonical_scene_leak_refuses_with_no_lists(self):
        with self.assertRaisesRegex(ValueError,'^R1_PROTECTED_ROOM_ROWS:pointing$'):
            self.call([self.bad],[self.bad])

    def test_canonical_scene_wins_over_conflicting_regular_fields(self):
        bad=dict(self.bad,canonical='scannet/scene9000_00',dataset='scannet',scene='scene9000_00')
        with self.assertRaisesRegex(ValueError,'^R1_PROTECTED_ROOM_ROWS:pointing$'):
            self.call([bad],[bad])

    def test_nonprotected_key_and_foreign_stream_key_refuse(self):
        for source in ([dict(self.good,qid='shared')], [self.good]):
            with self.assertRaisesRegex(ValueError,'^R1_PROTECTED_LIST_KEY_NOT_PROTECTED:pointing$'):
                self.call(source,[],[self.role(name=str(len(source))+str(source[0]['qid'])+'.jsonl')])

    def test_shared_key_cannot_drop_one_clean_row(self):
        with self.assertRaisesRegex(ValueError,'^R1_PROTECTED_LIST_KEY_NOT_PROTECTED:pointing$'):
            self.call([self.bad,dict(self.good,qid='shared')],[],[self.role()])

    def test_each_list_and_each_listed_key_checked(self):
        p=self.role();q=self.role(keys=('missing',),name='missing.jsonl')
        with self.assertRaisesRegex(ValueError,'R1_PROTECTED_LIST_KEY_NOT_PROTECTED'):
            self.call([self.bad],[],[p,q])

    def test_nested_pointing_and_label_keys_use_native_matching(self):
        row=dict(qid='x',pointing=dict(row_key='shared'),label_row_keys=['extra'],provenance=self.bad['provenance'])
        result=self.call([row],[],[self.role(keys=('shared','extra'))])
        self.assertEqual(result['checked_keys'],2)

    def test_unknown_admitted_room_cannot_pass_vacuously(self):
        for row in (dict(qid='x'),dict(qid='x',provenance=dict(canonical_scene='bad'))):
            with self.assertRaisesRegex(ValueError,'R1_PROTECTED_ROOM_UNRESOLVED:pointing'):
                self.call([row],[row])

    def test_k1_r0_reserve_r0_union_and_withheld_aliases_refuse(self):
        from student_pilot.r2_withheld import Withheld
        canonical=['scannet/scene0001_03','scannet/scene1001_00','scannet/scene0800_00',*sorted(Withheld().aliases)]
        for scene in canonical:
            with self.subTest(scene=scene), self.assertRaisesRegex(ValueError,'R1_PROTECTED_ROOM_ROWS:pointing'):
                row=dict(qid='x',provenance=dict(canonical_scene=scene));self.call([row],[row])

    def test_other_streams_resolve_native_canonical_and_alias(self):
        for stream in ('pose','vqa','routing'):
            for row in (dict(qid='shared',canonical='scannet/scene0001_02'),dict(qid='shared',dataset='d1',scene='alias')):
                with self.subTest(stream=stream), self.assertRaisesRegex(ValueError,'R1_PROTECTED_ROOM_ROWS:'+stream):
                    self.call([row],[row],stream=stream)
                p=self.role(stream,name=stream+row.get('scene','canonical')+'.jsonl')
                self.assertEqual(self.call([row,self.good],[self.good],[p],stream)['checked_keys'],1)

    def test_streams_do_not_validate_foreign_keys(self):
        p=self.role()
        self.assertEqual(self.call([self.good],[self.good],[p],stream='pose')['protected_lists'],0)

    def test_source_and_admitted_iterables_are_consumed_once(self):
        class Once:
            def __init__(self,rows):self.rows=rows;self.used=False
            def __iter__(self):
                if self.used:raise AssertionError('second pass')
                self.used=True;return iter(self.rows)
        self.assertEqual(rooms.check_protected_rooms(self.cfg0,'vqa',Once([self.good]),Once([self.good]))['admitted_rows'],1)

    def test_room_census_keeps_routing_slices_and_vqa_store_separate(self):
        row=dict(qid='shared',dataset='scannet',scene='scene0001_02')
        source=self.jsonl('slice.jsonl',[row]);write(self.root/'sources.json',dict(recovery=dict(source=source)))
        db=self.root/'rows.sqlite'
        with sqlite3.connect(db) as conn:
            conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT)')
            conn.execute('INSERT INTO rows VALUES(0,?)',(json.dumps(row),))
        write(self.root/'store.json',dict(database=file_pin(db)))
        write(self.root/'naming.json',dict(rows=[dict(qid='n'+str(i)) for i in range(109)]))
        empty=self.jsonl('empty.jsonl',[])
        def fixture_pin(pin):
            return Path(empty['path']) if pin['sha256'] in launch.REMOVAL_ORDER[:11] else pinned(pin)
        cfg=copy.deepcopy(self.cfg0)
        cfg['r1_training']['row_sources']=file_pin(self.root/'sources.json')
        cfg['streams']=dict(vqa=file_pin(self.root/'store.json'))
        with patch('student_pilot.r1_coverage.deferred'), patch('student_pilot.r1_coverage.validate_binding',return_value=None), \
                patch('student_pilot.r1_coverage.source_names',return_value=('recovery',)), \
                patch('student_pilot.row_removals.pinned',side_effect=fixture_pin):
            for stream,expected in [('pointing',(1,1)),('routing',(0,1)),('vqa',(1,0))]:
                cfg['remove_files']=self.cfg([self.role(stream,name=stream+'.jsonl')])['remove_files'];self.sync(cfg)
                audit,hits=rooms.census(cfg)
                self.assertEqual((audit['slices']['recovery']['unremoved_hits'],audit['store']['unremoved_hits']),expected)
                self.assertEqual(audit['remove_files'],cfg['remove_files'])

    def test_room_audit_binds_role_metadata_and_relocated_pins(self):
        cfg=copy.deepcopy(self.cfg0);cfg['remove_files']=self.cfg([self.role()])['remove_files'];self.sync(cfg)
        write(self.root/'sources.json',{})
        cfg['r1_training']['row_sources']=file_pin(self.root/'sources.json')
        db=dict(path=str(self.root/'unused.sqlite'),sha256='a'*64)
        write(self.root/'store.json',dict(database=db));cfg['streams']=dict(vqa=file_pin(self.root/'store.json'))
        audit=dict(schema='r1-room-audit-v1',complete=True,unknown_overlap=0,
            row_sources=cfg['r1_training']['row_sources'],remove_files=copy.deepcopy(cfg['remove_files']),
            authority=self.pins,slices={},store=dict(database=db,certification=self.pins['build'],
                scope='resolvable_rows_and_pinned_build_record',unresolved=0))
        real=rooms.pinned
        def fixture_pin(pin):
            return self.root/'unused' if pin['sha256'] in launch.REMOVAL_ORDER else real(pin)
        # The store is synthetic; exercise the unchanged metadata gate, not the production store seal.
        with patch('student_pilot.r1_coverage.deferred'), patch('student_pilot.r1_coverage.source_names',return_value=()), \
                patch('student_pilot.r1_launch22.bound',return_value=False), patch.object(rooms,'pinned',side_effect=fixture_pin):
            audit['remove_files'][11]['path']='/relocated/role.jsonl'
            write(self.root/'audit.json',audit)
            self.assertEqual(rooms.verify_audit(cfg,file_pin(self.root/'audit.json'))['remove_files'],audit['remove_files'])
            audit['remove_files'][11]['stream']='pose';write(self.root/'bad_audit.json',audit)
            with self.assertRaisesRegex(ValueError,'R1_PROOF_ROOM_AUTHORITY_INCOMPLETE'):
                rooms.verify_audit(cfg,file_pin(self.root/'bad_audit.json'))


class Consumers(Fixture):
    def test_same_keys_in_vqa_pose_routing_are_unchanged(self):
        p=self.role();rows=[dict(qid='shared'),dict(qid='other')];saved=copy.deepcopy(rows)
        rule=Removals([p]);counts={}
        for stream in launch.STREAMS:
            counts[stream]=[r for r in rows if rule.keep(r,stream)]
        self.assertEqual(counts['pointing'],rows[1:])
        for stream in ('vqa','pose','routing'):self.assertEqual(counts[stream],rows)
        self.assertEqual(rows,saved)
        with redirect_stdout(io.StringIO()):report=rule.report()
        self.assertEqual(report[0]['removed'],1);self.assertEqual(report[0]['matched'],1)
        self.assertEqual(report[0]['file'],p)

    def test_legacy_lists_keep_global_scope_and_role_lists_require_stream(self):
        p=self.role();legacy={k:p[k] for k in ('path','sha256')}
        self.assertFalse(Removals([legacy]).keep(dict(qid='shared')))
        with self.assertRaisesRegex(ValueError,'R1_PROTECTED_REMOVAL_STREAM_REQUIRED'):
            Removals([p]).keep(dict(qid='shared'))

    def test_native_selection_verifies_pose_mix_and_other_streams(self):
        p=self.role();db=self.root/'rows.sqlite'
        with sqlite3.connect(db) as conn:
            conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT)')
            conn.executemany('INSERT INTO rows VALUES(?,?)',[(0,json.dumps(dict(qid='shared'))),(1,json.dumps(dict(qid='other')))])
        write(self.root/'order.json',[[0,0]]);write(self.root/'indices.json',[1])
        selected=dict(count=1,database=file_pin(db),indices=file_pin(self.root/'indices.json'))
        streams=dict(vqa=dict(count=2,database=file_pin(db)),routing=dict(count=2,database=file_pin(db)),
            pointing=selected,pose=dict(kind='mix',count=1,order=file_pin(self.root/'order.json'),sources=[dict(kind='rows',database=file_pin(db))]))
        rule=Removals([p]);rule.verify_streams(streams)
        streams['pointing']=dict(count=2,database=file_pin(db))
        with self.assertRaisesRegex(ValueError,'REMOVE-listed row remains'):rule.verify_streams(streams)

    def test_target_filter_is_pointing_scoped_and_retains_metadata(self):
        from student_pilot.ground_target_filter import TargetFilter
        p=self.role();other=self.role('pose',name='pose.jsonl')
        self.assertFalse(TargetFilter([p]).keep(None,'shared','fixture')[0])
        self.assertTrue(TargetFilter([other]).keep(None,'shared','fixture')[0])
        self.assertEqual(TargetFilter([p]).settings()['removals'],[p])

    def test_routing_filters_use_the_explicit_stream(self):
        from student_pilot.r1_routing import Filters
        f=Filters.__new__(Filters);f.removals=Removals([self.role()]);f.cfg={}
        f.train={'d/s'};f.heldout=set();f.benchmark=f.reported=set();f.qids={}
        f.scenes=SimpleNamespace(excluded=lambda row:False)
        row=dict(qid='shared',dataset='d',scene='s')
        for stream in ('pose','vqa','routing'):self.assertIsNone(f.reason(row,stream))
        self.assertEqual(f.reason(row,'pointing'),'remove_files')

    def test_scene_gate_and_jsonl_filter_keep_foreign_keys(self):
        from student_pilot.scene_division_gate import check_rows
        from student_pilot.row_removals import filter_jsonl
        p=self.role();row=dict(qid='shared',dataset='d',scene='s')
        write(self.root/'division.json',dict(train_scenes=['d/s'],heldout_scenes=[]))
        for stream in ('vqa','routing'):
            result=check_rows([row],file_pin(self.root/'division.json'),removals=Removals([p]),stream=stream)
            self.assertEqual(result['admitted'],1)
        source=self.jsonl('source.jsonl',[row])
        with redirect_stdout(io.StringIO()):
            result=filter_jsonl(source,self.root/'kept.jsonl',[p],stream='vqa')
        self.assertEqual(result['kept'],1)

    def test_union_checks_use_hash_positions_not_total_length(self):
        from student_pilot.r1_coverage import union_rows,verify_union
        a=[dict(row_key='a',canonical='scannet/scene0001',reason='k1_heldout_v7')]
        b=[dict(row_key='b',canonical='scannet/scene0002',reason='k1_heldout_v7')]
        base=self.jsonl('base.jsonl',a);extra=self.jsonl('extra.jsonl',b)
        union=self.jsonl('union.jsonl',union_rows(a,b));n=self.jsonl('n.jsonl',[dict(row_key='n')])
        spec=dict(v7_k1_removal=union,v7_k1_union=dict(base=base,extra=extra,union=union))
        self.assertTrue(verify_union(spec,[base,union,n,self.role()],base['sha256'],n['sha256']))
        with self.assertRaisesRegex(ValueError,'R1_K1_UNION_ORDER'):
            verify_union(spec,[union,base,n,self.role(name='role2.jsonl')],base['sha256'],n['sha256'])

    def test_naming_rows_still_requires_exact_109_keys(self):
        from student_pilot.r1_launch22 import naming_rows
        write(self.root/'naming.json',dict(rows=[dict(qid='q'+str(i)) for i in range(109)]))
        self.assertEqual(len(naming_rows(file_pin(self.root/'naming.json'))),109)
        write(self.root/'bad.json',dict(rows=[dict(qid='q')]*109))
        with self.assertRaisesRegex(ValueError,'R1_NAMING_REMOVAL_CONTENT'):naming_rows(file_pin(self.root/'bad.json'))

    def production_nodes(self, relative, function, predicate):
        source=Path(__file__).resolve().parents[1]/relative
        tree=ast.parse(source.read_text())
        body=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==function)
        return [n for n in ast.walk(body) if predicate(n)]

    def evaluate(self, node, env):
        return eval(compile(ast.Expression(node),'<native consumer expression>','eval'),env)

    def test_prepare_and_rank0_removal_calls_carry_stream(self):
        # Execute the native call expressions without the unrelated model/admission setup.
        for function in ('prepare','prepared'):
            calls=self.production_nodes('student_pilot/carrier_c1_run.py',function,
                lambda n:isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='assert_clean')
            self.assertTrue(calls)
            for stream in ('vqa','pose','routing','pointing'):
                p=self.role(name=function+stream+'.jsonl')
                for node in calls:
                    context=stream if function=='prepare' and not isinstance(node.args[0],ast.Call) else 'pointing' if function=='prepare' else 'pose'
                    env=dict(removals=Removals([p]),name=stream,row=dict(qid='shared'),pointing_key=lambda row:'shared',json=json)
                    if function=='prepared':env['row']=json.dumps(dict(qid='shared'))
                    if context=='pointing':
                        with self.assertRaisesRegex(ValueError,'REMOVE-listed row remains'):self.evaluate(node,env)
                    else:self.evaluate(node,env)

    def test_shared_pool_preserves_rows_and_s1_routing_filters_only_routing(self):
        for filename,function,expected in [('s1_pool.py','prepare',None),('s1_pool.py','selected_rows',None),('s1_routing.py','_build','routing')]:
            calls=self.production_nodes('student_pilot/'+filename,function,
                lambda n:isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Removals')
            self.assertTrue(calls)
            for stream in ('pointing','vqa','routing','pose'):
                p=self.role(stream,name=filename+function+stream+'.jsonl')
                for node in calls:
                    rule=self.evaluate(node,dict(Removals=Removals,remove_files=[p],cfg=dict(remove_files=[p]),receipt=dict(remove_files=[p])))
                    if filename=='s1_pool.py' and rule.files:
                        # The receipt retains every pin for downstream stream materializers.
                        self.assertEqual(rule.files,[p])
                    else:
                        self.assertEqual(rule.keep(dict(qid='shared')),stream!=expected)

    def test_launch_s1_preserves_role_stream_and_defects(self):
        nodes=self.production_nodes('launch_s1/build.py','build',lambda n:isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=='cfg'
                    and isinstance(t.slice,ast.Constant) and t.slice.value=='remove_files' for t in n.targets))
        self.assertEqual(len(nodes),1)
        p=self.role();old=dict(self.jsonl('old.jsonl',[]),defects=['identity'])
        pins=self.evaluate(nodes[0].value,dict(pool=dict(remove_files=[old,p]),
            small_input=lambda name,pin:dict(path='/localized/'+name,sha256=pin['sha256'])))
        self.assertEqual(pins[1],dict(p,path='/localized/remove_1.jsonl'))
        self.assertEqual(pins[0]['defects'],old['defects'])

    def test_native_vqa_builder_retains_pointing_key_collision(self):
        from student_pilot.carrier_c1_data import build_stream
        from PIL import Image
        image=self.root/'frame.png';Image.new('RGB',(2,2)).save(image)
        frame=file_pin(image)
        row=dict(qid='shared',dataset='d',scene='s',target='yes',
            student_input=dict(frames=[frame]*32,frame_indices=list(range(32)),question='fixture'))
        source=self.jsonl('source.jsonl',[row])
        write(self.root/'division.json',dict(schema='diagnostic-whole-scene-division-v1',training_only=True,
              train_scenes=['d/s'],heldout_scenes=[]))
        with redirect_stdout(io.StringIO()):
            result=build_stream(source,file_pin(self.root/'division.json'),self.root/'stream','vqa',remove_files=[self.role()])
        self.assertEqual(result['count'],1)
        with sqlite3.connect(result['database']['path']) as conn:
            self.assertEqual(json.loads(conn.execute('SELECT row FROM rows').fetchone()[0]),row)

    def test_generic_kit_relocation_preserves_role_metadata(self):
        from launch_r2.build import relocate
        p=self.role();paths={};result=relocate(dict(remove_files=[p]),paths)['remove_files'][0]
        self.assertEqual({k:v for k,v in result.items() if k!='path'},{k:v for k,v in p.items() if k!='path'})
        self.assertEqual(result['path'],paths[p['path']])
        self.assertNotEqual(result['path'],p['path'])
