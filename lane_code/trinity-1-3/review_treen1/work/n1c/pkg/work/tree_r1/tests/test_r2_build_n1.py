"""R1 CPU producer/reader, continuation and refusal proofs."""
from collections import Counter
from copy import deepcopy
import json,os,sqlite3,unittest
from pathlib import Path
from unittest.mock import patch
import torch
from student_pilot.p3_provenance import load,file_pin,digest
from student_pilot import r1_training as contract, r1_mix
from student_pilot import carrier_c1_run as run
from tests.test_r2_data_path import PROOFS,LANE


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    return file_pin(path)


def configuration():
    cfg=load(LANE/'work/kit07ca49df_meta/m/k/b02e4385.json')
    cfg.update(geometry_connector='none',frame_count=32,frame_layout='duplicate',frame_markers=True,
               steps=1000,milestones=[100,200,400,600,800,1000],world_size=4)
    cfg['camera_overrides']={'weight_scale':1.0}
    cfg['recipe']['milestones']=cfg['milestones']
    cfg['r1_training']=dict(schema='r1-training-v1',s2=False,stop_after_step=None,
        continuation_identity='a'*64,store_hashes={'vqa':'b'*64},row_plan_sha256='c'*64)
    return cfg


def sampling(root):
    card=dict(schema='r1-card-v1',steps=1000,seed=17,quotas=contract.STREAMS,
        cells=[dict(type=k,stream=s,rows_per_step=n) for s,k,n in
               [('pose','pose',64),('vqa','direction',128),('routing','absolute_distance',64),('pointing','pointing',32)]])
    card_pin=write(root/'card.json',card)
    counts={c['type']:int(c['rows_per_step']*250) for c in card['cells']}
    evidence=write(root/'evidence.json',dict(synthetic_cpu_fixture=True))
    population=write(root/'population.json',dict(schema='r1-population-v1',complete=True,after_all_filters=True,
        card_sha256=card_pin['sha256'],counts=counts,evidence=[evidence]))
    indices=write(root/'indices.json',dict(population_sha256=population['sha256'],
        cells={k:list(range(n)) for k,n in counts.items()}))
    binding=dict(schema='r1-sampling-v1',card=card_pin,population=population,indices=indices)
    return binding,{c['stream']:counts[c['type']] for c in card['cells']}


