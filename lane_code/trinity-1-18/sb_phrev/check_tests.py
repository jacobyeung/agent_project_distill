"""Run the shipped behavioral tests without executing their output-writing main; add an independent vector probe."""
import hashlib, json, sys, unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
SRC=ROOT.parent/'sb_mask_phrase'
sys.path.insert(0,str(SRC))
import test_kit as shipped
import kit as K
import aggregate as G

class IndependentProbe(unittest.TestCase):
    def test_alias_candidates_and_vectors_rebuilt_from_original_cache(self):
        caps,ctx=K.setup(threads=8)
        c=next(c for c in caps if c['canonical']=='scannetpp/067e2e4e61')
        geo,cache,*_=K.T.R.geometry(c);F=K.T.F
        frames=[]
        for f in range(32):
            rec=cache['frames'][str(f)]['phrases']['heater']
            entries=sorted([e for e in rec['instances'] if e['source_prompt']=='radiator'],key=lambda e:-e['score'])
            entries=[e for e in entries if e['score']*e['source_presence']>=.05][:30]
            fr=[]
            for e in entries:
                r=e['mask'];mask=np.repeat(np.arange(len(r['counts']))%2==1,r['counts']).reshape(r['size'],order='F')
                fr.append(dict(mask=F.resize(mask,F.SHAPE),score=e['score'],presence=e['source_presence']))
            frames.append(fr)
        stage=K.T.StageOne(lambda name:frames,ctx[4],geo,rule='candidates_argmax')
        got,x=stage.features('radiator')
        props,_=F.candidates.lift(F.cache_for('radiator',frames),'radiator',geo,floor=.3,grids=stage.grids,phrase='radiator')
        tracks=F.candidates.link(props,'radiator');F.candidates.scene_candidates({'radiator':tracks},geo)
        expected=F.accept_features(tracks,frames,F.Geometry(geo))
        y=stage.SI.candidate_vectors(tracks,frames,F.Geometry(geo),expected)
        self.assertGreater(len(expected),0)
        self.assertEqual([a['candidate_id'] for a in got],[a['candidate_id'] for a in expected])
        np.testing.assert_array_equal(x,y)
        for p in props:
            e=frames[p.frame-1][p.index]
            self.assertEqual((p.score,p.presence),(e['score'],e['presence']))
        rawstage=K.T.StageOne(K.P.cache_detect(cache),ctx[4],geo,rule='candidates_argmax')
        raw,rx=rawstage.features('heater')
        self.assertNotEqual([a['candidate_id'] for a in raw],[a['candidate_id'] for a in got])
        self.assertFalse(np.array_equal(np.asarray(rx),np.asarray(x)))

    def test_distance_labels_are_not_accessed_by_choice(self):
        class Object(dict):
            def __getitem__(self,key):
                if key in ('label','prediction','distance'):raise AssertionError('distance accessed')
                return super().__getitem__(key)
            def get(self,key,*args):
                if key in ('label','prediction','distance'):raise AssertionError('distance accessed')
                return super().get(key,*args)
        fit=[Object(fold=1,on_target={'raw':False,'q:radiator':True}) for _ in range(5)]
        held=[Object(fold=0,on_target={'raw':True,'q:radiator':False}) for _ in range(30)]
        self.assertEqual(G.choose(fit+held,['q:radiator'],0)[0],'q:radiator')
        for o in held:o['on_target']={'raw':False,'q:radiator':True}
        self.assertEqual(G.choose(fit+held,['q:radiator'],0)[0],'q:radiator')

def main():
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(shipped),unittest.defaultTestLoader.loadTestsFromTestCase(IndependentProbe)])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    pins=dict(K.T.PINS)
    paths=[ROOT/'check_tests.py',ROOT/'run_review.sh',SRC/'kit.py',SRC/'aggregate.py',SRC/'test_kit.py',
           SRC/'out/DECISION.json',SRC/'out/PER_ITEM.jsonl',SRC/'out/OBJECTS.json',SRC/'out/BARS.json',
           SRC/'work/BARS.sha256',SRC/'work/A0_ROWS.json']+list((SRC/'work/caps2').glob('*.json.gz'))
    for p in paths:pins[str(p)]=K.sha(p)
    out=dict(command='bash run_review.sh check_tests.py',ran=result.testsRun,passed=result.wasSuccessful(),
             failures=[(str(t),e) for t,e in result.failures],errors=[(str(t),e) for t,e in result.errors],input_sha256=pins)
    (ROOT/'TEST_AUDIT.json').write_text(json.dumps(out,indent=1)+'\n')
    sys.exit(not result.wasSuccessful())
if __name__=='__main__':main()
