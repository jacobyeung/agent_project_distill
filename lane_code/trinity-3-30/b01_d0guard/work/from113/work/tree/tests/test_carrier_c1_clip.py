import copy
import gzip
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import numpy as np
from scipy.spatial.transform import Rotation

from student_pilot import carrier_c1_clip as clip
from student_pilot.camera_targets import quaternion_xyzw
from student_pilot.p3_provenance import file_pin, load, write


def trajectory(n=32):
    t=np.linspace(0,2.7,n)
    poses=np.tile(np.eye(4),(n,1,1))
    poses[:,:3,3]=np.stack((np.sin(t),np.cos(t),.2*t*t),axis=1)
    poses[:,:3,:3]=Rotation.from_euler('xyz',np.stack((t/9,t/7,t/5),axis=1)).as_matrix()
    return poses


def reference_metrics(pred,gt):
    """Independent Horn quaternion eigen-fit plus scalar SE(3) error loop.

    The metric reductions match MonST3R's evo calls: Sim(3), delta=1 frame,
    all adjacent pairs, RMSE for translation and rotation. No production helper
    or production SVD alignment is reused by this numerical reference.
    """
    x=pred[:,:3,3];y=gt[:,:3,3]
    a=x-x.mean(0);b=y-y.mean(0);h=a.T@b
    delta=np.array([h[1,2]-h[2,1],h[2,0]-h[0,2],h[0,1]-h[1,0]])
    k=np.empty((4,4));k[0,0]=np.trace(h);k[0,1:]=delta;k[1:,0]=delta
    k[1:,1:]=h+h.T-np.trace(h)*np.eye(3)
    _,eigen=np.linalg.eigh(k);q=eigen[:,-1]
    r=Rotation.from_quat(np.r_[q[1:],q[0]]).as_matrix()
    s=np.sum(b*(a@r.T))/np.sum(a*a)
    translation=y.mean(0)-s*r@x.mean(0)
    aligned=[]
    for p in pred:
        value=np.eye(4);value[:3,:3]=r@p[:3,:3];value[:3,3]=s*r@p[:3,3]+translation
        aligned.append(value)
    ate=[];trans=[];rot=[]
    for i in range(len(pred)):
        ate.append(np.linalg.norm(aligned[i][:3,3]-gt[i,:3,3]))
        if i:
            g=np.linalg.solve(gt[i-1],gt[i]);p=np.linalg.solve(aligned[i-1],aligned[i])
            error=np.linalg.solve(g,p)
            trans.append(np.linalg.norm(error[:3,3]))
            rot.append(np.degrees(Rotation.from_matrix(error[:3,:3]).magnitude()))
    return dict(zip(clip.METRICS,[np.sqrt(np.mean(np.square(v))) for v in (ate,trans,rot)]))


