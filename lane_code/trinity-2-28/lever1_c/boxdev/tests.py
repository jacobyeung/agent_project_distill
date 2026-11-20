"""CPU checks; synthetic scores are fixtures, never dev evidence."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import run as B
import hashlib,json,tempfile,types,unittest
from unittest.mock import patch
import numpy as np
B.setup();R=B.R
ROOT=Path(tempfile.mkdtemp(prefix='test_',dir=B.HERE))

def fixture():
    refs={r['item_id']:r for r in json.loads((R.KIT/'items544.json').read_text())['items']}
    C=np.repeat(np.eye(4)[None],32,0);C[:,:3,:3]=[[1,0,0],[0,0,1],[0,-1,0]]
    C[1:4,0,3]=.2
    K=np.repeat(np.array([[320.,0,320],[0,240,240],[0,0,1]])[None],32,0)
    A=np.repeat(np.diag([.64,.48,1.])[None],32,0)
    uv=np.linspace(0,1000,51);depth=np.broadcast_to(4.+uv[None,:,None]/2000+uv[None,None,:]/2000,(32,51,51)).copy()
    g=R.geometry.from_arrays(K=K,canvas_to_source=A,camera_to_world=C,scale=1.,depth_grid=depth,grid_uv=uv,anchor_frame_indices=list(range(32)))
    masks=[]
    for j in range(2):
        m=np.zeros((32,240,320),bool);m[:4,60:64,60+j*60:64+j*60]=True;masks.append(m)
    from gpkg.runtime.c import rle
    rows={};depths={}
    for iid,ref in refs.items():
        nn=R.names(ref)[0];ms=dict(zip(nn,masks));values,_=B.base_objects(nn,ms,g);gap=R.round_gap(R.gap_value(values))
        rows[iid]=dict(item_id=iid,pass_index=0,capture=ref['capture'],source_indices=ref['source_indices'],
          objects=[dict(name=n,selected_masks={str(f+1):rle(m[f]) for f in range(4)}) for n,m in zip(nn,masks)],
          calls=[dict(served=True,call=f'<gap a="{nn[0]}" b="{nn[1]}" rule="box_grid_5cm">',response=f'distance {gap:.2f} m')])
        meta=dict(capture=ref['capture'],frame_binding_sha256=ref['mapping']['frame_binding_sha256'],geometry=dict(K=K.tolist(),canvas_to_source=A.tolist(),camera_to_world_metric=C.tolist(),source_indices=ref['source_indices']))
        depths[ref['capture']]=dict(R.fmt.encode(g,meta),parity=dict(trusted=True))
    d=ROOT/'0.gz';w=R.fmt.Writer(d)
    for row in depths.values():w.append(row)
    w.close()
    c=ROOT/'capture.gz';w=R.fmt.Writer(c)
    for row in rows.values():w.append(row)
    w.close()
    receipt=ROOT/'4.json';B.write(receipt,dict(verified=True,sha256=R.sha(d),bytes=d.stat().st_size))
    return refs,rows,depths,g,masks,d,c,receipt

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.fx=fixture()

    def test_01_lossless_dump_and_base_equals_relift(self):
        refs,rows,depths,g,masks,d,c,receipt=self.fx
        for iid,ref in refs.items():
            restored=R.restore(depths[ref['capture']]);np.testing.assert_array_equal(restored.depth_grid,g.depth_grid)
            nn=R.names(ref)[0];ms=dict(zip(nn,masks))
            expected=R.round_gap(R.gap_value([R.fit_lift(n,ms[n],restored)[0] for n in nn]))
            self.assertEqual(B.arm(nn,ms,restored,'base')['gap_m'],expected)

    def test_02_full_150_synthetic_command(self):
        refs,rows,depths,g,masks,d,c,receipt=self.fx
        out=ROOT/'BOXDEV_SYNTHETIC.json'
        B.write(ROOT/'STOP',dict(status='STOP',reason='previous failure fixture'))
        with patch.object(R,'T1_SHA',R.sha(c)):
            code=B.main(['--depth',str(d),'--receipt',str(receipt),'--capture',str(c),'--out',str(out)])
        self.assertEqual(code,0)
        self.assertEqual(json.loads((ROOT/'STOP').read_text())['status'],'CLEARED')
        report=json.loads(out.read_text());self.assertEqual(len(report['rows']),150)
        self.assertTrue(report['base_equals_relift_a']);self.assertTrue(report['parity']['passed'])
        self.assertEqual([s['dataset'] for s in report['statistics']],['all','ARKit','ScanNet','ScanNet++'])
        B.write(B.HERE/'SYNTHETIC_MEASUREMENTS.json',dict(synthetic=True,hardware=report['hardware'],cost=report['cost'],objects=report['rows'][0]['measurements']))

    def test_03_failed_gate_never_evaluates_arms(self):
        refs,rows,depths,g,masks,d,c,receipt=self.fx
        bad={i:dict(r,calls=[dict(served=True,call='<gap a="a" b="b">',response='distance 999.00 m')]) for i,r in rows.items()}
        with patch.object(R,'read_records',return_value=bad),patch.object(B,'timed',side_effect=AssertionError('arm evaluated')) as arm:
            code=B.main(['--depth',str(d),'--receipt',str(receipt),'--out',str(ROOT/'bad/BOXDEV.json')])
            self.assertEqual(code,2);arm.assert_not_called()
        self.assertEqual(json.loads((ROOT/'bad/STOP').read_text())['status'],'STOP')

    def test_04_seed_and_registered_upper_bound(self):
        refs={str(i):dict(task=dict(room=str(i))) for i in range(3)}
        rows=[dict(room=str(i),dataset=d,base=50,vote=50+x,delta=x) for i,(d,x) in enumerate(zip(('ARKit','ScanNet','ScanNet++'),(-10,0,20)))]
        a=B.statistics(rows,refs);b=B.statistics(rows,refs);self.assertEqual(a,b)
        import random
        rng=random.Random(20261120);expected=[]
        for _ in range(10000):expected.append(np.mean([[-10,0,20][rng.choice(range(3))] for _ in range(3)]))
        np.testing.assert_array_equal(a[0]['paired_difference']['ci95'],np.percentile(expected,[2.5,97.5]))
        self.assertFalse(a[1]['does_not_lose']);self.assertTrue(a[2]['does_not_lose'])
        B.write(B.HERE/'BOOTSTRAP_TEST.json',dict(seed=20261120,draws=10000,ci95=a[0]['paired_difference']['ci95'],passed=True))

    def test_05_real_t1_capture_depth_free(self):
        refs=self.fx[0];rows=R.read_records(R.BASE/'cap/t1.gz',refs)
        checks=R.depth_free_parity(rows,refs)
        self.assertGreaterEqual(len(checks),20);self.assertTrue(all(c['match'] for c in checks))
        B.write(B.HERE/'REAL_T1_CHECK.json',dict(items=len(rows),checks=checks,passed=True,scope='real T1 stored boxes and printed gaps; no real depth available'))

    def test_06_frozen_vote_and_rendered_change(self):
        _,_,_,g,masks,*_=self.fx;names=['a','b'];ms=dict(zip(names,masks))
        obs={n:B.lift_frames(n,ms[n],g,R.grounding) for n in names}
        expected=B.session_distance(dict(operands=names,gt_instances={}),g,obs,R.grounding,B.RULE)[0]
        vote=B.arm(names,ms,g,'vote');base=B.arm(names,ms,g,'base')
        self.assertEqual(vote['gap_m'],expected)
        self.assertNotEqual(base['responses'],vote['responses'])
        self.assertEqual(vote['objects'][0]['lift_calls'],4);self.assertEqual(base['objects'][0]['lift_calls'],5)
        B.write(B.HERE/'RENDER_TEST.json',dict(base=base['responses'],vote=vote['responses'],changed=True))

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    B.write(B.HERE/'TEST_RESULTS.json',dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),passed=result.wasSuccessful(),fixture=str(ROOT)))
    raise SystemExit(not result.wasSuccessful())
