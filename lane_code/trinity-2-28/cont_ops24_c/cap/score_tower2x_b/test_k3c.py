"""Verify the registered decode control and A-prime baseline with camera fixtures."""
import copy
import unittest
import numpy as np
from test_score import fixture, trajectory
import score as S

def inputs():
    data,ref=fixture()
    ref.update(labels=["A'",'B'],baseline="A'",control_limit_deg=1.,control_required=8,active_comparisons=['B'])
    for r in data['rows']:r['arms']=r['arms'][:2]
    for r in ref['captures']:r['arms']=r['arms'][:2]
    return data,ref

def alter_controls(ref, count):
    for r in ref['captures'][:count]:r['t1']=trajectory(50).tolist()

class K3c(unittest.TestCase):
    def test_eight_pass_and_seven_void(self):
        for failures,want in [(0,'confirm'),(2,'confirm'),(3,'void')]:
            data,ref=inputs();alter_controls(ref,failures)
            out=S.score(data,ref)
            self.assertEqual(out['verdict'],want)
            self.assertEqual(out['decode_control']['passed_captures'],10-failures)
            self.assertEqual(out['decisions']['C']['verdict'],'skipped')
            if failures==3:self.assertIn('decode, not coverage',out['decisions']['B']['reason'])

    def test_control_uses_relative_rotation_and_one_degree(self):
        data,ref=inputs()
        for angle,want in [(.9,True),(1.1,False)]:
            c=trajectory();c[16:,:3,:3]=trajectory(angle)[8,:3,:3]
            # Normalize this fixture to a known all-pair RMS.
            actual=S.relative(c,trajectory())['rotation_deg']['rms']
            q=np.radians(angle/actual*angle*np.sin(8/5))
            c[16:,0,0]=c[16:,1,1]=np.cos(q);c[16:,0,1]=-np.sin(q);c[16:,1,0]=np.sin(q)
            ref['captures'][5]['t1']=(trajectory(50)[7]@c).tolist()
            out=S.score(data,ref)
            self.assertAlmostEqual(out['rows'][5]['control']['relative_rotation_rms_deg'],angle,places=8)
            self.assertEqual(out['rows'][5]['control']['passed'],want)

    def test_baseline_is_aprime_and_scale_ratio(self):
        data,ref=inputs();alter_controls(ref,2)
        for r in data['rows']:
            a=r['arms'][1];c=np.array(a['c2w']);c[:,:3,3]*=2;a['c2w']=c.tolist()
        out=S.score(data,ref)
        self.assertEqual(out['verdict'],'confirm')
        self.assertEqual(out['decisions']['B']['baseline_arm'],"A'")
        for r in out['rows']:self.assertAlmostEqual(r['arms']['B']['similarity']['scale_relative_to_baseline'],.5)
        self.assertIn("Scale/A'",S.render(out))

    def test_missing_baseline_or_b_is_incomplete(self):
        for arm in (0,1):
            data,ref=inputs();data['rows'][0]['arms'][arm]={'status':'budget'}
            self.assertEqual(S.score(data,ref)['verdict'],'incomplete')

    def test_void_has_precedence_over_missing_b(self):
        data,ref=inputs();alter_controls(ref,3);data['rows'][8]['arms'][1]={'status':'budget'}
        self.assertEqual(S.score(data,ref)['verdict'],'void')

    def test_stub_cannot_support_verdict(self):
        data,ref=inputs();alter_controls(ref,3);data['stub']=True
        self.assertEqual(S.score(data,ref)['verdict'],'synthetic')

    def test_threshold_boundaries(self):
        data,ref=inputs();rows=S.score(data,ref)['rows']
        for r in rows:
            r['arms']["A'"]['relative']['rotation_deg']['rms']=20 if r['group']=='failing' else 2
            r['arms']['B']['relative']['rotation_deg']['rms']=10 if r['group']=='failing' else 4
        self.assertEqual(S.decision(rows,baseline="A'",required=8)['verdict'],'confirm')
        rows[5]['arms']['B']['relative']['rotation_deg']['rms']=4.00001
        self.assertEqual(S.decision(rows,baseline="A'",required=8)['verdict'],'partial')
        for r in rows[:5]:
            r['arms']['B']['relative']['rotation_deg']['rms']=16
            r['arms']['B']['similarity']['classification']='gross'
        self.assertEqual(S.decision(rows,baseline="A'",required=8)['verdict'],'partial')
        rows[0]['arms']['B']['relative']['rotation_deg']['rms']=17
        rows[1]['arms']['B']['relative']['rotation_deg']['rms']=17
        rows[2]['arms']['B']['relative']['rotation_deg']['rms']=17
        self.assertEqual(S.decision(rows,baseline="A'",required=8)['verdict'],'refute')

if __name__=='__main__':unittest.main()
