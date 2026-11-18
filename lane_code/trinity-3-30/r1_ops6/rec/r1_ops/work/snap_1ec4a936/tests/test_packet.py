import copy,hashlib,importlib.util,json,os,stat,subprocess,sys,tempfile,unittest
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'work/tree'),str(ROOT/'work/tree/generator/derivgen_v7'),str(ROOT/'tools')]
from student_pilot import type_mix as m,carrier_c1_run as run,carrier_c1_data as data
from student_pilot.checkpoint_space import plan
from rebind import load,sha,write

def temp():return Path(tempfile.mkdtemp(prefix='test_',dir=ROOT/'work'))

class Mix(unittest.TestCase):
    def test_real_capped_table_and_actual_draws(self):
        report=load(ROOT/'out/proof/loader_audit.json');table=report['tables']['vqa']
        self.assertEqual(sum(v['final_cents'] for v in table.values()),12800)
        for n,v in table.items():
            self.assertLessEqual(v['final_cents']*1000,4*v['eligible']*100)
            if v['final_cents']:self.assertEqual(report['by_family']['vqa/'+n]['draws'],v['final_cents']*10)
        self.assertEqual(table['room']['final_cents'],0)
        self.assertEqual(table['room']['cut_cents'],200)
        self.assertEqual(table['direction']['refill_cents'],200)
        self.assertEqual(table['camera_absolute_distance']['eligible'],0)
        self.assertEqual(report['stream_draws'],{'vqa':128000})
        self.assertLessEqual(report['maximum_observed_repeats'],4)
        self.assertEqual(set(report['by_question_type']),{'vqa/'+t for t in load(ROOT/'out/ADMISSION_BY_TYPE.json')['types_covered']})
        for name,rows in report['traces']['vqa'].items():
            self.assertEqual(len(rows),5)
            for r in rows:self.assertEqual(hashlib.sha256(r['target'].encode()).hexdigest(),r['target_sha256'])

    def test_zero_population_refill_and_insufficient_capacity(self):
        policy=dict(cells={'a':{'cents':150},'b':{'cents':250}},refill=['b'])
        eff,t=m.allocate(policy,dict(a=0,b=1000),1000)
        self.assertEqual(eff,{'b':{'cents':400}});self.assertEqual(t['a']['cut_cents'],150)
        with self.assertRaisesRegex(ValueError,'Insufficient'):m.allocate(policy,dict(a=0,b=999),1000)

    def test_proportional_refill_respects_saturated_cells(self):
        policy=dict(cells={'a':{'cents':100},'b':{'cents':200},'c':{'cents':100}},refill=['a','b'],refill_mode='proportional')
        effective,table=m.allocate(policy,dict(a=300,b=1000,c=0),1000)
        self.assertEqual(effective,{'a':{'cents':120},'b':{'cents':280}})
        self.assertEqual(table['c']['cut_cents'],100)
        self.assertEqual(sum(v['refill_cents'] for v in table.values()),100)

    def test_exact_repeat_limit_and_resume(self):
        spec=dict(schema='type-mix-v2',max_repeats=4,size_selector=None,streams={
            'vqa':dict(cells={'a':{'cents':100},'b':{'cents':300}},refill=['b'])})
        groups={'vqa':{'a':list(range(250)),'b':list(range(250,1000))}}
        value=dict(spec=spec,effective={'vqa':spec['streams']['vqa']['cells']},populations=groups)
        def base():return data.mixed_indices({'vqa':1000},1000,training_mode='final',mix=['vqa'],world=4)
        full=list(m.plans(base(),value,17));resume=list(m.plans(base(),value,17,997))
        self.assertEqual(full[997:],resume)
        draws=Counter(i for p in full for _,ids in p for i in ids)
        self.assertEqual(set(draws.values()),{4})
        bad=copy.deepcopy(value);bad['populations']['vqa']['a'].pop()
        with self.assertRaisesRegex(ValueError,'Repeat cap'):list(m.plans(base(),bad,17))
        bad=copy.deepcopy(value);bad['populations']['vqa']['b'].append(0)
        with self.assertRaisesRegex(ValueError,'overlap'):next(m.plans(base(),bad,17))

    def test_family_metadata_and_room_contract(self):
        self.assertEqual(m.family(dict(question_type='object_counting',count_kind='total'),'vqa'),'totals')
        self.assertEqual(m.family(dict(question_type='object_rel_direction_hard',facing='away'),'vqa'),'facing')
        row=dict(question_type='room_size_estimation',target='12 square metres')
        self.assertEqual(m.family(row,'vqa'),'excluded_room_trace')
        row.update(target='Locate: the wall in frame 1.\nRelate: the floor spans the walls.\nEstimate: 12 square metres.',student_input={'frames':[{'path':'/f','sha256':'a'*64}]})
        self.assertEqual(m.family(row,'vqa'),'room')
        row['target']=row['target'].replace('frame 1','frame 2');self.assertEqual(m.family(row,'vqa'),'excluded_room_trace')
        self.assertEqual(m.family(dict(question_type='object_size_estimation',pool='x'),'vqa',{'field':'pool','equals':'y'}),'excluded_size_selector')

    def test_config_switches_disk_and_identity(self):
        cfg=load(ROOT/'configs/r1p.json');run.validate(cfg)
        self.assertFalse(cfg['h1']['faithful_own_camera_rows']);self.assertFalse(cfg['h1']['routing_pose_targets'])
        self.assertEqual(cfg['h1']['stop_after_step'],200);self.assertEqual(cfg['recipe']['steps'],1000)
        self.assertEqual(cfg['recipe']['milestones'],[100,200]);self.assertEqual(cfg['checkpoint_disk_guard'],plan(cfg['recipe'],200000000000))
        self.assertEqual(cfg['scheduled_sampling'],load(ROOT/'work/reference/configs/d0.json')['scheduled_sampling'])
        self.assertEqual(run.identity(cfg),load(ROOT/'out/BINDING.json')['config_identity'])
        c=copy.deepcopy(cfg);c['type_mix']['size_selector']={'field':'pool','equals':'different'}
        self.assertNotEqual(run.identity(c),run.identity(cfg))

