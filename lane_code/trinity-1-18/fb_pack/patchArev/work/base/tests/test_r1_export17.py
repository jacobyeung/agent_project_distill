"""Native export-only producer and persisted reader refusal twins."""
from copy import deepcopy
from pathlib import Path
import os
import unittest
from student_pilot.p3_provenance import load, file_pin
from student_pilot import r1_persisted as P, r1_handover as H
from launch_r1 import p_export_receipt as E
from tests.test_r2_build_n1 import write
from tests.test_r2_n1fix import handover_fixture
from tests import test_r1_build16 as b16


class Export17(unittest.TestCase):
    setUp = b16.Build16.setUp
    tearDown = b16.Build16.tearDown

    def fixture(self, step=400):
        root=Path(os.environ['R2_PROOFS'])/'export17'/str(step)
        root.mkdir(parents=True,exist_ok=True)
        cfg,p,model,artifact=handover_fixture(root/'producer',step=step,
                                            donor_scales={'h1':{'stop_after_step':600},'lm_lr_scale':.6,'pose_lr_scale':.6})
        value=cfg['r1_training']
        run={k:v for k,v in value['p_run'].items() if k!='checkpoint'}
        return root,cfg,run,model,artifact

    def export_only(self,root,cfg,run):
        r=cfg['r1_training'];r['p_run']=run;r['proof_mode']='q'
        r['handover_receipt']=E.produce(run,cfg['init_artifact']['artifact'],root/'h.json',
                                      job_id='fixture',trainer_commit='fixture')
        receipt=load(r['handover_receipt']['path']);paths={}
        for label,pin in receipt['pins'].items():
            path=root/'persisted'/pin['sha256'];path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(Path(pin['path']).read_bytes());paths[pin['sha256']]=str(path)
        r['persisted_files']=paths
        with P.proof_scope(),P.scope(paths):
            cfg=H.bind_target(cfg,root/'mapping_export.json')
        return cfg

    def test_export_only_admits_only_in_proof_scope(self):
        root,cfg,run,model,artifact=self.fixture()
        cfg=self.export_only(root,cfg,run)
        with P.proof_scope():
            result=P.admission(cfg,weights=True)
            self.assertEqual(result['absolute_resume_step'],400)
            self.assertTrue(result['export_bytes_verified'])
            self.assertFalse(result['unread'])
            self.assertFalse(any(k.startswith('checkpoint') for k in result['verified']))
        with self.assertRaisesRegex(ValueError,'PROOF_MODE_Q_REQUIRED_TRAINING_REFUSED'):
            P.admission(cfg,weights=True)
        from launch_r1.entry import admit
        with self.assertRaisesRegex(ValueError,'EXPORT_ONLY_TRAINING_LAUNCH_REFUSED'):
            admit(cfg)
        write(root/'RESULT.json',{k:v for k,v in result.items() if k!='paths'})

    def test_training_config_refuses(self):
        root,cfg,run,_,_=self.fixture();cfg=self.export_only(root,cfg,run)
        cfg['r1_training']['proof_mode']='train'
        with P.proof_scope(),self.assertRaisesRegex(ValueError,'PROOF_MODE_Q_REQUIRED_TRAINING_REFUSED'):
            P.admission(cfg,weights=True)

    def test_stop_producer_and_reader_refuse(self):
        root,cfg,run,_,_=self.fixture(600)
        with self.assertRaisesRegex(ValueError,'STOP_REQUIRES_CHECKPOINT'):
            E.produce(run,cfg['init_artifact']['artifact'],root/'h.json',job_id='fixture',trainer_commit='fixture')
        r=cfg['r1_training'];receipt=load(r['handover_receipt']['path'])
        receipt.update(schema=E.SCHEMA,stop_step=600,checkpoint_status=E.NO_CHECKPOINT)
        receipt['pins']={k:v for k,v in receipt['pins'].items() if not k.startswith('checkpoint')}
        r.update(p_run=run,proof_mode='q',persisted_files={},handover_receipt=write(root/'bad.json',receipt))
        with P.proof_scope(),self.assertRaisesRegex(ValueError,'STOP_REQUIRES_CHECKPOINT'):
            P.admission(cfg,weights=True)

    def test_altered_shard_refuses(self):
        root,cfg,run,_,_=self.fixture();cfg=self.export_only(root,cfg,run)
        r=cfg['r1_training'];receipt=load(r['handover_receipt']['path'])
        label=next(k for k in receipt['pins'] if k.startswith('export/') and k.endswith('.safetensors'))
        sha=receipt['pins'][label]['sha256']
        Path(r['persisted_files'][sha]).write_bytes(b'changed')
        with P.proof_scope(),self.assertRaisesRegex(ValueError,'HANDOVER_FILE_MISMATCH:export/'):
            P.admission(cfg,weights=True)

    def test_producer_binding_and_job_refuse(self):
        root,cfg,run,_,_=self.fixture()
        with self.assertRaisesRegex(ValueError,'JOB_IDENTITY_REQUIRED'):
            E.produce(run,cfg['init_artifact']['artifact'],root/'h.json',job_id='',trainer_commit='fixture')
        with self.assertRaisesRegex(ValueError,'TRAINER_COMMIT_MISMATCH'):
            E.produce(run,cfg['init_artifact']['artifact'],root/'h.json',job_id='fixture',trainer_commit='other')
        with self.assertRaisesRegex(ValueError,'RUN_KEYS'):
            E.collect(cfg['r1_training']['p_run'],cfg['init_artifact']['artifact'])
        bad=deepcopy(run);bound=load(run['binding']['path']);bound['config_sha256']='0'*64
        bad['binding']=write(root/'bad_binding.json',bound)
        with self.assertRaisesRegex(ValueError,'RUN_BINDING_MISMATCH'):
            E.collect(bad,cfg['init_artifact']['artifact'])

    def test_reader_status_and_closure_refuse(self):
        root,cfg,run,_,_=self.fixture();cfg=self.export_only(root,cfg,run)
        r=cfg['r1_training'];receipt=load(r['handover_receipt']['path'])
        receipt['checkpoint_status']='checkpoint exists'
        r['handover_receipt']=write(root/'bad_status.json',receipt)
        with P.proof_scope(),self.assertRaisesRegex(ValueError,'CHECKPOINT_STATUS_MISMATCH'):
            P.admission(cfg,weights=True)
        receipt['checkpoint_status']=E.NO_CHECKPOINT
        receipt['pins']['extra']=receipt['pins']['artifact']
        r['handover_receipt']=write(root/'bad_status.json',receipt)
        with P.proof_scope(),self.assertRaisesRegex(ValueError,'CLOSURE_MISMATCH'):
            P.admission(cfg,weights=True)

    def test_checkpoint_600_unchanged(self):
        root,cfg,_,_,_=self.fixture(600)
        result=P.admission(cfg,weights=True)
        self.assertEqual(result['absolute_resume_step'],600)
        self.assertEqual(result['receipt']['schema'],'p-handover-v1')
        self.assertTrue(result['unread'])
        write(root/'RESULT.json',{k:v for k,v in result.items() if k!='paths'})
