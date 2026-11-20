"""Scientific invariants and artifact reconciliation for the R8 audit."""
import unittest,json
import numpy as np
from analyze_round8 import OUT,CAM,ROOT,alignment,pair,category,metric_poses
from student_pilot.camera_targets import encode_cameras
class Audit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.x=json.loads((OUT/'CAMERA_ITEMS_R8.json').read_text())
        cls.f=json.loads((OUT/'CAPTURE_FEATURES_R8.json').read_text())
    def test_rigid_and_pair_invariance(self):
        b=np.tile(np.eye(4),(4,1,1));b[:,:3,3]=[[0,0,0],[1,0,0],[0,1,0],[0,0,1]]
        q=np.array([[0.,-1,0],[1,0,0],[0,0,1]]);a=b.copy();a[:,:3,:3]=q@b[:,:3,:3];a[:,:3,3]=b[:,:3,3]@q.T+[2,3,4]
        self.assertEqual(category(alignment(a,b)),'pass');p=pair(a,b,0,1)
        self.assertAlmostEqual(p['relative_rotation_error_deg'],0);self.assertAlmostEqual(p['translation_direction_error_deg'],0);self.assertAlmostEqual(p['distance_ratio'],1)
        a[:,:3,3]*=2;self.assertFalse(alignment(a,b)['accepted']);self.assertAlmostEqual(pair(a,b,0,1)['distance_ratio'],2)
    def test_payload_encode_decode_roundtrip(self):
        b=np.tile(np.eye(4),(32,1,1));t=np.arange(32)/31;b[:,:3,3]=np.column_stack([t,t*t,np.sin(t)])
        p,_,_=encode_cameras(b,np.tile(np.eye(3),(32,1,1)),(480,640),all_frames=True)
        a=metric_poses(p,[0,-1,0]);self.assertEqual(category(alignment(a,b)),'pass')
    def test_score_cohorts_and_loss(self):
        for step in (544,400):
            rr=[r for r in self.x['items'] if r['step']==step];self.assertEqual(len(rr),900)
            for ds in ('all','scannet','scannetppv2'):
             for typ in ('all','displacement','rotation','direction'):
                selected=[r for r in rr if (ds=='all' or r['dataset']==ds) and (typ=='all' or r['type']==typ)]
                tab=[r for r in self.x['tables'] if r['step']==step and r['dataset']==ds and r['type']==typ]
                self.assertEqual(sum(r['items'] for r in tab if r['capture_class']!='all'),len(selected))
                allrow=next(r for r in tab if r['capture_class']=='all')
                self.assertAlmostEqual(allrow['accuracy']['mean'],np.mean([r['score'] for r in selected]))
                loss=next(r for r in self.x['loss'] if r['step']==step and r['dataset']==ds and r['type']==typ)
                self.assertAlmostEqual(loss['total_loss'],sum(1-r['score'] for r in selected))
        self.assertEqual(len(self.x['bootstrap']['rooms']),37)
    def test_missing_GT_and_replay(self):
        self.assertEqual(len(self.x['no_GT']),18);self.assertEqual(sum(r['items_per_step']['544'] for r in self.x['no_GT']),324)
        rep=self.x['replay'];own=[r for r in rep if r['source']=='logged_own' and r['tool']=='move']
        self.assertEqual(sum(r['exact'] for r in own),0);self.assertEqual(sum(r['total'] for r in own),1025)
        rec=[r for r in rep if r['source']=='distance_reconstruction']
        self.assertEqual(sum(r['total'] for r in rec),842);self.assertEqual(sum(r['exact'] for r in rec),834)
        self.assertEqual(sum(r['within_one_print_unit'] for r in rec),842)
    def test_capture_union_and_auc(self):
        self.assertEqual(len(self.f['captures']),57)
        ds=[r for r in self.f['captures'] if r['in_distance_GT']];self.assertEqual(len(ds),38)
        self.assertEqual(sum(r['distance_class']=='pass' for r in ds),6);self.assertEqual(sum(r['distance_class']=='gross' for r in ds),10)
        self.assertEqual(sum(r['in_camera_GT'] for r in self.f['captures']),34)
        for r in self.f['captures']:
            self.assertAlmostEqual(sum(r['features'][f'orientation_{k}_share'] for k in ('upright','upside_down','sideways_left','sideways_right')),1)
            if len(r['tower_source_frame_indices'])==64:self.assertIsNone(r['features']['consecutive_tower_rotation_mean_deg'])
        for a in self.f['AUC']:
            if a['auc'] is not None:self.assertTrue(0<=a['auc']<=1)
    def test_GT_overlap_and_classes(self):
        gt=json.loads((ROOT/'out2/GT.json').read_text());pins=self.x['GT_provenance'];self.assertEqual(len(pins),34)
        for pin in pins:
            if pin['capture'] in gt:
                with np.load(pin['path'],allow_pickle=False) as z:np.testing.assert_allclose(z['c2w'],gt[pin['capture']]['c2w'],atol=1e-7)
        cmp=[r for r in self.x['comparisons'] if r['same_400_544'] is not None]
        self.assertEqual(len(cmp),15);self.assertTrue(all(r['same_400_544'] and all(r['same_camera_distance'].values()) for r in cmp))
    def test_no_question_or_wording_fields(self):
        forbidden={'question','question_text','stratum','selection_stratum','selection_rank','original','reworded','phrase_family'}
        def visit(v):
            if isinstance(v,dict):
                self.assertFalse(forbidden.intersection(v));[visit(x) for x in v.values()]
            elif isinstance(v,list):[visit(x) for x in v]
        visit(self.x);visit(self.f)
if __name__=='__main__':unittest.main()
