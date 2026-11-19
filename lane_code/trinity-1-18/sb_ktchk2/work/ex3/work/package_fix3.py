"""Package the CPU-validated kit and its review evidence."""
from pathlib import Path
import sys, tarfile, hashlib, json, csv
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import *
sha(__file__)
O=ROOT/'out';W=ROOT/'work'
tests=read_json(O/'TESTS.json');dry=read_json(O/'DRYRUN.json')
code=read_json(O/'CODE_SHA256.json');a0=read_json(O/'fix_validation/a0_rerun_summary.json')
probes=read_json(O/'FIX3_PROBES.json');stage=read_json(O/'STAGE_TOTALS.json')
assert tests['status']==dry['status']==probes['status']=='PASS'
assert code['code_sha256']==dry['code_sha256']==digest(code_pins())
assert a0['equal']==a0['rows']==1037 and a0['subset_1012']['equal']==a0['subset_1012']['rows']==1012
assert all(p['status']=='REFUSED' for p in probes['probes'].values())
sha(W/'ktchk_probes/REVIEW_VERDICT.md');sha(W/'ktchk_probes/reviewed_archive.sha256')
reviewed=(W/'ktchk_probes/reviewed_archive.sha256').read_text().split()[0]
assert reviewed.startswith('0c1f8f27cfaa2a24') and sha(O/'sb_ktfix2.tar')==reviewed
sha(O/'STAGE_LIST.tsv')
with (O/'STAGE_LIST.tsv').open() as f:rows=list(csv.DictReader(f,delimiter='\t'))
seen=set();incremental={}
for part in 'ABCH':
    selected={r['path']:int(r['bytes']) for r in rows if r['bytes'] and part in r['parts'].split(',')}
    incremental[part]=sum(n for p,n in selected.items() if p not in seen)
    seen.update(selected)
write_json(O/'STAGE_INCREMENTAL.json',dict(bytes=incremental,GB={p:v/1e9 for p,v in incremental.items()},command='bash scripts/cpu.sh work/package_fix3.py',schedule='A, B, C, H sequentially on one node'))
def loc(file,needle):
    return file+':'+str(next(i for i,l in enumerate((ROOT/file).read_text().splitlines(),1) if needle in l))
