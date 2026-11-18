import copy,hashlib,importlib.util,json,os,stat,subprocess,sys,tempfile,unittest
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'work/tree'),str(ROOT/'work/tree/generator/derivgen_v7'),str(ROOT/'tools')]
from student_pilot import type_mix as m,carrier_c1_run as run,carrier_c1_data as data
from student_pilot.checkpoint_space import plan
from rebind import load,sha,write

def temp():return Path(tempfile.mkdtemp(prefix='test_',dir=ROOT/'work'))

def parent_selection():
    from selection_check import project
    from student_pilot import s1_pool
    parent,_=project(load(ROOT/'work/records/pool_selection_eac5f9f0.json'))
    parent['implementation']=s1_pool.implementation()
    return parent

def staged_distance_rows():
    """Run the frozen converter on synthetic canonical trace/RGB fixtures."""
    sealed=Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_f719b05f/work/tree/student_pilot/carrier_c1_routing.py')
    if sha(sealed)!=sha(ROOT/'work/tree/student_pilot/carrier_c1_routing.py'):
        raise ValueError('The frozen c1_row converter changed')
    spec=importlib.util.spec_from_file_location('student_pilot._fix7_sealed_routing',sealed)
    routing=importlib.util.module_from_spec(spec);spec.loader.exec_module(routing)
    events=[dict(kind='plan',text='Measure the distance between the objects.')]
    target,spans=routing.render(events,'2')
    rgb=dict(frames=[dict(path='fixture/'+str(i)+'.png',sha256='0'*64,source_index=i) for i in range(32)],
             fps=1,total_num_frames=32)
    result=[]
    for prefix in ('scannetpp/','scannetppv2/','scannet/','arkitscenes/'):
        row=dict(schema='derivgen-row-v2',form='spec-v3.8-calculator-v2',infrastructure_only=False,
            qid='fixture_'+prefix,question_type='absolute_distance_object',question='How far apart?',
            events=events,answer='2',gt_answer='2',target=target,tool_output_spans=spans,
            provenance=dict(canonical=prefix+'scene',frame_indices=list(range(32)),source_row_sha256='1'*64))
        result.append(routing.c1_row(row,rgb))
    return result

