"""Independent regression inputs for the confirmation findings."""
from copy import deepcopy
import json, sqlite3, unittest
from unittest.mock import patch
from student_pilot import r1_training as contract, r1_handover as handover
from student_pilot.p3_provenance import load
from tests import test_r2_n1fix as prior
from tests.test_r2_n1fix import handover_fixture, write


class Confirmation(unittest.TestCase):
    root=prior.N1Fix.root

    def test_optimizer_config_scales(self):
        cfg,_,_,artifact=handover_fixture(self.root('scales_absent'),donor_scales={})
        cfg.update(lm_lr_scale=0.6,pose_lr_scale=0.6)
        with self.assertRaisesRegex(ValueError,'LR_SCHEDULE_MISMATCH:lm_lr_scale'):
            handover.progress(cfg,artifact)
        for key in ('lm_lr_scale','pose_lr_scale'):
            cfg,_,_,artifact=handover_fixture(self.root('scales_'+key),{key:1.0})
            cfg[key]=0.6
            with self.assertRaisesRegex(ValueError,'LR_SCHEDULE_MISMATCH:'+key):
                handover.progress(cfg,artifact)
            self.assertEqual(handover.optimizer_contract({**load(cfg['r1_training']['p_run']['config']['path']),key:1.0})[key],1.0)

    def test_target_forgery(self):
        cfg,_,_,artifact=handover_fixture(self.root('target'))
        mapping=load(cfg['r1_training']['handover_mapping']['path'])
        for fields in ({'continuation_identity':'7'*64}, {'store_hashes':{'vqa':'8'*64,'pose':'9'*64}},
                       {'continuation_identity':'7'*64,'store_hashes':{'vqa':'8'*64,'pose':'9'*64}}):
            bad=deepcopy(cfg);bad['r1_training'].update(fields)
            forged=deepcopy(mapping)
            forged['target'].update(config_identity=bad['r1_training']['continuation_identity'],stores=bad['r1_training']['store_hashes'])
            bad['r1_training']['handover_mapping']=write(self.root('target')/'forged_mapping.json',forged)
            with self.assertRaisesRegex(ValueError,'P_EXPORT_TARGET_'):contract.start(bad)

    def test_H2_binding_config(self):
        root=self.root('h2');cfg,_,_,artifact=handover_fixture(root)
        bound=load(cfg['r1_training']['p_run']['binding']['path']);bound['config_sha256']='2'*64
        cfg['r1_training']['p_run']['binding']=write(root/'wrong_binding.json',bound)
        cfg['r1_training']['p_run']['checkpoint']=write(root/'matching_complete.json',dict(schema='c1-checkpoint-v1',step=200,binding=bound))
        with self.assertRaisesRegex(ValueError,'RUN_BINDING_MISMATCH'):handover.donor(cfg,artifact)

    def test_H6_artifact_config(self):
        cfg,_,_,artifact=handover_fixture(self.root('h6'))
        with self.assertRaisesRegex(ValueError,'CONFIG_MISMATCH'):
            handover.donor(cfg,dict(artifact,config_sha256='6'*64))

    def test_preparation_checkpoint_anchor(self):
        root=self.root('preparation');cfg,p,_,artifact=handover_fixture(root)
        original=handover.sealed_identity(p)
        prep=load(cfg['r1_training']['p_run']['preparation']['path'])
        prep['streams']['vqa'].update(count=127,indices=write(root/'forged_indices.json',list(range(1,128))))
        pin=write(root/'forged_preparation.json',prep);p['preparation']=pin
        bound=load(cfg['r1_training']['p_run']['binding']['path']);bound['preparation']=pin
        cfg['r1_training']['p_run'].update(config=write(root/'forged_config.json',p),preparation=pin,binding=write(root/'forged_binding.json',bound))
        self.assertNotEqual(handover.sealed_identity(p),original)
        with self.assertRaisesRegex(ValueError,'CHECKPOINT_BINDING_MISMATCH'):handover.donor(cfg,artifact)

    def test_unicode_and_independent_reader(self):
        from student_pilot import row_text_audit as audit, carrier_c1_run as run
        chars=[chr(c) for c in (0x200b,0x200c,0x200d,0x2060,0xfeff,0xad,0x180e,0x2061,0x2062,0x2063,0x2064,0x34f,0x200e,0x200f,0x202a,0x202e,0x2066,0x2069)]
        variants=[s for c in chars for s in ('not'+c+'seen','not '+c+'seen','box'+c+'unavailable','no'+c+'t seen','un'+c+'resolved','heading'+c+'unavailable')]
        variants += ['heading'+s+'unavailable' for s in ('\u00a0','\t','  ')]
        self.assertEqual(len(variants),111)
        reader=run.Rows(dict(streams={},r1_training={'schema':'r1-training-v1'}),None)
        conn=sqlite3.connect(':memory:');reader.connections['vqa']=conn
        conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
        for text in variants:
            row=dict(target='<think>'+text+'</think>\n1')
            self.assertTrue(audit.reasons(row),text)
            conn.execute('INSERT OR REPLACE INTO rows VALUES(0,?,?)',(json.dumps(row),'{}'))
            with patch.object(audit,'reasons',return_value=[]),patch.object(audit,'PATTERNS',{}):
                with self.assertRaisesRegex(ValueError,'rule_only_text'):reader.row('vqa',0)
        reader.close()
        write(self.root('unicode')/'RESULT.json',dict(variants=len(variants),gate_refused=len(variants),reader_refused=len(variants),reader_gate_oracle_disabled=True))

    def test_relative_symlink_and_nonempty_token(self):
        from launch_r1 import entry
        root=self.root('tmp_confirm');job=root/'job'
        with patch.object(entry,'TMP_NAMESPACE',root):
            if not job.exists():token=entry.create_job_tmp(job)
            else:
                stat=job.stat();token=object();entry._FRESH_DIRECTORIES[token]=(job.resolve(),stat.st_dev,stat.st_ino)
            link=job/'rl'
            if not link.is_symlink():link.symlink_to('/home',target_is_directory=True)
            with self.assertRaisesRegex(ValueError,'PATH_OUTSIDE_JOB_TMP'):entry.temporary_paths('rl/x',job)
            with self.assertRaisesRegex(ValueError,'JOB_TMP_NOT_EMPTY'):
                entry.fresh_tmp(job/'work',{'job_tmp':str(job)},token)
