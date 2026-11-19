"""Native producer/reader and default-deny handover regressions."""
from copy import deepcopy
from pathlib import Path
import json,os,sqlite3,unittest
from unittest.mock import patch
import torch
from student_pilot import carrier_c1_run as C,r1_handover as H,r1_training as R,row_text_audit as A
from student_pilot.p3_provenance import file_pin,load
from tests.test_r2_n1fix import handover_fixture,write
from tests import test_r2_n1fix as prior
from launch_r1 import p_handover_receipt as P


class Build12(unittest.TestCase):
    root=prior.N1Fix.root

    def test_default_deny_and_native_meta(self):
        root=self.root('b12_topology');cfg,p,model,a=handover_fixture(root/'honest')
        self.assertEqual(R.start(cfg),200)
        meta=H.donor_meta_model(p)
        self.assertTrue(all(v.device.type=='meta' for v in meta.parameters()))
        tables=H.verify_trainable_groups(cfg,model)
        self.assertEqual(tables['source'],tables['target'])
        cases={'depth_enabled':False,'align':{'cam':{'layer':'final','weight':1},'patch':None},
               'camera':{'trunk_depth':6},'unknown_future_knob':True,'unknown_future_null':None}
        refusals={}
        for key,value in cases.items():
            bad,_,native,export=handover_fixture(root/('P_'+key),donor_scales={
                'lm_lr_scale':cfg['lm_lr_scale'],'pose_lr_scale':cfg['pose_lr_scale'],key:value})
            for fn,args in ((H.progress,(bad,export)),(H.verify_trainable_groups,(bad,native))):
                with self.assertRaisesRegex(ValueError,'P_EXPORT_CONFIG_DIFFERENCE:'+key):fn(*args)
            refusals[key]='P_EXPORT_CONFIG_DIFFERENCE:'+key
        # P's group builder must observe its own depth-disabled topology.
        disabled=deepcopy(p);prep=load(disabled['preparation']['path'])
        disabled['depth_enabled']=False
        other=H.trainable_group_table(disabled,H.donor_meta_model(disabled))
        self.assertNotEqual(other,tables['source'])
        self.assertNotIn('encoder_copy',[g['name'] for g in other['groups']])
        write(root/'RESULT.json',dict(refusals=refusals,tables=tables,disabled=other,
            step=R.start(cfg),meta_parameters=True))

    def test_trainer_hook_y5(self):
        from tests.test_carrier_c1_run import RunnerTests
        with patch.object(H,'verify_trainable_groups',wraps=H.verify_trainable_groups) as hook:
            RunnerTests().test_train_enables_native_decoder_checkpointing_after_eval_load()
        hook.assert_called_once()
        self.assertIsNone(H.verify_trainable_groups({},object()))

    def test_receipt_and_forged_preparation_complete(self):
        root=self.root('b12_receipt');cfg,p,model,a=handover_fixture(root/'producer')
        r=cfg['r1_training'];receipt=load(r['handover_receipt']['path'])
        self.assertTrue(any(k.startswith('checkpoint/rng') for k in receipt['pins']))
        self.assertTrue(any(k.startswith('export/model-') for k in receipt['pins']))
        self.assertEqual(P.verify_receipt(r['handover_receipt'],r['p_run'],cfg['init_artifact']['artifact']),receipt)
        absent=deepcopy(cfg);absent['r1_training'].pop('handover_receipt')
        with self.assertRaisesRegex(ValueError,'HANDOVER_RECEIPT_REQUIRED'):H.donor(absent,a)
        wrong=deepcopy(cfg);wrong['r1_training']['handover_receipt']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'HANDOVER_RECEIPT_UNVERIFIED'):H.donor(wrong,a)
        forged=deepcopy(cfg);pins=forged['r1_training']['p_run']
        prep=load(pins['preparation']['path']);prep['streams']['vqa'].update(count=127,
            indices=write(root/'forged_indices.json',list(range(1,128))))
        prep_pin=write(root/'forged_preparation.json',prep)
        source=deepcopy(p);source['preparation']=prep_pin
        bound=load(pins['binding']['path']);bound['preparation']=prep_pin
        complete=load(pins['checkpoint']['path']);complete['binding']=bound
        pins.update(config=write(root/'forged_config.json',source),preparation=prep_pin,
            binding=write(root/'forged_binding.json',bound),checkpoint=write(root/'forged_complete.json',complete))
        with self.assertRaisesRegex(ValueError,'HANDOVER_PIN_MISMATCH:config'):H.donor(forged,a)
        write(root/'RESULT.json',dict(receipt=r['handover_receipt'],closure=receipt['pins'],
            forged_preparation_and_complete='P_EXPORT_HANDOVER_PIN_MISMATCH:config',
            trusted_ledger='Operator records P allocation/job id, trainer commit, receipt path and sha256 from P job output.'))

    def test_receipt_refusal_edges(self):
        root=self.root('b12_receipt_edges');cfg,p,m,a=handover_fixture(root/'producer')
        r=cfg['r1_training'];pins=r['p_run'];ap=cfg['init_artifact']['artifact']
        with self.assertRaisesRegex(ValueError,'RUN_KEYS'):P.collect({},ap)
        for job,commit in (('', 'fixture'),('job','')):
            with self.assertRaisesRegex(ValueError,'JOB_IDENTITY_REQUIRED'):P.produce(pins,ap,root/'out.json',job_id=job,trainer_commit=commit)
        with self.assertRaisesRegex(ValueError,'TRAINER_COMMIT_MISMATCH'):P.produce(pins,ap,root/'out.json',job_id='job',trainer_commit='wrong')
        receipt=load(r['handover_receipt']['path'])
        bad=deepcopy(receipt);bad['schema']='wrong'
        with self.assertRaisesRegex(ValueError,'RECEIPT_INVALID'):P.verify_receipt(write(root/'bad.json',bad),pins,ap)
        bad=deepcopy(receipt);bad['pins']['heads']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'CLOSURE_MISMATCH'):P.verify_receipt(write(root/'bad.json',bad),pins,ap)
        with patch.dict(os.environ,SLURM_JOB_ID='cpu-wrapper'),patch.object(P,'write',write):
            pin=P.main(['--run-pins',str(write(root/'pins.json',pins)['path']),'--artifact',ap['path'],
                '--output',str(root/'cli.json'),'--trainer-commit','fixture'])
        self.assertEqual(load(pin['path'])['job_id'],'cpu-wrapper')

    def test_receipt_complete_closure_errors(self):
        root=self.root('b12_closure');cfg,p,m,a=handover_fixture(root/'producer')
        pins=cfg['r1_training']['p_run'];ap=cfg['init_artifact']['artifact']
        complete=load(pins['checkpoint']['path'])
        for label,change,reason in (
            ('step',lambda x:x.update(step=199),'RUN_BINDING_MISMATCH'),
            ('empty',lambda x:x.update(files={}), 'CHECKPOINT_FILES_REQUIRED'),
            ('escape',lambda x:x['files'].update({'../escape':{'sha256':'0'*64}}),'PATH_ESCAPE'),
            ('hash',lambda x:next(iter(x['files'].values())).update(sha256='0'*64),'FILE_MISMATCH')):
            bad=deepcopy(complete);change(bad)
            variant=dict(pins,checkpoint=write(root/('producer/checkpoint/'+label+'.json'),bad))
            with self.assertRaisesRegex(ValueError,reason):P.collect(variant,ap)
        for label,change,reason in (
            ('streams',lambda x:x['streams'].pop('vqa'),'STREAMS_MISMATCH'),
            ('receipt',lambda x:x['streams']['vqa'].update(receipt={}), 'STREAM_RECEIPT_MISMATCH')):
            prep=load(pins['preparation']['path']);change(prep)
            pp=write(root/(label+'_prep.json'),prep)
            source=deepcopy(p);source['preparation']=pp
            bound=load(pins['binding']['path']);bound['preparation']=pp
            cp=deepcopy(complete);cp['binding']=bound
            variant=dict(config=write(root/(label+'_cfg.json'),source),preparation=pp,
                binding=write(root/(label+'_bound.json'),bound),
                checkpoint=write(root/('producer/checkpoint/'+label+'.json'),cp))
            with self.assertRaisesRegex(ValueError,reason):P.collect(variant,ap)

    def test_meta_topology_refusal_and_initializer(self):
        root=self.root('b12_meta_edges');cfg,p,m,a=handover_fixture(root/'producer')
        bad=deepcopy(p);bad['preparation']=write(root/'missing.json',{})
        with self.assertRaisesRegex(ValueError,'TOPOLOGY_METADATA_UNVERIFIED'):H.donor_meta_model(bad)
        with self.assertRaisesRegex(ValueError,'TOPOLOGY_UNSUPPORTED'):H.donor_meta_model(dict(p,mdg={'unknown':True}))
        aligned=H.donor_meta_model(dict(p,align={'cam':{'layer':'final','weight':1},'patch':None}))
        self.assertTrue(hasattr(aligned.auxiliary_heads.pose,'projector'))
        depth_pin=write(root/'depth.json',{'synthetic_topology_only':True})
        frozen=H.donor_meta_model(dict(p,depth_init=depth_pin))
        self.assertTrue(all(not v.requires_grad for v in frozen.auxiliary_heads.depth.model.visual.parameters()))
        c,_,_,artifact=handover_fixture(root/'sampler',donor_scales={
            'lm_lr_scale':.6,'pose_lr_scale':.6,'r1_training':{'unsupported_sampler':True}})
        with self.assertRaisesRegex(ValueError,'SAMPLER_UNSUPPORTED'):H.progress(c,artifact)
        row=dict(ground_record={'geometry_mode':'tower'})
        self.assertIn('tower_scale_provenance_not_from_head',A.reasons(row))
        with self.assertRaisesRegex(ValueError,'tower_scale_provenance_not_from_head'):A.check(row,'vqa')

    def test_parent_544_and_P_initialized_from_parent(self):
        lane=Path(os.environ['R2_FIXTURES']).parent
        source=load(lane/'work/n1fix2/inputs/config.json')
        parent=dict(source['init_artifact']['artifact'],path=str(lane/'work/n1fix2/inputs/init_artifact.json'))
        self.assertEqual(file_pin(parent['path']),parent)
        source['init_artifact']['artifact']=parent
        self.assertEqual(parent['sha256'],'1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef')
        self.assertFalse(load(parent['path']).get('head_init'))
        self.assertEqual(R.start(source),0)
        self.assertIsNone(H.verify_trainable_groups(source,object()))
        cfg,p,model,a=handover_fixture(self.root('b12_parent'),donor_scales={
            'init_artifact':source['init_artifact'],'lm_lr_scale':.6,'pose_lr_scale':.6})
        self.assertEqual(H.progress(cfg,a)['step'],200)
        self.assertEqual(R.start(cfg),200)

    def test_confusable_class_independent_reader(self):
        variants=['not ѕeen','NOТ SEEN','box unаvailable','tower_scale_rule'.replace('i','і'),
                  'tower_sсale_rule','ΝOT SEEN','NOΤ SEEN','nօt seen','new\u0501word']
        for text in variants:
            row={'target':'<think>'+text+'</think>\n1'}
            self.assertTrue(A.reasons(row))
            with patch.object(A,'reasons',return_value=[]),patch.object(A,'normalized_text',return_value=''),patch.object(A,'PATTERNS',{}):
                with self.assertRaisesRegex(ValueError,'rule_only_text'):A.check(row,'vqa')

    def test_fixed_constants_repin_and_tamper(self):
        from tests.test_carrier_c1 import fixture
        from tests.test_carrier_c1_run import RunnerTests
        root=self.root('b12_constants');model,_,_=fixture(4);dest=root/'modern'
        if not dest.exists():
            with RunnerTests().local_collectives(),patch('student_pilot.fsdp_training.publication_state',return_value=model.state_dict()):
                C.export(dest,model,model,dict(base_identity='fixture',trace_program_version='3.13'),200)
        a=load(dest/'artifact.json');C.load_artifact(model,file_pin(dest/'artifact.json'))
        state=torch.load(a['heads']['path'],weights_only=True)
        state['depth_readout.stencil']*=2
        torch.save(state,root/'changed.pt')
        bad=dict(a,heads=file_pin(root/'changed.pt'))
        with self.assertRaisesRegex(ValueError,'FIXED_READOUT_CONSTANT_MISMATCH:depth_readout.stencil'):
            C.load_artifact(model,write(root/'changed.json',bad))
        bad['heads']['sha256']=a['heads']['sha256']
        with self.assertRaisesRegex(ValueError,'Missing or changed pinned input'):
            C.load_artifact(model,write(root/'changed.json',bad))

    def test_batch_integrity_errors_raise(self):
        from student_pilot import carrier_c1_batch_decode as B,carrier_c1_decode as D
        # The existing native decoder fixture supplies model/prompt setup.
        from tests.test_batched_routed_decode import fixture
        model,p,batch=fixture()
        for prompts in (batch,[batch,batch]):
            with patch.object(B.Row,'step',side_effect=ValueError('heading threshold differs from artifact')):
                with self.assertRaisesRegex(ValueError,'heading threshold differs from artifact'):
                    D.generate(model,p,prompts)

    def test_native_cli_and_parity_loader(self):
        import runpy,sys
        from types import SimpleNamespace
        from student_pilot import live_parity_adapter as adapter
        root=self.root('b12_cli_loader');cfg,p,model,a=handover_fixture(root/'producer')
        r=cfg['r1_training'];ap=cfg['init_artifact']['artifact']
        write(root/'run_pins.json',r['p_run'])
        native_open=Path.open
        def overwrite(path,mode='r',*args,**kwargs):
            return native_open(path,mode.replace('x','w') if path.is_relative_to(root) else mode,*args,**kwargs)
        with patch.dict(os.environ,SLURM_JOB_ID='cpu-cli'),patch.object(Path,'open',overwrite),patch.object(sys,'argv',[
                str(P.__file__),'--run-pins',str(root/'run_pins.json'),'--artifact',ap['path'],
                '--output',str(root/'entry.json'),'--trainer-commit','fixture']):
            runpy.run_path(str(P.__file__),run_name='__main__')
        prep=load(p['preparation']['path'])
        write(root/'generation/generation_config.json',dict(eos_token_id=1,pad_token_id=0))
        inputs=dict(carrier_config=r['p_run']['config'],carrier_manifest=prep['model'],
                    carrier_receipt=p['preparation'],artifact=ap,hf_checkpoint=str(root/'generation'),audit_dir=str(root))
        with patch.object(C,'processor_for_receipt',return_value=SimpleNamespace()),patch.object(C,'load_model',return_value=model):
            loaded,_=adapter.load(inputs,'cpu')
        self.assertEqual(loaded.readout_evaluation_config,p)

    def test_preserved_legacy_entry_refusals(self):
        from evalpath import runtime,heldout_loss
        for fn,args in ((runtime.load_model,('routed',{})),(heldout_loss.run_worker,({},0,4)),
                        (C.inference,({},None,torch.device('cpu')))):
            with self.assertRaisesRegex(ValueError,'Legacy reader has no authenticated R2 bank adapter'):fn(*args)
