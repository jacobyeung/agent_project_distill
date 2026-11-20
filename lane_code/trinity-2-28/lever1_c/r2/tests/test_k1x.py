"""Contract tests plus exact replay assertions when full-run outputs exist."""
import ast,json,hashlib
from pathlib import Path
import unittest
import numpy as np
import k1x as K


class FactorialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args=K.options(['test']);cls.D=K.dependencies(cls.args)

    def test_vendor_exact_sources(self):
        for r in json.loads((K.ROOT/'vendor/LADDER_COPIES.json').read_text()):
            a=Path(r['source']).read_bytes();b=Path(r['copy']).read_bytes()
            self.assertEqual(a,b);self.assertEqual(hashlib.sha256(a).hexdigest(),r['sha256'])

    def fixture(self):
        n=32;uv=np.linspace(0,1000,51)
        C=np.repeat(np.eye(4)[None],n,axis=0)
        C[:,:3,:3]=np.array([[1,0,0],[0,0,1],[0,-1,0]])
        C[:,0,3]=np.arange(n)*.02
        intr=np.repeat(np.array([[500.,0,500],[0,500,500],[0,0,1]])[None],n,axis=0)
        A=np.repeat(np.eye(3)[None],n,axis=0)
        yy,xx=np.meshgrid(uv,uv,indexing='ij')
        dep=np.broadcast_to(2+.0001*xx+.00005*yy,(n,51,51)).copy()
        geo=self.D.geometry.from_arrays(K=intr,canvas_to_source=A,camera_to_world=C,
            depth_grid=dep,grid_uv=uv,scale=2.,anchor_frame_indices=np.arange(n))
        gt=dict(depth=dep*3,c2w=C.copy(),valid=np.ones(n,bool))
        gt['c2w'][:,1,3]=np.arange(n)*.05
        tower=dict(depth_grid=dep,grid_uv=uv)
        own=dict(depth=dep*2)
        meta=dict(served_scale=2.,oracle_scale=3.)
        return geo,tower,own,gt,meta

    def test_unswapped_geometry_exact(self):
        geo,t,own,gt,meta=self.fixture()
        new=K.swapped(geo,t,own,gt,meta,'G3T','G3T','own',self.D)
        for name in ['C','K','A','depth_grid']:np.testing.assert_array_equal(getattr(geo,name),getattr(new,name))
        uv=np.array([[100.,100.],[505.,505.],[900.,700.]])
        for f in [1,14,32]:
            for a,b in zip(geo.lift(f,uv),new.lift(f,uv)):np.testing.assert_array_equal(a,b)

    def test_gt_endpoint_and_mixed_units(self):
        geo,t,own,gt,meta=self.fixture()
        new=K.swapped(geo,t,own,gt,meta,'GT','GT','GT',self.D)
        np.testing.assert_array_equal(new.C,gt['c2w'])
        np.testing.assert_array_equal(new.depth_grid,K.sample_gt(gt,t['grid_uv']))
        np.testing.assert_array_equal(new.K,geo.K)
        ownunit=K.swapped(geo,t,own,gt,meta,'GT','GT','own',self.D)
        np.testing.assert_allclose(ownunit.depth_grid,new.depth_grid*(2/3))
        np.testing.assert_allclose(ownunit.C[:,:3,3],new.C[:,:3,3]*(2/3))
        mixed=K.swapped(geo,t,own,gt,meta,'G3T','GT','own',self.D)
        np.testing.assert_array_equal(mixed.depth_grid,geo.depth_grid)
        np.testing.assert_array_equal(mixed.C,ownunit.C)

    def test_bounded_gt_rotation_precision(self):
        geo,t,own,gt,meta=self.fixture()
        exact=gt['c2w'].copy()
        gt['c2w'][0,0,1]+=3e-6
        repaired,receipt=K.gt_camera_poses(gt)
        self.assertEqual(len(receipt['repaired_anchors']),1)
        np.testing.assert_allclose(repaired[0,:3,:3]@repaired[0,:3,:3].T,np.eye(3),atol=1e-12)
        np.testing.assert_array_equal(repaired[:,:3,3],exact[:,:3,3])
        K.swapped(geo,t,own,gt,meta,'GT','GT','GT',self.D)
        gt['c2w'][0,0,1]=.01
        with self.assertRaises(ValueError):K.gt_camera_poses(gt)

    def test_endpoint_program_prints_and_copied_program(self):
        geo,t,own,gt,meta=self.fixture()
        mask=np.zeros((32,51,51),bool);mask[0,8:19,8:19]=True
        maskb=np.zeros_like(mask);maskb[2,29:40,29:40]=True
        masks={'a':mask,'b':maskb};r=dict(operands=['a','b'],gt_instances={'a':1,'b':2})
        base=K.predict(r,geo,K.lifted(masks,geo,self.D),self.D)
        no_swap=K.swapped(geo,t,own,gt,meta,'G3T','G3T','own',self.D)
        self.assertEqual(K.clean(base),K.clean(K.predict(r,no_swap,K.lifted(masks,no_swap,self.D),self.D)))
        endpoint=K.swapped(geo,t,own,gt,meta,'GT','GT','GT',self.D)
        direct=self.D.geometry.from_arrays(K=geo.K,canvas_to_source=geo.A,camera_to_world=gt['c2w'],
            depth_grid=K.sample_gt(gt,t['grid_uv']),grid_uv=t['grid_uv'],scale=1.,anchor_frame_indices=K.c_anchors(geo))
        got=K.predict(r,endpoint,K.lifted(masks,endpoint,self.D),self.D)
        expected=K.predict(r,direct,K.lifted(masks,direct,self.D),self.D)
        self.assertEqual(K.clean(got),K.clean(expected));self.assertIsNotNone(got['prediction'])
        source=K.declarations(self.args.ladder/'pricing.py',['lift_frames','session_distance'],
            dict(np=np,re=K.re,fusion_box=self.D.mathv.fusion_box))
        obs={n:dict(source.lift_frames(n,m,geo,self.D.G),boxes={}) for n,m in masks.items()}
        p,ref,raw,printed=source.session_distance(r,geo,obs,self.D.G)
        self.assertEqual(K.clean(base),K.clean(dict(prediction=p,refusal=ref,printed=printed)))

    def test_room_bootstrap_paired(self):
        rows=[dict(room='a')]+[dict(room='b')]*3
        got=K.bootstrap(rows,[0,100,100,100])[0]
        self.assertEqual(got['mean'],75.);self.assertEqual(got['ci95'],[0.,100.])
        got=K.bootstrap(rows,np.zeros((4,2)))
        self.assertEqual(got[0]['ci95'],[0.,0.]);self.assertEqual(got[0],got[1])

    def test_mechanical_gates(self):
        stats={k:dict(mean=0.,ci95=[-1.,1.]) for k in K.CONTRAST_PAIRS}
        stats['C1']=dict(mean=4.,ci95=[.1,7.])
        stats['C3_depth']=dict(mean=6.,ci95=[1.,10.])
        stats['C5']=dict(mean=-6.,ci95=[-8.,-4.])
        stats['C6']=dict(mean=5.,ci95=[.1,9.])
        v=K.verdicts(stats)
        self.assertEqual(v['C1'],'geometry pays now');self.assertEqual(v['C5'],'own depth cannot carry distance')
        self.assertTrue(v['arm_B_full_gate']['passed']);self.assertEqual(v['C6'],'opens arm C')
        stats['Pi3X']=dict(mean=3.,ci95=[.1,6.])
        v=K.verdicts(stats);self.assertFalse(v['arm_B_full_gate']['passed'])
        self.assertEqual(v['Pi3X'],'proposes a new pin')

    def test_scoring_thresholds(self):
        self.assertEqual(K.mra(None,1),0);self.assertEqual(K.mra(1,1),1)
        self.assertEqual(K.mra(1.25,1),.5);self.assertEqual(K.mra(1.5,1),0)

    def test_full_replay_when_available(self):
        p=K.ROOT/'out/PARITY.json'
        if not p.exists():self.skipTest('full raster parity has not run')
        r=json.loads(p.read_text());self.assertTrue(r['passed'])
        for p in r['parity']:self.assertEqual(p['exact_prints'],1037)
        self.assertEqual(len(r['checks']),2074)

    def test_complete_population_when_available(self):
        r=json.loads((K.ROOT/'out/K1X.json').read_text())
        if r.get('contract')!=K.CONTRACT or r.get('status')=='AWAITING_HEAVY_IO_APPROVAL':self.skipTest('full factorial has not run')
        self.assertEqual(r['status'],'COMPLETE');self.assertEqual(len(r['rows']),1253)
        self.assertEqual(len({x['row_id'] for x in r['rows']}),1253)
        for row in r['rows']:self.assertEqual(set(row['cells']),set(K.CELLS+K.EXTRAS))
        self.assertEqual(r['tables']['heldout']['all'][K.BASE]['n'],216)
        self.assertEqual(r['tables']['train1012']['all'][K.BASE]['n'],1012)
        self.assertEqual(r['tables']['train']['all'][K.BASE]['n'],1037)
        self.assertLessEqual(len((K.ROOT/'out/REPORT_R2.md').read_text().splitlines()),100)

if __name__=='__main__':unittest.main()
