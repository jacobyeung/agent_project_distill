import ast
import copy
import gzip
import hashlib
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest
import zlib
import numpy as np
import build
ROOT=build.ROOT
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'kit2/kit/rerun2'))
from gpkg.capture_io import Records
from gpkg.grid import resize
from gpkg.join_v2 import join
from gpkg.score_ceiling import bootstrap,gap_score,official_mra,score
from gpkg.runtime.c import rle,unrle,Writer
from gt import v2
from dry import fixture


def temp():return Path(tempfile.mkdtemp(prefix='r2_',dir=ROOT/'work/tests'))
def receipt(path):return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size)


class ReaderTests(unittest.TestCase):
    def test_nonpoints_exact_submitted_bytes(self):
        info=build.build(temp())
        self.assertNotEqual(info['delivery_sha256'],'f4509a4ad19b8e2bd2f9f5fd3fe7c32130ab13c10db5aa00407a84582fdb8d00')
        self.assertNotEqual(info['token'],'a5d6f41359166')
        self.assertEqual(info['delivery_sha256'],build.build(temp())['delivery_sha256'])

    def test_trailerless_and_incomplete_line_salvage_raw_hash(self):
        root=temp();codec=zlib.compressobj(wbits=31)
        raw=codec.compress(b'{"a":1}\n{"a":2}\n{"a":')+codec.flush(zlib.Z_SYNC_FLUSH)
        path=root/'cut.gz';path.write_bytes(raw)
        records=Records(path,receipt(path))
        self.assertEqual(list(records),[{'a':1},{'a':2}]);self.assertTrue(records.report['salvaged'])
        self.assertEqual(records.report['records'],2);self.assertEqual(records.report['discarded_partial_line_bytes'],5)
        with self.assertRaisesRegex(ValueError,'SHA256'):Records(path,{'sha256':'0'*64})
        path=root/'trailer.gz';path.write_bytes(gzip.compress(b'{"a":1}\n')[:-8])
        records=Records(path,receipt(path));self.assertEqual(list(records),[{'a':1}]);self.assertTrue(records.report['salvaged'])
        path=root/'good.gz';path.write_bytes(gzip.compress(b'{"a":1}\n'))
        records=Records(path,receipt(path));self.assertEqual(list(records),[{'a':1}]);self.assertFalse(records.report['salvaged'])
        bad=bytearray(path.read_bytes());bad[-8]^=1;path=root/'bad.gz';path.write_bytes(bad)
        with self.assertRaises(zlib.error):list(Records(path,receipt(path)))

    def test_scorer_thresholds_units_missing_and_shared_room_draws(self):
        refs=json.loads((ROOT/'kit2/kit/rerun2/items544.json').read_text())['items']
        f=ROOT/'kit2/kit/analyze.py';tree=ast.parse(f.read_text());fn=next(n for n in tree.body if getattr(n,'name',None)=='mra');ns={}
        exec(compile(ast.Module([fn],type_ignores=[]),str(f),'exec'),ns)
        for pred in [0,.05,.1,.15,.2,.25,.5,1,1.05,1.5,2]:
            for truth in [0,.1,1,2]:self.assertAlmostEqual(100*official_mra(pred,truth),ns['mra'](pred,truth))
        calls=[dict(call='<gap a="a" b="b">',served=True,response='distance 0.30 m')]
        self.assertEqual(gap_score(calls,'in centimeters',30)['score'],100)
        self.assertEqual(gap_score([],'in meters',1)['score'],0)
        rows=[dict(room='a',baseline=0,points=10,point_minus_baseline=10,size_band='x',baseline_lt3=True),
              dict(room='a',baseline=10,points=20,point_minus_baseline=10,size_band='x',baseline_lt3=True),
              dict(room='b',baseline=90,points=100,point_minus_baseline=10,size_band='y',baseline_lt3=False)]
        value=bootstrap(rows,['a','b'],1000)
        self.assertEqual(value['groups']['all']['metrics']['point_minus_baseline']['ci95'],[10,10])
        self.assertEqual(value['groups']['all']['metrics']['points']['mean'],130/3)
        self.assertGreater(value['groups']['size_band=x']['metrics']['points']['undefined_draws'],0)
        root=temp();path=root/'cut.gz';codec=zlib.compressobj(wbits=31)
        # The scorer keeps the full 150-item denominator, despite one returned item.
        row=dict(item_id=refs[0]['item_id'],capture=refs[0]['capture'],source_indices=refs[0]['source_indices'],pass_index=0,calls=refs[0]['calls'],objects=[])
        path.write_bytes(codec.compress((json.dumps(row)+'\n').encode())+codec.flush(zlib.Z_SYNC_FLUSH))
        r=root/'receipt.json';r.write_text(json.dumps(receipt(path)))
        result=score(ROOT/'kit2/kit/rerun2/items544.json',path,r)
        self.assertEqual(result['denominator'],150);self.assertEqual(result['statistics']['resampled_rooms'],46)
        self.assertTrue(result['capture_read']['points']['salvaged']);self.assertEqual(sum(r['point_record_present'] for r in result['rows']),1)


