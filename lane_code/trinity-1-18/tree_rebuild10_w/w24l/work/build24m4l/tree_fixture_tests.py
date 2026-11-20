from common import *
import types,unittest,tempfile
tempfile.tempdir=str(D/'tmp');os.environ.update(LANE_TEST_OUTPUT=str(D/'tree_tests'),R2_PROOFS=str(D/'tree_tests'))
suite=unittest.TestSuite();edits=[]
for name,old,new,cls,method in [('test_host24j','max_pixels=4096, min_pixels=1024','max_pixels=None, min_pixels=None','NativeAdmission','test_native_export_bind_audit_and_admit'),
 ('test_carrier_c1_single_image',"base_identity='fixture', frame_layout='paired'","base_identity='fixture', trace_program_version='3.13', frame_layout='paired'",'SingleImageTests','test_prepare_skips_paired_layout_only_for_single_images')]:
 raw=(T/'tests'/ (name+'.py')).read_text();assert old in raw
 raw=raw.replace(old,new)
 if name=='test_carrier_c1_single_image':
  raw=raw.replace("        manifest = dict(kind='base'", "        codepath=root/'code.json';write(codepath,dict(schema='fixture'))\n        manifest = dict(kind='base'")
  raw=raw.replace("base_identity='fixture', trace_program_version='3.13', frame_layout='paired'", "code=file_pin(codepath), base_identity='fixture', trace_program_version='3.13', frame_layout='paired'")
 target=D/(name+'_fixture.py');target.write_text(raw)
 module=types.ModuleType(name+'_fixture');module.__file__=str(target);exec(compile(raw,str(target),'exec'),vars(module))
 suite.addTest(getattr(module,cls)(method));edits.append(dict(source='tests/'+name+'.py',old=old,new=new))
r=unittest.TextTestRunner(verbosity=2).run(suite)
J.write(D/'TREE_FIXTURE_TESTS.json',dict(successful=r.wasSuccessful(),tests=r.testsRun,fixture_only_edits=edits,errors=[(str(t),v) for t,v in r.errors],failures=[(str(t),v) for t,v in r.failures],tree_unchanged=True))
raise SystemExit(not r.wasSuccessful())
