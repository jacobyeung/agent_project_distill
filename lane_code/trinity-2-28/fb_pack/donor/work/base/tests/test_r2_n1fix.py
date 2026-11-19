"""Sealed producer handover and independent input-refusal regressions."""
import ast
from copy import deepcopy
import json, math, os, sqlite3, unittest
from pathlib import Path
from unittest.mock import patch
import torch
from student_pilot import carrier_c1_run as run, r1_training as contract, r1_handover
from student_pilot.p3_provenance import digest, file_pin, load
from tests.test_r2_build_n1 import configuration, sampling, write
from tests.test_r2_data_path import PROOFS


def sealed_functions():
    path = Path(__file__).resolve().parents[2]/'base/tree_b01ce449/student_pilot/carrier_c1_run.py'
    # Frozen packages preserve the same work/tree_r1 and work/base layout.
    nodes = [node for node in ast.parse(path.read_text()).body
             if isinstance(node, ast.FunctionDef) and node.name in ('export', 'identity', 'bind_output', 'checkpoint')]
    space = dict(vars(run))
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), space)
    return space


def produce_receipt(*args, **kwargs):
    from launch_r1 import p_handover_receipt as producer
    # Only retained proof metadata overwrites; production receipts remain exclusive.
    with patch.object(producer,'write',write):
        return producer.produce(*args,**kwargs)


def handover_fixture(root, scales=None, donor_scales=None, step=200):
    from tests.test_carrier_c1 import fixture
    root.mkdir(parents=True, exist_ok=True)
    cfg = configuration()
    # The tiny producer model has no Stage-1 initialization on either side.
    cfg.pop('depth_init', None)
    cfg.pop('checkpoint_disk_guard', None)
    cfg.pop('code', None)
    if scales is not None:cfg.update(scales)
    model, _, _ = fixture(4,training_mode='final')
    cfg.update(base_identity='fixture', trace_program_version='3.13',frame_layout='spread',
               depth_fov_source='private',routing_opener_init='keep')
    p = deepcopy(cfg)
    for key in ('r1_training','r2_sampling','init_artifact','preparation'):p.pop(key,None)
    p.update(recipe=deepcopy(run.recipe_for(cfg)), streams={})
    p.update({key:deepcopy(cfg[key]) for key in ('mix','world_size','reference_world_size','steps','milestones')})
    p['scheduled_sampling']=deepcopy(p['recipe']['scheduled_sampling'])
    p.update({k:cfg.get(k,1.0) for k in ('lm_lr_scale','pose_lr_scale')})
    if donor_scales is not None:
        for key in ('lm_lr_scale','pose_lr_scale'):p.pop(key,None)
        p.update(donor_scales)
    p['recipe']=run.recipe_for(p)
    streams = {}
    for name, count in contract.STREAMS.items():
        db = dict(path=str(root/(name+'.db')), sha256=digest(name))
        pin = write(root/(name+'.json'), dict(database=db, count=count))
        p['streams'][name] = pin
        streams[name] = dict(receipt=pin, database=db, count=count, source_count=count)
    ident = r1_handover.export_identity(p)
    model_pin=write(root/'model/config.json',model.config.to_dict())
    manifest=write(root/'model.json',dict(root=str(root/'model'),files={'config.json':model_pin['sha256']}))
    prep = write(root/'preparation.json', dict(schema='c1-preparation-v1', config_sha256=ident,
                 streams=streams, recipe=p['recipe'], training_mode='final',model=manifest,
                 camera=model.auxiliary_heads.pose.settings,
                 depth=dict(weight=.05,d_proj=16,mlp_hidden=16,num_heads=4,context_depth=1,vit_layers=[1,2,3])))
    p['preparation'] = prep
    ppin = write(root/'config.json', p)
    bound = dict(config_sha256=ident, preparation=prep, world_size=4, trainer_commit='fixture')
    functions = sealed_functions()
    if (root/'binding.json').exists():write(root/'binding.json',bound)
    functions['bind_output'](root, bound, resume=(root/'binding.json').exists())
    destination = root/f'm{step}'
    from tests.test_carrier_c1_run import RunnerTests
    mkdir=Path.mkdir
    native_open=Path.open
    # Fixture retention permits overwriting the same owned proof folder.
    def retain(path,mode=0o777,parents=False,exist_ok=False):
        return mkdir(path,mode=mode,parents=parents,exist_ok=True if path.is_relative_to(root) else exist_ok)
    def overwrite(path,mode='r',*args,**kwargs):
        return native_open(path,mode.replace('x','w') if path.is_relative_to(root) else mode,*args,**kwargs)
    with RunnerTests().local_collectives(), patch.object(Path,'mkdir',retain), patch.object(Path,'open',overwrite), \
            patch('student_pilot.fsdp_training.publication_state', return_value=model.state_dict()):
        complete=functions['checkpoint'](root/'checkpoint',model,
            torch.optim.AdamW(run.parameter_groups(model)),bound,step)
        functions['export'](destination, model, model, p, step)
    pin = file_pin(destination/'artifact.json')
    artifact = load(pin['path'])
    assert artifact['config_sha256'] == functions['identity'](p)
    assert artifact['training_mode'] == p['training_mode']
    assert 'r1_progress' not in artifact
    cfg['init_artifact'] = dict(artifact=pin)
    cfg['r1_training'].update(donor_config_sha256=ident,
        p_run=dict(config=ppin, preparation=prep, binding=file_pin(root/'binding.json'),checkpoint=complete))
    cfg['r1_training']['handover_receipt']=produce_receipt(cfg['r1_training']['p_run'],pin,root/'handover.json',
        job_id='cpu-producer-fixture',trainer_commit='fixture')
    _, _, actual, plan = r1_handover.donor(cfg, artifact)
    cfg['r1_training'].update(continuation_identity=actual['config_identity'],
        store_hashes=actual['stores'], row_plan_sha256=actual['row_plan_sha256'])
    binding, counts=sampling(root/'n_sampler')
    cfg['r2_sampling']=binding
    cfg['streams']=deepcopy(p['streams'])
    cfg['r1_training']['row_plan_sha256']=digest(binding)
    target=contract.target_identity(cfg)
    cfg['r1_training'].update(continuation_identity=target['config_identity'],store_hashes=target['stores'])
    expected=contract.boundary(cfg,step)
    cfg['r1_training']['handover_mapping']=write(root/'native_to_cells.json',dict(
        schema='r1-handover-map-v1',artifact_sha256=pin['sha256'],step=step,source=actual,
        target={key:expected[key] for key in actual}))
    return cfg, p, model, artifact


