"""Summarize the fixed kit from hashed CPU evidence."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import *
sha(__file__)
V=ROOT/'out/fix_validation'
a=read_json(V/'part_a_summary.json');b=read_json(V/'a0_rerun_summary.json');m=read_json(V/'mutations.json');d=read_json(ROOT/'out/DRYRUN.json');t=read_json(ROOT/'out/TESTS.json')
pins=code_pins();h=digest(pins)
assert d['code_sha256']==h and a['code_sha256']==h
assert m['killed']==m['total']==12 and t['status']=='PASS' and d['status']=='PASS'
assert a['complete'] and b['equal']==b['rows']==1037
# Each edit points at the delivered implementation, rather than a patch's old offsets.
def line(file,needle):
 return str(next(i for i,s in enumerate((ROOT/file).read_text().splitlines(),1) if needle in s))
def loc(file,needle):return file+':'+line(file,needle)
missing=[]
for r in a['no_convert_export']:
 missing.append(str(capdir({'canonical':r['capture']},'/scratch/jjyeung/k1/run_convert_2')/'geometry.npz'))
text=f'''All required fixes 1–5 and all three optional safeguards are implemented. CPU only; GPU hours used: 0.
Accepted spec: 133e8cfdbb149401767c76fc5908154b9dd106d2a4b580bcca81d207615169aa (`sha256sum inputs/KIT_SPEC_tower_frames_v2.md`).
GPU GO must bind code_sha256 `{h}`; `out/CODE_SHA256.json` lists its files.
1. {loc('code/evaluate_v2.py','def scale_record')}: missing convert exports yield NO_CONVERT_EXPORT; {loc('code/evaluate_v2.py','checked_scales=')}: only exported scales enter agreement/stored-rule checks, and each relative error must be ≤1e-4.
2. {loc('code/evaluate_v2.py','def update')}: discard MISSING placeholders and retain part bars; {loc('code/evaluate_v2.py','gains=gains_once')}: persist added_frame_gain and its verdict under bars.B.
   {loc('scripts/finalize_v3.py',"for n in ('A_POSE.json'")}: finalization writes no placeholder DECISION.json; the inherited placeholder is preserved in work/inherited_DECISION.json outside runtime outputs.
3. {loc('code/runner.py',"g=ROOT/'inbox/DA3_GO.txt'")}: Part C requires a standalone GO line before capture work; code/README.md:11 and {loc('scripts/finalize_v3.py','launch_blockers=list')}: document and report the missing approval inputs.
4. {loc('code/metrics.py',"out['reader_C64_licensed']=")}: only context_pays_pose licenses C64 camera context.
5. {loc('code/test_kit.py','def test_pose_sign')}: regressions cover pose sign, A2 direction, lifting arm, DECISION persistence, held-out guard, dense best-frame remapping, and run_a without a convert export.
Optional: {loc('code/runner.py','def admit_ready')}: check HALTED before admission and write NOT_ADMITTED receipts; {loc('code/kbox_hook.py','assert {')}: require the complete reference row set.
Claims: {loc('scripts/finalize_v3.py','Section 8b:')}: response matching re-formats the prediction because kbox4 stores no response text.
Disclosures: {loc('scripts/finalize_v3.py','At N=64')}, code/README.md:19: selector frame counts retain 32/31 divisors at N=64; raw depth AbsRel uses unscaled G3T depth.
Relocation: scripts/cpu.sh:3, scripts/gpu_environment.sh:3 and scripts/run_A.sh:3 (also B/C) resolve this workspace; copied provenance and kbox paths preserve original byte hashes.
Tests: {t['tests']}/{t['tests']} PASS — `bash scripts/cpu.sh code/test_kit.py > out/tests_v3.log 2>&1`.
Mutations: {m['killed']}/{m['total']} killed — `bash scripts/cpu.sh work/mutate.py > out/fix_validation/mutations.log 2>&1`.
The reviewer probe's 12 replacements and execution remain unchanged; only workspace/output routing, logs and hashed receipts are adapted. The original is work/reviewer_mutate_original.py.
Dry run: {d['status']}; all {d['numbering']['captures']} captures and {d['numbering']['frame_sha256_assertions']} numbering hashes pass — `bash scripts/cpu.sh code/dryrun.py > out/dryrun_v3.log 2>&1`.
A0: {b['equal']}/{b['rows']} rows match predictions, re-formatted responses, member frames and boxes; all {b['set_equal']}/{b['captures']} capture row sets match — `bash scripts/cpu.sh work/a0_rerun.py > out/fix_validation/a0_rerun.log 2>&1`.
Part A: all {a['captures']} train captures complete; each of four arms has 1,037 rows; pose and lifting bars are FAIL with zero deltas, not MISSING — `bash scripts/cpu.sh work/part_a_cpu.py > out/fix_validation/part_a.log 2>&1`.
This CPU self-comparison substitutes stored C64 for C32, caches identical replay calls, and keeps its results under out/fix_validation; it provides no evidence that either context is better. Real GPU decisions remain uncomputed.
Scale: {a['scale_checked']}/237 available exports agree; agreement_fraction={a['agreement_fraction']}, maximum relative error={a['scale_max_relative_error']} (same Part A command).
NO_CONVERT_EXPORT: scannetpp/0f69aefe3d and scannetpp/2c7c10379b retain their {a['no_convert_export_rows']} train rows; missing files are:
- {missing[0]}
- {missing[1]}
MISSING launch inputs: {ROOT}/inbox/GPU_GO.json (orchestrator GO), {ROOT}/inbox/DA3_GO.txt, and {ROOT}/inbox/SHARED_GPU_RESERVATION.json.
Shell validation: `bash -n scripts/cpu.sh scripts/gpu_environment.sh scripts/run_A.sh scripts/run_B.sh scripts/run_C.sh`.
Delivery: `bash scripts/cpu.sh work/write_fix_report.py`, then `bash scripts/cpu.sh scripts/finalize_v3.py`; verify `sha256sum -c out/sb_ktfix.tar.sha256`.
The archive contains the fixed code, reports and CPU evidence. No GPU, network, SSH, Git, tmux, process stopping or external writes ran; no mirror was attempted.
All generated result JSON files record input hashes. No revision-history prose was retained in the README or report.
'''
assert len(text.splitlines())<=50
(ROOT/'out/FIX_REPORT.md').write_text(text)
write_json(V/'FIX_EVIDENCE.json',dict(status='PASS',code_sha256=h,tests=t['tests'],mutations_killed=m['killed'],a0_matches=b['equal'],part_a_captures=a['captures'],report_sha256=sha(ROOT/'out/FIX_REPORT.md'),commands=['bash scripts/cpu.sh code/test_kit.py','bash scripts/cpu.sh work/mutate.py','bash scripts/cpu.sh code/dryrun.py','bash scripts/cpu.sh work/a0_rerun.py','bash scripts/cpu.sh work/part_a_cpu.py']))
(ROOT/'STATUS.md').write_text(f"All {t['tests']} regressions pass and all 12 reviewer mutations are killed. The CPU dry run passes; N=32 reproduces every one of the 1,037 A0 rows and all 209 capture row sets. The Part A CPU self-comparison completes all 239 train captures, checks 237 convert scales, and reports two NO_CONVERT_EXPORT captures without blanking the bars. GPU work remains unrun pending the three named approval/reservation inputs; the fix report is ready for packaging.\\n")
print(h)
