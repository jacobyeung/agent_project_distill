"""Independent geometry and classification fixtures for the CPU audit."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import unittest
import numpy as np
from project_round6 import project_box, box_metrics, pair_errors
from analyze_s2_round6 import metrics, classify, summarize


class ProjectionTests(unittest.TestCase):
    def test_known_perspective_box(self):
        mask=np.full((100,100),-1);mask[25:75,25:75]=7
        K=np.array([[100.,0,50],[0,100,50],[0,0,1]])
        box=dict(center=[0,0,5],full_lengths=[2,2,2],axes=np.eye(3))
        p=project_box(box,np.eye(4),K,mask,7)
        self.assertTrue(p['centroid_inside_mask'])
        np.testing.assert_allclose(p['projected_bbox'],[25,25,75,75])
        self.assertEqual(box_metrics(p['projected_bbox'],[25,25,75,75])['bbox_iou'],1)

    def test_row_axes_and_world_transform(self):
        Q=np.array([[0.,-1,0],[1,0,0],[0,0,1]])
        pose=np.eye(4);pose[:3,:3]=Q;pose[:3,3]=[4,6,8]
        mask=np.ones((100,100),dtype=int)
        K=np.array([[100.,0,50],[0,100,50],[0,0,1]])
        box=dict(center=[4,6,13],full_lengths=[4,2,2],axes=Q.T)
        p=project_box(box,pose,K,mask,1)
        np.testing.assert_allclose(p['projected_bbox'],[0,25,100,75])

    def test_portrait_and_scale(self):
        mask=np.full((320,240),-1);mask[150:171,110:131]=3
        K=np.array([[200.,0,120],[0,200,160],[0,0,1]])
        box=dict(center=[0,0,5],full_lengths=[.2,.2,.2],axes=np.eye(3))
        self.assertTrue(project_box(box,np.eye(4),K,mask,3)['centroid_inside_mask'])
        native=np.diag([2.,2.,1.])@K
        self.assertFalse(project_box(box,np.eye(4),native,mask,3)['centroid_inside_mask'])
        scaled=np.diag([.5,.5,1.])@native
        self.assertTrue(project_box(box,np.eye(4),scaled,mask,3)['centroid_inside_mask'])

    def test_near_plane_and_behind_camera(self):
        mask=np.ones((100,100),dtype=int)
        K=np.array([[100.,0,50],[0,100,50],[0,0,1]])
        box=dict(center=[0,0,.5],full_lengths=[2,2,2],axes=np.eye(3))
        p=project_box(box,np.eye(4),K,mask,1)
        np.testing.assert_allclose(p['projected_bbox'],[0,0,100,100])
        self.assertEqual(sum(v is None for v in p['corners_uv']),4)
        box['center']=[0,0,-5]
        p=project_box(box,np.eye(4),K,mask,1)
        self.assertIsNone(p['projected_bbox']);self.assertFalse(p['centroid_inside_mask'])

    def test_relative_pose_world_invariance(self):
        a=np.repeat(np.eye(4)[None],4,axis=0)
        a[:,:3,3]=[[0,0,0],[1,0,0],[1,2,0],[1,2,3]]
        world=np.eye(4);world[:3,:3]=[[0,-1,0],[1,0,0],[0,0,1]];world[:3,3]=[7,2,1]
        errors=pair_errors(a,world@a)
        self.assertAlmostEqual(errors['rotation_deg']['max'],0)
        self.assertAlmostEqual(errors['translation_m']['max'],0)


class MaskTests(unittest.TestCase):
    def test_part_bleed_and_other(self):
        gt=np.full((10,10),-1);gt[:5,:5]=1;gt[5:,:5]=2
        pred=np.zeros((10,10),bool);pred[:2,:5]=True
        p=metrics(gt,1,pred)
        self.assertEqual(p['frame_class'],'part of the object')
        self.assertEqual(p['coverage'],.4);self.assertEqual(p['precision'],1)
        pred[:]=True
        p=metrics(gt,1,pred)
        self.assertEqual(p['frame_class'],'superset/background bleed')
        self.assertEqual(p['coverage'],1);self.assertEqual(p['precision'],.25)
        pred[:]=False;pred[5:,:5]=True
        p=metrics(gt,1,pred)
        self.assertEqual(p['frame_class'],'another instance')
        self.assertEqual(p['best_other_iou']['instance_id'],2)
        self.assertEqual(p['best_other_iou']['iou'],1)

    def test_exact_thresholds(self):
        self.assertEqual(classify(1,.49,.8,0,0),'part of the object')
        self.assertEqual(classify(1,.5,.8,0,0),'empty/other')
        self.assertEqual(classify(1,.8,.49,0,0),'superset/background bleed')
        self.assertEqual(classify(1,.8,.5,0,0),'empty/other')
        self.assertEqual(classify(1,0,0,.5,.5),'empty/other')
        self.assertEqual(classify(1,0,.19,0,.51),'another instance')

    def test_half_match_and_strict_majority(self):
        gt=np.full((2,2),1)
        good=metrics(gt,1,np.ones((2,2),bool));good['point_in_gt']=True
        bad=metrics(gt,1,np.array([[1,0],[0,0]],bool));bad['point_in_gt']=False
        s=summarize([good,bad])
        self.assertTrue(s['matches_gt_in_at_least_half_nonempty_frames'])
        self.assertEqual(s['point_class'],'tied');self.assertEqual(s['majority_class'],'mixed')
        self.assertEqual(s['iou_gt_025_frames'],1)


if __name__=='__main__':
    unittest.main()
