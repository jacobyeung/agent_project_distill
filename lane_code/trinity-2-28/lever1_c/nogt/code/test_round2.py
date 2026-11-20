"""Regression tests for parity thresholds, raw extraction and audit semantics."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from round2 import *
from audit_functions import summary, MODES, packed, iou
from raw_functions import build_memberships
from check_captures import geometry_check

class Round2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work=OUT/'test_artifacts'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        cls.work.mkdir(parents=True)

    def compare(self,name,x,y,dataset='scannet'):
        a=self.work/(self._testMethodName+'_a.npz');b=self.work/(self._testMethodName+'_b.npz')
        np.savez_compressed(a,**{name:x});np.savez_compressed(b,**{name:y})
        return compare_arrays(a,b,dataset)

    def test_float_tolerance_accepts_rounding(self):
        y=np.array([1.],np.float32);x=y+4*np.finfo(np.float32).eps
        self.assertTrue(self.compare('c2w',x,y)['passed'])

    def test_float_tolerance_rejects_geometry_change(self):
        y=np.array([1.],np.float32);x=y+16*np.finfo(np.float32).eps
        self.assertFalse(self.compare('depth',x,y)['passed'])

    def test_exact_mask_required(self):
        self.assertFalse(self.compare('inst',np.array([1],np.int32),np.array([2],np.int32))['passed'])

    def test_depth_support_cannot_use_float_slack(self):
        self.assertFalse(self.compare('depth',np.array([1e-8],np.float32),np.array([0],np.float32))['passed'])

    def test_arkit_depth_requires_exact_scaling(self):
        self.assertFalse(self.compare('depth',np.array([1+1e-7],np.float32),np.array([1],np.float32),'arkitscenes')['passed'])

    def test_dtype_mismatch_rejected(self):
        self.assertFalse(self.compare('ids',np.array([1],np.int64),np.array([1],np.int32))['passed'])

    def test_raw_csr_preserves_overlapping_memberships(self):
        faces=np.array([[0,1,2],[1,2,3]])
        groups=[dict(id=7,segments=[3]),dict(id=8,segments=[3,4])]
        r=build_memberships(faces,np.array([3,4]),groups,True)
        np.testing.assert_array_equal(r['membership_face_offsets'],[0,1,3])
        np.testing.assert_array_equal(r['membership_face_indices'],[0,0,1])

    def test_binding_alternative_requires_paired_gain(self):
        frames=[]
        for s,a in [(0.9,None),(0.2,0.45),(0.1,0.35)]:
            frames.append(dict(gt_visible=True,best_iou={'same':s,'shift_+1':a},proposal_count=1,gt_pixels_by_mode={'same':1,'shift_+1':1 if a is not None else None}))
        r=summary(frames,['same','shift_+1'])
        self.assertTrue(r['changed'])
        self.assertAlmostEqual(r['max_paired_median_gain'],.25)

    def test_empty_binding_does_not_prove_agreement(self):
        r=summary([],MODES)
        self.assertIsNone(r['same_median'])

    def test_packed_mask_iou(self):
        a=np.array([[1,0],[1,0]],bool);b=np.array([[1,1],[0,0]],bool)
        self.assertAlmostEqual(iou(*packed(a),*packed(b)),1/3)

    def test_reproduction_receipts(self):
        r=read(OUT/'REPRODUCTION.json')
        for dataset in ('scannet','scannetppv2'):
            self.assertTrue(r[dataset]['passed'])
            self.assertTrue(all(a['passed'] for a in r[dataset]['arrays'].values()))
            self.assertEqual(r[dataset]['tolerance_sha256'],sha(OUT/'REPRO_TOLERANCE.md'))
        self.assertEqual(read(OUT/'prepared/scene0166_00/PREPARATION.json')['sens']['decoded_poses'],32)
        self.assertEqual(read(OUT/'prepared/scene0166_00/PREPARATION.json')['sens']['decoded_images'],0)

    def test_build_gate_and_capture_count(self):
        r=read(OUT/'REPRODUCTION.json');builds=read(OUT/'BUILDS.json')
        self.assertEqual(len(builds),22)
        for c,b in builds.items():
            if b['built']:self.assertTrue(r[c.split('/')[0]]['passed'])

    def test_completed_capture_audits(self):
        builds=read(OUT/'BUILDS.json');checks=read(OUT/'CAPTURE_CHECKS.json')['captures']
        self.assertEqual(set(checks),{c for c,b in builds.items() if b['built']})
        for c,r in checks.items():
            self.assertEqual(len(r['frames']),32)
            self.assertTrue(r['identity_passed'])
            self.assertEqual(set(r['arms']),{'t1','t2'})
            if r['passed']:
                self.assertTrue(r['geometry']['passed'] and r['binding_passed'] and r['colmap_passed'])

    def test_delivered_npz_schema_and_anchor_binding(self):
        builds=read(OUT/'BUILDS.json');repro=read(OUT/'REPRODUCTION.json')
        manifest={r['scene']:r for r in read(ROOT/'DEVS1_MANIFEST.json')['captures']}
        for c,b in builds.items():
            if not b['built']:continue
            d=c.split('/')[0]
            with np.load(b['path']) as z,np.load(repro[d]['reference']) as ref:
                self.assertEqual(set(z.files),set(ref.files))
                for k in z.files:
                    if k!='labels':self.assertEqual(z[k].dtype,ref[k].dtype)
                self.assertEqual(z['labels'].dtype.kind,'U')
                self.assertEqual(z['frame_indices'].tolist(),manifest[c]['anchor_indices'])
                self.assertEqual(z['depth'].shape,z['inst'].shape)
                self.assertEqual(z['depth'].shape[0],32)
                self.assertTrue(z['valid'].all())
                np.testing.assert_array_equal(z['K'],z['K_frames'][0])
                self.assertTrue(np.all(z['obb_lengths']>0))
                self.assertEqual(len(z['ids']),len(z['labels']))
                self.assertEqual(sha(b['path']),b['evidence']['sha256'])

if __name__=='__main__':unittest.main(verbosity=2)
