"""Write the concise validation report and reproducible review archive."""
from pathlib import Path
import sys,tarfile,hashlib,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import *
sha(__file__)
O=ROOT/'out'
tests=read_json(O/'TESTS.json');dry=read_json(O/'DRYRUN.json');a0=read_json(O/'fix_validation/a0_rerun_summary.json');st=read_json(O/'STAGE_TOTALS.json');ex=read_json(O/'EXCLUSIONS.json');code=read_json(O/'CODE_SHA256.json')
assert tests['status']==dry['status']==ex['status']=='PASS'
assert code['code_sha256']==dry['code_sha256']==digest(code_pins())
assert a0['equal']==a0['rows']==1037 and a0['subset_1012']['equal']==a0['subset_1012']['rows']==1012
assert all(not v['unlisted'] for v in st['trace_check'].values())
assert not (O/'looks/HELDOUT_once.json').exists()
def loc(file,needle):
 return file+':'+str(next(i for i,line in enumerate((ROOT/file).read_text().splitlines(),1) if needle in line))
review=Path('/scratch/jjyeung/orch_n30/sb_ktrev2/REVIEW_VERDICT.md')
sha(review)
review_copy=ROOT/'work/REVIEW_VERDICT_sb_ktrev2.md';review_copy.write_bytes(review.read_bytes());sha(review_copy)
lines=[
'The tower-frames kit passes CPU validation. No GPU work ran; GPU peaks below are reviewer estimates.',
f'Required held-out fix: {loc("code/evaluate_v2.py","held-out look not consumed")} checks labels before consume_heldout; {loc("code/test_kit.py","def test_missing_heldout_does_not_consume")} proves the receipt stays unwritten.',
f'Review edit 1: {loc("code/evaluate_v2.py","def scale_record")} retains NO_CONVERT_EXPORT rows; {loc("code/evaluate_v2.py","checked_scales=")} asserts every available scale agrees within 1e-4.',
f'Review edit 2: {loc("code/evaluate_v2.py","def update")} discards MISSING placeholders; {loc("code/evaluate_v2.py","gains=gains_once")} persists added_frame_gain; {loc("scripts/finalize_v3.py","for n in (\'A_POSE.json\'")} writes no DECISION placeholder.',
f'Review edits 3–4: {loc("code/runner.py","g=ROOT/\'inbox/DA3_GO.txt\'")} requires a standalone GO; {loc("code/metrics.py","out[\'reader_C64_licensed\']")} licenses C64 only through context_pays_pose.',
f'Review edit 5: {loc("code/test_kit.py","def test_pose_sign")} and subsequent regressions cover pose sign, lifting direction, decision persistence, missing geometry, held-out guards and dense remapping.',
f'Optional review safeguards: {loc("code/runner.py","def admit_ready")} checks HALTED before admission and records NOT_ADMITTED; {loc("code/kbox_hook.py","Produced row set differs")} requires the full reference row set.',
f'Review disclosures: {loc("scripts/finalize_v3.py","Section 8b:")} identifies re-formatted responses; code/README.md records selector 32/31 divisors and unscaled raw depth AbsRel.',
f'24 GB policy: {loc("code/runner.py","def validate_card")} and {loc("code/vendor/geo_bakeoff/backends.py","if memory < 24_000_000_000")} reject smaller or pre-Ampere cards; both allocation fractions retain min(1,40e9/memory).',
f'Runtime hash coverage: {loc("code/gpu_models.py","sys.path.insert(0,str(ROOT/\'code/vendor\'))")} loads vendored geo_bakeoff; code_pins includes its backend.',
'All GPU parts are estimated to fit 24 GB Ampere: A 9–11 GB; B G3T 11–15 GB and sequential SAM 3 5–7 GB; C DA3 13–17 GB. H is CPU only.',
'Estimate source: `sed -n \'/## 24 GB cards/,$p\' work/REVIEW_VERDICT_sb_ktrev2.md`. B/C assume fused attention; actual peaks require the first GPU capture.',
f'Exclusions: {loc("code/exclusions.py","def authority")} uses pinned R0 bdb5d402, withheld-80 634820b4, dev-S1 969cdb56, BENCH v2 3119aa4a and K1 held-out 4d4736cf.',
f'{loc("code/test_kit.py","def test_five_exclusions_and_withheld_planted_row")} plants a row for each list; {loc("code/test_kit.py","def test_withheld_rows_cannot_flip_gains")} proves excluded rows cannot flip a decision.',
'`bash scripts/cpu.sh code/exclusions.py` produced out/EXCLUSIONS.json: 1,012 decision rows, 1,037 report rows, 25 excluded rows in five priced captures; all six affected captures are excluded from pose decisions.',
'The excluded captures are scannet/scene0201_02, scene0478_00, scene0478_01, scene0614_02, scene0692_03 and scene0255_01; the last has no distance rows.',
f'Freeze rule: {loc("code/process_guard.py","def freeze")} writes parts/<part>/BARS.json first and records its SHA256 in FREEZE.json; {loc("code/runner.py","freeze(OUT,a.part)")} precedes A/B/C preflight; scripts/run_H.sh:4 freezes H before its look.',
f'Scoring guard: {loc("code/process_guard.py","def require_score")} rejects existing per-item files, missing bars/receipts, changed bars hashes and changed code; A/B/H and camera parity/scoring call it before output.',
f'{loc("code/test_kit.py","def test_process_planted_per_item")} through the altered-bars test exercise all four parts: 12 subprocess cases exit non-zero with byte-identical output trees.',
f'`bash scripts/cpu.sh code/test_kit.py > out/tests_fix2.log 2>&1`: {tests["tests"]}/{tests["tests"]} PASS; freeze ordering, resume integrity, legacy scores and part isolation also pass.',
f'`bash scripts/cpu.sh code/dryrun.py > out/dryrun_fix2.log 2>&1`: PASS; {dry["numbering"]["captures"]} captures, {dry["numbering"]["frame_sha256_assertions"]} numbering hashes, {dry["C"]["records_loaded"]} camera records.',
'`bash scripts/cpu.sh work/a0_rerun.py > out/a0_fix2.log 2>&1`: 1,037/1,037 A0 rows and 209/209 capture row sets match; the eligible subset matches 1,012/1,012 rows and 204/204 capture row sets.',
'A0 checks predictions, re-formatted responses, member frames and boxes; out/fix_validation/a0_rerun_summary.json records both populations and input hashes.',
'`bash scripts/cpu.sh scripts/finalize_v3.py > out/finalize_fix2.log 2>&1` binds the passing dry run and code in out/CODE_SHA256.json and GPU_NEED.json.',
f'Code SHA256 for the GO: `{code["code_sha256"]}`.',
'`bash scripts/cpu.sh work/refresh_stage.py > out/stage_fix2.log 2>&1` verifies the saved stage_list.py inventory and updates changed kit bytes/hashes; external hashes and trace checks are reused.',
'',
'| Part | Staged bytes | GB (decimal) | Smallest listed staging set |',
'|---|---:|---:|---|',
]
sets={'A':'A-tagged TSV rows: Python, G3T, K1 frames/caches/GT and kit','B':'B-tagged rows: Python, G3T, SAM 3, K1 frames/caches/GT and kit; A outputs also required','C':'C-tagged rows: Python, G3T, DA3, dev-S1 frames/records and kit','H':'H-tagged incremental rows; requires the A/B installation and outputs','union':'All unique TSV paths'}
for part in ('A','B','C','H','union'):
 b=st['totals'][part]['bytes'];lines.append(f'| {part} | {b:,} | {b/1e9:.6f} | {sets[part]} |')
