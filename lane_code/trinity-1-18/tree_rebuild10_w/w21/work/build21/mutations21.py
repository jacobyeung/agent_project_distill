"""Reuse one mutant module directory; execute the corresponding regression test."""
from pathlib import Path
import importlib.util,json,sys,unittest,io
L=Path(__file__).resolve().parents[2];B=L/'work/build21';T=L/'work/tree_r1';M=B/'mutant';O=B/'proofs/mutations'
M.mkdir(exist_ok=True);O.mkdir(parents=True,exist_ok=True);sys.path[:0]=[str(T),str(B)]
from student_pilot import r1_coverage as C
import coverage_tests21 as tests
source=(T/'student_pilot/r1_coverage.py').read_text();records=[]
changes=[
 ('wording_guard',"if pattern.fullmatch(normalize(question)):","if False:",'test_wording_all_templates_unicode_and_native_reader'),
 ('wording_auth',"if pin.get('sha256')!=SPLIT:","if False:",'test_wording_authentication'),
 ('source_pair',"if extra and extra!=set(PINS):", "if False:",'test_source_binding'),
 ('source_pin',"if sources[name]['source']['sha256']!=h:","if False:",'test_source_binding'),
 ('union_order',"not hashes.index(base_hash)<hashes.index(pin['sha256'])<hashes.index(n_hash)","False",'test_union_content_authentication_and_order'),
 ('union_content',"if read_list(pin)!=expected:","if False:",'test_union_content_authentication_and_order'),
 ('union_conflict',"if row['row_key'] in values and values[row['row_key']]!=row:","if False:",'test_union_content_authentication_and_order'),
 ('geometry_equality',"if a!=b:","if False:",'test_rewording_changes_only_identifiers'),
 ('parent_identity',"or a['candidate_id']==b['candidate_id']", "or False",'test_rewording_changes_only_identifiers'),
]
for name,old,new,test in changes:
 assert old in source,name
 p=M/'r1_coverage.py';p.write_text(source.replace(old,new,1))
 spec=importlib.util.spec_from_file_location('student_pilot.mutation_coverage',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 tests.C=mod
 # Runtime reader imports use the same mutant while the single test runs.
 sys.modules['student_pilot.r1_coverage']=mod
 output=io.StringIO();result=unittest.TextTestRunner(stream=output).run(unittest.TestSuite([tests.Coverage21(test)]))
 caught=not result.wasSuccessful();records.append(dict(mutation=name,test=test,caught=caught,log=output.getvalue()))
 sys.modules['student_pilot.r1_coverage']=C;tests.C=C
 assert caught,name
(O/'RESULT.json').write_text(json.dumps(records,indent=2));print('caught',len(records))