class Mix(unittest.TestCase):
    def test_real_capped_table_and_actual_draws(self):
        report=load(ROOT/'out/proof/loader_audit.json');table=report['tables']['vqa']
        self.assertEqual(sum(v['final_cents'] for v in table.values()),12800)
        for n,v in table.items():
            self.assertLessEqual(v['final_cents']*1000,4*v['eligible']*100)
            if v['final_cents']:self.assertEqual(report['by_family']['vqa/'+n]['draws'],v['final_cents']*10)
        self.assertEqual(table['room']['final_cents'],min(table['room']['proposed_cents'],table['room']['cap_cents']))
        self.assertEqual(table['room']['cut_cents'],table['room']['proposed_cents']-table['room']['final_cents'])
        self.assertEqual(table['size']['final_cents'],0)
        self.assertEqual(table['size']['eligible'],9778)
        self.assertEqual(table['direction']['final_cents'],3289-table['room']['final_cents'])
        self.assertNotIn('vqa/size',report['by_family'])
        self.assertEqual(table['direction']['refill_cents'],table['room']['cut_cents'])
        self.assertEqual(table['camera_absolute_distance']['eligible'],0)
        self.assertEqual(report['stream_draws'],{'vqa':128000})
        self.assertLessEqual(report['maximum_observed_repeats'],4)
        self.assertEqual(set(report['by_question_type']),{'vqa/'+t for t in load(ROOT/'out/ADMISSION_BY_TYPE.json')['types_covered'] if t not in ('object_size_estimation','absolute_size_object','relative_size_object') and (t not in ('room_size_estimation','absolute_size_room') or table['room']['final_cents'])})
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
        row.update(pool='r1_room_traced',target='<think>\nSeen: the wall in frame 1.\nThe walls are far apart.\n</think>\n12',student_input={'frames':[{'path':'/f','sha256':'a'*64}]})
        self.assertEqual(m.family(row,'vqa'),'room')
        row['target']=row['target'].replace('frame 1','frame 2');self.assertEqual(m.family(row,'vqa'),'excluded_room_trace')
        self.assertEqual(m.family(dict(question_type='object_size_estimation',pool='x'),'vqa',{'field':'pool','equals':'y'}),'excluded_size_selector')

    def test_all_room_rows_and_mutants(self):
        import sqlite3
        binding=load(ROOT/'out/BINDING.json')
        conn=sqlite3.connect('file:'+binding['database']['path']+'?mode=ro&immutable=1',uri=True)
        counts=Counter()
        try:
            for encoded, in conn.execute('SELECT row FROM rows ORDER BY i'):
                row=json.loads(encoded)
                if row.get('question_type') not in ('room_size_estimation','absolute_size_room'):continue
                traced=row.get('pool')=='r1_room_traced'
                counts['traced' if traced else 'one_line']+=1
                self.assertEqual(m.room_trace(row),traced,row['qid'])
                if not traced:continue
                for target in (row['target'].replace('frame ', 'frame 999'),
                               '\n'.join(line for line in row['target'].splitlines() if not ('apart' in line)),
                               row['target'].replace('</think>','Area: 17.51 square meters.\n</think>'),
                               row['target'].replace('</think>','Area: seventeen square meters.\n</think>')):
                    self.assertFalse(m.room_trace({**row,'target':target}),row['qid'])
                bad=copy.deepcopy(row);bad['student_input']['frames']=[{'path':'x','sha256':'bad'}]*len(bad['student_input']['frames'])
                self.assertFalse(m.room_trace(bad))
                self.assertFalse(m.room_trace({**row,'pool':'other'}))
        finally:conn.close()
        self.assertEqual(counts['traced'],431)
        for source in (Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/rows_slices/slices_final/a0_room.jsonl'),
                       Path('/scratch/jjyeung/orch_n30/rows_a2/out/a2_room_ft2_v1/slice_a2_room_ft2.jsonl')):
            with source.open() as stream:
                for line in stream:
                    row=json.loads(line);counts['one_line']+=1
                    self.assertFalse(m.room_trace(row),row['qid'])
        self.assertEqual(counts['one_line'],571)
        write(ROOT/'out/proof/ROOM_GRAMMAR.json',dict(status='PASS',counts=dict(counts),mutants_per_traced_row=6))

    def test_audit_draw_breakdown(self):
        from student_pilot.loader_audit import row_metadata,draw_breakdown
        rows={0:row_metadata(dict(question_type='object_rel_direction_hard',facing='away',answer='B',student_input={'options':['A. front','B. back-left']}),'vqa','facing'),
              1:row_metadata(dict(question_type='object_rel_direction_easy',facing='toward',answer='A'),'vqa','facing')}
        staged=staged_distance_rows()
        self.assertTrue(all('provenance' not in r and 'canonical' in r['routing'] for r in staged))
        routing={i:row_metadata(row,'routing','absolute_distance') for i,row in enumerate(staged)}
        for i,u in enumerate(('cm','ft','in'),4):routing[i]=row_metadata(dict(ground_record={'unit':u}),'routing','units')
        draws=Counter({('vqa',0):3,('vqa',1):1,**{('routing',i):i+1 for i in range(7)}})
        report=draw_breakdown({'vqa':rows,'routing':routing},draws,routing_available=True)
        self.assertEqual(report['facing']['away']['share_of_facing'],.75)
        self.assertEqual(report['away_hard']['back_share'],1);self.assertEqual(report['away_hard']['exact_back_share'],0)
        self.assertEqual(report['units']['draws'],{'cm':5,'ft':6,'in':7})
        self.assertEqual(report['routing_absolute_distance']['drawn'],{'scannetpp/':1,'scannetppv2/':2,'scannet/':3,'arkitscenes/':4,'unknown':0})
        local=load(ROOT/'out/proof/loader_audit.json')['draw_breakdown']
        self.assertEqual(sum(v['draws'] for v in local['facing'].values()),load(ROOT/'out/proof/loader_audit.json')['by_family']['vqa/facing']['draws'])
        self.assertEqual(local['routing_absolute_distance']['status'],'NOT_RUN')

    def test_routing_canonical_precedence_and_exact_prefixes(self):
        from student_pilot.loader_audit import row_metadata
        prefix=lambda row:row_metadata(row,'routing','absolute_distance')['prefix']
        for row in staged_distance_rows():
            expected=row['routing']['canonical'].split('/')[0]+'/'
            row['routing']['provenance']={'canonical':'scannet/wrong'}
            row['provenance']={'canonical':'arkitscenes/wrong'}
            self.assertEqual(prefix(row),expected)
        self.assertEqual(prefix({'routing':{'provenance':{'canonical':'scannetppv2/scene'}}}),'scannetppv2/')
        self.assertEqual(prefix({'routing':{},'provenance':{'canonical':'scannet/scene'}}),'scannet/')
        for canonical in ('scannetppv20/scene','scannetpp','arkit/scene','scannet_extra/scene','unknown/scene',''):
            self.assertEqual(prefix({'routing':{'canonical':canonical}}),'unknown')

    def test_routing_unknown_threshold_fails_loader_check(self):
        import sqlite3,types,contextlib,io
        from unittest.mock import patch
        from student_pilot import loader_audit,checkpoint_space,vehicle_p
        fixtures=staged_distance_rows();cases=[]
        for total,unknown in ((100,0),(100,1),(100,2),(99,1),(4,4)):
            with self.subTest(total=total,unknown=unknown):
                root=temp();db=root/'routing.db';conn=sqlite3.connect(db)
                conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
                for i in range(total):
                    row=copy.deepcopy(fixtures[i%4]);row['qid']='fixture_'+str(i)
                    if i<unknown:row['routing']['canonical']='unrecognized/scene'
                    conn.execute('INSERT INTO rows VALUES(?,?,?)',(i,json.dumps(row),json.dumps(row['target'])))
                conn.commit();conn.close()
                cfg=dict(type_mix=dict(schema='type-mix-v2',max_repeats=4,size_selector=None,
                    streams={'routing':dict(cells={'absolute_distance':{'cents':400}},refill=['absolute_distance'])}),
                    recipe=dict(mix=['routing'],world_size=4,steps=1,seed=17),training_mode='final',preparation_output=str(root/'p'))
                (root/'p').mkdir(mode=0o700)
                receipt=m.prepare(dict(config_sha256='fixture',streams={'routing':dict(database=dict(path=str(db),sha256=sha(db)),count=total)}),cfg)
                write(root/'prepared.json',receipt);cfg['preparation']=dict(path=str(root/'prepared.json'),sha256=sha(root/'prepared.json'))
                write(root/'selection.json',dict(sources={}))
                cfg['s1_routing']=dict(selection=dict(path=str(root/'selection.json'),sha256=sha(root/'selection.json')))
                cfg['checkpoint_disk_guard']=dict(reserve_bytes=0)
                write(root/'config.json',cfg);write(root/'k/launch.json',dict(config={'file':'config.json'},in_job_admission={'directory':str(root/'inputs')}))
                expected='FAIL' if unknown*100>total else 'PASS'
                module=types.ModuleType('d');module.effective=lambda *_:cfg
                printed=io.StringIO()
                with contextlib.redirect_stdout(printed),patch.dict(sys.modules,{'d':module}),patch.object(run,'identity',return_value='fixture'),patch.object(checkpoint_space,'plan',return_value=cfg['checkpoint_disk_guard']),patch.object(vehicle_p,'required_families',return_value={'status':'PASS','absent_on_P':[]}):
                    before=sys.path[:]
                    try:
                        if expected=='FAIL':
                            with self.assertRaisesRegex(ValueError,'Required packet proof checks failed'):loader_audit.main(root)
                        else:loader_audit.main(root)
                    finally:sys.path[:]=before
                records=[json.loads(line) for line in printed.getvalue().splitlines()]
                self.assertEqual(records[0]['census_code_map_sha256'],sha(ROOT/'out/CENSUS_CODES.local.json'))
                def assert_opaque_keys(value):
                    if isinstance(value,dict):
                        for key,item in value.items():
                            for dataset in ('scannetpp','scannetppv2','scannet','arkitscenes'):self.assertNotIn(dataset,key)
                            assert_opaque_keys(item)
                    elif isinstance(value,list):
                        for item in value:assert_opaque_keys(item)
                assert_opaque_keys(records)
                report=load(root/'inputs/a.json');check=report['checks']['loader_audit']
                self.assertEqual(report['status'],expected);self.assertEqual(check['status'],expected)
                self.assertEqual(check['unknown_rows'],unknown);self.assertEqual(check['total_rows'],total)
                cases.append(dict(total_rows=total,unknown_rows=unknown,status=expected))
        write(ROOT/'out/proof/ROUTING_PREFIX.json',dict(status='PASS',scope='Frozen c1_row fixtures and real SQLite loader audit; production routing unavailable',config_identity=load(ROOT/'out/BINDING.json')['config_identity'],loader_sha256=sha(ROOT/'work/tree/student_pilot/loader_audit.py'),cases=cases,converter_sha256=sha(ROOT/'work/tree/student_pilot/carrier_c1_routing.py')))

    def test_config_switches_disk_and_identity(self):
        cfg=load(ROOT/'configs/r1p.json');run.validate(cfg)
        self.assertFalse(cfg['h1']['faithful_own_camera_rows'])
        expected=load(Path(load(ROOT/'out/FIX10_VARIANT.json')['snapshot'])/'out/config.json')['h1']['routing_pose_targets']
        self.assertIs(cfg['h1']['routing_pose_targets'],expected)
        self.assertEqual(cfg['h1']['stop_after_step'],600);self.assertEqual(cfg['recipe']['steps'],1000)
        self.assertEqual(cfg['recipe']['milestones'],[400,600]);self.assertEqual(cfg['checkpoint_disk_guard'],plan(cfg['recipe'],200000000000))
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
        from student_pilot import s1_pool
        self.assertEqual(load(ROOT/'out/proof/selection/r.json')['implementation'],s1_pool.implementation())
        new['implementation']=load(ROOT/'out/proof/selection/r.json')['implementation']
        current=load(ROOT/'out/proof/selection/r.json')
        self.assertEqual({k:v for k,v in current['sources'].items() if k!='U_Faithful'},new['sources'])
        self.assertEqual(current['selected_rows'],new['selected_rows']+current['sources']['U_Faithful']['retained'])
        self.assertEqual(sum(removed.values()),586)
        for name in set(parent['sources'])-set(removed):self.assertEqual(enc(parent['sources'][name]),enc(new['sources'][name]))
        for value in new['sources'].values():
            if value['status']=='ELIGIBLE':self.assertFalse(set(value['per_type'])&{'room_size_estimation','absolute_size_room'})
        a=load(ROOT/'out/ADMISSION_BY_TYPE.json')
        self.assertEqual(a['vqa_rows'],204413);self.assertEqual(len(a['vqa_by_type']),17)
        self.assertEqual(a['traced_room']['rows'],431);self.assertEqual(a['traced_room']['sealed_row_checks_pass'],425)
        self.assertEqual(a['traced_room']['eligible'],load(ROOT/'out/proof/loader_audit.json')['tables']['vqa']['room']['eligible'])
        self.assertEqual(a['reworded_away']['rows'],8511)
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
        self.assertIn('"$ROOT/b/r.sh" p 0',script);self.assertIn('from student_pilot.loader_audit import main',script);self.assertNotIn('-m student_pilot',script)
        self.assertNotIn('newest || true',script)
        self.assertNotIn('"$ROOT/b/r8.py"',script)
        root=temp();(root/'e.sh').write_text(script)
        subprocess.run(['bash','-n',str(root/'e.sh')],check=True)
        text=(ROOT/'out/proof/p.py').read_text()
        for name in ('disk_plan','routing_selection','empty_root','temporary_paths','runtime_binaries','directory_modes','loader_audit','required_families'):self.assertIn(name,text)
        self.assertNotIn('/usr/bin/bwrap',text)

    def test_main_builds_receipt_with_all_evaluated_checks(self):
        self.proof_receipt()

    def test_post_admission_receipt_failures_refuse(self):
        for failure in ('missing_audit','pin','identity','failed_check','missing_required',
                        'execution','verification','resume','directory'):
            with self.subTest(failure=failure):
                self.proof_receipt(failure)

    def proof_receipt(self, failure=None):
        from unittest.mock import patch
        import types,contextlib,signal,io
        p=self.p;root=temp();kh=root/'k0';bun=root/'b0';scratch=root/'tmp'
        for d in (kh,kh/'k',kh/'o',bun,scratch):d.mkdir(mode=0o700)
        cfg=load(ROOT/'out/config.json');binding=load(ROOT/'out/BINDING.json');key=binding['run_key']
        cfg['s1_routing']['selection']['sha256']='selection'
        write(kh/'k/c.json',cfg);write(kh/'k/selection_equality.json',{'equal':True})
        (kh/'SHA256SUMS.txt').write_text('fixture manifest')
        launch=dict(status='READY',config={'file':'k/c.json'},run_directory='/tmp/jjyeung/a_'+key+'/runs/'+key,persistent_run_root=str(root/'runs'))
        write(kh/'k/launch.json',launch);write(bun/'ids.json',dict(identity='identity',contract='contract'))
        (bun/'jb.sh').write_text('wrapper');(kh/'job.sh').write_text('job')
        write(bun/'compare.json',dict(manifest_sha256=sha(kh/'SHA256SUMS.txt'),config_key='c'))
        (bun/'e.txt').write_bytes((ROOT/'out/operator/e.txt').read_bytes())
        authority=dict(kh=str(kh),bun=str(bun),job_name='a15_cot_ap1234',identity='identity',contract='contract',
            wrapper_sha256=sha(bun/'jb.sh'),bundle_files={},runtime={},selection_sha256='selection',
            equality_sha256=sha(kh/'k/selection_equality.json'),run_key=key,tag='fixture',persistent_root=str(root/'runs'),partition='advanced')
        mods={'i':types.SimpleNamespace(identity=lambda c:'identity',allocation_gpus=lambda *a:0),
              'd':types.SimpleNamespace(contract=lambda *a:None,digest=lambda c:'contract'),
              'a':types.SimpleNamespace(main=lambda k:None)}
        original_execute=p.execute
        def execute(args,script,log,verify):
            physical=scratch/'p_fixture_12345'/('tmp/jjyeung/a_'+key+'/runs/'+key)
            inputs=physical/'inputs';inputs.mkdir(parents=True,mode=0o700)
            write(inputs/'l.json',dict(status='PASS',fixture=True))
            checks=dict(disk_plan=dict(status='PASS' if plan(cfg['recipe'],cfg['checkpoint_disk_guard']['reserve_bytes'])==cfg['checkpoint_disk_guard'] else 'FAIL'),
                routing_selection=dict(status='PASS' if cfg['s1_routing']['selection']['sha256']==authority['selection_sha256'] else 'FAIL'),
                loader_audit=dict(status='PASS',pin={'sha256':sha(inputs/'l.json')}),
                required_families=dict(status='PASS',absent_on_P=[]))
            if failure=='failed_check':checks['routing_selection']['status']='FAIL'
            if failure=='missing_required':checks.pop('required_families')
            if failure!='missing_audit':
                write(inputs/'a.json',dict(original_config_identity='wrong' if failure=='identity' else 'identity',checks=checks))
            if failure=='pin':write(inputs/'l.json',dict(tampered=True))
            if failure=='directory':inputs.chmod(0o755)
            def verified():
                if failure=='verification':raise ValueError('Prepared data differ')
                return {'prepared_seals':{'fixture':True}}
            return original_execute([sys.executable,'-c','raise SystemExit(9)' if failure=='execution' else 'pass'],script,log,verified)
        cwd=Path.cwd();path=list(sys.path);handlers={sig:signal.getsignal(sig) for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGUSR1)}
        try:
            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.dict(os.environ,dict(SLURM_JOB_ID='12345',SLURM_JOB_NAME=authority['job_name'],SLURM_JOB_PARTITION='advanced',SLURM_GPUS_ON_NODE='0')))
                stack.enter_context(patch.dict(sys.modules,mods))
                stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                stack.enter_context(patch.object(p,'Path',lambda value: scratch if str(value)=='/tmp/jjyeung' else Path(value)))
                stack.enter_context(patch.object(p,'kit_bwrap',return_value=sys.executable))
                stack.enter_context(patch.object(p,'namespace_probe',return_value=''))
                stack.enter_context(patch.object(p,'program',return_value='fixture'))
                stack.enter_context(patch.object(p,'command',side_effect=lambda bw,kh,w,rs:['--bind',str(w/'tmp'),'/tmp','--bind',str(kh/'o'),str(kh/'o')]))
                stack.enter_context(patch.object(p,'execute',side_effect=execute))
                stack.enter_context(patch.object(p,'resume_fixture',return_value={'status':'FAIL' if failure=='resume' else 'PASS','fixture':True}))
                paths=stack.enter_context(patch.object(p,'temporary_paths',wraps=p.temporary_paths))
                rc=p.main(authority)
                if failure:self.assertNotEqual(rc,0)
                else:self.assertEqual(rc,0)
                paths.assert_called_once()
            receipt=load(kh/'o/12345.proof.json')
            if failure:
                self.assertEqual(receipt['status'],'FAIL')
                self.assertNotEqual(receipt['rc'],0)
                return
            required={'resume_pointer','disk_plan','routing_selection','empty_root','temporary_paths','runtime_binaries','directory_modes','loader_audit','required_families'}
            self.assertEqual(set(receipt['checks']),required)
            self.assertEqual({v['status'] for v in receipt['checks'].values()},{'PASS'})
            self.assertEqual(receipt['status'],'PASS');self.assertFalse(receipt['production_authorized'])
            self.assertTrue(receipt['checks']['temporary_paths']['writable_mounts'])
            self.assertTrue(receipt['checks']['runtime_binaries']['binaries'])
            self.assertEqual(receipt['checks']['directory_modes']['bad'],[])
        finally:
            os.chdir(cwd);sys.path[:]=path
            for sig,handler in handlers.items():signal.signal(sig,handler)

    def test_submit_gate_rejects_bad_go_with_optimization(self):
        import shlex
        script=(ROOT/'out/operator/s.sh').read_text()
        line=next(line for line in script.splitlines() if "<<'P'" in line)
        self.assertTrue(line.startswith('env -u PYTHONOPTIMIZE python3 -I -B - '))
        code=script.split("<<'P'\n",1)[1].split('\nP\n',1)[0]
        root=temp();write(root/'go.json',{'production_go_granted':False});write(root/'ids.json',{'identity':'fixture'})
        argv=shlex.split(line.split(' "$KH"',1)[0])+[str(root),str(root)]
        argv[argv.index('python3')]=sys.executable
        for optimize in ('1','2'):
            env=dict(os.environ,PYTHONOPTIMIZE=optimize)
            result=subprocess.run(argv,input=code,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env)
            self.assertNotEqual(result.returncode,0);self.assertIn('AssertionError',result.stdout)

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

