import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import score as S
BASE=HERE.parents[1]/'gbuild'
KIT=BASE/'orchard_tower2x_b'
spec=importlib.util.spec_from_file_location('worker',KIT/'2.py')
W=importlib.util.module_from_spec(spec);spec.loader.exec_module(W)

def trajectory(angle=0):
    t=np.arange(32)/5
    c=np.tile(np.eye(4),(32,1,1));c[:,:3,3]=np.c_[np.cos(t),np.sin(t),t/10]
    q=np.radians(angle*np.sin(t))
    c[:,0,0]=c[:,1,1]=np.cos(q);c[:,1,0]=np.sin(q);c[:,0,1]=-np.sin(q)
    return c

def fixture(fix=True):
    refs,rows=[],[]
    anchor=list(range(0,187,6))
    plans=[anchor,sorted(anchor+list(range(3,186,6))),sorted(anchor+list(range(2,186,6))+list(range(4,186,6)))]
    for k in range(10):
        gt,before=trajectory(),trajectory(120 if k<5 else 0)
        ref=dict(key=str(k),capture=str(k),group='failing' if k<5 else 'reference',
                 t1=before.tolist(),gt=gt.tolist(),scale=1.,gravity=[0.,0.,1.],arms=[])
        row=dict(key=str(k),arms=[])
        for a,ids in enumerate(plans):
            slots=[ids.index(i) for i in anchor]
            plan=dict(ids=ids,slots=slots,sha256=[f'{i:064x}' for i in ids],raw_sha256=[f'{i+1:064x}' for i in ids])
            full=np.tile(np.eye(4),(len(ids),1,1));full[slots]=before if a==0 or not fix else gt
            row['arms'].append(dict(status='ok',**plan,c2w=full.tolist(),scale=1.,gravity=ref['gravity']))
            ref['arms'].append(plan)
        refs.append(ref);rows.append(row)
    return dict(rows=rows,complete=True,stub=False),dict(captures=refs,labels=['A','B','C'])

