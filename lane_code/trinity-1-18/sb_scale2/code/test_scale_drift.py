import sys
sys.dont_write_bytecode=True
import unittest
from pathlib import Path
import numpy as np
import scale_drift as a
class Tests(unittest.TestCase):
    def test_folds(self):
        b=a.read(a.BASE/'out/BARS_FROZEN.json')
        for f in b['folds']:
            self.assertFalse(set(f['fit_rooms'])&set(f['test_rooms']))
        self.assertEqual(b['folds'][0]['fit_rooms'],b['folds'][1]['test_rooms'])
        if (a.OUT/'BARS_FROZEN.json').exists():
            self.assertEqual(a.read(a.OUT/'BARS_FROZEN.json')['folds'],b['folds'])
    def test_dataset_fit_isolation(self):
        r=[dict(room=room,dataset=ds,gt=np.array([g]),pred={'A':np.array([1.])}) for room,ds,g in [('fit','x',2.),('test','x',999.),('fit','y',99.)]]
        c=a.s.fit([x for x in r if x['dataset']=='x'],{'fit'},'A')
        self.assertAlmostEqual(c,2.)
        r[1]['gt'][:]=.001; r[2]['gt'][:]=.001
        self.assertAlmostEqual(c,a.s.fit([x for x in r if x['dataset']=='x'],{'fit'},'A'))
    def test_refusal(self):
        for name in a.SCORE_FILES:
            d=a.OUT/'refusal_tests'/name; d.mkdir(parents=True,exist_ok=True)
            (d/name).write_text('sentinel')
            with self.assertRaisesRegex(RuntimeError,'score file exists'): a.refuse(d)
    def test_refusal_is_zero_score(self):
        v,_=a.metric([dict(room='x',p=[np.nan,1.],gt=[1.,1.])])
        self.assertEqual(v['mra'],50.)
        self.assertEqual(v['refusals'],1)
    def test_strict_mra_parity(self):
        p=np.array([1.,1.05,1.1,1.5,np.nan]); g=np.ones(5)
        self.assertTrue(np.allclose(a.s.pair_scores(p,g),[100*a.s.mra(x,1.) for x in p]))
if __name__=='__main__': unittest.main()