class VehicleP(unittest.TestCase):
    def test_absences_and_missing_required_family(self):
        from student_pilot.vehicle_p import required_families,ROUTING
        cfg=load(ROOT/'configs/r1p.json');a=load(ROOT/'out/proof/loader_audit.json')
        a['eligible_by_family']['vqa']['room']=431
        a['tables']['vqa']['room']['final_cents']=cfg['type_mix']['streams']['vqa']['cells']['room']['cents']
        a['eligible_by_family']['routing']={**{n:20000 for n in ROUTING},'units':a['unit_counts']['sampling_eligible']}
        a['tables']['routing']={n:dict(final_cents=c['cents']) for n,c in cfg['type_mix']['streams']['routing']['cells'].items()}
        gate=required_families(cfg,a)
        self.assertEqual(gate['status'],'PASS')
        self.assertEqual({x['family'] for x in gate['absent_on_P']},{'recovery','size','units/cm','units/in'} | ({'room'} if not cfg['type_mix']['streams']['vqa']['cells']['room']['cents'] else set()))
        self.assertTrue(all(x['reason'] for x in gate['absent_on_P']))
        self.assertIn('units',gate['required']['routing'])
        a['eligible_by_family']['routing']['absolute_distance']=0
        gate=required_families(cfg,a);self.assertEqual(gate['status'],'FAIL')
        self.assertIn('routing/absolute_distance',gate['missing'])
        a['eligible_by_family']['vqa']['direction']=0
        self.assertIn('vqa/direction',required_families(cfg,a)['missing'])

    def test_fallback_filter_and_deployed_diff_baseline(self):
        import sqlite3
        from rebind import diff,H
        cfg=load(ROOT/'configs/r1p.json')
        self.assertEqual(load(ROOT/'configs/diff_against_h1_1.json'),diff(load(H/'build/fx/k/d12ae795.json'),cfg))
        self.assertEqual((ROOT/'configs/diff_against_h1_1.json').read_bytes(),(ROOT/'configs/diff_against_deployed.json').read_bytes())
        root=temp();db=root/'v.db';conn=sqlite3.connect(db)
        conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
        for i,qid in enumerate(('original','reworded_away_opp')):
            row=dict(qid=qid,question_type='object_rel_direction_hard',facing='away',target='trace')
            conn.execute('INSERT INTO rows VALUES(?,?,?)',(i,json.dumps(row),json.dumps('trace')))
        conn.commit();conn.close();src=dict(database={'path':str(db),'sha256':sha(db)},count=2)
        groups,_,_,excluded=m.populations('vqa',src,{'facing':{'cents':100}},exclude_qid_suffix='_away_opp')
        self.assertEqual(groups['facing'],[0]);self.assertEqual(excluded,{'excluded_qid_suffix:_away_opp':1})
        binding=load(ROOT/'out/BINDING.json');dest=root/'packet';dest.mkdir(mode=0o700)
        (dest/'ADMISSION_BY_TYPE.json').write_bytes((ROOT/'out/ADMISSION_BY_TYPE.json').read_bytes())
        command=[sys.executable,'-B',str(ROOT/'tools/rebind.py'),'--receipt',binding['source_receipt']['path'],
            '--receipt-sha256',binding['receipt_sha256'],'--database',binding['database']['path'],
            '--orchard-store',binding['orchard_store'],'--room-cents','0','--exclude-qid-suffix','_away_opp',
            '--reuse-census','--skip-audit','--out',str(dest)]
        result=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (root/'rebind.log').write_text(result.stdout);self.assertEqual(result.returncode,0,result.stdout[-2000:])
        rebound=load(dest/'config.json');cells=rebound['type_mix']['streams']['vqa']['cells']
        self.assertEqual(cells['room']['cents'],0);self.assertEqual(cells['direction']['cents'],3289)
        self.assertEqual(rebound['type_mix']['exclude_qid_suffix'],'_away_opp')
        self.assertEqual(load(dest/'BINDING.json')['database_sha256'],binding['database_sha256'])
        self.assertEqual(load(ROOT/'configs/r1p.json'),cfg)

    def test_units_refused_when_unbound(self):
        cfg=load(ROOT/'configs/r1p.json');mix=cfg['type_mix']
        mix['unit_rows']=None;mix['streams']['routing']['cells']['units']['cents']=0
        mix['streams']['routing']['cells']['units']['cents']=1
        with self.assertRaisesRegex(ValueError,'unbound'):m.validate(mix,cfg['recipe'])
        mix['streams']['routing']['cells']['units']['cents']=0
        mix['streams']['routing']['refill'].append('units')
        with self.assertRaisesRegex(ValueError,'unbound'):m.validate(mix,cfg['recipe'])

    def test_unit_binding_native_regeneration_cap_and_threshold(self):
        from unit_binding import build,regenerate,inspect_rows,NAME
        from student_pilot import ground_rows,s1_pool
        from student_pilot.vehicle_p import unit_name,required_families,ROUTING
        import gzip,contextlib,io
        root=temp();templates={}
        # This fixture supplies packed rows directly; slice packing has a separate opt-in test.
        slices=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/rows_slices/slices_final/a0_units.jsonl')
        with slices.open() as f:
            for line in f:
                raw=json.loads(line);record=dict(raw['ground_record'],suffix=raw['target'])
                row={**raw,**ground_rows.pack(record,raw['provenance'])}
                try:s1_pool.validate_source_row(row,'packed')
                except ValueError:continue
                unit=unit_name(row)
                frames=[dict(path='/data2/k6tk/'+('a'*2)+'/'+('a'*64)+'.png',sha256='a'*64) for _ in range(32)]
                row['student_input']=dict(frames=frames)
                templates.setdefault(unit,row)
                if len(templates)==3:break
        # The supplied diagnostic slice has no admitted cm example. This synthetic
        # metadata variant tests the cm counter only, not real cm conversion fidelity.
        # Native admission still validates every unchanged answer/event envelope.
        if 'cm' not in templates:
            templates['cm']=copy.deepcopy(templates['ft'])
            templates['cm']['ground_record']['unit']='centimeters'
        self.assertEqual(set(templates),{'cm','ft','in'})
        rows=[]
        for unit,n in (('cm',100),('ft',100),('in',99)):
            for i in range(n):
                row=copy.deepcopy(templates[unit]);row['qid']=row['ground_record']['qid']='fixture_'+unit+'_'+str(i)
                rows.append(row)
        source=root/'faithful.jsonl';source.write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
        cfg=load(ROOT/'configs/r1p.json');parent=parent_selection()
        manifest=load(ROOT/'work/records/pool_manifest.json');indices=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k')
        with contextlib.redirect_stdout(io.StringIO()):
            candidate,binding=build(source,sha(source),parent,manifest,cfg['s1_routing']['catalog'],indices,root/'bound')
            regenerated=regenerate(parent,binding,root/'bound',indices,cfg['s1_routing']['catalog'],root/'replay')
        self.assertEqual(candidate,regenerated)
        self.assertEqual(gzip.decompress((root/'bound/u.gz').read_bytes()),source.read_bytes())
        self.assertEqual(candidate['sources'][NAME]['retained'],299)
        self.assertEqual(binding['counts']['by_unit'],dict(cm=100,ft=100,**{'in':99}))
        self.assertEqual(binding['counts']['missing_units'],['in'])
        self.assertEqual(sum(binding['counts']['by_dataset'].values()),299)
        policy=copy.deepcopy(cfg['type_mix']['streams']['routing']);policy['cells']['units']['cents']=287
        _,table=m.allocate(policy,{**{n:20000 for n in ROUTING},'units':299},1000)
        self.assertEqual(table['units']['final_cents'],119)
        self.assertLessEqual(table['units']['final_cents']/100,4*299/1000)
        cfg['type_mix']['unit_rows']=binding['source'];cfg['type_mix']['streams']['routing']['cells']['units']['cents']=119
        a=load(ROOT/'out/proof/loader_audit.json');a['tables']['routing']=table
        a['eligible_by_family']['vqa']['room']=431
        a['tables']['vqa']['room']['final_cents']=cfg['type_mix']['streams']['vqa']['cells']['room']['cents']
        a['eligible_by_family']['routing']={n:20000 for n in ROUTING};a['eligible_by_family']['routing']['units']=299
        a['unit_counts']=binding['counts']
        self.assertEqual(required_families(cfg,a)['missing_units'],['in']);self.assertEqual(required_families(cfg,a)['status'],'PASS')
        self.assertIn(dict(family='units/in',eligible=99,reason='Fewer than 100 eligible rows.'),required_families(cfg,a)['absent_on_P'])
        a['unit_counts']['by_unit']['in']=100
        self.assertEqual(required_families(cfg,a)['status'],'PASS')
        packet=root/'packet';packet.mkdir(mode=0o700)
        (packet/'ADMISSION_BY_TYPE.json').write_bytes((ROOT/'out/ADMISSION_BY_TYPE.json').read_bytes())
        current=load(ROOT/'out/BINDING.json')
        command=[sys.executable,'-B',str(ROOT/'tools/rebind.py'),'--receipt',current['source_receipt']['path'],
            '--receipt-sha256',current['receipt_sha256'],'--database',current['database']['path'],
            '--orchard-store',current['orchard_store'],'--unit-rows',str(source),'--unit-rows-sha256',sha(source),
            '--reuse-census','--skip-audit','--out',str(packet)]
        result=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (root/'rebind.log').write_text(result.stdout);self.assertEqual(result.returncode,0,result.stdout[-2000:])
        bound=load(packet/'BINDING.json');policy=load(packet/'config.json')['type_mix']
        self.assertEqual(policy['units_allowlist'],['ft']);self.assertEqual(bound['unit_binding']['sampling_eligible'],100)
        self.assertEqual(policy['streams']['routing']['cells']['units']['cents'],40)
        self.assertEqual(sum(v['cents'] for v in policy['streams']['routing']['cells'].values()),6400)
        weights={n:load(ROOT/'configs/mix.json')['streams']['routing']['cells'][n]['cents'] for n in ROUTING}
        for name in ROUTING:self.assertLess(abs(policy['streams']['routing']['cells'][name]['cents']-6360*weights[name]/6400),1)
        with self.assertRaisesRegex(ValueError,'SHA differs'):build(source,'0'*64,parent,manifest,cfg['s1_routing']['catalog'],indices,root/'badsha')
        bad=copy.deepcopy(rows[0]);bad['answer']='0.00'
        with self.assertRaises(ValueError):inspect_rows(json.dumps(bad).encode())
        bad=copy.deepcopy(rows[0]);bad.pop('events')
        with self.assertRaises((KeyError,ValueError)):inspect_rows(json.dumps(bad).encode())
        bad=copy.deepcopy(rows[0]);bad['student_input']['frames']=[]
        with self.assertRaisesRegex(ValueError,'frame pins'):inspect_rows(json.dumps(bad).encode())

    def test_optional_unit_slice_packing_and_native_binding(self):
        import gzip,contextlib,io
        from unit_binding import pack_slice,build,regenerate,pin
        from student_pilot import ground_rows,s1_pool
        from student_pilot.vehicle_p import unit_name
        source=Path('/scratch/jjyeung/orch_n30/rows_r1/out/units_p_slice_v3/rows.jsonl')
        before=sha(source);metadata=load(source.parent/'COUNTS.json');self.assertEqual(before,metadata['rows_sha256'])
        counts=Counter();first=None
        with source.open() as stream:
            for line in stream:
                row=json.loads(line);first=first or row
                envelope=ground_rows.pack(dict(row['ground_record'],suffix=row['target']),row['provenance'])
                packed={**row,'events':envelope['events']}
                for key,value in envelope.items():
                    if key in row and key!='source_qid':self.assertEqual(row[key],value)
                s1_pool.validate_source_row(packed,'packed');counts[unit_name(row)]+=1
        self.assertEqual(sum(counts.values()),metadata['kept']);self.assertEqual(dict(counts),{'ft':683,'in':64})
        root=temp();fixture=root/'slice.jsonl';fixture.write_text(json.dumps(first)+'\n')
        d,scene=first['provenance']['alias'].split('/');ids=first['frame_indices']
        frames=[dict(d=d,s=scene,i=i,path='/data2/k6tk/aa/'+('a'*64)+'.png',sha256='a'*64) for i in ids]
        (root/'map.gz').write_bytes(gzip.compress(''.join(json.dumps(r)+'\n' for r in frames).encode(),mtime=0))
        (root/'plan.gz').write_bytes(gzip.compress(json.dumps({'v':{scene:{'g':d,'raw_n':max(ids)+1}}}).encode(),mtime=0))
        write(root/'fps.json',{'schema':'s1-fps-authority-v1','by_scene':{d+'/'+scene:24.0}})
        authority={k:pin(root/n) for k,n in [('frame_map','map.gz'),('frame_plan','plan.gz'),('fps_authority','fps.json')]}
        parent=parent_selection();dest=root/'packed.jsonl'
        receipt=pack_slice(fixture,sha(fixture),authority,authority,parent,dest)
        packed=json.loads(dest.read_text());self.assertEqual(len(packed['student_input']['frames']),32)
        for k,v in first.items():self.assertEqual(packed[k],v)
        self.assertEqual(packed['source_qid'],first['source_qid']);self.assertFalse(receipt['payload_changed'])
        cfg=load(ROOT/'configs/r1p.json');manifest=load(ROOT/'work/records/pool_manifest.json')
        indices=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k')
        with contextlib.redirect_stdout(io.StringIO()):
            selected,bound=build(dest,sha(dest),parent,manifest,cfg['s1_routing']['catalog'],indices,root/'bound')
            self.assertEqual(selected,regenerate(parent,bound,root/'bound',indices,cfg['s1_routing']['catalog'],root/'regenerated'))
        bad=copy.deepcopy(authority);bad['frame_map']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'authority differs'):pack_slice(fixture,sha(fixture),bad,authority,parent,root/'bad.jsonl')
        with self.assertRaisesRegex(ValueError,'slice SHA differs'):pack_slice(fixture,'0'*64,authority,authority,parent,root/'bad.jsonl')
        altered=copy.deepcopy(first);altered['answer']='999'
        fixture.write_text(json.dumps(altered)+'\n')
        with self.assertRaisesRegex(ValueError,'payload'):pack_slice(fixture,sha(fixture),authority,authority,parent,root/'bad.jsonl')
        fixture.write_text(json.dumps(first)+'\n')
        # The real CLI refuses packing unless all explicit pins are supplied.
        current=load(ROOT/'out/BINDING.json')
        command=[sys.executable,'-B',str(ROOT/'tools/rebind.py'),'--receipt',current['source_receipt']['path'],
                 '--receipt-sha256',current['receipt_sha256'],'--pack-unit-slice']
        result=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        self.assertNotEqual(result.returncode,0);self.assertIn('requires pinned unit rows',result.stdout)
        self.assertIsNotNone(current['unit_binding']);self.assertEqual(before,sha(source))
        write(ROOT/'out/proof/UNIT_PACKING_CHECK.json',dict(status='PASS',source=pin(source),counts=dict(counts),
            sealed_event_reconstruction_rows=sum(counts.values()),existing_payload_unchanged=True,
            fixture_packing=receipt,fixture_native_binding_and_regeneration=True,production_bound=False,
            limitation='Synthetic frame pins test the native resolver and binding path; Orchard must supply real RGB authorities and bytes.'))

    def test_real_unit_slice_rebind_refuses_unpacked_input_without_mutation(self):
        source=Path('/scratch/jjyeung/orch_n30/rows_r1/out/units_p_slice_v3/rows.jsonl')
        root=temp();fixture=root/'rows.jsonl';fixture.write_bytes(source.read_bytes());before=sha(source)
        from student_pilot.vehicle_p import unit_name
        rows=[json.loads(line) for line in fixture.read_text().splitlines()]
        self.assertEqual(Counter(unit_name(row) for row in rows),{'ft':683,'in':64})
        binding=load(ROOT/'out/BINDING.json');dest=root/'packet';dest.mkdir(mode=0o700)
        (dest/'ADMISSION_BY_TYPE.json').write_bytes((ROOT/'out/ADMISSION_BY_TYPE.json').read_bytes())
        command=[sys.executable,'-B',str(ROOT/'tools/rebind.py'),'--receipt',binding['source_receipt']['path'],
            '--receipt-sha256',binding['receipt_sha256'],'--database',binding['database']['path'],
            '--orchard-store',binding['orchard_store'],'--unit-rows',str(fixture),'--unit-rows-sha256',sha(fixture),
            '--units-allowlist','ft','--unit-cents','100','--reuse-census','--skip-audit','--out',str(dest)]
        result=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (root/'rebind.log').write_text(result.stdout)
        self.assertNotEqual(result.returncode,0);self.assertIn("Unit rows require top-level events",result.stdout)
        self.assertFalse((dest/'BINDING.json').exists())
        self.assertEqual(sha(source),before);self.assertEqual(sha(fixture),before)
        self.assertEqual(load(ROOT/'out/BINDING.json'),binding)
        write(ROOT/'out/proof/UNIT_CANDIDATE.json',dict(status='DIRECT_UNPACKED_INPUT_REFUSED',source={'path':str(source),'sha256':before},fixture={'path':str(fixture),'sha256':sha(fixture)},counts={'ft':683,'in':64,'cm':0},command=command,returncode=result.returncode,reason='Missing top-level events and all 32 frame pins',log={'path':str(root/'rebind.log'),'sha256':sha(root/'rebind.log')},production_bound=False))

    def test_unit_allowlist_populations_cap_and_named_absences(self):
        import sqlite3
        from student_pilot.loader_audit import unit_counts
        from student_pilot.vehicle_p import required_families,ROUTING
        root=temp();db=root/'u.db';conn=sqlite3.connect(db)
        conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
        i=0
        for unit,count in [('ft',1130),('in',94)]:
            for j in range(count):
                row=dict(qid=unit+str(j),question_type='object_abs_distance',target='trace',ground_record={'unit':unit},s1_source={'source':{'sha256':'a'*64}})
                conn.execute('INSERT INTO rows VALUES(?,?,?)',(i,json.dumps(row),json.dumps('trace')));i+=1
        conn.commit();conn.close();source=dict(database={'path':str(db),'sha256':sha(db)},count=i)
        groups,_,traces,excluded=m.populations('routing',source,{'units':{'cents':100}},unit_rows={'sha256':'a'*64},units_allowlist=['ft'])
        self.assertEqual(len(groups['units']),1130);self.assertEqual(excluded['excluded_unit:in'],94)
        self.assertTrue(all(r['qid'].startswith('ft') for r in traces['units']))
        counts=unit_counts(source,['ft']);self.assertEqual(counts['sampling_eligible'],1130)
        cfg=load(ROOT/'configs/r1p.json');cfg['type_mix']['unit_rows']={'path':'fixture','sha256':'a'*64}
        cfg['type_mix']['streams']['routing']['cells']['units']['cents']=100
        a=load(ROOT/'out/proof/loader_audit.json');a['unit_counts']=counts
        a['eligible_by_family']['vqa']['room']=431;a['tables']['vqa']['room']['final_cents']=cfg['type_mix']['streams']['vqa']['cells']['room']['cents']
        a['eligible_by_family']['routing']={**{n:20000 for n in ROUTING},'units':1130}
        a['tables']['routing']={'units':{'final_cents':100}}
        gate=required_families(cfg,a);self.assertEqual(gate['status'],'PASS')
        missing={r['family']:r.get('eligible') for r in gate['absent_on_P']}
        self.assertEqual(missing['units/cm'],0);self.assertEqual(missing['units/in'],94)
        self.assertNotIn('units/ft',missing)
        _,table=m.allocate({'cells':{'units':{'cents':100}},'refill':[]},{'units':1130},1000)
        self.assertEqual(table['units']['final_cents'],100)
        self.assertEqual(table['units']['cap_cents'],452)

    def test_partition_parameter_and_cpu_resources(self):
        from unittest.mock import patch
        spec=importlib.util.spec_from_file_location('partition_proof',ROOT/'out/proof/p.py')
        proof=importlib.util.module_from_spec(spec);spec.loader.exec_module(proof)
        for partition in ('advanced','general','bootstrap'):
            with patch.dict(os.environ,dict(SLURM_JOB_PARTITION=partition,SLURMD_NODENAME='fixture-node',CUDA_VISIBLE_DEVICES='',SLURM_GPUS_ON_NODE='0')):
                self.assertEqual(proof.proof_allocation({'partition':partition}),dict(partition=partition,node='fixture-node'))
                with self.assertRaisesRegex(ValueError,'partition differs'):proof.proof_allocation({'partition':'other'})
            root=temp();(root/'proof').mkdir();write(root/'BINDING.json',load(ROOT/'out/BINDING.json'))
            subprocess.run([sys.executable,'-B',str(ROOT/'tools/make_proof.py'),'--out',str(root),'--partition',partition],check=True,stdout=subprocess.DEVNULL)
            script=(root/'proof'/('p_'+load(ROOT/'out/BINDING.json')['run_key']+'.sh')).read_text()
            self.assertIn('-p '+partition,script);self.assertIn('-c 48 --mem=800G -t 04:00:00',script)
            self.assertNotIn('--gres',script);self.assertIn('CUDA_VISIBLE_DEVICES',script)
        with patch.dict(os.environ,dict(SLURM_JOB_PARTITION='advanced',CUDA_VISIBLE_DEVICES='0')):
            with self.assertRaisesRegex(ValueError,'CPU-only'):proof.proof_allocation({'partition':'advanced'})

from test_derivation_pre_submit import DerivationEvidence
from test_fix8 import Fix8
from test_fix9 import Fix9
from test_fix10 import Fix10
from test_fix11 import Fix11
from test_fix12 import Fix12
from test_cont1 import Continuation
from test_cont2 import ZContinuationModes
from test_cont3 import ZTrainingAuthority
from test_cont4 import ZPostAdmission
from test_canary_c import ZCanaryC

if __name__=='__main__':unittest.main(verbosity=2)
