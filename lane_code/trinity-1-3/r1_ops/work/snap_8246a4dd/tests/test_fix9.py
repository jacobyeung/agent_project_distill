"""S2-only deployment guards and unchanged proof-2 sampling contracts."""
import ast,copy,importlib.util,inspect,json,math,sys,tarfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'work/tree'),str(ROOT/'work/tree/generator/derivgen_v7')]
from rebind import load,sha,write,diff,AS
from build_fix9 import SNAPSHOT,FROZEN_ID,FROZEN_SHA

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

class Fix9(unittest.TestCase):
    def test_switch_guards_all_combinations_and_deployed_copies(self):
        cfg=load(ROOT/'out/config.json');cases=[]
        for s1 in (False,True):
            for s2 in (False,True):
                for top in (0,.5):
                    for recipe in (0,.5):
                        candidate=copy.deepcopy(cfg)
                        candidate['h1'].update(faithful_own_camera_rows=s1,routing_pose_targets=s2)
                        candidate['scheduled_sampling']['max_own_probability']=top
                        candidate['recipe']['scheduled_sampling']['max_own_probability']=recipe
                        cases.append((candidate,not s1 and s2 and top==recipe==0))
        for location,key in (('h1','routing_pose_targets'),('h1','faithful_own_camera_rows'),
                             ('scheduled_sampling','max_own_probability')):
            candidate=copy.deepcopy(cfg);candidate[location].pop(key);cases.append((candidate,False))
        for key,value in (('routing_pose_targets',1),('routing_pose_targets','true'),('faithful_own_camera_rows',0)):
            candidate=copy.deepcopy(cfg);candidate['h1'][key]=value;cases.append((candidate,False))
        for location in ('top','recipe'):
            for value in (-1,float('nan'),float('inf'),False,'0',None):
                candidate=copy.deepcopy(cfg)
                container=candidate if location=='top' else candidate['recipe']
                container['scheduled_sampling']['max_own_probability']=value;cases.append((candidate,False))
            candidate=copy.deepcopy(cfg)
            container=candidate if location=='top' else candidate['recipe']
            container['scheduled_sampling'].pop('max_own_probability');cases.append((candidate,False))
        paths=['tools/derive_deployment.py','tools/seal_proof.py','out/operator/d.py','out/operator/p.py','out/proof/p.py']
        guards=[]
        for i,name in enumerate(paths):
            loaded=module('fix9_guard_'+str(i),ROOT/name)
            guards.append(inspect.getsource(loaded.validate_switches))
            tree=ast.parse((ROOT/name).read_text())
            self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='validate_switches' for n in ast.walk(tree)))
            for case,(candidate,accepted) in enumerate(cases):
                with self.subTest(path=name,case=case):
                    if accepted:loaded.validate_switches(candidate)
                    else:
                        with self.assertRaisesRegex(ValueError,'Launch requires'):loaded.validate_switches(candidate)
        self.assertTrue(all(g==guards[0] for g in guards))
        op=load(ROOT/'out/OPERATOR.json')
        with tarfile.open(ROOT/'out'/op['archive']) as archive:
            for deployed,source in [('d.py','tools/derive_deployment.py'),('p.py','tools/seal_proof.py')]:
                self.assertEqual(archive.extractfile(deployed).read(),(ROOT/source).read_bytes())
        write(ROOT/'out/proof/SWITCH_GUARDS.json',dict(status='PASS',config_identity=load(ROOT/'out/BINDING.json')['config_identity'],
            copies=paths,cases_per_copy=len(cases),total_checks=len(cases)*len(paths),
            accepted_per_copy=1,all_other_cases_refused=True,archived_copies_exact=True))

    def test_only_authorized_config_and_identity_paths_change(self):
        old=load(SNAPSHOT/'out/config.json');new=load(ROOT/'out/config.json')
        changes=diff(old,new)
        permitted={'h1.routing_pose_targets','output','preparation_output','code.path','admission.path','admission.sha256',
                   'streams.vqa.path','streams.vqa.sha256','s1_route_policy.table.path','s1_routing.selection.path'}
        permitted.add('s1_routing.catalog.'+load(ROOT/'out/BINDING.json')['selection_sha256'])
        self.assertEqual({x['field'] for x in changes},permitted)
        self.assertEqual(changes,load(ROOT/'out/CONFIG_DIFF9.json'))
        for field in ('type_mix','scheduled_sampling','recipe'):
            self.assertEqual(old[field],new[field])
        self.assertFalse(new['h1']['faithful_own_camera_rows']);self.assertTrue(new['h1']['routing_pose_targets'])
        self.assertEqual(new['scheduled_sampling']['max_own_probability'],0)
        self.assertEqual(new['recipe']['scheduled_sampling']['max_own_probability'],0)

    def test_trainer_and_bound_inputs_remain_frozen(self):
        old=load(SNAPSHOT/'out/BINDING.json');new=load(ROOT/'out/BINDING.json')
        for key in ('tree_sha256','code_archive_sha256','code_sha256','mix','unit_binding','selection_sha256',
                    'receipt_sha256','database_sha256','orchard_store','database','source_receipt'):
            self.assertEqual(old[key],new[key],key)
        for name in ('proof/selection/r.json','proof/selection/q.json','r1p_code.tar',
                     'units/u.gz','units/packed.jsonl','units/m.json','units/i.json','units/u.json','FRAME_AUTHORITY.local.json'):
            self.assertEqual(sha(SNAPSHOT/'out'/name),sha(ROOT/'out'/name),name)
        from student_pilot import source_seal
        self.assertEqual(source_seal.inventory(ROOT/'work/tree'),source_seal.inventory(SNAPSHOT/'work/tree'))
        inherited=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/tree/student_pilot')
        for name in ('h1.py','carrier_c1.py'):
            self.assertEqual(sha(inherited/name),sha(ROOT/'work/tree/student_pilot'/name))
        def rows_get(path):
            tree=ast.parse(path.read_text())
            rows=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Rows')
            return ast.dump(next(n for n in rows.body if isinstance(n,ast.FunctionDef) and n.name=='get'))
        self.assertEqual(rows_get(inherited/'carrier_c1_run.py'),rows_get(ROOT/'work/tree/student_pilot/carrier_c1_run.py'))
        self.assertEqual(sha(ROOT/'out/p_6f8ed106.tar'),FROZEN_SHA)
        self.assertNotIn(load(ROOT/'out/OPERATOR.json')['archive'],('p_c5f3847d.tar','p_6f8ed106.tar'))
        self.assertNotEqual(old['run_key'],new['run_key']);self.assertNotEqual(FROZEN_ID,new['config_identity'])

    def test_first_batch_s2_all_four_ranks(self):
        evidence=load(ROOT/'out/proof/FIRST_BATCH.json')
        self.assertEqual(evidence['config_identity'],load(ROOT/'out/BINDING.json')['config_identity'])
        self.assertEqual([r['rank'] for r in evidence['ranks']],[0,1,2,3])
        for rank in evidence['ranks']:
            self.assertEqual(rank['rows'],72);self.assertEqual(rank['real_vqa'],32)
            observed=set()
            for row in rank['records']:
                self.assertTrue(row['finite']);self.assertTrue(all(math.isfinite(v) for v in row['components'].values()))
                if row['stream']=='routing':
                    observed.add(row['s2']['family'])
                    if row['s2']['s2_supervised']:
                        self.assertEqual(row['s2']['supervised_frames'],32)
                        self.assertTrue(row['s2']['target_matches_own_frames']);self.assertGreater(row['components']['pose'],0)
                    else:self.assertEqual(row['components']['pose'],0)
                elif row['stream']!='pose':self.assertEqual(row['components']['pose'],0)
            self.assertEqual(observed,{'camera_displacement','camera_movement_direction','camera_rotation','absolute_distance_object','units/ft'})

    def test_off_identity_uses_d0_switches_and_exact_rank_states(self):
        cfg=load(ROOT/'work/reference/configs/d0.json')
        self.assertFalse(cfg.get('h1',{}).get('faithful_own_camera_rows',False))
        self.assertFalse(cfg.get('h1',{}).get('routing_pose_targets',False))
        self.assertEqual(cfg['scheduled_sampling']['max_own_probability'],0)
        self.assertEqual(cfg['recipe']['scheduled_sampling']['max_own_probability'],0)
        left=load(ROOT/'out/proof/off_sealed.json');right=load(ROOT/'out/proof/off_candidate.json')
        self.assertEqual(left['config_identity'],right['config_identity']);self.assertEqual(left['ranks'],right['ranks'])
        frozen=load(SNAPSHOT/'out/proof/off_sealed.json')
        self.assertEqual(left['ranks'],frozen['ranks']);self.assertEqual(left['config_identity'],frozen['config_identity'])

    def test_h1_missing_labels_are_masked_and_bad_camera_labels_refuse(self):
        import torch
        from student_pilot.h1 import pose_targets
        cfg=load(ROOT/'out/config.json');batch=dict(aux_camera_positions=torch.arange(32)[None])
        row={'routing':{'question_type':'camera_displacement'}}
        targets,counts=pose_targets(row,batch,cfg['h1'])
        self.assertEqual(counts['reason'],'missing_gt_fields');self.assertFalse(targets['aux_camera_mask'].any())
        row['routing'].update(gt_pose9=[[0,0,0,0,0,0,1,1,1]]*31,gt_up=[0,-1,0])
        with self.assertRaisesRegex(ValueError,'finite gt_pose9'):pose_targets(row,batch,cfg['h1'])

if __name__=='__main__':unittest.main(verbosity=2)