lines += [
'',
'The parts column of out/STAGE_LIST.tsv defines each set; directory manifests bind its files. B needs A outputs for the joint gain; transfer them if parts use different nodes.',
'MISSING: /scratch/jjyeung/orch_n30/sb_kbox2/heldout_labels.json. No held-out look was consumed. Part C dense-input gaps remain named in out/BLOCKERS.json.',
'GPU launches require GPU_GO.json bound to this hash, SHARED_GPU_RESERVATION.json and, for C, DA3_GO.txt. Actual GPU performance remains unmeasured.',
'`bash -n scripts/cpu.sh scripts/gpu_environment.sh scripts/run_A.sh scripts/run_B.sh scripts/run_C.sh scripts/run_H.sh` passes.',
'`bash scripts/cpu.sh work/package_fix2.py` writes this report and out/sb_ktfix2.tar; `sha256sum -c out/sb_ktfix2.tar.sha256` verifies the archive.',
'`bash scripts/cpu.sh work/verify_fix2.py` verifies code/test/dry-run agreement, staging manifests, both A0 populations and every archive member.',
'Every result JSON records input hashes. The package verifies all archived members against out/FIX2_MEMBERS.json. Writing skills: no-archaeology and summary; no borderline history sentences retained.',
]
assert len(lines)<=45
(O/'FIX2_REPORT.md').write_text('\n'.join(lines)+'\n')
(ROOT/'STATUS.md').write_text('The tower-frames kit passes all CPU validation: '+str(tests['tests'])+' tests, the dry run, 1,037/1,037 A0 rows and the 1,012/1,012 decision subset. All four parts freeze bars before their outputs and reject missing or altered bars and existing per-item scores. Both GPU checks require 24 GB and Ampere or newer; the pinned five-list checker excludes all six withheld captures from decisions. out/FIX2_REPORT.md, out/STAGE_LIST.tsv, out/sb_ktfix2.tar and its SHA256 file deliver the kit. GPU approvals and the missing box-kit held-out labels remain external prerequisites.\n')
paths=[]
for folder in ('code','configs','inputs'):
 paths += [p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
paths += [ROOT/'scripts'/n for n in (*DELIVERY_SCRIPTS,'finalize_v3.py','bind_camera.py')]
paths += [ROOT/'work'/n for n in ('a0_rerun.py','stage_list.py','refresh_stage.py','verify_fix2.py','package_fix2.py','REVIEW_VERDICT_sb_ktrev2.md','stage_baseline_STAGE_LIST.tsv','stage_baseline_STAGE_TOTALS.json','stage_baseline_code_manifest.sha256')]
paths += [O/n for n in ('FIX2_REPORT.md','DRYRUN.json','GPU_NEED.json','BLOCKERS.json','CAMERA_BINDING.json','CODE_SHA256.json','EDITED_LINES.json','EDITED_LINES.patch','TESTS.json','VALIDATION.json','EXCLUSIONS.json','STAGE_LIST.tsv','STAGE_TOTALS.json','tests_fix2.log','dryrun_fix2.log','exclusions.log','a0_fix2.log','stage_fix2.log','finalize_fix2.log')]
paths += [p for p in (O/'tower_frames').rglob('*') if p.is_file() and p.name!='B_HELDOUT_once.txt']
paths += [p for p in (O/'manifests').glob('*') if p.is_file()]
paths += [O/'fix_validation'/n for n in ('a0_rerun.jsonl','a0_rerun_summary.json')]+[ROOT/'STATUS.md']
paths=sorted(set(paths));assert all(p.is_file() for p in paths)
member_pins={str(p.relative_to(ROOT)):sha(p) for p in paths}
write_json(O/'FIX2_MEMBERS.json',dict(files=member_pins,code_sha256=code['code_sha256']))
paths.append(O/'FIX2_MEMBERS.json')
archive=O/'sb_ktfix2.tar'
with tarfile.open(archive,'w',format=tarfile.PAX_FORMAT) as t:
 for p in paths:
  info=t.gettarinfo(str(p),arcname=str(p.relative_to(ROOT)));info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
  with p.open('rb') as f:t.addfile(info,f)
with tarfile.open(archive) as t:
 for n,h in member_pins.items():
  assert hashlib.sha256(t.extractfile(n).read()).hexdigest()==h,n
h=sha(archive);(O/'sb_ktfix2.tar.sha256').write_text(h+'  out/sb_ktfix2.tar\n')
write_json(O/'PACKAGE.json',dict(status='PASS',archive=str(archive),sha256=h,bytes=archive.stat().st_size,members=len(paths),report_lines=len(lines),code_sha256=code['code_sha256'],command='bash scripts/cpu.sh work/package_fix2.py'))
print(json.dumps(dict(status='PASS',code_sha256=code['code_sha256'],archive_sha256=h,bytes=archive.stat().st_size,members=len(paths),report_lines=len(lines))))