class N1Fix(unittest.TestCase):
    def root(self, name):
        root = PROOFS/'n1fix'/name
        root.mkdir(parents=True, exist_ok=True)
        return root

    def test_sealed_export_continuation(self):
        root = self.root('handover')
        cfg, p, model, artifact = handover_fixture(root)
        self.assertEqual(contract.start(cfg), 200)
        proof = r1_handover.progress(cfg, artifact)
        self.assertEqual(proof['sampler_positions'], {s:200*n for s,n in contract.STREAMS.items()})
        from student_pilot.carrier_c1_data import mixed_indices
        plan = proof['donor_row_plan']
        full = list(mixed_indices(dict(plan['counts']), 201, training_mode='final', mix=p['recipe']['mix'], world=4))
        self.assertEqual(digest(full[200]), proof['donor_next_plan_sha256'])
        binding, counts=sampling(root/'n_sampler')
        full_n=list(mixed_indices(counts,201,world=4,r2_sampling=binding))
        resumed_n=list(mixed_indices(counts,201,start_step=contract.start(cfg),world=4,r2_sampling=binding))
        self.assertEqual(resumed_n,full_n[200:])
        from student_pilot.decoupled_v import learning_rate
        recipe = run.recipe_for(cfg)
        warm = math.ceil(recipe['steps']*recipe['warmup_ratio'])
        expected = recipe['learning_rate']*(1+math.cos(math.pi*(201-warm)/(recipe['steps']-warm)))/2
        self.assertAlmostEqual(learning_rate(contract.start(cfg)+1,recipe), expected, places=15)
        from tests.test_carrier_c1 import fixture
        fresh, _, _ = fixture(4,training_mode='final')
        run.load_artifact(fresh, cfg['init_artifact']['artifact'])
        for key, value in fresh.state_dict().items():
            torch.testing.assert_close(value, model.state_dict()[key].to(value.dtype), rtol=0, atol=0)
        write(root/'RESULT.json', dict(step=200, next_step=201, learning_rate=expected, progress=proof,
            n_next_plan_sha256=digest(resumed_n[0]),mapping=cfg['r1_training']['handover_mapping'],
            producer=str(Path(__file__).resolve().parents[2]/'base/tree_b01ce449/student_pilot/carrier_c1_run.py'),
            stand_ins='Tiny seeded native model replaces pretrained GPU weights; local rank/barrier and FSDP publication replace distributed GPU collectives. Sealed export and bind_output, native artifact reader, donor validation and sampler run. Run preparation metadata is synthetic; no production P export was supplied.'))

    def test_forged_receipt_and_mismatches(self):
        root = self.root('handover')
        cfg, _, _, artifact = handover_fixture(root)
        forged = deepcopy(cfg)
        forged['r1_training'].pop('p_run')
        forged['r1_training']['continuation_receipt'] = write(root/'forged.json',
            dict(contract.boundary(cfg, 200), artifact_sha256=cfg['init_artifact']['artifact']['sha256'],
                 p_store_hashes={'vqa':'d'*64}, p_row_plan_sha256='e'*64))
        with self.assertRaisesRegex(ValueError, 'RUN_FILE_REQUIRED:config.json'):
            contract.start(forged)
        no_mapping=deepcopy(cfg);no_mapping['r1_training'].pop('handover_mapping')
        with self.assertRaisesRegex(ValueError,'explicit sha-bound'):contract.start(no_mapping)
        for key, value in [('donor_config_sha256','d'*64), ('continuation_identity','d'*64),
                            ('store_hashes',{'vqa':'d'*64}), ('row_plan_sha256','e'*64)]:
            bad = deepcopy(cfg); bad['r1_training'][key] = value
            with self.assertRaisesRegex(ValueError, 'P_EXPORT_'):
                contract.start(bad)
        mapped = deepcopy(cfg); mapped['r1_training']['row_plan_sha256']='e'*64
        mapped['r1_training']['continuation_identity']=contract.target_identity(mapped)['config_identity']
        actual = r1_handover.donor(cfg,artifact)[2]
        expected = contract.boundary(mapped,200)
        mapping = dict(schema='r1-handover-map-v1', artifact_sha256=cfg['init_artifact']['artifact']['sha256'],
                       step=200, source=actual, target={k:expected[k] for k in actual})
        mapped['r1_training']['handover_mapping']=write(root/'mapping.json',mapping)
        self.assertEqual(contract.start(mapped),200)
        mapping['source']['stores']['vqa']='f'*64
        mapped['r1_training']['handover_mapping']=write(root/'mapping_bad.json',mapping)
        with self.assertRaisesRegex(ValueError,'MAPPING_MISMATCH'): contract.start(mapped)

    def test_M09_absent_scene(self):
        from student_pilot.scene_division_gate import check_rows
        root=self.root('scene')
        pin=write(root/'division.json',dict(train_scenes=['d1/train'],heldout_scenes=['d1/held']))
        with self.assertRaisesRegex(ValueError,'DIVISION'):
            check_rows([dict(dataset='d1',scene='absent',qid='outside')],pin)

    def test_M12_own_probability(self):
        cfg=configuration()
        cfg['scheduled_sampling']=dict(run.recipe_for(cfg)['scheduled_sampling'],max_own_probability=0.1)
        with self.assertRaisesRegex(ValueError,'OWN_PROBABILITY'): contract.validate(cfg)

    def test_M07_room_frames(self):
        row=dict(question_type='room_size_estimation',answer='12',
            student_input={'question':'What is the floor area in square meters?'},
            target='<think>\nLocate: the shelf is seen in frame 1.\nRelate: the floor is below the shelf.\nRelate: the table is to the left of the shelf.\n</think>\n\n12')
        from student_pilot.trace_grammar import validate_row
        self.assertEqual(validate_row(dict(row,form='direct')),[])
        with self.assertRaisesRegex(ValueError,'ONE_LINE_ROOM'): contract.row_check(row,'vqa')

    def test_format_status_and_reader(self):
        from student_pilot.row_text_audit import reasons
        reader=run.Rows(dict(streams={},r1_training={'schema':'r1-training-v1'}),None)
        conn=sqlite3.connect(':memory:');reader.connections['vqa']=conn
        conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
        conn.execute('INSERT INTO rows VALUES(0,?,?)',('{}','{}'))
        for character in ('\u200b','\u200c','\u200d','\u2060','\ufeff'):
            for status in ('not'+character+'seen','not '+character+'seen','box'+character+'unavailable'):
                row=dict(target='<think>'+status+'</think>\n1')
                self.assertIn('runtime_box_status',reasons(row))
                conn.execute('UPDATE rows SET row=? WHERE i=0',(json.dumps(row),))
                with self.assertRaisesRegex(ValueError,'rule_only_text'): reader.row('vqa',0)
        reader.close()

    def test_r1_reader_reserves_r0(self):
        from student_pilot.r0_exclusion import reserve
        reader=run.Rows(dict(streams={},r1_training={'schema':'r1-training-v1'}),None)
        self.assertFalse(reader.b7_inputs)
        conn=sqlite3.connect(':memory:');reader.connections['vqa']=conn
        conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
        scene=next(iter(sorted(reserve().names)))
        row=dict(target='<think>Locate: the chair in frame 1.</think>\n1',dataset=scene.split('/')[0],scene=scene.split('/')[1])
        conn.execute('INSERT INTO rows VALUES(0,?,?)',(json.dumps(row),'{}'))
        with self.assertRaisesRegex(ValueError,'r0_room_refused'): reader.row('vqa',0)
        row['scene']='fixture'
        conn.execute('UPDATE rows SET row=? WHERE i=0',(json.dumps(row),))
        self.assertEqual(reader.row('vqa',0)[0],row)
        reader.close()

    def test_fresh_job_tmp_and_path_closure(self):
        from launch_r1 import entry
        root=self.root('tmp_paths')
        with self.assertRaisesRegex(ValueError,'JOB_TMP_REQUIRED'): entry.fresh_tmp(root,{})
        with patch.object(entry,'TMP_NAMESPACE',root):
            present=root/'present';present.mkdir(exist_ok=True)
            with self.assertRaisesRegex(ValueError,'NOT_FRESH'): entry.fresh_tmp(present/'work',{'job_tmp':str(present)})
            job=root/'fresh'
            self.assertEqual(entry.fresh_tmp(job/'work',{'job_tmp':str(job)}),job)
            for value in ('/home/x','/data2/x','/tmp/other','u/../x',{'x':['/outside']}):
                with self.assertRaisesRegex(ValueError,'OUTSIDE_JOB_TMP'): entry.temporary_paths(value,job)
            entry.temporary_paths({'x':[str(job/'u/x'),'u/x',None]},job)

    def test_donor_evidence_edges(self):
        root=self.root('handover')
        cfg, p, _, artifact=handover_fixture(root)
        baseline=deepcopy(cfg)
        def candidate(change, authenticated=False):
            c=deepcopy(baseline); source=deepcopy(p)
            prep=load(c['r1_training']['p_run']['preparation']['path'])
            bound=load(c['r1_training']['p_run']['binding']['path'])
            change(source,prep,bound)
            ident=r1_handover.export_identity(source)
            prep['config_sha256']=ident;bound['config_sha256']=ident
            pin=write(root/'edge_preparation.json',prep)
            source['preparation']=pin;bound['preparation']=pin
            complete=load(baseline['r1_training']['p_run']['checkpoint']['path'])
            complete['binding']=bound
            c['r1_training'].update(donor_config_sha256=ident,
                p_run=dict(config=write(root/'edge_config.json',source),preparation=pin,
                           binding=write(root/'edge_binding.json',bound),
                           checkpoint=write(root/'checkpoint/edge_complete.json',complete)))
            if authenticated:
                ap=write(root/'edge_artifact.json',dict(artifact,config_sha256=ident))
                c['init_artifact']['artifact']=ap
                c['r1_training']['handover_receipt']=produce_receipt(c['r1_training']['p_run'],ap,root/'edge_handover.json',
                    job_id='cpu-edge-producer',trainer_commit='fixture')
            c['r1_training']['continuation_identity']=contract.target_identity(c)['config_identity']
            return c,dict(artifact,config_sha256=ident)
        for key in ('binding','preparation'):
            c=deepcopy(cfg);c['r1_training']['p_run'].pop(key)
            with self.assertRaisesRegex(ValueError,'RUN_FILE_REQUIRED'):r1_handover.donor(c,artifact)
        cases=[
            (lambda s,p,b:p.update(schema='wrong'),'RUN_BINDING'),
            (lambda s,p,b:b.update(world_size=8),'RECIPE'),
            (lambda s,p,b:p['streams']['vqa'].update(receipt={}), 'STORE_RECEIPT'),
            (lambda s,p,b:p['streams']['vqa'].update(count=1),'RUN_FILE_REQUIRED'),
            (lambda s,p,b:p['streams']['vqa'].update(indices=write(root/'bad_indices.json',[0])), 'INDEX_COUNT'),
        ]
        for change,error in cases:
            c,a=candidate(change)
            with self.assertRaisesRegex(ValueError,error):r1_handover.donor(c,a)
        c,a=candidate(lambda s,p,b:p['streams']['vqa'].update(indices=write(root/'indices.json',list(range(128)))),True)
        self.assertIn('vqa',r1_handover.donor(c,a)[3]['indices'])
        c=deepcopy(cfg);c['recipe']['warmup_ratio']=.1
        with self.assertRaisesRegex(ValueError,'LR_SCHEDULE'):r1_handover.progress(c,artifact)
        c,a=candidate(lambda s,p,b:s.update(row_start_step=1),True)
        with self.assertRaisesRegex(ValueError,'CONFIG_DIFFERENCE:row_start_step'):r1_handover.progress(c,a)
        c,a=candidate(lambda s,p,b:s.update(mix=['pose','vqa','routing','pointing']),True)
        c['r1_training']['continuation_identity']=contract.target_identity(c)['config_identity']
        with self.assertRaisesRegex(ValueError,'SAMPLER_POSITION'):r1_handover.progress(c,a)
        tiny=dict(readout={'contiguous_clips':1,'x':2},frame_layout='spread')
        self.assertEqual(r1_handover.export_identity(tiny),digest({'readout':{'x':2}}))

    def test_frame_host_local_namespace(self):
        from launch_r1 import entry
        from student_pilot.checkpoint_space import plan
        root=self.root('host_namespace')
        cfg=configuration()
        cfg={k:cfg[k] for k in ('training_mode','mix','world_size','reference_world_size','steps','milestones','scheduled_sampling','recipe')}
        cfg['checkpoint_disk_guard']=plan(run.recipe_for(cfg),retained_archive_copies=1)
        job=root/'job'
        if job.exists():
            with patch.object(entry,'TMP_NAMESPACE',root),self.assertRaisesRegex(ValueError,'NOT_FRESH'):
                entry.frame_host(cfg,job/'empty',{'job_tmp':str(job),'binaries':['python']})
            return
        with patch.object(entry,'TMP_NAMESPACE',root),patch.dict(os.environ,PATH='/usr/bin:/bin'):
            result=entry.frame_host(cfg,job/'work',{'job_tmp':str(job),'binaries':['bash']})
        self.assertTrue(result['assertions']['job_tmp'])
        self.assertEqual(result['missing'],['R1_HOST_STAGING_AND_SELECTION_INPUTS_MISSING'])
        self.assertEqual((job.stat().st_mode & 0o777),0o700)

    def test_prestaged_tmp_token_is_single_use(self):
        from launch_r1 import entry
        root=self.root('tmp_token')
        job=root/'job'
        with patch.object(entry,'TMP_NAMESPACE',root):
            if job.exists():
                with self.assertRaises(FileExistsError):entry.create_job_tmp(job)
                return
            token=entry.create_job_tmp(job)
            from student_pilot.checkpoint_space import plan
            cfg=configuration()
            cfg={k:cfg[k] for k in ('training_mode','mix','world_size','reference_world_size','steps','milestones','scheduled_sampling','recipe')}
            cfg['checkpoint_disk_guard']=plan(run.recipe_for(cfg),retained_archive_copies=1)
            with patch.dict(os.environ,PATH='/usr/bin:/bin'):
                result=entry.frame_host(cfg,job/'work',{'job_tmp':str(job),'binaries':['bash']},job_tmp_token=token)
            self.assertTrue(result['assertions']['job_tmp'])
            self.assertEqual(result['missing'],['R1_HOST_STAGING_AND_SELECTION_INPUTS_MISSING'])
            with self.assertRaisesRegex(ValueError,'TOKEN_INVALID'):
                entry.fresh_tmp(job/'work',{'job_tmp':str(job)},token)
            with self.assertRaisesRegex(ValueError,'TOKEN_INVALID'):
                entry.fresh_tmp(job/'work',{'job_tmp':str(job)},object())
        with self.assertRaisesRegex(ValueError,'JOB_TMP_REQUIRED'):entry.create_job_tmp('/outside')