class ClipTests(unittest.TestCase):
    def test_sim3_gauge_invariance_and_reference_on_noisy_trajectories(self):
        rng=np.random.default_rng(32)
        gt=trajectory()
        r=Rotation.from_euler('xyz',[.4,-.7,1.1]).as_matrix()
        for noise in (0.,.001,.03,.2):
            pred=gt.copy()
            pred[:,:3,3]=2.3*(pred[:,:3,3]@r.T)+[1.,-3.,2.]
            pred[:,:3,:3]=r@pred[:,:3,:3]
            if noise:
                pred[:,:3,3]+=rng.normal(0,noise,(32,3))
                pred[:,:3,:3]=pred[:,:3,:3]@Rotation.from_rotvec(rng.normal(0,noise,(32,3))).as_matrix()
            actual=clip.trajectory_metrics(pred,gt);reference=reference_metrics(pred,gt)
            for key in clip.METRICS:
                self.assertAlmostEqual(actual[key],reference[key],delta=2e-6)
                if not noise:
                    self.assertLess(actual[key],2e-6)
            self.assertEqual(actual['relative_pairs'],31)

    def test_camera_vectors_are_inverted_and_rotation_drift_is_detected(self):
        gt=trajectory(); w2c=np.linalg.inv(gt)
        camera=np.column_stack((w2c[:,:3,3],np.array([quaternion_xyzw(p[:3,:3]) for p in w2c]),np.ones((32,2))))
        np.testing.assert_allclose(clip.pose_vectors_to_c2w(camera),gt,atol=1e-12)
        pred=gt.copy()
        pred[:,:3,:3]=pred[:,:3,:3]@Rotation.from_euler('z',np.arange(32)*.01).as_matrix()
        result=clip.trajectory_metrics(pred,gt)
        self.assertLess(result['ate_rmse_m'],1e-12)
        self.assertGreater(result['rpe_rot_rmse_deg'],.1)
        for bad in (np.zeros((32,4,4)), np.full((32,4,4),np.nan)):
            with self.assertRaises(ValueError):
                clip.trajectory_metrics(bad,gt)
        with self.assertRaises(ValueError):
            clip.trajectory_metrics(np.tile(np.eye(4),(32,1,1)),gt)
        reflected=gt.copy();reflected[:,:3,3][:,0]*=-1
        self.assertGreater(clip.trajectory_metrics(reflected,gt)['ate_rmse_m'],1e-4)

    def fixture(self):
        root=Path(tempfile.mkdtemp(prefix='clip_',dir=os.environ['LANE_TEST_OUTPUT']))
        write(root/'rgb.json',{'tiny_fixture':True})
        write(root/'frames.json',dict(frames=[file_pin(root/'rgb.json')]*94))
        np.savez(root/'poses.npz',c2w=trajectory(94),frame_indices=np.arange(94))
        scenes=[['d',str(i)] for i in range(38)]
        write(root/'heldout.json',dict(scenes=scenes));write(root/'train.json',dict(scenes=[['d','train']]))
        sources=[dict(dataset=d,scene=s,recording_id=s,frames=file_pin(root/'frames.json'),
            poses=file_pin(root/'poses.npz'),total_num_frames=94,fps=30.) for d,s in scenes]
        write(root/'sources.json',dict(recordings=sources))
        cfg=dict(recordings=file_pin(root/'sources.json'),heldout_scenes=file_pin(root/'heldout.json'),
            training_scenes=file_pin(root/'train.json'),output=str(root/'clips.json'))
        return root,cfg,scenes

    def test_full_recording_builder_exact_38_scene_cohort_and_stride(self):
        root,cfg,scenes=self.fixture()
        document=clip.build_clips(cfg)
        self.assertEqual(len(document['clips']),38)
        first=document['clips'][0]
        self.assertEqual(first['student_input']['frame_indices'],list(range(0,94,3)))
        np.testing.assert_allclose(first['gt_c2w'],trajectory(94)[::3])
        for mutate in ('stride','missing','duplicate','sparse','overlap','pose','qid'):
            bad=copy.deepcopy(document); training=[['d','train']]
            if mutate=='stride': bad['clips'][0]['student_input']['frame_indices'][-1]=95
            if mutate=='missing': bad['clips']=bad['clips'][:-1]
            if mutate=='duplicate': bad['clips'][-1]=bad['clips'][0]
            if mutate=='sparse': bad['clips'][0]['source_kind']='sparse_anchor_bank'
            if mutate=='overlap': training=[['d','0']]
            if mutate=='pose': bad['clips'][0]['gt_c2w'][0][0][0]=10.
            if mutate=='qid': bad['clips'][0].pop('qid')
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):
                clip.check_clips(bad,scenes,training)
        rows=[dict(dataset=d,scene=s,**dict(zip(clip.METRICS,[.1,.2,3.]))) for d,s in scenes]
        result=clip.summarize(rows)
        self.assertEqual(result['scenes'],38)
        self.assertAlmostEqual(result['mean']['ate_rmse_m'],.1)
        with self.assertRaises(ValueError):
            clip.summarize(rows[:-1])

    def test_evaluate_emits_both_readouts_and_pose_only_gate_requires_them(self):
        from student_pilot import carrier_c1_run as run
        from student_pilot.carrier_c1_data import C1_A
        from student_pilot.compact_label_bank import frame_set_sha256
        root,cfg,scenes=self.fixture(); document=clip.build_clips(cfg)
        clip_pin=file_pin(root/'clips.json')
        write(root/'bank.json',{'fixture':True})
        write(root/'m400/artifact.json',{'fixture':True}); artifact=file_pin(root/'m400/artifact.json')
        with gzip.open(root/'rows.gz','wt') as handle:
            for row in document['clips']:
                value={**row,'student_input':{**row['student_input'],'frame_indices':list(range(32))}}
                handle.write(json.dumps(value)+'\n')
        write(root/'inventory.json',dict(files=[file_pin(root/'rows.gz')]))
        config=dict(training_mode='pose_only',carrier_placement=C1_A,output=str(root),readout=dict(
            bank=file_pin(root/'bank.json'),rows_inventory=file_pin(root/'inventory.json'),
            training_scenes=cfg['training_scenes'],contiguous_clips=clip_pin))
        bank=dict(dataset_tokens=np.array(['d']*38),scene_tokens=np.array([str(i) for i in range(38)]),
            frame_set_sha256=np.array([frame_set_sha256(list(range(32)))]*38),
            camera=np.zeros((38,32,9)),camera_mask=np.ones((38,32),bool),gravity=np.zeros((38,3)),
            gravity_mask=np.ones(38,bool),trajectory_scale=np.ones(38),point_depth_uv=np.zeros((38,32,1,2)),
            point_depth_gt=np.zeros((38,32,1)),point_depth_mask=np.zeros((38,32,1),bool),depth_anchor_frames=np.arange(32))
        model=Mock();model.auxiliary_heads=object()
        w2c=np.linalg.inv(np.asarray(document['clips'][0]['gt_c2w']))
        camera=np.column_stack((w2c[:,:3,3],np.array([quaternion_xyzw(p[:3,:3]) for p in w2c]),np.ones((32,2))))
        model.pose_readout.return_value=camera
        model.readout.return_value=dict(raw_pose=camera.tolist(),gravity_up=[0,1,0],trajectory_step_m=1.,
            point_depth=None,invalid_fov_frames=[],geometry_error=None)
        detail=dict(protocol='head_acc_origin_metric_v1',all_frames={'all':dict(scenes=38,rot_deg=dict(mean=2.,median=1.))})
        with patch.object(run,'inference',return_value=(model,None,{},dict(step=400))), \
             patch('student_pilot.all_frame_bank.read_bank',return_value=bank), \
             patch('student_pilot.all_frame_readout.evaluate',return_value=detail) as sparse, \
             patch.object(run.data,'encode',return_value=({},None,{})) as encoder:
            unbound=copy.deepcopy(config);unbound['readout'].pop('contiguous_clips')
            sparse_report=run.evaluate(unbound,artifact,root/'sparse.json')
            self.assertEqual(encoder.call_count,38)
            model.pose_readout.assert_not_called()
            self.assertIsNone(sparse_report['contiguous_clip'])
            self.assertTrue(sparse_report['contiguous_clip_pending'])
            self.assertEqual(run.identity(config),run.identity(unbound))
            self.assertNotEqual(run.readout_identity(config),run.readout_identity(unbound))
            encoder.reset_mock()
            report=run.evaluate(config,artifact,root/'readout.json')
            bad=copy.deepcopy(config);bad['readout']['contiguous_clips']['sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'pinned input'):
                run.evaluate(bad,artifact,root/'invalid.json')
            bad['readout']['contiguous_clips']={}
            with self.assertRaisesRegex(ValueError,'exact path/SHA256 pin'):
                run.evaluate(bad,artifact,root/'malformed.json')
        self.assertEqual(len(encoder.call_args_list),76)
        self.assertEqual(sparse.call_args.args[1],{'pose'})
        self.assertEqual(report['contiguous_clip']['scenes'],38)
        self.assertLess(report['contiguous_clip']['mean']['ate_rmse_m'],1e-10)
        self.assertEqual(encoder.call_args_list[0].args[1]['student_input']['frame_indices'],list(range(32)))
        self.assertEqual(encoder.call_args_list[-1].args[1]['student_input']['frame_indices'],clip.ORDINALS)
        gate=dict(schema='c1-m400-gate-v1',verdict='PASS',reviewer='fixture',step=400,
            config_sha256=run.identity(config),artifact=artifact,reports={'pose':file_pin(root/'readout.json')},
            metrics=dict(pose_scenes=38,pose_statistic='head_acc_mean',rotation_deg=2.))
        write(root/'gate.json',gate)
        run.milestone_gate({**config,'milestone_gate':file_pin(root/'gate.json')})
        write(root/'sparse_gate.json',{**gate,'reports':{'pose':file_pin(root/'sparse.json')}})
        for candidate in (config,unbound):
            with self.assertRaisesRegex(ValueError,'Both sparse'):
                run.milestone_gate({**candidate,'milestone_gate':file_pin(root/'sparse_gate.json')})
        for i,changed in enumerate(({'contiguous_clip':{}},{'artifact':{}},{'step':200},
                                    {'contiguous_clips':{}},{'readout_sha256':'0'*64},{'detail':{}},
                                    {'contiguous_clip':{**report['contiguous_clip'],'scenes':37}})):
            write(root/f'bad_report{i}.json',{**report,**changed})
            write(root/f'bad_gate{i}.json',{**gate,'reports':{'pose':file_pin(root/f'bad_report{i}.json')}})
            with self.assertRaises(ValueError):
                run.milestone_gate({**config,'milestone_gate':file_pin(root/f'bad_gate{i}.json')})


if __name__ == '__main__':
    unittest.main()