class Evidence(unittest.TestCase):
    def test_actual_question_types_follow_pose_mix_order(self):
        import sqlite3
        from student_pilot.loader_audit import question_types,examples
        root=temp();sources=[]
        for child in range(2):
            db=root/(str(child)+'.db');conn=sqlite3.connect(db)
            conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
            for i in range(3):
                row=dict(qid=str(i),question_type='type_'+str(child)+'_'+str(i),target='trace')
                conn.execute('INSERT INTO rows VALUES(?,?,?)',(i,json.dumps(row),json.dumps('trace')))
            conn.commit();conn.close()
            sources.append(dict(database=dict(path=str(db),sha256=sha(db)),count=3))
        order=root/'order.json';write(order,[[1,2],[0,1],[1,0]])
        mixed=dict(kind='mix',count=3,sources=sources,order=dict(path=str(order),sha256=sha(order)))
        self.assertEqual(question_types('pose',mixed),{0:'type_1_2',1:'type_0_1',2:'type_1_0'})
        self.assertEqual([r['question_type'] for r in examples('pose',mixed)],['type_1_2','type_0_1','type_1_0'])

    def test_loader_audit_enforces_cap_on_unchanged_streams(self):
        import sqlite3
        from student_pilot.loader_audit import audit
        root=temp();db=root/'pose.db';conn=sqlite3.connect(db)
        conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
        for i in range(2):
            conn.execute('INSERT INTO rows VALUES(?,?,?)',(i,json.dumps(dict(qid=str(i),target='trace')),json.dumps('trace')))
        conn.commit();conn.close()
        cfg=dict(type_mix=dict(schema='type-mix-v2',max_repeats=4,size_selector=None,streams={}),
                 recipe=dict(mix=['pose'],world_size=4,steps=5,seed=17),training_mode='final',preparation_output=str(root/'p'))
        (root/'p').mkdir(mode=0o700)
        receipt=dict(config_sha256='test',streams=dict(pose=dict(database=dict(path=str(db),sha256=sha(db)),count=2)))
        receipt=m.prepare(receipt,cfg)
        with self.assertRaisesRegex(ValueError,'Family draws exceed'):
            audit(cfg,receipt)

    def test_deployment_refuses_unbound_source_and_forged_packet(self):
        from derive_deployment import derive
        source=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx')
        with self.assertRaisesRegex(ValueError,'Source manifest binding'):
            derive(source,temp()/'new',ROOT/'out/operator','0'*64,fixture=True)
        with self.assertRaisesRegex(ValueError,'Source member absent'):
            derive(source,temp()/'new',ROOT/'out/operator',sha(source/'SHA256SUMS.txt'))

    def test_submitter_retains_separate_authorization_and_named_gates(self):
        text=(ROOT/'out/operator/s.sh').read_text()
        self.assertIn('production_go_granted',text)
        self.assertIn('required_families',text)
        self.assertIn('loader_audit',text)
        self.assertNotIn("proof.get('status') in",text)

    def test_admission_implementation_unchanged(self):
        parent=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/tree')
        for name in ('ground_rows.py','s1_pool.py','s1_admission.py','s1_routing.py','s1_exclusions.py','row_removals.py'):
            self.assertEqual(sha(ROOT/'work/tree/student_pilot'/name),sha(parent/'student_pilot'/name))
        r=load(ROOT/'out/ROUTING_DIAGNOSIS.json')
        self.assertEqual(r['a0_units']['counts']['supplied_rows'],2000)
        self.assertEqual(r['a0_units']['counts']['repacked_admitted'],216)
        self.assertEqual(r['a0_units']['counts']['ValueError: Absolute label mismatch'],1784)
        self.assertEqual(r['a0_recovery']['counts']['ValueError: Grounding membership flags differ'],1532)
        census=load(ROOT/'out/ADMISSION_BY_TYPE.json')['routing']
        self.assertEqual(census['a0_units']['admitted'],216)
        self.assertEqual(census['a0_recovery']['eligible'],0)
        self.assertEqual(census['a0_units']['slice_form_validation']['admitted'],0)

    def test_selection_and_room_source_exclusion(self):
        from selection_check import project,enc
        parent=load(ROOT/'work/records/pool_selection_eac5f9f0.json');new,removed=project(parent)
        self.assertEqual(new,load(ROOT/'out/proof/selection/r.json'));self.assertEqual(sum(removed.values()),586)
        for name in set(parent['sources'])-set(removed):self.assertEqual(enc(parent['sources'][name]),enc(new['sources'][name]))
        for value in new['sources'].values():
            if value['status']=='ELIGIBLE':self.assertFalse(set(value['per_type'])&{'room_size_estimation','absolute_size_room'})
        a=load(ROOT/'out/ADMISSION_BY_TYPE.json')
        self.assertEqual(a['vqa_rows'],195471);self.assertEqual(len(a['vqa_by_type']),16)
        self.assertTrue(a['all_types_covered'])
        self.assertEqual(sum(v['admitted'] for v in a['direct_room'].values()),0)