a_items=loc('code/evaluate_v2.py', "items_file(prices,'A'")
b_items=loc('code/evaluate_v2.py', "items_file(prices,'B'")
h_items=loc('code/evaluate_v2.py', 'items_file([dict(r,source_part=part)')
c_items=loc('code/camera_pricing.py', "items_file(rows,'C'")
bars_check=loc('code/process_guard.py', "if read_json(bars).get('code_sha256')")
h_freeze=loc('code/runner.py', "if a.part=='A':freeze")
lines=[
    'The tower-frames kit passes CPU validation. All four required edits are implemented; no GPU work ran.',
    f"Edit 1: {loc('code/process_guard.py','def score_files')} counts scored reports and nested BARS/FREEZE files; test_plant_A_report/B_report/C_report/H_report and test_report_guard_pose_and_nested_receipt refuse them.",
    f"Edit 1 ordering: {a_items}, {b_items}, {h_items}, {c_items} write per-item files before reports; test_per_item_written_before_reports and test_camera_and_heldout_item_order verify interrupted reporting.",
    f"Edit 2: {loc('code/process_guard.py','shared=dict')}, {bars_check} bind BARS.json to current code independently of FREEZE.json; test_plant_A_planted_FREEZE_after_code_edit refuses a forged receipt for every part.",
    f"Edit 2 H freeze: {h_freeze} freezes H before A preflight; test_a_freezes_h_before_preflight checks both bars.",
    f"Edit 3: {loc('code/evaluate_v2.py','def a_train_rows')} reads parts/A/PER_ITEM_A_train.jsonl, removes only per-row provenance, and requires equality with A_DISTANCE.txt; test_plant_B_reads_planted_A_DISTANCE refuses both planted scores.",
    f"Edit 3 duplicates: {loc('code/evaluate_v2.py','keys=[(r')} rejects duplicate (row_id, arm); test_duplicate_row_arm_refuses covers the appended-row probe. B takes only A's C32 baseline arms when assembling gains.",
    f"Edit 4: {loc('scripts/gpu_environment.sh','export CUDA_DEVICE_ORDER')} exports PCI_BUS_ID and runtime/nv; {loc('scripts/gpu_environment.sh','for reading in 1 2')} logs two memory/utilization and compute-app readings 300 seconds apart and refuses either busy reading.",
    f"Edit 4 tests: {loc('code/test_fix3.py','def test_gpu_idle')} and the following GPU fixtures verify exports, 300-second wait, appended logs, each busy reading, the 1-GiB boundary, and query failures. Fixture mode always exits before GPU execution.",
    f"Probe regressions: {loc('code/test_fix3.py','class Fix3Tests')} covers all nine plant.py probes plus the duplicate-row probe; out/FIX3_PROBES.json records refusals and input hashes.",
    f"`bash scripts/cpu.sh code/test_kit.py > out/tests_fix3.log 2>&1`: {tests['tests']}/{tests['tests']} PASS.",
    f"`bash scripts/cpu.sh code/dryrun.py > out/dryrun_fix3.log 2>&1`: PASS; {dry['numbering']['captures']} captures, {dry['numbering']['frame_sha256_assertions']} numbering hashes, {dry['C']['records_loaded']} camera records.",
    '`bash scripts/cpu.sh work/a0_rerun.py > out/a0_fix3.log 2>&1`: 1,037/1,037 full A0 rows and 209/209 capture row sets match; 1,012/1,012 decision rows and 204/204 capture row sets match.',
    'A0 checks predictions, re-formatted responses, member frames and boxes; out/fix_validation/a0_rerun_summary.json records both populations and input hashes.',
    '`bash scripts/cpu.sh scripts/finalize_v3.py > out/finalize_fix3.log 2>&1` binds out/CODE_SHA256.json and out/GPU_NEED.json to the passing dry run.',
    f"New code_sha256 for inbox/GPU_GO.json: `{code['code_sha256']}`. No GPU authorization was created.",
    '`bash scripts/cpu.sh work/refresh_stage.py > out/stage_fix3.log 2>&1` refreshes kit hashes in out/STAGE_LIST.tsv; external hashes and the verified trace inventory are reused.',
    '`bash scripts/cpu.sh work/package_fix3.py` computes sequential staging from STAGE_LIST.tsv into out/STAGE_INCREMENTAL.json: A 22.24 GB, +B 3.86 GB, +C 7.59 GB, +H 0.31 GB (decimal).',
    'Run parts one at a time on one node, staged at /scratch/jjyeung/orch_n30/sb_ktfix2. Keep A outputs for B and A/B outputs for H.',
    'The 24e9-byte bound remains unchanged. The reviewer cautions that A10/A10G report about 23.8e9 bytes and are refused; 3090/4090/A5000 pass the memory bound. These are reviewer card figures, not GPU measurements here.',
    'Card and staging source: `sed -n \'/6. 24 GB policy:/,/10. Unbacked claims:/p\' work/ktchk_probes/REVIEW_VERDICT.md`.',
    'MISSING: /scratch/jjyeung/orch_n30/sb_kbox2/heldout_labels.json. No held-out look was consumed; GPU performance remains unmeasured.',
    '`bash -n scripts/cpu.sh scripts/gpu_environment.sh scripts/run_A.sh scripts/run_B.sh scripts/run_C.sh scripts/run_H.sh` passes.',
    '`bash scripts/cpu.sh work/package_fix3.py` writes out/sb_ktfix3.tar, verifies every member against out/FIX3_MEMBERS.json, and writes out/sb_ktfix3.tar.sha256.',
    '`bash scripts/cpu.sh work/verify_fix3.py` verifies delivery receipts, both replay populations, staging totals, code pins, archive members and the unchanged reviewed archive.',
    'Verify the new archive with `sha256sum -c out/sb_ktfix3.tar.sha256`; out/sb_ktfix2.tar retains its reviewed SHA256.',
    'Writing skill: no-archaeology. No borderline history sentences were retained.',
]
assert len(lines)<=40
(O/'FIX3_REPORT.md').write_text('\n'.join(lines)+'\n')
(ROOT/'STATUS.md').write_text(f"The tower-frames kit passes {tests['tests']} CPU tests, all reviewer refusal probes, the dry run, 1,037/1,037 A0 replay rows and the 1,012/1,012 decision subset. The four review fixes and fake GPU-idleness tests are complete. out/FIX3_REPORT.md and out/sb_ktfix3.tar deliver the kit; out/sb_ktfix3.tar.sha256 binds the archive. The reviewed sb_ktfix2.tar remains unchanged. GPU authorization and the missing held-out labels remain external prerequisites.\n")
paths=[]
for folder in ('code','configs','inputs'):
    paths += [p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
paths += [ROOT/'scripts'/n for n in (*DELIVERY_SCRIPTS,'finalize_v3.py','bind_camera.py')]
paths += [W/n for n in ('a0_rerun.py','stage_list.py','refresh_stage.py','verify_fix3.py','package_fix3.py','stage_baseline_STAGE_LIST.tsv','stage_baseline_STAGE_TOTALS.json','stage_baseline_code_manifest.sha256')]
paths += [p for p in (W/'ktchk_probes').glob('*') if p.is_file()]
paths += [O/n for n in ('FIX3_REPORT.md','FIX3_PROBES.json','DRYRUN.json','GPU_NEED.json','BLOCKERS.json','CAMERA_BINDING.json','CODE_SHA256.json','EDITED_LINES.json','EDITED_LINES.patch','TESTS.json','VALIDATION.json','EXCLUSIONS.json','STAGE_LIST.tsv','STAGE_TOTALS.json','STAGE_INCREMENTAL.json','tests_fix3.log','dryrun_fix3.log','a0_fix3.log','stage_fix3.log','finalize_fix3.log')]
paths += [p for p in (O/'tower_frames').rglob('*') if p.is_file() and p.name!='B_HELDOUT_once.txt']
paths += [p for p in (O/'manifests').glob('*') if p.is_file()]
paths += [O/'fix_validation'/n for n in ('a0_rerun.jsonl','a0_rerun_summary.json')]+[ROOT/'STATUS.md']
paths=sorted(set(paths));assert all(p.is_file() for p in paths)
member_pins={str(p.relative_to(ROOT)):sha(p) for p in paths}
write_json(O/'FIX3_MEMBERS.json',dict(files=member_pins,code_sha256=code['code_sha256']))
paths.append(O/'FIX3_MEMBERS.json')
archive=O/'sb_ktfix3.tar'
with tarfile.open(archive,'w',format=tarfile.PAX_FORMAT) as t:
    for p in paths:
        info=t.gettarinfo(str(p),arcname=str(p.relative_to(ROOT)));info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
        with p.open('rb') as f:t.addfile(info,f)
with tarfile.open(archive) as t:
    for n,h in member_pins.items():assert hashlib.sha256(t.extractfile(n).read()).hexdigest()==h,n
h=sha(archive);(O/'sb_ktfix3.tar.sha256').write_text(h+'  out/sb_ktfix3.tar\n')
write_json(O/'PACKAGE.json',dict(status='PASS',archive=str(archive),sha256=h,bytes=archive.stat().st_size,members=len(paths),report_lines=len(lines),code_sha256=code['code_sha256'],command='bash scripts/cpu.sh work/package_fix3.py'))
print(json.dumps(dict(status='PASS',code_sha256=code['code_sha256'],archive_sha256=h,bytes=archive.stat().st_size,members=len(paths),report_lines=len(lines),staging_incremental_bytes=incremental)))
