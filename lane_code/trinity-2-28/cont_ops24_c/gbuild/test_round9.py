"""Independent controls for frame shifts, portrait rotation, and cohort accounting."""
import unittest
import numpy as np
from analyze_round9 import packed, iou, analyze_object, summary, OUT, read
from gpkg.runtime.c import rle

class BindingTests(unittest.TestCase):
    def test_bitpacked_iou(self):
        rng=np.random.default_rng(9)
        for shape in ((240,320),(320,240),(7,9)):
            a=rng.random(shape)>.8;b=rng.random(shape)>.7
            actual=iou(*packed(a),*packed(b))
            self.assertAlmostEqual(actual,float((a&b).sum()/(a|b).sum()))

    def test_shift_sign_and_edges(self):
        raster=np.full((32,240,320),-1,np.int32)
        for k in range(32):raster[k,20:40,4*k:4*k+3]=7
        obj=dict(proposals=[dict(frame=k+1,source_index=10*k,mask=rle(raster[k+1]==7)) for k in range(31)],selected_masks={})
        out=analyze_object(obj,'test',7,raster,list(range(0,320,10)),'t1_raw')
        self.assertEqual(out['summary']['best_alternative'],'shift_+1')
        self.assertEqual(out['summary']['best_alternative_median'],1.)
        self.assertTrue(out['summary']['changed'])
        self.assertIsNone(out['frames'][-1]['best_iou']['shift_+1'])
        self.assertIsNone(out['frames'][0]['best_iou']['shift_-1'])
        self.assertEqual(out['frames'][-1]['best_iou']['same'],0.)

    def test_portrait_rotation(self):
        raster=np.full((32,320,240),-1,np.int32);raster[:,35:70,20:50]=4
        obj=dict(proposals=[dict(frame=k+1,mask=rle(np.rot90(raster[k]==4))) for k in range(32)],selected_masks={})
        out=analyze_object(obj,'portrait',4,raster,list(range(32)),'t1_raw')
        self.assertEqual(out['summary']['best_alternative'],'rot90_ccw')
        self.assertEqual(out['summary']['best_alternative_median'],1.)

    def test_results(self):
        x=read(OUT/'BINDING_R9.json')
        self.assertEqual(len(x['captures']),38)
        self.assertEqual(len(x['identity']),38)
        self.assertEqual(sum(c['camera_pass'] for c in x['captures']),6)
        self.assertEqual(x['capture_reads']['t1']['records'],160)
        self.assertEqual(x['capture_reads']['t2']['records'],310)
        self.assertEqual(sum(r['objects'] for r in x['funnel_tables']),300)
        self.assertEqual(sum(r['items'] for r in x['funnel_tables']),150)
        self.assertEqual({o['arm'] for o in x['objects']},{'t1_raw','points_raw','points_selected'})
        for o in x['objects']:
            self.assertEqual(len(o['frames']),32)
            for f in o['frames']:
                self.assertTrue(all(v is None or 0<=v<=1 for v in f['best_iou'].values()))
        for r in x['identity']:
            self.assertEqual(len(r['anchors']),32)
            self.assertTrue(all(a['gt_frame_index']==a['reader_frame_index'] for a in r['anchors']))
            self.assertFalse(r['gt_rgb_hash_bindable'])

if __name__=='__main__':unittest.main()