class Scoring(unittest.TestCase):
    def test_confirm_and_refute_separate_arms(self):
        for fix,expected in [(True,'confirm'),(False,'refute')]:
            data,ref=fixture(fix)
            out=S.score(data,ref)
            self.assertEqual([out['decisions'][x]['verdict'] for x in 'BC'],[expected]*2)

    def test_control_void(self):
        data,ref=fixture();data['rows'][0]['arms'][0]['c2w']=trajectory().tolist()
        self.assertEqual(S.score(data,ref)['verdict'],'void')

    def test_missing_c_does_not_void_b(self):
        data,ref=fixture();data['complete']=False
        for r in data['rows']:r['arms'][2]=dict(status='budget')
        out=S.score(data,ref)
        self.assertEqual(out['decisions']['B']['verdict'],'confirm')
        self.assertEqual(out['decisions']['C']['verdict'],'incomplete')
        data['rows']=[]
        self.assertEqual(S.score(data,ref)['verdict'],'incomplete')

    def test_dropped_c_is_skipped(self):
        data,ref=fixture();ref['active_comparisons']=['B']
        for row,expected in zip(data['rows'],ref['captures']):
            row['arms'][2]=dict(status='unavailable');expected['arms'][2]=None
        out=S.score(data,ref)
        self.assertEqual(out['decisions']['B']['verdict'],'confirm')
        self.assertEqual(out['decisions']['C']['verdict'],'skipped')

    def test_synthetic(self):
        data,ref=fixture();data['stub']=True
        self.assertEqual(S.score(data,ref)['verdict'],'synthetic')

    def test_reference_regression(self):
        data,ref=fixture()
        a=data['rows'][5]['arms'][1];full=np.array(a['c2w']);full[a['slots']]=trajectory(10);a['c2w']=full.tolist()
        self.assertEqual(S.score(data,ref)['verdict'],'partial')

    def test_similarity_scale_relative_to_A(self):
        data,ref=fixture()
        for row in data['rows']:
            for a,factor in enumerate((2.,4.,.5)):
                arm=row['arms'][a];c=np.array(arm['c2w']);c[:,:3,3]*=factor;arm['c2w']=c.tolist()
        out=S.score(data,ref)
        for row in out['rows']:
            for label,scale,ratio in [('A',.5,1.),('B',.25,.5),('C',2.,4.)]:
                fit=row['arms'][label]['similarity']
                self.assertAlmostEqual(fit['scale'],scale)
                self.assertAlmostEqual(fit['scale_relative_to_A'],ratio)
            self.assertFalse(row['arms']['B']['rigid']['accepted'])
            self.assertTrue(row['arms']['B']['similarity']['accepted'])

    def test_similarity_known_gauge(self):
        a=trajectory(22);g=trajectory(57)[5];b=g@a;b[:,:3,3]=3.4*(a[:,:3,3]@g[:3,:3].T)+[2.,-4.,1.]
        fit=S.similarity(a,b)
        self.assertAlmostEqual(fit['scale'],3.4)
        self.assertLess(fit['translation_rms_m'],1e-12)
        self.assertLess(fit['rotation_max_deg'],3e-6)

    def test_gravity_transport_and_gauge(self):
        a=trajectory()
        t=np.linspace(0,1,32);r=np.tile(np.eye(3),(32,1,1))
        r[:,1,1]=r[:,2,2]=np.cos(t);r[:,2,1]=np.sin(t);r[:,1,2]=-np.sin(t)
        a[:,:3,:3]=r
        err=S.gravity(a,a,[0,0,1])
        self.assertLess(err['max_deg'],2e-6)
        moved=trajectory(80)[3]@a
        np.testing.assert_allclose(S.gravity(moved,a,[0,0,1])['predicted_up'],err['predicted_up'],atol=1e-12)
        tilted=S.gravity(a,a,[1,0,0])
        self.assertAlmostEqual(tilted['mean_deg'],90.)
        self.assertAlmostEqual(tilted['max_deg'],90.)

    def test_bad_bindings_fail(self):
        for key in ('ids','slots','sha256','raw_sha256'):
            data,ref=fixture();data['rows'][0]['arms'][1][key]=list(reversed(data['rows'][0]['arms'][1][key]))
            with self.assertRaises(ValueError):S.score(data,ref)

    def test_degenerate(self):
        c=trajectory();c[:,:3,3]=0
        self.assertEqual(S.similarity(c,c)['classification'],'moderate')
        self.assertIsNone(S.similarity(c,c)['scale'])

    def test_k2_rigid_and_496_pairs(self):
        ref=json.loads((HERE.parent/'score_tower2x/REFERENCE.json').read_text())
        prior={r['capture']:r for r in json.loads((HERE.parent/'score_t1/CAMERA_SPLIT.json').read_text())['captures']}
        for r in ref['captures']:
            a,b=S.poses(r['t1']),S.poses(r['gt']);fit=S.rigid(a,b)
            for k in ('translation_rms_m','rotation_rms_deg','rotation_max_deg'):
                self.assertAlmostEqual(fit[k],prior[r['capture']]['rigid_fit'][k],places=6)
            pair=S.relative(a,b);self.assertEqual(pair['pairs'],496)
            self.assertAlmostEqual(pair['rotation_deg']['rms'],prior[r['capture']]['relative_errors']['rotation_deg']['rms'],delta=1e-5)
            gravity=S.gravity(a,b,r['gravity'])
            up=a[:,:3,:3].transpose(0,2,1)@np.array([0.,0.,1.])
            np.testing.assert_allclose(gravity['predicted_up'],up,atol=1e-10)

    def test_63_94_bindings(self):
        data,_=fixture();row=dict(x4=[])
        for a in data['rows'][0]['arms']:
            row['x4'].append(dict(x0=a['ids'],x1=a['sha256'],x2=a['slots'],x3=a['sha256'],x5=[False]*len(a['ids']),x6=a['raw_sha256']))
        self.assertEqual([len(W.binding(row,a)[0]) for a in range(3)],[32,63,94])
        self.assertFalse(set(row['x4'][1]['x0'])<=set(row['x4'][2]['x0']))

    def test_deadline_and_arm_order(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        cfg=json.loads((BASE/'orchard_tower2x/1.json').read_text())
        cfg.update(xq=20,xr=[0,1,2],xs=3.,xt=True)
        for row in cfg['x3']:row['x4']=[{}, {}, {}]
        class Fake:
            def __init__(self,*args):
                self.pt=SimpleNamespace(cuda=SimpleNamespace(max_memory_allocated=lambda:0,max_memory_reserved=lambda:0))
            def run(self,row,arm):return dict(status='ok',seconds=0.)
        with patch.object(W,'Engine',Fake):
            out=W.run(cfg)
            self.assertTrue(out['complete'])
            self.assertEqual(out['ran'],[[r,a] for a in range(3) for r in range(10)])
            cfg['xe']=0
            out=W.run(cfg)
            self.assertTrue(out['finished']);self.assertFalse(out['complete']);self.assertEqual(out['ran'],[])
            self.assertTrue(all(a['status']=='budget' for r in out['rows'] for a in r['arms']))

if __name__=='__main__':unittest.main()
