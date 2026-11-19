from pathlib import Path
from copy import deepcopy
import importlib.util,json,sys,unittest
from contextlib import ExitStack
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];D=L/'work/build23';T=L/'work/tree_r1'
sys.path[:0]=[str(T),str(L/'work/n1fix2')]
from monitor9 import Monitor
m=Monitor(T)
from student_pilot import r1_coverage as C
from student_pilot.r1_population import Membership, produce
from student_pilot.p3_provenance import write,file_pin,load
from student_pilot.r1_training import STREAMS
R=D/'proofs/unit';R.mkdir(parents=True,exist_ok=True)
def pin(name,value):
    (R/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');return file_pin(R/name)
def config():return dict(r1_training=dict(routing_slices='deferred_first_boundary'))
def card():
    return dict(schema='r1-card-v1',steps=1000,seed=17,quotas=STREAMS,cells=[
        dict(type=s if s!='routing' else 'routing_base',stream=s,rows_per_step=q) for s,q in STREAMS.items()]+[
        dict(type=s,stream='routing',rows_per_step=0) for s in ('recovery','absolute_distance','units','coverage','coverage_distance','coverage_units','camera_wording')])
class Minimal(unittest.TestCase):
    def test_explicit_declaration_and_full_default(self):
        self.assertEqual(C.source_names({},config()),())
        self.assertEqual(C.source_names({}),('recovery','absolute_distance','units'))
        self.assertFalse(C.deferred({}))
        for bad in (None,True,'minimal','full',{},[]):
            with self.subTest(bad=bad),self.assertRaisesRegex(ValueError,'R1_ROUTING_SLICES_INVALID'):
                C.deferred({'r1_training':{'routing_slices':bad}})
        for inputs in ({},None,{'x':{}}):
            c=config();c['r1_training']['routing_inputs']=inputs
            with self.assertRaisesRegex(ValueError,'R1_DEFERRED_ROUTING_INPUTS_PRESENT'):C.source_names({},c)
    def test_nonzero_deferred_cells(self):
        c=card();C.deferred_card(c)
        for name in ('recovery','absolute_distance','units','coverage','coverage_distance','coverage_units','camera_wording'):
            v=deepcopy(c);next(x for x in v['cells'] if x['type']==name)['rows_per_step']=1
            for a,counts,indices in ((v,None,None),(c,{name:1},None),(c,None,{name:[0]})):
                with self.subTest(name=name),self.assertRaisesRegex(ValueError,'R1_DEFERRED_CELL_NONZERO:'+name):C.deferred_card(a,counts,indices)
            next(x for x in v['cells'] if x['type']==name)['stream']='vqa'
            with self.assertRaisesRegex(ValueError,'R1_DEFERRED_CELL_NONZERO:'+name):C.deferred_card(v)
        for change in ({'rows_per_step':63},{'stream':'vqa'},{'type':'camera_displacement'}):
            v=deepcopy(c);v['cells'][2].update(change)
            with self.assertRaisesRegex(ValueError,'R1_DEFERRED_BASE_CELL_REQUIRED'):C.deferred_card(v)
    def test_membership_and_P_distance(self):
        p=pin('member.json',dict(schema='r1-source-membership-v1',sources={}))
        member=Membership(p,minimal=True)
        row=dict(qid='p_distance',question_type='object_abs_distance')
        self.assertEqual(member.cell(row,'routing'),'routing_base')
        self.assertEqual(member.cell(dict(qid='p_pose'),'pose'),'pose')
        with self.assertRaisesRegex(ValueError,'R1_BASE_DISTANCE_OR_UNIT_RETAINED'):Membership(p).cell(row,'routing')
        row['r1_source']={'family':'absolute_distance','sha256':'a'*64}
        with self.assertRaisesRegex(ValueError,'R1_DEFERRED_ROW_PRESENT'):member.cell(row,'routing')
        p=pin('member_bad.json',dict(schema='r1-source-membership-v1',sources={'camera_wording':{}}))
        with self.assertRaisesRegex(ValueError,'R1_DEFERRED_MEMBERSHIP_NONEMPTY'):Membership(p,minimal=True)
    def test_request_authentication(self):
        db=pin('db.json',[]);division=pin('division.json',{})
        value=dict(schema='c1-routing-stream-v1',scene_role='train',heldout_overlap=0,database=db,division=division)
        base=pin('base.json',value);cfg=config();cfg['streams']={'routing':base}
        self.assertTrue(C.routing_request(cfg,{'routing_base':base}))
        for request in ({},{'routing_base':dict(base,sha256='0'*64)}):
            with self.assertRaisesRegex(ValueError,'R1_ROUTING_BASE_DIFFERS'):C.routing_request(cfg,request)
        for inputs in (None,{},[],'x'):
            with self.assertRaisesRegex(ValueError,'R1_DEFERRED_ROUTING_INPUTS_PRESENT'):
                C.routing_request(cfg,dict(routing_base=base,routing_inputs=inputs))
        for change in ({'schema':'wrong'},{'scene_role':'heldout'},{'heldout_overlap':1},{'source_membership':{'x':1}}):
            p=pin('base_bad.json',dict(value,**change));cfg['streams']['routing']=p
            with self.assertRaisesRegex(ValueError,'R1_ROUTING_BASE_INVALID'):C.routing_request(cfg,{'routing_base':p})
    def test_validation_checks_population_and_indices(self):
        cfg=config();cfg['r1_training']['mix']=pin('card.json',card());C.validate_binding(cfg)
        cfg['r2_sampling']=dict(population=pin('pop.json',dict(counts={'absolute_distance':1})),indices=pin('indices.json',dict(cells={})))
        with self.assertRaisesRegex(ValueError,'R1_DEFERRED_CELL_NONZERO'):C.validate_binding(cfg)
        cfg['r2_sampling']['population']=pin('pop.json',dict(counts={}))
        cfg['r2_sampling']['indices']=pin('indices.json',dict(cells={'camera_wording':[1]}))
        with self.assertRaisesRegex(ValueError,'R1_DEFERRED_CELL_NONZERO'):C.validate_binding(cfg)

    def test_frame_entry_reaches_regenerated_selection(self):
        from launch_r1 import entry
        from student_pilot.r1_persisted import scope
        from student_pilot.p3_provenance import digest
        base=pin('entry_base.json',dict(schema='c1-routing-stream-v1',heldout_overlap=0,
            database={'path':'d','sha256':'0'*64},division={'path':'v','sha256':'1'*64}))
        point=pin('entry_point.json',dict(division={'path':'v','sha256':'1'*64}))
        stage=pin('entry_stage.json',dict(entries=[]))
        selection=pin('entry_selection.json',dict(regenerated_sha256=digest({})))
        aliases={p['sha256']:p['path'] for p in (base,point,stage,selection)}
        def local(p):return dict(p,path='u/'+p['sha256'])
        cfg=config();cfg.update(checkpoint_disk_guard={},streams=dict(routing=local(base),pointing=local(point)))
        root=R/('entry'+str(len(list(R.glob('entry[0-9]*')))))
        request=dict(job_tmp=str(root),binaries=['python3'],staging=local(stage),routing_selection=local(selection),routing_base=local(base))
        with ExitStack() as stack:
            stack.enter_context(scope(aliases))
            stack.enter_context(patch.object(entry,'TMP_NAMESPACE',R))
            for target,value in [('student_pilot.carrier_c1_sweep.recipe_for',{}),('student_pilot.checkpoint_space.plan',{}),
                                 ('launch_r2.staging.validate_plan',None),('launch_r2.staging.stage_inputs',None),
                                 ('student_pilot.scene_division_gate.check_bound',{}),('student_pilot.mdg_parent.model_pin',{})]:
                stack.enter_context(patch(target,return_value=value))
            selected=stack.enter_context(patch('student_pilot.s1_routing.build',return_value={}))
            native=stack.enter_context(patch('student_pilot.s1_admission.admit',side_effect=ValueError('NATIVE_ADMISSION_BOUNDARY')))
            result=entry.frame_host(cfg,root/'host',request)
            spec=importlib.util.spec_from_file_location('entry_before',L/'attic/build23/tree/launch_r1/entry.py')
            before=importlib.util.module_from_spec(spec);spec.loader.exec_module(before);before.TMP_NAMESPACE=R
            old_root=R/(root.name+'_before');old_request=dict(request,job_tmp=str(old_root))
            old_result=before.frame_host(cfg,old_root/'host',old_request)
        self.assertEqual(result['missing'],['NATIVE_ADMISSION_BOUNDARY'])
        self.assertEqual(old_result['missing'],['R1_ROUTING_COMPOSITION_INPUTS_MISSING'])
        (D/'ENTRY_BEFORE_AFTER.json').write_text(json.dumps(dict(before=old_result['missing'],after=result['missing'],regenerated_selection_equal=result['assertions']['routing_selection'])))
        self.assertTrue(result['assertions']['routing_selection']);selected.assert_called_once();native.assert_called_once()

    def test_launch_defers_required_slice_counts_only(self):
        from launch_r1 import entry
        from student_pilot.p3_provenance import digest
        cfg=config();cfg['r1_training']['mix']=pin('launch_card.json',card())
        cfg['r2_sampling']=dict(card=cfg['r1_training']['mix'])
        value=cfg['r1_training'];value.update(store_hashes={s:'0'*64 for s in STREAMS},registry={},row_plan_sha256=digest(cfg['r2_sampling']))
        value['host_receipt']=pin('host.json',dict(status='PASS',config_identity='i',assertions=dict.fromkeys(entry.ASSERTIONS,True),
            loader_audit=dict(complete=True,routing_training_counts={'recovery':0,'units':{}})))
        value['review']=pin('review.json',dict(verdict='PASS',config_identity='i'))
        with ExitStack() as stack:
            for target,result in [('student_pilot.r1_training.validate',{}),('student_pilot.r1_training.training_components',{}),
                ('student_pilot.r1_training.boundary',{}),('student_pilot.b7_inputs.layout',None),
                ('student_pilot.r1_mix.validate_binding',None),('student_pilot.carrier_c1_run.identity','i'),('student_pilot.r1_training.start',400)]:
                stack.enter_context(patch(target,return_value=result))
            self.assertEqual(entry.admit(cfg),400)
            with patch('student_pilot.r1_training.training_components',side_effect=ValueError('component evidence DEFERRED')):
                with self.assertRaisesRegex(ValueError,'component evidence DEFERRED'):entry.admit(cfg)
            cfg['r1_training'].pop('routing_slices')
            with self.assertRaisesRegex(ValueError,'RECOVERY_ROWS_ABSENT,UNIT_ROWS_ABSENT'):entry.admit(cfg)

    def test_native_builder_emits_no_slice_inputs(self):
        from launch_r1.build import build
        from student_pilot.r1_persisted import scope
        uploads=load(L/'work/build21/UPLOADS.json')
        aliases={x['sha256']:x['local_path'] for x in uploads['files']}
        root=R/('kit'+str(len(list(R.glob('kit[0-9]*')))))
        with scope(aliases):
            result=build(L/'work/build21/inputs/kit_config.json',L/'work/n1fix2/inputs',root)
        self.assertFalse(result['GO'])
        self.assertEqual(load(root/'k/c.json')['r1_training']['row_slice_inputs'],{})
        self.assertNotIn('routing_inputs',load(root/'k/h.json'))
if __name__=='__main__':
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Minimal))
    m.save(R);(D/'TESTS.json').write_text(json.dumps(dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),successful=r.wasSuccessful())))
    raise SystemExit(not r.wasSuccessful())
