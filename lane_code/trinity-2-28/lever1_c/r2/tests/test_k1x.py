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

    def test_missing_gt_frame_preserves_pose_and_repins(self):
        geo,t,own,gt,meta=self.fixture()
        gt['depth'][0]=0
        a=np.zeros((32,51,51),bool);a[0,5:30,5:30]=True;a[1,8:19,8:19]=True
        b=np.zeros_like(a);b[2,29:40,29:40]=True
        row=dict(operands=['a','b'],gt_instances={'a':1,'b':2})
        for pose in ('GT','G3T'):
            g=K.swapped(geo,t,own,gt,meta,'GT',pose,'own',self.D)
            self.assertTrue(g.has(1));np.testing.assert_array_equal(g.cam(1)[0],g.C[0,:3,:3])
            obs=K.lifted({'a':a,'b':b},g,self.D)
            self.assertEqual(obs['a']['visible'],[2]);self.assertEqual(obs['a']['best'],2)
            out=K.predict(row,g,obs,self.D)
            self.assertIsNotNone(out['prediction']);self.assertEqual(out['selected_frames']['a'],2)
            self.assertTrue(out['gt_depth_support'])
        served=K.swapped(geo,t,own,gt,meta,'G3T','G3T','own',self.D)
        self.assertEqual(K.lifted({'a':a},served,self.D)['a']['best'],1)
        a[1]=False
        obs=K.lifted({'a':a,'b':b},g,self.D)
        self.assertFalse(obs['a']['seen']);self.assertIsNone(K.predict(row,g,obs,self.D)['prediction'])

    def test_gt_partial_holes_never_mix_zero_depth(self):
        geo,t,own,gt,meta=self.fixture()
        gt['depth'][:]=6.;gt['depth'][0,25,25]=0
        g=K.swapped(geo,t,own,gt,meta,'GT','G3T','GT',self.D)
        self.assertTrue(np.isnan(g.depth_grid[0,25,25]))
        values=g.depth(1,np.array([[500.,500.],[510.,510.],[520.,520.]]))
        self.assertTrue(np.isnan(values[0]));np.testing.assert_allclose(values[1:],6.)
        P,Pc,sp=g.lift(1,np.array([[510.,510.],[520.,520.]]))
        self.assertTrue(np.isfinite(P).all());np.testing.assert_allclose(Pc[:,2],6.)
        np.testing.assert_allclose(sp,0.)

    def test_box_base_and_floor_zero_exact(self):
        from box_followup import capture_box
        from types import SimpleNamespace
        geo,t,own,gt,meta=self.fixture()
        a=np.zeros((32,51,51),bool);a[0,8:19,8:19]=True
        b=np.zeros_like(a);b[2,29:40,29:40]=True
        masks={m:{'a':a,'b':b} for m in ('GT','deployed')}
        objects={m:K.lifted(ms,geo,self.D) for m,ms in masks.items()}
        r=dict(id='test',operands=['a','b'],gt_instances={'a':1,'b':2})
        result=capture_box(dict(rows=[r]),geo,masks,objects,self.D,SimpleNamespace(freeze='vote_10_3_best'))['test']
        for m in masks:
            expected=K.predict(r,geo,objects[m],self.D)
            self.assertEqual(K.clean(result[m+'/base']),K.clean(expected))
            self.assertEqual(K.clean(result[m+'/floor_0']),K.clean(expected))

    def test_e3_fused_provider_exact_including_point_cap(self):
        from e3_box import fused_objects
        from trace_format.box_v313 import FusedBoxProvider,in_f1
        geo,t,own,gt,meta=self.fixture()
        points=np.random.default_rng(9).normal(size=(22000,3))
        obj=dict(seen=True,frames=[1,2],best=1,points={'1':points[:11000],'2':points[11000:]})
        raw=fused_objects({'a':obj})['a']['boxes']['e3_fused']
        got=in_f1(geo,raw['centroid'],raw['axesLengths'],raw['normalizedAxes'])
        self.assertEqual(K.clean(got),K.clean(FusedBoxProvider()('a',obj,geo,1)))

    def test_valid_support_is_paired_and_keeps_supported_refusals(self):
        from summarize_round4 import paired
        rows=[]
        for i,(a,b) in enumerate(((True,True),(True,False),(False,True))):
            rows.append(dict(row_id=str(i),room=str(i),label=1.,cells={
                'a':dict(prediction=None,gt_depth_support=a),
                'b':dict(prediction=1.,gt_depth_support=b)}))
        allrows=paired(rows,'a','b',False);valid=paired(rows,'a','b',True)
        self.assertEqual(allrows['n'],3);self.assertEqual(valid['n'],1)
        self.assertEqual(valid['row_ids'],['0']);self.assertEqual(valid['answered_arm'],0)
        self.assertEqual(valid['delta']['mean'],-100.)

    def test_area_floor_selection_ignores_heldout(self):
        from box_followup import select_floor,FLOORS
        rows=[]
        for i in range(6):
            rows.append(dict(row_id=str(i),room=str(i),label=1.,
                box={'deployed/floor_'+str(f):dict(prediction=1. if f==0 else None) for f in FLOORS}))
        ids={str(i) for i in range(5)}
        a=select_floor(rows,ids)
        for value in rows[-1]['box'].values():value['prediction']=100.
        self.assertEqual(a,select_floor(rows,ids));self.assertEqual(a['floor'],0)

    def test_oracle_failure_scoped_to_operand(self):
        geo,t,own,gt,meta=self.fixture()
        box=dict(centroid=np.zeros(3),axesLengths=np.ones(3),normalizedAxes=np.eye(3))
        objects={n:dict(seen=True,boxes={'best1':box}) for n in ['a','b','missing']}
        c=dict(canonical='example',gt_name_ids={'a':[1],'b':[2],'missing':[3]})
        boxes={('example',i):dict(status='full' if i!=3 else 'unknown',box=box) for i in [1,2,3]}
        result=K.extent_objects(c,objects,gt,geo,boxes,'oracle_extent')
        self.assertNotIn('oracle_error',result['a']);self.assertNotIn('oracle_error',result['b'])
        self.assertEqual(result['missing']['oracle_error'],'unresolved_extent_convention')
        out=K.predict(dict(operands=['a','missing']),geo,result,self.D)
        self.assertFalse(out['input_available'])
        centre=K.extent_objects(c,objects,gt,geo,boxes,'oracle_centre')
        self.assertTrue(all('oracle_error' not in v for v in centre.values()))

    def test_endpoint_program_prints_and_copied_program(self):
        geo,t,own,gt,meta=self.fixture()
        mask=np.zeros((32,51,51),bool);mask[0,8:19,8:19]=True
        maskb=np.zeros_like(mask);maskb[2,29:40,29:40]=True
        masks={'a':mask,'b':maskb};r=dict(operands=['a','b'],gt_instances={'a':1,'b':2})
        base=K.predict(r,geo,K.lifted(masks,geo,self.D),self.D)
        no_swap=K.swapped(geo,t,own,gt,meta,'G3T','G3T','own',self.D)
        repeated=K.predict(r,no_swap,K.lifted(masks,no_swap,self.D),self.D)
        self.assertEqual(K.clean(base),K.clean({k:repeated[k] for k in base}))
        endpoint=K.swapped(geo,t,own,gt,meta,'GT','GT','GT',self.D)
        direct=self.D.geometry.from_arrays(K=geo.K,canvas_to_source=geo.A,camera_to_world=gt['c2w'],
            depth_grid=K.sample_gt(gt,t['grid_uv']),grid_uv=t['grid_uv'],scale=1.,anchor_frame_indices=K.c_anchors(geo))
        got=K.predict(r,endpoint,K.lifted(masks,endpoint,self.D),self.D)
        expected=K.predict(r,direct,K.lifted(masks,direct,self.D),self.D)
        self.assertEqual(got['prediction'],expected['prediction']);self.assertEqual(got['refusal'],expected['refusal'])
        for n in expected['printed']:
            for k in expected['printed'][n]:np.testing.assert_allclose(got['printed'][n][k],expected['printed'][n][k],rtol=0,atol=1e-12)
        self.assertIsNotNone(got['prediction'])
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
        p=K.ROOT/'out4/PARITY.json'
        if not p.exists():p=K.ROOT/'out/PARITY.json'
        if not p.exists():self.skipTest('full raster parity has not run')
        r=json.loads(p.read_text());self.assertTrue(r['passed'])
        for p in r['parity']:self.assertEqual(p['exact_prints'],1037)
        self.assertEqual(len(r['checks']),2074)

    def test_complete_population_when_available(self):
        path=K.ROOT/'out4/K1X4.json'
        r=json.loads((path if path.exists() else K.ROOT/'out/K1X.json').read_text())
        if r.get('contract')!=K.CONTRACT or r.get('status')=='AWAITING_HEAVY_IO_APPROVAL':self.skipTest('full factorial has not run')
        self.assertEqual(r['status'],'COMPLETE');self.assertEqual(len(r['rows']),1253)
        self.assertEqual(len({x['row_id'] for x in r['rows']}),1253)
        for row in r['rows']:self.assertEqual(set(row['cells']),set(K.CELLS+K.EXTRAS))
        self.assertEqual(r['tables']['heldout']['all'][K.BASE]['n'],216)
        self.assertEqual(r['tables']['train1012']['all'][K.BASE]['n'],1012)
        self.assertEqual(r['tables']['train']['all'][K.BASE]['n'],1037)
        if path.exists():self.assertLessEqual(len((K.ROOT/'out4/REPORT_R2_4.md').read_text().splitlines()),60)

    def test_round4_served_cells_unchanged_per_row(self):
        path=K.ROOT/'out4/K1X4.json'
        if not path.exists():self.skipTest('round 4 has not finished')
        new=json.loads(path.read_text());old=json.loads((K.ROOT/'out/K1X.json').read_text())
        reference={r['row_id']:r for r in old['rows']}
        cells=[c for c in K.CELLS if c.split('/')[1]=='G3T']
        for r in new['rows']:
            for c in cells:
                for field in ('prediction','refusal','printed'):
                    self.assertEqual(r['cells'][c][field],reference[r['row_id']]['cells'][c][field],(r['row_id'],c,field))

    def test_box_full_base_parity_and_train_only_freeze(self):
        path=K.ROOT/'out_box/BOX.json'
        if not path.exists():self.skipTest('BOX has not finished')
        result=json.loads(path.read_text())
        self.assertEqual(len(result['base_parity']),2506)
        self.assertTrue(all(c['passed'] for c in result['base_parity']))
        heldout={r['room'] for r in result['rows'] if r['split']=='heldout'}
        self.assertFalse(heldout&set(result['freeze']['room_folds']))
        for r in result['rows']:
            if r['split']=='heldout':
                self.assertEqual({k for k in r['box'] if '/floor_' in k},
                    {m+'/floor_'+str(result['freeze']['floor']) for m in ('GT','deployed')})

if __name__=='__main__':unittest.main()
