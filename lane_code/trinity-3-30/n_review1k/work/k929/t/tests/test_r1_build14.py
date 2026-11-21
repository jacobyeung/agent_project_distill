"""Effective config contracts and absolute milestone handover proofs."""
from copy import deepcopy
from pathlib import Path
import unittest
from student_pilot import r1_training as R, r1_handover as H
from student_pilot.p3_provenance import load, file_pin
from launch_r1 import p_handover_receipt as P
from tests.test_r2_build_n1 import configuration, write
from tests.test_r2_n1fix import handover_fixture, produce_receipt
from tests import test_r2_n1fix as prior


class Build14(unittest.TestCase):
    root = prior.N1Fix.root

    def test_scale_card_config_and_override(self):
        cfg=configuration();R.validate(cfg)
        for change,reason in [({'steps':999,'milestones':[100,200]},'RECIPE_DIFFERS'),
                ({'h1':{'faithful_own_camera_rows':True}},'OWN_ROWS_REFUSED'),
                ({'milestones':[100,200]},'MILESTONES_DIFFER')]:
            with self.assertRaisesRegex(ValueError,reason):R.validate(dict(cfg,**change))
        for scale in (None, -1, float('nan'), True, 1.0):
            bad=deepcopy(cfg);bad['r1_training']['weight_scale']=scale
            with self.assertRaisesRegex(ValueError,'SCALE_WEIGHT'):R.validate(bad)
        bad=deepcopy(cfg);bad['camera_overrides']['weight_scale']=1.0
        with self.assertRaisesRegex(ValueError,'SCALE_WEIGHT'):R.validate(bad)
        for change in ({'weight_focal':1.0},{'weight_gravity':.1}):
            bad=deepcopy(cfg);bad['camera_overrides'].update(change)
            with self.assertRaisesRegex(ValueError,'CAMERA_OVERRIDES'):R.validate(bad)
        cfg['r1_training']['weight_scale']=cfg['camera_overrides']['weight_scale']=0.08
        with self.assertRaisesRegex(ValueError,'SCALE_WEIGHT'):R.validate(cfg)
        cfg['r1_training']['mix']=write(self.root('b14_scale')/'card.json',{'weight_scale':.08})
        R.validate(cfg)

    def test_defaults_pins_unknowns_and_boundary_keys(self):
        cfg=configuration();cfg.pop('init_artifact',None)
        for key,default in H.EFFECTIVE_DEFAULTS.items():
            a=deepcopy(cfg);a.pop(key,None);b=dict(a,**{key:default});H.compare_configs(a,b)
            with self.assertRaisesRegex(ValueError, key):H.compare_configs(a,dict(b,**{key:'different'}))
        root=self.root('b14_pins')
        first=write(root/'one.json',{'fixture':1});same=write(root/'two.json',{'fixture':1})
        different=write(root/'three.json',{'fixture':2})
        a=dict(cfg,known_input=first)
        H.compare_configs(a,dict(a,known_input=same))
        with self.assertRaisesRegex(ValueError,'known_input'):
            H.compare_configs(a,dict(a,known_input=different))
        H.compare_configs(dict(cfg,depth_init=first),dict(cfg,depth_init=same))
        with self.assertRaisesRegex(ValueError,'MISMATCH:depth_init'):
            H.compare_configs(dict(cfg,depth_init=first),dict(cfg,depth_init=different))
        with self.assertRaisesRegex(ValueError,'unknown_null'):H.compare_configs(cfg,dict(cfg,unknown_null=None))
        for key in H.HANDOVER_ROW_KEYS:
            if key!='h1':H.compare_configs(cfg,dict(cfg,**{key:[100,200] if key=='milestones' else {'new_rows':True}}))
        for h in ({'future_loss':0},{'faithful_own_camera_rows':True}):
            with self.assertRaisesRegex(ValueError,'h1'):H.compare_configs(cfg,dict(cfg,h1=h))
        bad=deepcopy(cfg);bad['recipe']['weights']['pose']=9
        with self.assertRaisesRegex(ValueError,'recipe'):H.compare_configs(cfg,bad)
        bad=deepcopy(cfg);bad['recipe']['weight_decay']=.9
        with self.assertRaisesRegex(ValueError,'recipe'):H.compare_configs(cfg,bad)

    def test_effective_camera_and_metadata_refusal(self):
        cfg,p,_,_=handover_fixture(self.root('b14_camera'))
        prep=load(p['preparation']['path']);prep['camera']['weight_scale']=.04
        pp=write(self.root('b14_camera')/'effective.json',prep)
        p['preparation']=pp
        p['camera_overrides'].pop('weight_scale')
        H.compare_configs(p,cfg)
        no_overrides=deepcopy(p);no_overrides.pop('camera_overrides')
        explicit=deepcopy(no_overrides);explicit['camera_overrides']={}
        H.compare_configs(no_overrides,explicit)
        bad=deepcopy(cfg);other=deepcopy(prep);other['camera']['weight']+=.1
        bad['preparation']=write(self.root('b14_camera')/'other.json',other)
        with self.assertRaisesRegex(ValueError,'camera_overrides'):H.compare_configs(p,bad)
        for key,value in [('weight_scale',.08),('trunk_depth',99),('weight',.7)]:
            bad=deepcopy(cfg);bad['camera_overrides'][key]=value
            with self.assertRaisesRegex(ValueError,'camera_overrides'):H.compare_configs(p,bad)
        p.pop('preparation')
        with self.assertRaisesRegex(ValueError,'CAMERA_METADATA_UNVERIFIED'):H.compare_configs(p,cfg)

    def test_milestone_producer_reader(self):
        results=[]
        for step in (100,200,400,600):
            root=self.root('b14_m'+str(step))
            milestones=[100,200] if step<=200 else [400,600]
            cfg,p,_,artifact=handover_fixture(root,donor_scales={'lm_lr_scale':.6,'pose_lr_scale':.6,'milestones':milestones},step=step)
            pins=cfg['r1_training']['p_run'];ap=cfg['init_artifact']['artifact']
            receipt=P.verify_receipt(cfg['r1_training']['handover_receipt'],pins,ap)
            progress=H.progress(cfg,artifact)
            self.assertEqual((receipt['step'],R.start(cfg),progress['schedule_step']),(step,step,step))
            self.assertEqual(progress['sampler_positions'],{s:step*n for s,n in R.STREAMS.items()})
            from student_pilot.r1_mix import plans
            from itertools import islice
            counts={s:n*250 for s,n in R.STREAMS.items()}
            resumed=next(plans(cfg['r2_sampling'],counts,step+1,start_step=step))
            uninterrupted=next(islice(plans(cfg['r2_sampling'],counts,step+1),step,None))
            self.assertEqual(resumed,uninterrupted)
            forged=dict(receipt,step=step+1)
            with self.assertRaisesRegex(ValueError,'RECEIPT_INVALID'):
                P.verify_receipt(write(root/'forged.json',forged),pins,ap)
            complete=load(pins['checkpoint']['path']);complete['step']=step+1
            wrong=dict(pins,checkpoint=write(root/'bad_complete.json',complete))
            with self.assertRaisesRegex(ValueError,'RUN_BINDING_MISMATCH'):P.collect(wrong,ap)
            nonmilestone=dict(artifact,step=step+1)
            with self.assertRaisesRegex(ValueError,'STEP_NOT_MILESTONE'):
                P.collect(pins,write(root/'bad_artifact.json',nonmilestone))
            results.append({'step':step,'sampler_positions':progress['sampler_positions'],'milestones':milestones,
                            'N_resumed_plan_equals_uninterrupted':True})
        write(self.root('b14_milestones')/'RESULT.json',{'results':results,'stand_in':'Tiny native CPU model and local collectives replace pretrained GPU weights; sealed checkpoint/export and receipt producer/reader execute.'})
