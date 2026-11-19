"""Before controls for the new admission bindings, with one reusable mutant directory."""
from pathlib import Path
from unittest.mock import patch
import ast,importlib.util,json,sys,os,unittest,io
L=Path(__file__).resolve().parents[2];B=L/'work/build21';T=L/'work/tree_r1';O=B/'proofs/new_controls';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(T),str(B)]
from student_pilot.p3_provenance import load
from student_pilot import r1_rooms as rooms
cfg=load(B/'inputs/config.json');audit=cfg['r1_training']['room_audit']
spec=importlib.util.spec_from_file_location('student_pilot.before_rooms',B/'base/student_pilot/r1_rooms.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
try:old.verify_audit(cfg,audit);before=False
except ValueError as e:before='K1_REMOVAL' in str(e)
rooms.verify_audit(cfg,audit);records=[dict(fix='verified K1 union',before_fails=before,after_passes=True)]
import review21,joblib as J
kit=B/'kits/q';p=kit/'k/p.json';saved=p.read_bytes()
from launch_r2.build import capsule_json
value=J.load(p);value['p_files'].pop('ANON_OK.json');p.write_bytes(capsule_json(value))
try:
 result=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.TestSuite([review21.Review21('test_anon_inventory')]))
 records.append(dict(mutation='missing ANON_OK staging entry',caught=not result.wasSuccessful()));assert not result.wasSuccessful()
finally:p.write_bytes(saved)
with patch.object(J,'screen',side_effect=lambda line,*args:line):
 result=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.TestSuite([review21.Review21('test_log_names')]))
 records.append(dict(mutation='raw log leak',caught=not result.wasSuccessful()));assert not result.wasSuccessful()
from student_pilot import job_env
with patch.object(job_env,'key',side_effect=lambda name:name):
 result=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.TestSuite([review21.Review21('test_env_aliases')]))
 records.append(dict(mutation='opaque environment names ignored',caught=not result.wasSuccessful()));assert not result.wasSuccessful()
import preflight_tests21
source=(T/'launch_r1/production_proof.py').read_text();target=B/'mutant/production_proof.py'
target.write_text(source.replace("            training_components(cfg['r1_training']['registry'], cfg)","            pass"))
spec=importlib.util.spec_from_file_location('launch_r1.mutant_production_proof',target);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
prior=preflight_tests21.Q;preflight_tests21.Q=mod
try:
 result=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.TestSuite([preflight_tests21.Preflight21('test_component_refusal_precedes_store_producers')]))
 records.append(dict(mutation='late component refusal',caught=not result.wasSuccessful()));assert not result.wasSuccessful()
finally:preflight_tests21.Q=prior
import opener_tests21
source=(T/'student_pilot/r2_openers.py').read_text();target=B/'mutant/r2_openers.py'
target.write_text(source.replace('start(start_context(receipt))','start(receipt)'))
spec=importlib.util.spec_from_file_location('student_pilot.mutant_openers',target);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
prior=opener_tests21.O;opener_tests21.O=mod
try:
 result=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.TestSuite([opener_tests21.Opener21('test_initialize_uses_full_context_and_witness')]))
 records.append(dict(mutation='initialize from incomplete receipt',caught=not result.wasSuccessful()));assert not result.wasSuccessful()
finally:opener_tests21.O=prior
import coverage_tests21
source=(T/'student_pilot/r1_rooms.py').read_text();target=B/'mutant/r1_rooms.py'
target.write_text(source.replace('if wording is not None:wording.check(row)','if False:wording.check(row)'))
spec=importlib.util.spec_from_file_location('student_pilot.mutant_rooms',target);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
with patch.object(rooms,'census',mod.census):
 result=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.TestSuite([coverage_tests21.Coverage21('test_census_planted_wording_refuses_by_name')]))
 records.append(dict(mutation='census ignores held-out wording',caught=not result.wasSuccessful()));assert not result.wasSuccessful()
assert before
(O/'RESULT.json').write_text(json.dumps(records,indent=2));print(json.dumps(records,indent=2))
