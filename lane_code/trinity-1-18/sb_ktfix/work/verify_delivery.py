"""Verify delivery contents without extraction or writes outside this workspace."""
from pathlib import Path
import sys,tarfile,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import *
sha(__file__)
pins=code_pins();h=digest(pins);out=ROOT/'out';v=out/'fix_validation'
dry=read_json(out/'DRYRUN.json');code=read_json(out/'CODE_SHA256.json');gpu=read_json(out/'GPU_NEED.json')
assert dry['status']=='PASS' and dry['code_sha256']==code['code_sha256']==gpu['code_sha256']==h
assert code['files']==pins
mut=read_json(v/'mutations.json');assert mut['killed']==mut['total']==12
expected=['test_geometry64_and_printed32','test_pose_sign_lifting_arm_and_camera_license','test_no_object_variant_single_gain','test_update_discards_placeholder_and_retains_bars','test_heldout_labels_guard','test_camera_formatter','test_shared_ledger_budget','test_heldout_requires_decision_and_consumes_once','test_pose_sign_lifting_arm_and_camera_license','test_run_a_no_geometry_and_a2_direction','test_resume_hashes','test_dense_best_uses_remapped_anchor_areas']
for row,name in zip(mut['results'],expected,strict=True):assert row['killed'] and name in row['failing_tests'],row
baseline=read_json(out/'TESTS.json');assert baseline['status']=='PASS' and baseline['tests']==28
parta=read_json(v/'part_a_summary.json');assert parta['complete'] and parta['captures']==239 and parta['no_convert_export_rows']==12
assert parta['scale_checked']==237 and parta['scale_max_relative_error']==0 and parta['agreement_fraction']==1
assert all(n==1037 for n in parta['rows_per_arm'].values())
for k in ('move_mra','short_displacement_mra','lifting'):
 assert parta['bars'][k]['status']=='FAIL'
 assert parta['bars'][k]['train']['point']==parta['bars'][k]['train']['low']==parta['bars'][k]['train']['high']==0
assert not (out/'tower_frames/DECISION.json').exists()
assert (ROOT/'work/inherited_DECISION.json').is_file()
assert {Path(x['expected_path']).name for x in gpu['launch_blockers']}=={'GPU_GO.json','DA3_GO.txt','SHARED_GPU_RESERVATION.json'}
assert all(x['status']=='MISSING' and not Path(x['expected_path']).exists() for x in gpu['launch_blockers'])
a0=read_json(v/'a0_rerun_summary.json');assert a0['equal']==a0['rows']==1037 and a0['set_equal']==a0['captures']==209
report=out/'FIX_REPORT.md';assert len(report.read_text().splitlines())<=50
archive=out/'sb_ktfix.tar';archive_sha=sha(archive)
assert (out/'sb_ktfix.tar.sha256').read_text().split()[0]==archive_sha
required=['out/FIX_REPORT.md','out/fix_validation/mutations.json','out/fix_validation/a0_rerun_summary.json','out/fix_validation/part_a_summary.json','work/reviewer_mutate_original.py','work/write_fix_report.py']
with tarfile.open(archive) as tar:
 names=tar.getnames()
 assert all(p in names for p in required)
 assert 'out/tower_frames/DECISION.json' not in names
 for path,want in pins.items():assert hashlib.sha256(tar.extractfile(path).read()).hexdigest()==want,path
 for name in required:assert tar.extractfile(name).read()==(ROOT/name).read_bytes(),name
for p in [out/'DRYRUN.json',out/'TESTS.json',out/'GPU_NEED.json',out/'CODE_SHA256.json',out/'PACKAGE.json',*v.glob('*.json'),* (v/'part_a').glob('*.json')]:
 d=read_json(p);assert d.get('input_sha256'),p
write_json(out/'DELIVERY_CHECK.json',dict(status='PASS',code_sha256=h,archive_sha256=archive_sha,archive_members=len(names),verified_code_files=len(pins),tests=28,mutations_killed=12,a0_rows=1037,part_a_captures=239,report_lines=len(report.read_text().splitlines()),command='bash scripts/cpu.sh work/verify_delivery.py'))
print(json.dumps(dict(status='PASS',code_sha256=h,archive_sha256=archive_sha,members=len(names))))
