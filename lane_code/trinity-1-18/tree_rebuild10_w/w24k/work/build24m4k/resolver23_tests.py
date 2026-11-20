from pathlib import Path
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import importlib.util,json,sys,unittest
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build24m4k/proofs/resolver23'
sys.path[:0]=[str(Path(__file__).resolve().parent), '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24k/work/tree_r1']
sys.path[:0]=[str(Path(__file__).resolve().parent), '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24k/work/tree_r1']
import joblib as J
import resolver21e as R
D.mkdir(parents=True,exist_ok=True)
R.K=L/'work/build24/kits/q';R.D=D/'f';R.D.mkdir(exist_ok=True)
class ResolverMinimal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f=R.fixture()
        import hashlib,tarfile
        original=J.load
        spec=deepcopy(original(R.K/'k/p.json'))
        with tarfile.open(cls.f['m']/'s.tar') as archive:spec['m4']['v']=hashlib.sha256(archive.extractfile('MANIFEST.json').read()).hexdigest()
        marker=(cls.f['pool']/spec['p_root']/'o/gcs_6ed2c7aa_m400.done').read_text().split();spec['m4'].update(t=marker[2],b=int(marker[1]))
        cls.pin_patch=patch.object(J,'load',side_effect=lambda p:deepcopy(spec) if Path(p)==R.K/'k/p.json' else original(p));cls.pin_patch.start()
    @classmethod
    def tearDownClass(cls):cls.pin_patch.stop()
    def test_real_base_and_preserved_N_streams(self):
        template=J.load(R.K/'k/n.json')
        with R.external_boundary(self.f):result=J.resolve(R.K,self.f['pool'],self.f['listing'],D/'resolved.json')
        self.assertEqual(result['request']['routing_base'],result['config']['streams']['routing'])
        self.assertEqual(result['request']['routing_base']['sha256'],'ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984')
        self.assertNotIn('routing_inputs',result['request'])
        for name in ('pose','vqa','pointing'):self.assertEqual(result['config']['streams'][name],template['streams'][name])
        spec=importlib.util.spec_from_file_location('old23','/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24k/work/build24m4k/old23.py')
        old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
        with R.external_boundary(self.f,module=old):before=old.resolve(R.K,self.f['pool'],self.f['listing'],D/'resolved_before.json')
        self.assertNotEqual(before['config']['streams']['vqa'],template['streams']['vqa'])
        J.write(D/'RESOLVER.json',dict(status='PASS',old_overwrites_N_vqa=True,new_preserves_N_streams=True,routing_base=result['request']['routing_base'],identity_checks_unchanged=True))
    def test_different_base_refuses(self):
        original=J.load;cfg=deepcopy(original(R.K/'k/n.json'));cfg['streams']['routing']['sha256']='0'*64
        with R.external_boundary(self.f),patch.object(J,'load',side_effect=lambda p:cfg if Path(p)==R.K/'k/n.json' else original(p)):
            with self.assertRaisesRegex(ValueError,'^E55$'):J.resolve(R.K,self.f['pool'],self.f['listing'],D/'bad_resolved.json')
if __name__=='__main__':
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ResolverMinimal))
    J.write(D/'RESOLVER_TESTS.json',dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),successful=r.wasSuccessful()))
    raise SystemExit(not r.wasSuccessful())