class R1(unittest.TestCase):
    def root(self,name):
        root=PROOFS/'r1'/name;root.mkdir(parents=True,exist_ok=True);return root

    def test_loader_dimensions_from_question_and_printed_response(self):
        from student_pilot.r1_loader import row_dimensions
        row=dict(question_type='absolute_distance',student_input={'question':'How far in feet?'},
                 target='<tool_response>{"status":"ok","value":3}</tool_response>')
        self.assertEqual(row_dimensions(row),('ft',['ok']))
        row['target']='<tool_response>unavailable</tool_response>'
        self.assertEqual(row_dimensions(row),('ft',['unparsed_printed_response']))

    def test_switches_and_identity(self):
        cfg=configuration();contract.validate(cfg)
        same=deepcopy(cfg);same['r1_training'].update(host_receipt={'x':1},review={'x':2})
        self.assertEqual(run.identity(cfg),run.identity(same))
        for key,value in [('s2',True),('stop_after_step',1001)]:
            bad=deepcopy(cfg);bad['r1_training'][key]=value
            with self.assertRaises(ValueError):contract.validate(bad)
        for key,value in [('geometry_connector','gf1'),('frame_count',64),('camera_overrides',{'weight_scale':0})]:
            bad=deepcopy(cfg);bad[key]=value
            with self.assertRaises(ValueError):contract.validate(bad)
        bad=deepcopy(cfg);bad['r1_training']['continuation_identity']=None
        with self.assertRaisesRegex(ValueError,'CONTINUATION_IDENTITIES'):contract.boundary(bad,0)

    def test_size_cell_is_one_parameter(self):
        lane=Path(__file__).resolve().parents[3]
        card=load(lane/'work/build_n1/inputs/mix.json')
        counts={c['type']:100000 for c in card['cells']}
        card['size_rows_per_step']=5
        proof=r1_mix.allocate(card,counts)
        self.assertEqual(proof['draws']['object_size'],5000)
        self.assertEqual(proof['draws']['direction'],27890)
        counts['object_size']=100
        proof=r1_mix.allocate(card,counts)
        self.assertEqual(proof['draws']['object_size'],400)
        self.assertEqual(proof['cuts']['object_size']['ceiling'],400)
        self.assertEqual(proof['draws']['direction'],32490)

    def test_native_reader_room_and_own_refusals(self):
        row=dict(qid='room',dataset='d1',scene='fixture',question_type='room_size_estimation',answer='12',
            student_input={'question':'What is the floor area in square meters?'},
            target='<think>\nThe question asks for the floor area in square meters.\nLocate: the shelf is seen in frame 1.\nLocate: the table is seen in frame 2.\nRelate: the shelf is to the right of the table.\n</think>\n\n12')
        reader=run.Rows(dict(streams={},r1_training={'schema':'r1-training-v1'}),None)
        conn=sqlite3.connect(':memory:');reader.connections['vqa']=conn
        conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
        conn.execute('INSERT INTO rows VALUES(0,?,?)',(json.dumps(row),'{}'))
        self.assertEqual(reader.row('vqa',0)[0],row)
        bad=deepcopy(row);bad['target']='<think>\nThe floor area is estimated.\n</think>\n\n12'
        conn.execute('UPDATE rows SET row=? WHERE i=0',(json.dumps(bad),))
        with self.assertRaisesRegex(ValueError,'ONE_LINE_ROOM'):reader.row('vqa',0)
        bad=deepcopy(row);bad['own_valued']=True
        conn.execute('UPDATE rows SET row=? WHERE i=0',(json.dumps(bad),))
        with self.assertRaisesRegex(ValueError,'OWN_VALUED'):reader.row('vqa',0)
        with self.assertRaisesRegex(ValueError,'ROOM_PROGRAM'):contract.row_check(row,'routing')
        reader.close()

    def test_full_schedule_repeat_cap_and_resume(self):
        root=self.root('sampler');binding,counts=sampling(root)
        from student_pilot.carrier_c1_data import mixed_indices
        full=list(mixed_indices(counts,1000,world=4,r2_sampling=binding))
        resumed=list(mixed_indices(counts,1000,start_step=200,world=4,r2_sampling=binding))
        self.assertEqual(full[200:],resumed)
        hits=Counter((s,i) for plan in full for s,indices in plan for i in indices)
        self.assertEqual(max(hits.values()),4)
        self.assertEqual(sum(hits.values()),288000)
        bad=load(binding['population']['path']);bad['counts']['direction']=1
        write(root/'population.json',bad);binding['population']=file_pin(root/'population.json')
        ix=load(binding['indices']['path']);ix['population_sha256']=binding['population']['sha256']
        binding['indices']=write(root/'indices.json',ix)
        with self.assertRaisesRegex(ValueError,'CAPACITY_SHORTFALL'):list(r1_mix.plans(binding,counts,1000))
        write(root/'RESULT.json',dict(draws=sum(hits.values()),maximum_repeat=4,resume_identical=True,
            scope='Synthetic metadata population through the production native sampler; no real population claim'))

    def test_export_load_and_continuation(self):
        from tests.test_r2_n1fix import handover_fixture
        root=self.root('export')
        cfg, donor, model, artifact = handover_fixture(root)
        artifact_pin=cfg['init_artifact']['artifact']
        self.assertEqual(contract.start(cfg),200)
        from student_pilot.decoupled_v import learning_rate
        import math
        recipe=run.recipe_for(configuration())
        lr=learning_rate(contract.start(cfg)+1,recipe)
        warm=math.ceil(recipe['steps']*recipe['warmup_ratio'])
        self.assertAlmostEqual(lr,recipe['learning_rate']*(1+math.cos(math.pi*(201-warm)/(recipe['steps']-warm)))/2)
        from student_pilot.r2_openers import initialize,vocabulary,preparation
        from types import SimpleNamespace
        processor=SimpleNamespace(tokenizer=SimpleNamespace(get_vocab=lambda:{'a':0}),_routing_tokens={'a':0})
        cfg['init_artifact']['lm']='full';cfg['routing_opener_init']='keep'
        from tests.r2_init_fixture import INIT
        cfg['r2_identity']={'init':INIT}
        cfg['routing_vocabulary']=write(root/'vocabulary.json',dict(artifact_sha256=artifact_pin['sha256'],
            lineage_sha256=INIT['artifact_sha256'],**vocabulary(processor)))
        preparation(cfg)
        holder=SimpleNamespace(init_report={'lm_tensors':1,'r2_lineage':None})
        self.assertEqual(initialize(holder,processor,cfg),'kept')
        write(root/'RESULT.json',dict(step=200,next_step=201,learning_rate=lr,artifact=artifact_pin,
            stand_ins='Seeded tiny native model replaces pretrained GPU weights; FSDP publication and rank/barrier collectives are local stand-ins. Native export, weight reader, state reload, progress and LR functions run unchanged.'))

    def test_scale_missing_and_partial(self):
        live={'pose.head.scale_token':torch.ones(2),'pose.head.scale_branch.weight':torch.ones(2), 'pose.x':torch.ones(1)}
        original={k:v.clone() for k,v in live.items()}
        self.assertEqual(contract.scale_init(live,{'pose.x':live['pose.x']},enabled=True),set(live)-{'pose.x'})
        for k,v in live.items():torch.testing.assert_close(v,original[k],rtol=0,atol=0)
        with self.assertRaisesRegex(ValueError,'PARTIAL_SCALE'):contract.scale_init(live,{'pose.head.scale_token':live['pose.head.scale_token']},enabled=True)
        self.assertEqual(contract.scale_init(live,live,enabled=True),set())

    def test_native_absent_scale_load(self):
        from tests.test_carrier_c1 import fixture
        root=self.root('scale_load');model,_,_=fixture(4,training_mode='final')
        model.r1_training={'schema':'r1-training-v1'}
        state=model.auxiliary_heads.state_dict()
        absent={k:v.clone() for k,v in state.items() if k.startswith(contract.SCALE)}
        self.assertTrue(absent)
        donor={k:v.clone() for k,v in state.items() if not k.startswith(contract.SCALE)}
        torch.save(donor,root/'heads.pt')
        artifact=dict(schema='carrier-c1-artifact-v1',step=200,pose_backing='lm_final_norm',
            placement=model.carrier_placement,frame_layout=model.frame_layout,training_mode='final',
            carrier_position_policy=model.carrier_position_policy,heads=file_pin(root/'heads.pt'))
        pin=write(root/'artifact.json',artifact)
        report=run.init_from_artifact(model,dict(artifact=pin,heads=['pose','depth','frame_embeddings'],lm='base'))
        self.assertEqual(set(report['planned_init']),set(absent))
        for k,v in absent.items():torch.testing.assert_close(model.auxiliary_heads.state_dict()[k],v,rtol=0,atol=0)
        write(root/'RESULT.json',dict(planned_init=report['planned_init'],native_loader=True,
            initialization='Unmodified seeded native constructor tensors; no fitted replacement'))

    def test_real_parent_starts_new_schedule(self):
        lane=Path(__file__).resolve().parents[3]
        cfg=configuration();cfg['init_artifact']={'artifact':file_pin(lane/'work/build_n1/inputs/init_artifact.json')}
        self.assertEqual(contract.start(cfg),0)

    def test_store_switch_uses_one_receipt_parameter(self):
        lane=Path(__file__).resolve().parents[3]
        cfg=configuration()
        selected=[]
        for name in ('v6_receipt.json','v7_receipt.json'):
            pin=file_pin(lane/'work/build_n1/inputs'/name)
            value=contract.configure_store(cfg,pin)
            self.assertEqual(value['streams']['vqa'],pin)
            self.assertEqual(value['r1_training']['store_hashes']['vqa'],load(pin['path'])['database']['sha256'])
            value['streams']['vqa']=cfg['streams']['vqa']
            value['r1_training'].pop('store_parameter')
            value['r1_training']['store_hashes']=cfg['r1_training']['store_hashes']
            selected.append(value)
        self.assertEqual(selected[0],selected[1])

    def test_host_empty_root_and_missing_inputs(self):
        from launch_r1.entry import frame_host
        from student_pilot.checkpoint_space import plan
        root=self.root('host')
        with self.assertRaisesRegex(ValueError,'JOB_TMP_REQUIRED'):
            frame_host(configuration(),root/'empty_validated',{'binaries':['python']})
