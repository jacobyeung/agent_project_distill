"""Run the native kit tests against the newly sealed upload set."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import json,os,sys,unittest
L=Path(__file__).resolve().parents[2];D=L/'work/build22';B=L/'work/build21';K=D/'kits/q'
sys.path[:0]=[str(D),str(B),str(L/'work/tree_r1')]
os.environ['B22_ROOM_FIXTURE']=str(D/'proofs/capacity/600/request_config.json')
import joblib as J,naming22 as N,jobtest,review21,resolver21e
from launch_r2.build import capsule_json
jobtest.B=review21.B=D;review21.scan_decoded=N.scan_decoded
resolver21e.K=K;resolver21e.D=D/'proofs/resolver';resolver21e.D.mkdir(parents=True,exist_ok=True)
class NewKit22(unittest.TestCase):
    def test_bound_inputs_and_unchanged_code(self):
        cfg=J.load(K/'k/n.json');spec=J.load(K/'k/p.json')
        self.assertEqual(cfg['routing_opener_init'],'keep')
        self.assertEqual(cfg['r2_identity']['init']['step'],544)
        self.assertEqual(set(cfg['r1_training']['not_present_slots']),{'0','1'})
        from student_pilot.r1_launch22 import validate_removals
        from student_pilot.r1_coverage import validate_binding
        validate_removals(cfg);validate_binding(cfg)
        sources=J.load(Path(cfg['r1_training']['row_sources']['path']))
        components=J.load(Path(cfg['r1_training']['component_rows']['path']))
        required=[cfg['remove_files'][-1],cfg['r1_training']['camera_wording_exclusion'],
                  sources['camera_wording']['source'],cfg['r1_training']['component_rows'],
                  components['proven']['pose_family_record']['source']]
        required.extend(cfg['r1_training']['direction_twins'][key] for key in ('rows','binding','aliases','source_map'))
        for pin in required:
            self.assertIn(pin['sha256'],spec['pin_paths'])
        for name in ('b/z.py','k/j.json'):self.assertEqual((K/name).read_bytes(),(B/'kits/q'/name).read_bytes())
    def test_inventory_mutation(self):
        p=K/'k/c0.json';value=J.load(p);value['files'][next(iter(value['files']))]='0'*64;raw=capsule_json(value)
        original=Path.read_bytes;original_text=Path.read_text
        with patch.object(Path,'read_bytes',lambda q:raw if q==p else original(q)), \
             patch.object(Path,'read_text',lambda q,*a,**kw:raw.decode() if q==p else original_text(q,*a,**kw)):
            with self.assertRaisesRegex(ValueError,'SOURCE_INVENTORY'):N.scan_decoded(K)
    def test_helper_mutation(self):
        p=K/'b/o.py';text=p.read_text()+'\ndef helper(env):\n env["".join(["BeNcH","mArK"]) ]="q"\ne={**os.environ}\nhelper(env=e)\n'
        original=Path.read_text
        with patch.object(Path,'read_text',lambda q,*a,**kw:text if q==p else original(q,*a,**kw)):
            with self.assertRaisesRegex(ValueError,'ENV_UNRESOLVED'):N.scan_decoded(K)
    def test_component_name_remains_forbidden(self):
        p=K/'k/n.json';value=J.load(p);value['r1_training']['not_present_slots'][0]='heads_gf1_connector';raw=capsule_json(value)
        original=Path.read_bytes;original_text=Path.read_text
        with patch.object(Path,'read_bytes',lambda q:raw if q==p else original(q)), \
             patch.object(Path,'read_text',lambda q,*a,**kw:raw.decode() if q==p else original_text(q,*a,**kw)):
            with self.assertRaisesRegex(ValueError,'INPUT_NAME'):N.scan_decoded(K)
    def test_preserved_resolver_refuses_600(self):
        jobtest.Job20.setUpClass();root=jobtest.Job20.pool/jobtest.Job20.spec['milestone'];p=root/'DONE.json';saved=p.read_bytes()
        try:
            J.write(p,dict(step=600,ok=1,checkpoint_overlap='no'))
            with self.assertRaisesRegex(ValueError,'^E20$'):jobtest.Job20().resolve()
        finally:p.write_bytes(saved)
    def test_own_config_native_boundary(self):
        from launch_r1.production_proof import run
        from student_pilot.p3_provenance import file_pin
        root=D/'proofs/operator';root.mkdir(parents=True,exist_ok=True)
        p=root/'own_request_config.json';J.write(p,J.load(K/'k/n.json'));pin=file_pin(p)
        result=run(dict(config=pin,staged_pins=[pin]),root/'own_request')
        self.assertEqual(result['status'],'REFUSE')
        self.assertEqual(result['refusal'],'ValueError:R1_PROOF_NATIVE_ROUTING_REQUIRED')
        self.assertFalse(result['GO']);J.write(D/'NATIVE_KIT_BOUNDARY.json',result)
suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(NewKit22),
    unittest.defaultTestLoader.loadTestsFromTestCase(jobtest.Job20),
    unittest.defaultTestLoader.loadTestsFromTestCase(review21.Review21),
    unittest.defaultTestLoader.loadTestsFromTestCase(resolver21e.Resolver21e)])
result=unittest.TextTestRunner(verbosity=2).run(suite)
J.write(D/'KIT_TESTS.json',dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),successful=result.wasSuccessful()))
raise SystemExit(not result.wasSuccessful())
