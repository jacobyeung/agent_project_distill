"""Donor opener policy and native export-to-witness CPU proofs."""
from copy import deepcopy
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch
import unittest
import torch
from student_pilot import r1_handover as H, r1_training as R, r2_openers as O
from student_pilot import carrier_c1_run as run
from student_pilot.p3_provenance import load, file_pin
from launch_r1 import p_opener_witness as W
from tests.test_r2_n1fix import handover_fixture
from tests import test_r2_n1fix as prior
from tests.test_r2_build_n1 import configuration, write
from tests import test_carrier_c1 as tiny


def kit_config():
    return load(Path(__file__).resolve().parents[2]/'build15/inputs/kit_config.json')


class Build15(unittest.TestCase):
    root = prior.N1Fix.root

    def test_boundary_policy(self):
        cfg=configuration();cfg.pop('init_artifact',None);cfg['routing_opener_init']='keep'
        for value in (None,'reset','keep','historical-policy'):
            p=deepcopy(cfg)
            if value is None:p.pop('routing_opener_init',None)
            else:p['routing_opener_init']=value
            H.compare_configs(p,cfg)
        for value in ('reset','unknown'):
            n=deepcopy(cfg)
            if value is None:n.pop('routing_opener_init',None)
            else:n['routing_opener_init']=value
            with self.assertRaisesRegex(ValueError,'P_EXPORT_ROUTING_OPENER_KEEP_REQUIRED'):H.compare_configs(cfg,n)
        parent=kit_config();parent['routing_opener_init']='reset'
        self.assertEqual(parent['init_artifact']['artifact']['sha256'],R.PARENT)
        O.preparation(parent)
        self.assertEqual(O.policy(parent),'reset')

    def test_export_witness_and_native_keep(self):
        root=self.root('b15_witness')
        from tokenizers import Tokenizer, models
        from transformers import PreTrainedTokenizerFast
        tokenizer=PreTrainedTokenizerFast(tokenizer_object=Tokenizer(models.WordLevel(
            {**{str(i):i for i in range(16)},'<unk>':16},unk_token='<unk>')),unk_token='<unk>')
        tokenizer.save_pretrained(root/'model')
        def processor_boundary(path):
            return SimpleNamespace(tokenizer=PreTrainedTokenizerFast.from_pretrained(path,local_files_only=True))
        with patch.object(run,'processor_for',processor_boundary):
            processor=run.processor_for_receipt({'root':str(root/'model')},{'training_mode':'final'})
        opener=processor._routing_tokens['ids']['<move']
        native=tiny.fixture
        def fixture(*args,**kwargs):
            result=native(*args,**kwargs);model=result[0]
            model.routing_vocabulary=O.vocabulary(processor)
            with torch.no_grad():
                model.get_input_embeddings().weight[opener].fill_(3)
                model.get_output_embeddings().weight[opener].fill_(5)
            return result
        def metadata_write(path,value):
            if path==root/'model.json':
                value['files'].update({p.name:file_pin(p)['sha256'] for p in (root/'model').glob('*.json')})
            return write(path,value)
        parent=kit_config()['init_artifact']
        parent['artifact']=file_pin(Path(__file__).resolve().parents[2]/'n1fix2/inputs/init_artifact.json')
        with patch.object(tiny,'fixture',fixture),patch.object(prior,'write',metadata_write):
            cfg,p,model,artifact=handover_fixture(root,scales={'r2_identity':kit_config()['r2_identity']},
                donor_scales={'routing_opener_init':'reset','lm_lr_scale':.6,'pose_lr_scale':.6,'init_artifact':parent})
        cfg['init_artifact'].update(lm='full',heads=[])
        # These fixture-only boundary fields do not change the continuation identity.
        cfg['r1_training']['continuation_identity']=R.target_identity(cfg)['config_identity']
        actual=H.donor(cfg,artifact)[2];expected=R.boundary(cfg,artifact['step'])
        cfg['r1_training']['handover_mapping']=write(root/'native_to_cells.json',dict(schema='r1-handover-map-v1',
            artifact_sha256=cfg['init_artifact']['artifact']['sha256'],step=artifact['step'],source=actual,
            target={key:expected[key] for key in actual}))
        with patch.object(W,'write',write),patch.object(run,'processor_for',processor_boundary):
            cfg['routing_vocabulary']=W.produce(cfg,root/'v.json')
            config_pin=write(root/'witness_config.json',cfg)
            self.assertEqual(W.main(['--config',config_pin['path'],'--output',str(root/'v.json')]),cfg['routing_vocabulary'])
        cfg['r1_training']['continuation_identity']=R.target_identity(cfg)['config_identity']
        expected=R.boundary(cfg,artifact['step'])
        cfg['r1_training']['handover_mapping']=write(root/'native_to_cells.json',dict(schema='r1-handover-map-v1',
            artifact_sha256=cfg['init_artifact']['artifact']['sha256'],step=artifact['step'],source=actual,
            target={key:expected[key] for key in actual}))
        witness=load(cfg['routing_vocabulary']['path'])
        self.assertEqual(witness['artifact_sha256'],cfg['init_artifact']['artifact']['sha256'])
        self.assertEqual(witness['lineage_sha256'],R.PARENT)
        self.assertNotIn('routing_vocabulary',artifact)
        self.assertEqual(witness['tokens'],processor._routing_tokens)
        O.preparation(cfg)
        live=native(4,training_mode='final')[0]
        live.init_report=run.init_from_artifact(live,cfg['init_artifact'],part='lm')
        before=[live.get_input_embeddings().weight[opener].detach().clone(),live.get_output_embeddings().weight[opener].detach().clone()]
        self.assertEqual(O.initialize(live,processor,cfg),'kept')
        self.assertTrue(torch.equal(before[0],live.get_input_embeddings().weight[opener]))
        self.assertTrue(torch.equal(before[1],live.get_output_embeddings().weight[opener]))
        wrong_lineage=deepcopy(cfg);wrong_lineage['r2_identity']['init']['step']=545
        with self.assertRaisesRegex(ValueError,'OPENER_LINEAGE_MISMATCH'):W.produce(wrong_lineage,root/'unused.json')
        def rebind(n):
            n['r1_training']['continuation_identity']=R.target_identity(n)['config_identity']
            expected=R.boundary(n,artifact['step'])
            n['r1_training']['handover_mapping']=write(root/'case_map.json',dict(schema='r1-handover-map-v1',
                artifact_sha256=n['init_artifact']['artifact']['sha256'],step=artifact['step'],source=actual,
                target={key:expected[key] for key in actual}))
            return n
        refusals={}
        for policy in ('reset',None):
            bad=deepcopy(cfg)
            if policy is None:bad.pop('routing_opener_init')
            else:bad['routing_opener_init']=policy
            for name,call in [('compare',lambda:H.compare_configs(p,bad)),('preparation',lambda:O.preparation(bad)),
                    ('initialize',lambda:O.initialize(live,processor,bad)),('start',lambda:R.start(bad)),('producer',lambda:W.produce(bad,root/'unused.json'))]:
                with self.assertRaisesRegex(ValueError,'P_EXPORT_ROUTING_OPENER_KEEP_REQUIRED') as caught:call()
                refusals[name+'/'+str(policy)]=str(caught.exception)
        for key in ('artifact_sha256','lineage_sha256','vocabulary_sha256','tokens'):
            wrong=dict(witness);wrong[key]='f'*64 if key!='tokens' else {'ids':{'<move':6}}
            bad=rebind(dict(deepcopy(cfg),routing_vocabulary=write(root/'wrong.json',wrong)))
            with self.assertRaisesRegex(ValueError,'vocabulary'):O.initialize(live,processor,bad)
            if key in ('artifact_sha256','lineage_sha256'):
                with self.assertRaisesRegex(ValueError,'vocabulary'):O.preparation(bad)
        bad=deepcopy(cfg);bad.pop('routing_vocabulary');rebind(bad)
        with self.assertRaisesRegex(ValueError,'Missing routing vocabulary'):O.preparation(bad)
        with self.assertRaisesRegex(ValueError,'Missing routing vocabulary'):O.initialize(live,processor,bad)
        with self.assertRaisesRegex(ValueError,'full warm'):W.produce(dict(cfg,init_artifact={'artifact':cfg['init_artifact']['artifact']}),root/'unused.json')
        with self.assertRaisesRegex(ValueError,'REQUIRES_DONOR_EXPORT'):W.produce(kit_config(),root/'unused.json')
        write(root/'RESULT.json',dict(witness=cfg['routing_vocabulary'],artifact=cfg['init_artifact']['artifact'],
            lineage_sha256=R.PARENT,input_row_kept=True,output_row_kept=True,refusals=refusals,
            stand_ins='Tiny native CPU model and tokenizer replace pretrained GPU weights; local collectives replace distributed GPU publication. Native sealed export, checkpoint, receipt, witness producer, LM artifact loader, preparation and opener initializer execute.'))

    def test_tokenizer_metadata_refusals(self):
        root=self.root('b15_tokenizer')
        model=root/'model';model.mkdir(exist_ok=True)
        files={name:write(model/name,{})['sha256'] for name in ('config.json','tokenizer.json','tokenizer_config.json')}
        def source(pins):
            manifest=write(root/'model.json',dict(root=str(model),files=pins))
            return dict(preparation=write(root/'prep.json',dict(model=manifest)))
        with self.assertRaisesRegex(ValueError,'TOKENIZER_FILES_REQUIRED'):W.prepared_vocabulary(source({}))
        write(model/'unbound.json',{})
        with self.assertRaisesRegex(ValueError,'TOKENIZER_FILE_UNBOUND'):W.prepared_vocabulary(source(files))
        files['unbound.json']='f'*64
        with self.assertRaisesRegex(ValueError,'Missing or changed pinned input'):W.prepared_vocabulary(source(files))
