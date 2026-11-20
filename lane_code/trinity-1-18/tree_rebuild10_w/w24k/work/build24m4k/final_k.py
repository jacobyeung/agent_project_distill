from common import *
import subprocess,stat
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r1.build import verify
from student_pilot.carrier_c1_run import identity

baseline=J.load(D/'BASELINE.json')
seals={n:verify(kit(n)) for n in NAMES}
assert seals==baseline['kits']
for n in NAMES:
 k=kit(n)
 current={str(p.relative_to(k)):dict(sha256=J.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in k.rglob('*') if p.is_file()}
 assert current==baseline['files'][n],n
 assert J.load(k/'BUILD.json')['GO']==(n=='n_go')
 assert J.load(k/'k/a.json')['GO']==(n=='n_go')
tree=digest(inventory(T));assert tree==baseline['tree']
go=identity(J.load(kit('n_go')/'k/c.json'))
assert go=='e0b9e4af8bb01f0b1cb060ca3adf5c97c69634d1210a146f99aa3b8757ad245b'
old=J.load(D/'TEST_RUNS.json');assert len(old)==16 and all(v['returncode']==0 for v in old)
new=J.load(D/'FINAL_TEST_RUNS.json');assert len(new)==6 and all(v['returncode']==0 for v in new)
records=J.load(D/'CONFIG_TESTS.json');assert len(records)==16
for r in records:
 if r['variant']=='current':assert r['compare']=='PASS' and r['layout_refusal']=='processor_resolution_pin_missing'
 else:
  assert r['compare_refusal']=='P_EXPORT_CONFIG_DIFFERENCE:max_pixels'
  assert r['layout']==dict(min_pixels=16384,max_pixels=147456,frame_count=32,frame_layout='duplicate',frame_markers=True)
comp=J.load(D/'COMPARE_TESTS.json');assert len(comp)==16
assert all(r.get('compare')=='PASS' if r['variant']=='current' else r.get('compare_refusal')=='P_EXPORT_CONFIG_DIFFERENCE:max_pixels' for r in comp)
evidence=['PATCH_TESTS','PATCH_UNIT_TESTS','P_CONFIG_TESTS','MODE_R_PLAN_TEST','RCJ_K_TESTS','RCJ_CONTRACT_TESTS','MOUNT_TESTS','RDIFF_MOUNT_TEST','TRANSPORT_TESTS','EXTRA_TESTS','RCJ_SCAN','RECORD_TEST']
for name in evidence:assert J.load(D/(name+'.json'))['status']=='PASS',name
patch=(L/'out/TREE_CHANGE_24M4K.patch').read_text()
for part in ('+++ b/student_pilot/carrier_c1_run.py','+++ b/launch_r1/entry.py','+++ b/tests/test_r1_processor_compat.py'):assert part in patch
assert J.load(D/'PATCH_UNIT_TESTS.json')['tests']==3
assert not J.load(D/'PATCH_TESTS.json')['tree_modified']
assert J.load(D/'EXTRA_TESTS.json')['arming_full_replay']
assert not J.load(D/'MODE_R_PLAN_TEST.json')['unmapped']
assert not J.load(D/'MODE_R_PLAN_TEST.json')['frame_payloads_requested']
assert J.load(D/'MODE_R_PLAN_TEST.json')['export_weights_required']
subprocess.run(['bash','-n',str(L/'out/rcj/rcj.sh')],check=True)
compile((L/'out/rcj/x.py').read_text(),str(L/'out/rcj/x.py'),'exec')
up=J.load(L/'out/UPLOADS_24M4K.json');assert up['case']=='b' and not up['GO'] and not up['kit_changes']
assert up['baseline_kit_seals']==seals
assert len(up['files'])==up['total_files']==2
for v in up['files']:
 assert v['name'] in ('rcj/rcj.sh','rcj/x.py')
 for p in (Path(v['local_path']),L/'out'/v['name']):
  assert J.sha(p)==v['sha256'] and p.stat().st_size==v['bytes'] and p.stat().st_mode&511==int(v['mode'],8)
assert sum(v['bytes'] for v in up['files'])==up['total_bytes']
assert not J.load(L/'out/UPLOADS_24M4K_GO.json')['files']
report=(L/'out/BUILD24M4K_REPORT.md').read_text().splitlines()
assert len(report)<15 and report[0].startswith('CASE b')
runner=(D/'run.sh').read_text()
assert 'ulimit -v 16777216' in runner and '--ro-bind / / --bind "$J" "$J"' in runner
assert '/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B' in runner
v=dict(status='PASS',scope='LOCAL_CASE_B_TESTS',case='b',refusal='P_EXPORT_CONFIG_DIFFERENCE:max_pixels',tree_sha256=tree,kits=seals,kit_n_go_identity=go,kit_inventories_unchanged=True,GO=False,patch='out/TREE_CHANGE_24M4K.patch',patch_applied=False,existing_suites=old,new_suites=new,evidence=evidence,helper_files=up['files'],production_executed=False,full_admission_tested=False,all_production_rows_tested=False,planner_payload_boundaries_stubbed=True,ORCH_tree_review_required=True,report_lines=len(report))
J.write(D/'VALIDATION.json',v)
print('LOCAL_CASE_B_TESTS PASS; tree and four complete kit inventories unchanged; 16 existing suites; 12 evidence records; helper delta verified')
