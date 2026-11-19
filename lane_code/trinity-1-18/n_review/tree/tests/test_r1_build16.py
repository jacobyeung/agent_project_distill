"""Counting admission and relocated persisted-export tests."""
from copy import deepcopy
from pathlib import Path
import json
import os
import unittest
from unittest.mock import patch
from student_pilot.p3_provenance import load, file_pin, pinned
from student_pilot import r1_counting as K, r1_persisted as P
from tests.test_r2_n1fix import handover_fixture
from tests.test_r2_build_n1 import write


class Build16(unittest.TestCase):
    def setUp(self):
        original=Path.open
        root=Path(os.environ['R2_PROOFS'])
        def opened(path,mode='r',*args,**kwargs):
            return original(path,mode.replace('x','w') if path.is_relative_to(root) else mode,*args,**kwargs)
        self.open_patch=patch.object(Path,'open',opened)
        self.open_patch.start()

    def tearDown(self):
        self.open_patch.stop()

    def root(self, name):
        path=Path(os.environ['R2_PROOFS'])/'b16'/name
        path.mkdir(parents=True,exist_ok=True)
        return path

    def test_classifier_and_named_refusals(self):
        cases=[({'target':'count it once'},'counting','PROC',None),
               ({'target':'count each once'},'counting','PROC',None),
               ({'target':'by first appearance: a (left)'},'counting','FS_LIST_REGION','LIST_FORM'),
               ({'target':'first seen in: a'},'counting','FS_LIST','LIST_FORM'),
               ({'count_kind':'total','target':'(middle)'},'totals','TOTALS_REGION','TOTALS_ROW'),
               ({'count_kind':'odd'},'counting','TOTALS','TOTALS_ROW'),
               ({'target':'unknown'},'counting','OTHER','PROCEDURE_REQUIRED')]
        for row,cell,form,error in cases:
            self.assertEqual(K.classify(row)[1],form)
            if error:
                with self.assertRaisesRegex(ValueError,error):K.admit(row,cell)
            else:K.admit(row,cell)
        self.assertEqual(K.classify({'question_type':'first_seen_frame'}),('first_seen','FIRST_SEEN'))
        K.admit({},'direction')

    def test_producer_refuses_without_z(self):
        from student_pilot.r1_population import produce
        from student_pilot.r1_routing import Filters
        L=Path(os.environ.get('R2_LANE_ROOT',Path(__file__).resolve().parents[3]))
        cfg=load(L/'work/build16/inputs/config.json')
        examples=load(L/'work/build16/proofs/census/z_examples.json')
        cfg['remove_files']=cfg['remove_files'][:-1]
        filters=Filters(cfg,cfg['scene_division'])
        root=self.root('without_z')
        member=write(root/'membership.json',dict(schema='r1-source-membership-v1',sources={}))
        admitted=[r for r in examples if not filters.reason(r,'vqa')]
        self.assertTrue(admitted)
        for row in admitted:
            class Reader:
                def count(self,s):return int(s=='vqa')
                def row(self,s,i):return row,{}
            with self.assertRaisesRegex(ValueError,'R1_(TOTALS_ROW|COUNTING_LIST_FORM)_REFUSED'):
                produce(Reader(),cfg['r1_training']['mix'],member,[member],root/'population')

    def fixture(self,step=400):
        root=self.root('persisted_'+str(step))
        cfg,p,model,artifact=handover_fixture(root/'producer',step=step)
        r=cfg['r1_training'];receipt=load(r['handover_receipt']['path'])
        paths={};dest=root/'n';dest.mkdir(exist_ok=True)
        for label,pin in receipt['pins'].items():
            if label.startswith('checkpoint/') and not label.startswith('checkpoint/rng'):
                path=dest/('absent_'+pin['sha256'])
            else:
                if label.startswith('export/'):
                    path=dest/'e'/label.removeprefix('export/')
                elif label=='full_weights':path=dest/'e/full_weights.json'
                else:path=dest/(pin['sha256']+'.json')
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(Path(pin['path']).read_bytes())
            paths[pin['sha256']]=str(path)
        receipt_path=dest/'h.json';receipt_path.write_bytes(Path(r['handover_receipt']['path']).read_bytes())
        r['handover_receipt']=file_pin(receipt_path);r['persisted_files']=paths
        from student_pilot import r1_training as R, r1_handover as H
        with P.scope(paths):
            r['continuation_identity']=R.target_identity(cfg)['config_identity']
            actual=H.donor(cfg,artifact)[2];expected=R.boundary(cfg,step)
        r['handover_mapping']=write(root/'mapping.json',dict(schema='r1-handover-map-v1',
            artifact_sha256=cfg['init_artifact']['artifact']['sha256'],step=step,source=actual,
            target={key:expected[key] for key in actual}))
        return root,cfg,model,artifact

    def test_persisted_400_600_native_reader_and_init(self):
        from student_pilot.carrier_c1_run import init_from_artifact
        from tests.test_carrier_c1 import fixture
        for step in (400,600):
            root,cfg,model,artifact=self.fixture(step)
            result=P.admission(cfg,weights=True)
            self.assertEqual(result['absolute_resume_step'],step)
            self.assertTrue(result['unread'])
            self.assertTrue(all(not v['present'] for v in result['unread'].values()))
            self.assertTrue(result['export_bytes_verified'])
            live=fixture(4,training_mode='final')[0]
            cfg['init_artifact'].update(lm='full',heads=[])
            with P.scope(result['paths']):
                report=init_from_artifact(live,cfg['init_artifact'],part='lm')
            self.assertEqual(report['step'],step)
            write(root/'RESULT.json',{k:v for k,v in result.items() if k!='paths'})

    def test_persisted_forgery_and_mismatch(self):
        root,cfg,model,artifact=self.fixture()
        r=cfg['r1_training'];ap=cfg['init_artifact']['artifact']
        def verify(r=r):return P.verify(r.get('handover_receipt'),r['p_run'],ap,r['persisted_files'],weights=True)
        verify()
        for key in ('config','preparation','checkpoint'):
            bad=deepcopy(r);bad['p_run'][key]=write(root/'forged.json',{'forged':key})
            with self.assertRaisesRegex(ValueError,'HANDOVER_PIN_MISMATCH:'+key):verify(bad)
        for label in ('artifact','config','preparation','checkpoint','heads','full_weights','stream/vqa'):
            receipt=load(r['handover_receipt']['path']);sha=receipt['pins'][label]['sha256']
            bad=deepcopy(r);wrong=root/'wrong.json';wrong.write_text('{}')
            bad['persisted_files'][sha]=str(wrong)
            with self.assertRaisesRegex(ValueError,'HANDOVER_FILE_MISMATCH:'+label):verify(bad)
        bad=deepcopy(r);bad['handover_receipt']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'RECEIPT_UNVERIFIED'):verify(bad)
        bad=deepcopy(r);bad.pop('handover_receipt')
        with self.assertRaisesRegex(ValueError,'RECEIPT_REQUIRED'):verify(bad)
        bad=deepcopy(r);bad['persisted_files']['0'*64]=str(root/'wrong.json')
        with self.assertRaisesRegex(ValueError,'UNBOUND_RELOCATION'):verify(bad)
        bad=deepcopy(r);sha=load(r['handover_receipt']['path'])['pins']['stream/vqa']['sha256']
        bad['persisted_files'][sha]=str(root/'absent')
        with self.assertRaisesRegex(ValueError,'FILE_REQUIRED:stream/vqa'):verify(bad)
        pin=write(root/'scope.json',{})
        with P.scope({pin['sha256']:str(root/'absent')}):
            with self.assertRaises(ValueError):pinned(pin)
        self.assertEqual(pinned(pin),Path(pin['path']))

    def test_proof_default_deny(self):
        from launch_r1.production_proof import run
        result=run({},self.root('empty_proof'))
        self.assertEqual(result['status'],'REFUSE')
        self.assertIn('STAGED_PINS_REQUIRED',result['refusal'])

    def test_final_preparation_handover_binding(self):
        from launch_r1.production_proof import bind_handover
        from student_pilot.carrier_c1_run import identity, init_from_artifact
        from tests.test_carrier_c1 import fixture
        for step in (400,600):
            root,cfg,_,artifact=self.fixture(step)
            cfg['preparation']=cfg['r1_training']['p_run']['preparation']
            cfg['code']=write(root/'fixture_source.json',dict(schema='fixture'))
            # Native preparation changes the stores and config identity before this boundary.
            cfg['preparation_output']=str(root/'new_preparation')
            with P.scope(cfg['r1_training']['persisted_files']):
                final=load(pinned(bind_handover(cfg,root/'bound')))
                receipt=load(pinned(final['preparation']))
                self.assertEqual(receipt['r1_training'],final['r1_training'])
                self.assertEqual(receipt['config_sha256'],identity(final))
                self.assertEqual(P.admission(final)['absolute_resume_step'],step)
                bad=deepcopy(cfg);bad['lm_lr_scale']=2.0
                with self.assertRaisesRegex(ValueError,'LR_SCHEDULE_MISMATCH'):
                    bind_handover(bad,root/'bad_bound')
                live=fixture(4,training_mode='final')[0]
                report=init_from_artifact(live,dict(final['init_artifact'],lm='full',
                    heads=['pose','frame_embeddings','depth']),part='heads')
                self.assertGreater(report['head_tensors'],0)

    def test_proof_input_refusals(self):
        from launch_r1.production_proof import run
        root=self.root('proof_inputs')
        card=write(root/'card.json',{})
        cfg=write(root/'cfg.json',dict(r1_training=dict(mix=card)))
        request=dict(config=cfg,staged_pins=[cfg,card])
        result=run(request,root/'out')
        self.assertIn('COUNTING_ADMISSION_REQUIRED',result['refusal'])
        card=write(root/'card.json',dict(counting_admission='procedure_only_v1'))
        cfg=write(root/'cfg.json',dict(r1_training=dict(mix=card)))
        request.update(config=cfg,staged_pins=[cfg,card])
        self.assertIn('NATIVE_ROUTING_REQUIRED',run(request,root/'out')['refusal'])
        cfg=write(root/'cfg.json',dict(s1_routing={'fixture':True},r1_training=dict(mix=card,routing_inputs={'fixture':True})))
        room=write(root/'room.json',dict(complete=False))
        request.update(config=cfg,staged_pins=[cfg,card,room],room_audit=room)
        self.assertIn('ROOM_AUTHORITY_INCOMPLETE',run(request,root/'out')['refusal'])
        request['staged_pins'][0]['sha256']='f'*64
        self.assertIn('Missing or changed pinned input',run(request,root/'out')['refusal'])

    def test_native_first_resumed_batch(self):
        from types import SimpleNamespace
        import sqlite3
        from student_pilot import carrier_c1_run as C
        from student_pilot import r1_mix as M
        from tests.test_carrier_c1 import fixture
        from launch_r1.production_proof import forward
        root,cfg,donor,artifact=self.fixture()
        receipt=dict(streams={},training_mode='final',r1_training=cfg['r1_training'])
        card,idx,_=M.validate_binding(cfg['r2_sampling'])
        connection=sqlite3.connect(':memory:')
        connection.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
        for cell in card['cells']:
            stream=cell['stream'];n=len(idx['cells'][cell['type']])
            db=root/(stream+'.sqlite')
            connection.execute('CREATE TABLE IF NOT EXISTS marker(x)')
            # A tiny native database contains only the first resumed offsets.
            plan=next(M.plans(cfg['r2_sampling'],{c['stream']:len(idx['cells'][c['type']]) for c in card['cells']},1000,start_step=400))
            selected=sorted({i for s,values in plan if s==stream for i in values})
            target='<think>The printed response gives the displacement.</think><answer>right</answer>'
            for i in selected:
                row=dict(qid=stream+'_'+str(i),question_type='camera_displacement' if stream=='routing' else 'object_rel_direction_easy',target=target)
                connection.execute('INSERT OR REPLACE INTO rows VALUES(?,?,?)',(i,json.dumps(row),'{}'))
            connection.commit();db.write_bytes(connection.serialize())
            receipt['streams'][stream]=dict(database=file_pin(db),count=n)
        connection.close()
        model,batch,targets=fixture(4,training_mode='final')
        initialized=deepcopy(cfg['init_artifact']);initialized.update(lm='full',heads=[])
        with P.scope(cfg['r1_training']['persisted_files']):
            model.init_report=C.init_from_artifact(model,initialized,part='lm')
        cfg['preparation']=write(root/'native_preparation.json',receipt)
        model.r1_training=cfg['r1_training']
        processor=SimpleNamespace(tokenizer=SimpleNamespace(decode=lambda ids:'x'))
        def encode(processor,row,target,stream,*args,**kwargs):
            return dict(batch),targets if stream=='pose' else None,dict(qid=row['qid'])
        def routing_encode(processor,row,*args,**kwargs):
            return dict(batch),dict(qid=row['qid'])
        # Host metadata/RGB/tokenization and pretrained weights stand in.
        # Native Rows.row/get, fetch, row checks, resumed sampler and full model forward execute.
        with patch.object(C,'validate'),patch.object(C,'prepared',return_value=(receipt,{})),\
             patch.object(C,'processor_for_receipt',return_value=processor),\
             patch.object(C,'load_model',return_value=model),\
             patch.object(C.data,'encode',side_effect=encode),patch.object(C.routing,'encode',side_effect=routing_encode):
            value=forward(cfg,root,400)
        self.assertEqual(value['ranks'],[0,1,2,3])
        records=load(value['records']['path'])['records']
        self.assertEqual([(r['stream'],r['index']) for r in records],
                         [(s,i) for s,indices in plan for i in indices])
        self.assertEqual({s:v['count'] for s,v in value['loss_by_stream'].items()},dict(pose=64,vqa=128,routing=64,pointing=32))
        write(root/'FORWARD.json',dict(value,standins='Synthetic host metadata, RGB/tokenizer encoding, and tiny native weights. This does not certify the complete production mode.'))

    def test_persisted_metadata_only_and_closure_refusals(self):
        root,cfg,model,artifact=self.fixture(600)
        r=cfg['r1_training'];receipt=load(r['handover_receipt']['path'])
        ap=cfg['init_artifact']['artifact']
        paths=dict(r['persisted_files'])
        for label,pin in receipt['pins'].items():
            if label in ('heads','full_weights') or label.startswith('export/'):
                paths[pin['sha256']]=str(root/('absent_'+pin['sha256']))
        result=P.verify(r['handover_receipt'],r['p_run'],ap,paths)
        self.assertFalse(result['export_bytes_verified'])
        self.assertIn('heads',result['absent'])
        with self.assertRaisesRegex(ValueError,'FILE_REQUIRED:heads'):
            P.verify(r['handover_receipt'],r['p_run'],ap,paths,weights=True)
        variants=[('schema',lambda x:x.update(schema='wrong'),'RECEIPT_INVALID'),
                  ('step',lambda x:x.update(step=400),'RUN_BINDING_MISMATCH'),
                  ('commit',lambda x:x.update(trainer_commit='wrong'),'RUN_BINDING_MISMATCH'),
                  ('heads',lambda x:x['pins']['heads'].update(sha256='f'*64),'CLOSURE_MISMATCH:heads')]
        state=next(k for k in receipt['pins'] if k.startswith('checkpoint/') and not k.startswith('checkpoint/rng'))
        variants.append(('state',lambda x:x['pins'][state].update(sha256='e'*64),'CLOSURE_MISMATCH:'+state))
        for name,change,reason in variants:
            bad=deepcopy(receipt);change(bad)
            pin=write(root/'changed_h.json',bad)
            allowed={p['sha256'] for p in bad['pins'].values()}
            relocated={k:v for k,v in r['persisted_files'].items() if k in allowed}
            with self.assertRaisesRegex(ValueError,reason):P.verify(pin,r['p_run'],ap,relocated)
        with self.assertRaisesRegex(ValueError,'RUN_KEYS'):
            P.verify(r['handover_receipt'],{},ap,r['persisted_files'])
