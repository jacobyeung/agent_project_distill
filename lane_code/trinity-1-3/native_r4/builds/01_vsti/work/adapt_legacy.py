"""Relocate inherited test fixtures; keep test bodies intact."""
from pathlib import Path
import ast,json,sys,types,unittest,uuid
B=Path(__file__).resolve().parents[1];R=B.parents[1];OLD=R/'from113/builds/02_c8r'
CORE=B/'code/sj/orch_cd/evalx/work/milestone'
sys.path.extend([str(B/'code'),str(CORE/'native/out2'),str(CORE/'orchard_native'),str(CORE),str(R/'from113/work/tree')])
import paths;paths.install(R/'from113/work/tree')
from adapter import dump
fixture=OLD/'work/rh_pilot_op1/runs/c80000001'
# Only safe unit logic is selected. Transport tests have filesystem side effects forbidden by the build brief.
selected={
 'test_core.py': {'test_p9_project','test_program_refusal_project','test_program_refusal_sole_family_timing','test_all_program_refusals','test_pilot_with_refusals','test_guard_report','test_limit_source','test_selector_dev','test_selector_camera_free','test_selector_empty','test_pilot_zero_refusals'},
 'test_guard.py': {'test_sealed_inspect_identity','test_source_refusal','test_terminal_ast_refusal','test_second_install','test_foreign_exception','test_earlier_failure','test_inverted_conventions','test_near_nadir_passes','test_unbound_context_refusal','test_invalid_context','test_install_success','test_five_geometries_unchanged','test_worker_install_refusal_receipt','test_all_real_capture_decisions'},
 'test_package.py': {'test_guard_changed_verdict_refused','test_guard_capture_set_refused','test_request_guard_identity_refused'},
}
suite=unittest.TestSuite();inventory=[]
for filename,names in selected.items():
 source=(OLD/'out/tests'/filename).read_text();tree=ast.parse(source)
 source=source.replace("B=Path(__file__).resolve().parents[2]",'B=Path('+repr(str(B))+')')
 source=source.replace("W=B.parents[1]/'work'",'W=Path('+repr(str(R/'from113/work'))+')')
 source=source.replace("ROOT=B/'out/c8r/sources/sj/orch_cd/evalx/work/milestone'",'ROOT=Path('+repr(str(CORE))+')')
 source=source.replace("R=B/'out/c8r/sources/sj/orch_cd/evalx/work/milestone'",'R=Path('+repr(str(CORE))+')')
 source=source.replace("W/'p9/native/probe/PILOT_REPORT.json'",'Path('+repr(str(B/'work/legacy_pilot.json'))+')')
 source=source.replace("W/'p9/native/geometry/GEOMETRY_MANIFEST.json'",'Path('+repr(str(fixture/'native/geometry/GEOMETRY_MANIFEST.json'))+')')
 source=source.replace("W/'p9/native/geometry'",'Path('+repr(str(fixture/'native/geometry'))+')')
 # Package setup reads the inherited family; preserve that fixture.
 source=source.replace("B/'out/c8r/FAMILY_C8R.json'",'Path('+repr(str(R/'work/c8r/FAMILY.json'))+')')
 module=types.ModuleType('legacy_'+filename[:-3]);module.__file__=str(OLD/'out/tests'/filename)
 exec(compile(source,module.__file__,'exec'),module.__dict__)
 for cls in module.__dict__.values():
  if not isinstance(cls,type) or not issubclass(cls,unittest.TestCase):continue
  for method in unittest.defaultTestLoader.getTestCaseNames(cls):
   included=method in names
   inventory.append(dict(file=str(OLD/'out/tests'/filename),test=method,executed=included,
     reason=None if included else 'Requires the old allocation, deleted-path cleanup, or fixtures outside the new read contract; not certified by this build.'))
   if included:suite.addTest(cls(method))
result=unittest.TextTestRunner(verbosity=2).run(suite)
dump(B/'out/LEGACY_TESTS.json',dict(run=result.testsRun,failures=[(str(t),s) for t,s in result.failures],errors=[(str(t),s) for t,s in result.errors],inventory=inventory,
    transport_tests='not executed: inherited transport fixtures mutate and clean their temporary pool; the build forbids those operations'))
if not result.wasSuccessful():sys.exit(1)