class Proof(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('packet_proof',ROOT/'out/proof/p.py');cls.p=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.p)

    def test_private_empty_root_and_refusals(self):
        root=temp();work=root/'parent'/'new';self.p.create_work(work,'abcd0123')
        for d,_,_ in os.walk(root):self.assertEqual(stat.S_IMODE(Path(d).stat().st_mode),0o700)
        with self.assertRaises(FileExistsError):self.p.create_work(work,'abcd0123')
        parent=root/'public';parent.mkdir(mode=0o755);parent.chmod(0o755)
        with self.assertRaises(ValueError):self.p.create_work(parent/'new','abcd0123')
        link=root/'link';link.symlink_to(work)
        with self.assertRaises(ValueError):self.p.create_work(link/'new','abcd0123')

    def test_runtime_resolution_and_fail_closed(self):
        inventory=self.p.host_preflight()
        for item in inventory.values():self.assertEqual(sha(item['path']),item['sha256'])
        root=temp()
        failed=self.p.execute([sys.executable,'-c','raise SystemExit(9)'],'',root/'bad.log',lambda:{})
        self.assertEqual(failed['status'],'FAIL');self.assertEqual(failed['rc'],9)
        failed=self.p.execute([sys.executable,'-c','pass'],'',root/'seal.log',lambda:(_ for _ in ()).throw(ValueError('seal differs')))
        self.assertEqual(failed['status'],'FAIL')
        args=['--bind',str(root/'work'),'/tmp','--bind',str(root/'kit/o'),str(root/'kit/o')]
        self.assertEqual(self.p.temporary_paths(args,root/'kit',root)['status'],'PASS')
        with self.assertRaisesRegex(ValueError,'Ambient writable'):
            self.p.temporary_paths(['--bind','/var/tmp','/tmp'],root/'kit',root)

    def test_native_proof_boundary_and_named_checks(self):
        parent=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1')
        script=self.p.program((parent/'payload/jb.sh').read_text(),(parent/'build/fx/job.sh').read_text())
        self.assertIn('"$ROOT/b/r.sh" p 0',script);self.assertIn('-m student_pilot.loader_audit',script)
        self.assertNotIn('newest || true',script)
        self.assertNotIn('"$ROOT/b/r8.py"',script)
        root=temp();(root/'e.sh').write_text(script)
        subprocess.run(['bash','-n',str(root/'e.sh')],check=True)
        text=(ROOT/'out/proof/p.py').read_text()
        for name in ('disk_plan','routing_selection','empty_root','temporary_paths','runtime_binaries','private_directories','loader_audit','required_families'):self.assertIn(name,text)
        self.assertNotIn('/usr/bin/bwrap',text)

    def test_final_wrapper_and_export_destinations_are_bound(self):
        cfg=load(ROOT/'out/config.json');binding=load(ROOT/'out/BINDING.json')
        exports=self.p.export_plan(ROOT/'out/operator',cfg,binding['run_key'])
        self.assertEqual(exports['planned_weight_exports'],3)
        self.assertEqual(exports['reserved_part_destinations'],20)
        wrapper=(ROOT/'out/operator/jb.sh').read_text()
        for old in ('i_1be16f28','x_07ca49df','x_3fdda0fb','a_17c4ffa4'):self.assertNotIn(old,wrapper)
        self.assertIn('i_'+binding['store_key']+'/v.py',wrapper)
        self.assertIn('i_'+binding['store_key']+'/b0.json',wrapper)
        script=self.p.program(wrapper,(Path(load(ROOT/'out/proof/DERIVATION.json')['fixture_paths'][0])/'job.sh').read_text())
        self.assertIn('student_pilot.loader_audit',script)
        root=temp();(root/'p.sh').write_text(script)
        subprocess.run(['bash','-n',str(root/'p.sh')],check=True)
        bad=copy.deepcopy(cfg);bad['recipe']['milestones']=[100]
        with self.assertRaisesRegex(ValueError,'Export disk count'):self.p.export_plan(ROOT/'out/operator',bad,binding['run_key'])

    def test_staging_preserves_private_directory_modes(self):
        script=(Path(load(ROOT/'out/proof/DERIVATION.json')['fixture_paths'][0])/'b/c.sh').read_text()
        self.assertNotIn('chmod -R a-w',script)
        helper=script[script.index('tk_readonly_files() {'):script.index('tk_stage_model() {')]
        root=temp();tree=root/'tree';tree.mkdir(mode=0o700)
        nested=tree/'nested';nested.mkdir(mode=0o700);(nested/'file').write_text('pinned bytes')
        subprocess.run(['bash','-c',helper+'\ntk_readonly_files "$1"','test',str(tree)],check=True)
        self.assertEqual(stat.S_IMODE(nested.stat().st_mode),0o700)
        self.assertEqual((nested/'file').stat().st_mode&0o222,0)

if __name__=='__main__':unittest.main(verbosity=2)
