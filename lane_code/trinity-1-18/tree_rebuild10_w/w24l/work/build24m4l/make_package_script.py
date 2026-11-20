from common import *
source=(L/'work/build24m4j/package.py').read_text()
source=source.replace('build24m4j','build24m4k').replace('24M4J','24M4K').replace('b24m4j','b24m4k')
source=source.replace("source=W/'w24i/out/tree_rebuild_b24m4i_ca5561be.tar'", "source=W/'w24j/out/tree_rebuild_b24m4j_6a1635a0.tar'")
source=source.replace("expected_source=source.with_suffix('.tar.sha256').read_text().split()[0]", "expected_source='b85621108f1f77772731c3a38b19672621fe73f139adc5d81613d9dd03a2e386'")
source=source.replace("status='LOCAL_CHECKS_PASS_ORCHARD_JOB_UNSUBMITTED'", "status='CASE_B_LOCAL_TESTS_PASS_TREE_CHANGE_REQUIRED',case='b',tree_patch='out/TREE_CHANGE_24M4K.patch',tree_patch_applied=False,refusing_check='P_EXPORT_CONFIG_DIFFERENCE:max_pixels',ORCH_tree_review_required=True,production_executed=False")
source=source.replace("import_audit='work/build24m4l/IMPORT_AUDIT.md'", "import_audit='out/IMPORT_AUDIT.md'")
assert "w24i/out/" not in source
(D/'package_k.py').write_text(source)
print('Full-package script prepared with the supplied 24m4j archive SHA256')