class GT2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.values,cls.audit=v2.convert(ROOT.parent/'gt',ROOT/'kit2/kit/rerun2/items544.json')
        cls.out=temp()
        (cls.out/'GT.json').write_text(json.dumps(cls.values))
        (cls.out/'AUDIT.json').write_text(json.dumps(cls.audit))

    def test_all38_visibility_extents_binding_portrait(self):
        self.assertEqual(self.audit['available_captures'],38);self.assertEqual(self.audit['portrait_unknown'],9)
        self.assertEqual(self.audit['unique_bindings'],142)
        for record in self.audit['files']:
            value=self.values[record['capture']]
            with np.load(record['path'],allow_pickle=False) as z:
                inst=z['inst'];ids=z['ids'];lengths=z['obb_lengths']
                for i,iid in enumerate(ids):
                    expected=[int(np.count_nonzero(frame==iid)) for frame in inst]
                    actual=record['instances'][i]
                    self.assertEqual(actual['visible_pixels'],expected)
                    if actual['full_obb']:
                        factor=2 if value['dataset']=='scannetppv2' else 1
                        np.testing.assert_allclose(actual['full_obb']['full_lengths'],lengths[i]*factor)
                    if value['dataset']=='scannet':self.assertIsNotNone(actual['half_extent_obb'])
                for target in value['targets'].values():
                    if target['binding_reviewed'] and value['orientation']['status']!='U':
                        self.assertEqual(len(target['masks']),32)
                        for f,s in enumerate(value['source_indices']):
                            np.testing.assert_array_equal(unrle(target['masks'][str(s)]['240x320']),inst[f]==target['instance_id'])
                    if value['orientation']['status']=='U':self.assertFalse(target['annotation_complete'])
        self.assertEqual(v2.bind(' Lamp ',[1],['lamp'])['instance_id'],1)
        self.assertEqual(v2.bind('chair',[1,2],['Chair',' chair '])['status'],'U')
        self.assertEqual(v2.bind('chairs',[1],['chair'])['status'],'U')

    def test_camera_rigid_no_scale_and_rotation_gates(self):
        rng=np.random.default_rng(3);a=np.tile(np.eye(4),(32,1,1));a[:,:3,3]=rng.normal(size=(32,3))
        angle=.3;T=np.eye(4);T[:3,:3]=[[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]];T[:3,3]=[2,3,4]
        b=T@a;r=v2.alignment(a,b);self.assertTrue(r['accepted']);np.testing.assert_allclose(r['reader_world_to_gt_world'],T,atol=1e-12)
        b2=b.copy();b2[:,:3,3]*=1.5;r=v2.alignment(a,b2);self.assertFalse(r['accepted']);self.assertFalse(r['fit_scale'])
        b2=b.copy();b2[:,:3,:3]=np.eye(3);self.assertFalse(v2.alignment(a,b2)['accepted'])
        self.assertFalse(v2.alignment(np.tile(np.eye(4),(32,1,1)),np.tile(np.eye(4),(32,1,1)))['accepted'])

    def test_synthetic_adapter_join_pipeline_and_grid(self):
        ref=json.loads((ROOT/'kit2/kit/rerun2/items544.json').read_text())['items'][0]
        row,gt=fixture(ref);obj=row['objects'][0];name='object'
        # The original synthetic capture has stationary cameras, so S4/S5 must be U.
        root=temp();inst=np.full((32,240,320),-1,np.int32)
        for f,m in obj['selected_masks'].items():inst[int(f)-1][unrle(m)]=1
        z=root/'synthetic.npz'
        np.savez_compressed(z,inst=inst,ids=[1],labels=[name],frame_indices=ref['source_indices'],valid=np.ones(32,bool),
                            c2w=row['geometry']['camera_to_world_metric'],K_frames=np.tile(np.eye(3),(32,1,1)),
                            obb_centroid=[[0,0,0]],obb_lengths=[[1,1,1]],obb_axes=[np.eye(3).ravel()])
        ref2=copy.deepcopy(ref);ref2['calls']=[dict(call='<ground obj="object" mode="box">'),dict(call='<ground obj="other" mode="box">')]
        converted,audit=v2.convert_file(z,[ref2],[row]);joined=join(row,converted)
        self.assertEqual(joined[0]['stage'],'U');self.assertEqual(joined[0]['evidence']['selected_correct_frames'],3)
        self.assertIn('extent_readings',joined[0]);self.assertFalse(audit['alignment']['accepted'])
        path=root/'capture.gz';row['pass_index']=0;w=Writer(path);w.append(row);w.close()
        rp=root/'receipt.json';rp.write_text(json.dumps(dict(trusted=False,items=1,capture_records=1,capture_sha256=receipt(path)['sha256'],per_item=[])))
        gp=root/'gt.json';gp.write_text(json.dumps({ref['capture']:converted}))
        from gpkg.join_capture import score as join_score
        joinedpath=root/'joined.jsonl';join_score(path,rp,gp,joinedpath)
        self.assertEqual(json.loads(joinedpath.read_text())['stage'],'U')
        cut=root/'cut.gz';cut.write_bytes(path.read_bytes()[:-8])
        upload=root/'upload.json';upload.write_text(json.dumps(receipt(cut)))
        salvage=join_score(cut,rp,gp,root/'salvaged.jsonl',upload)
        self.assertTrue(salvage['salvaged']);self.assertEqual(salvage['records'],1)
        # Explicitly distinguish ScanNet full versus half readings at S4/S5.
        converted['alignment']=dict(accepted=True)
        target=converted['targets'][ref['item_id']+':object']
        target.update(world_alignment_reviewed=True,reader_world_to_gt_world=np.eye(4).tolist())
        changed=copy.deepcopy(row);changed['objects'][0]['fitted_box']['world']['centroid']=[.9,0,0]
        dual=join(changed,converted)[0]
        self.assertEqual(dual['extent_readings']['as_full']['stage'],'S4')
        self.assertEqual(dual['extent_readings']['as_half']['stage'],'S5')
        self.assertEqual(dual['stage'],'U')
        # Pin exact reader resize, including its endpoint-aligned scipy sampling.
        from scipy import ndimage
        m=np.arange(480*640).reshape(480,640)%7==0
        np.testing.assert_array_equal(resize(m,(240,320)),ndimage.zoom(m,(.5,.5),order=0,prefilter=False))


if __name__=='__main__':unittest.main()
