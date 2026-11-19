"""Produce the review-fix report and honest unrun-compute request from validated CPU receipts."""
from common import *
from gates import run_code_hashes,merge_inputs,verify_inputs
import socket
records={n:read(W/f'out/{n}.json') for n in ['S0','DRYRUN','K1_REPRODUCTION','TESTS']}
assert all(r['verdict'] in ('PASS','COMPLETE') for r in records.values())
inputs={str(W/f'out/{n}.json'):sha(W/f'out/{n}.json') for n in records}
for p in [W/'review/ROOMKIT_REVIEW_VERDICT.md',W/'review/RK_CHECK.json',W/'review/RK_PROBE.json',W/'review/RK_FORWARD.json',W/'OPERATOR.md',W/'KIT_SPEC_room_pricing.md',Path(__file__).resolve(),W/'out/SCORER_SELF_TEST.log',W/'configs/KERNEL_PROVENANCE.json',W/'configs/READER_RECEIPT.json',W/'configs/GO.template.json']:
 inputs[str(p)]=sha(p)
merge_inputs(inputs,run_code_hashes())
verification=dict(inputs)
for r in records.values():merge_inputs(verification,r['input_sha256'])
if any(not p.startswith('/scratch/') for p in verification):raise ValueError('only local input verification is permitted')
verify_inputs(verification)
review=read(W/'review/RK_CHECK.json');k=review['report']['S1']['k1']
mean32=sum(r['k1_32']['seconds'] for r in k)/len(k)
mean64=sum(r['k1_64']['seconds'] for r in k)/len(k)
mean_gpu64=sum(r['gpu_seconds'] for r in k)/len(k)
exponent=__import__('math').log(mean64/mean32,2)
gpu32=mean_gpu64/(2**exponent);gpu94=mean_gpu64*(94/64)**exponent
cpu12=110*mean32/2/3600;cpu8=110*mean32*6/8/3600
need=dict(status='MISSING: S1c selection and R0-dev inference are unrun',cards=1,minimum_card_gb=48,
          estimated_gpu_hours=dict(S1c=0.09,R0_dev_f32=0.09,total_f32=0.18,R0_dev_u94_if_selected=98*gpu94/3600),
          measured_gpu_hours_this_task=0,cumulative_cap_gpu_hours=1.5,
          derivation=dict(k1_32_cpu_seconds_mean=mean32,k1_64_cpu_seconds_mean=mean64,k1_64_gpu_seconds_mean=mean_gpu64,scaling_exponent=exponent,estimated_gpu_seconds_f32=gpu32,estimated_gpu_seconds_u94=gpu94,unrounded_S1c_gpu_hours=110*gpu32/3600,unrounded_R0_dev_f32_gpu_hours=98*gpu32/3600),
          cpu_fallback=dict(script='scripts/s1c_cpu.sh',workers=1,threads=8,estimated_hours=cpu8,two_six_thread_workers_estimated_hours=cpu12,within_two_hours=False,executed=False),
          missing=[str(W/'out/room_pricing/SELECTION.json'),str(W/'configs/KERNEL_PROVENANCE.json')+' VERIFIED source evidence',str(W/'configs/READER_RECEIPT.json')+' VERIFIED source evidence',str(W/'configs/GO.json')],
          command='bash scripts/s1c_gpu.sh --run-id <authorized unique run ID> --go-file configs/GO.json --provenance configs/KERNEL_PROVENANCE.json --reader-receipt configs/READER_RECEIPT.json')
write(W/'out/GPU_NEED.json',need,inputs)
write(W/'out/S1C_STATUS.json',dict(status='MISSING',expected_output=str(W/'out/room_pricing/SELECTION.json'),reason='No S1c forward was run: CPU fallback exceeds two hours at eight cores; GPU is prohibited in this task',gpu_script='scripts/s1c_gpu.sh',cpu_script='scripts/s1c_cpu.sh'),inputs)
inputs[str(W/'out/GPU_NEED.json')]=sha(W/'out/GPU_NEED.json');inputs[str(W/'out/S1C_STATUS.json')]=sha(W/'out/S1C_STATUS.json')
count=records['TESTS']['tests'];dry=records['DRYRUN'];rep=records['K1_REPRODUCTION']
report=f'''# Room-kit review fixes: CPU delivery

The kit enforces one R0-dev comparison: the single K1-selected DA3 arm under R0 against direct. All {count} CPU tests pass. S0, stored-forward aggregation and K1 reproduction pass. S1c and real R0-dev inference remain unrun; no adoption decision exists.

## Review requirements

1. The runner captures one selected arm. price.py scores R0 only, produces no secondary comparison, and excludes T10 and Part B. u94 receives no additional look; it can be the sole arm only if K1 selects it. SETTINGS.secondary is null. The specification and operator guide state these limits.
2. S1c registers the exact 110 K1-train captures before inference. Its GPU and CPU scripts run 32-anchor DA3 and use reproduce.py's shared converter/kernel. Its fixed rule selects f32 unless dense-64 wins with paired 95% lower bound above zero. SELECTION.json must contain complete train rows, hashes and choice before R0-dev starts. The required real selection is MISSING at `{W}/out/room_pricing/SELECTION.json`.
3. price.py exclusively creates DECISION_REGISTRATION.json before conversion or scoring. It binds the bar, arm, R0, decision and code digest. Existing registration, ROOM_PRED.jsonl or PRICING_TABLE.json blocks execution; a failed read also consumes the look. The scorer CLI rejects --pred.
4. The runner converts torch's bare UUID to GPU- plus the UUID. The integration fixture supplies a bare hexadecimal UUID and executes the actual authorization path.
5. DONE receipts retain host/card/run, while resume compares only prediction identity. A STARTED-only folder requires manual COST.json closure naming its interrupted run. The guide documents accounting and fresh GO requirements; corrupt or partial predictions remain blocked.
6. The sensor-depth label audit is described as proposed, unbuilt. Original mesh labels and native scale remain fixed.
7. The stub-backend integration tests execute gpu_run.py and price.py for both possible selections. They cover cross-host/card/run skips, OOM drop without fallback, missing selection, manual interruption recovery, registration-before-conversion and repeated-look refusal. Separate S1c tests price all 110 synthetic training rows and exercise both choice outcomes. Fixtures are synthetic and cannot establish real selection or GPU correctness.
8. No secondary memory probe or secondary pass remains. OOM terminates the selected-arm experiment without lowering resolution or pricing an incomplete set.
9. preauthorize runs before prerequisite hashing. The gate merges prerequisite digests, rejects conflicts and hashes each distinct path once. A behavioral test checks that order and deduplication.
10. env.sh preserves caller shell options; tests cover errexit/nounset/pipefail. S0.json records the exact s0.py hash.

## Commands and evidence

Run these commands from `{W}`. `scripts/cpu.sh` disables CUDA and applies nice priority 10 with eight-thread limits.

- `bash scripts/cpu.sh scripts/s0.py > out/S0.log 2>&1`: COMPLETE; {records['S0']['verified_files']:,} input hashes, {records['S0']['pngs']:,} R0 PNGs, {records['S0']['scenes']} scenes, {records['S0']['room_items']} room items. S0 hashes its own script.
- `bash scripts/cpu.sh scripts/reproduce.py > out/S1b.log 2>&1`: PASS; {rep['rebuilt_equals_stored'][0]}/{rep['rebuilt_equals_stored'][1]} stored areas and {len(rep['train'])} K1-train table entries match. Held-out variants remain null.
- `bash scripts/cpu.sh scripts/summarize_s1.py > out/S1_summary.log 2>&1`: PASS; validates the six supplied CPU-forward receipts without launching a tower. K1 64-frame areas are {dry['k1'][0]['k1_64']:.2f} and {dry['k1'][1]['k1_64']:.2f} m² against {dry['k1'][0]['stored_gpu_m2']:.2f} and {dry['k1'][1]['stored_gpu_m2']:.2f}; both meet the 5% check. These two captures do not select a frame budget.
- `bash scripts/cpu.sh tests/test_roomkit.py > out/TESTS.log 2>&1`: {count} tests PASS, zero failures and errors. The suite discovers all tests in tests/.
- `bash scripts/cpu.sh scripts/score_room_pricing.py --direct evidence/direct_m200_room134.json --self-test > out/SCORER_SELF_TEST.log 2>&1`: PASS using synthetic echo/oracle/refusal predictions.
- `bash scripts/cpu.sh scripts/make_go_template.py > out/GO_IDENTITY.txt`: writes NOT_GO with final code identity.
- `bash scripts/cpu.sh out/finalize_delivery.py > out/FINALIZE.log 2>&1`: verifies {len(verification):,} distinct local input digests and produces this report, GPU_NEED.json and S1C_STATUS.json.
- `bash scripts/cpu.sh scripts/package.py`: creates out/sb_rkfix.tar and its SHA256 file; verifies all archive members against out/DELIVERY_SHA256.txt.

## Compute and remaining inputs

Request **S1c approximately 0.09 GPU-hours plus f32 R0-dev approximately 0.09 GPU-hours on one 48 GB card**, plus model-load/CPU-pricing overhead within the cumulative 1.5 GPU-hour cap. These are estimates from the review's stored timings, not measurements from this task. If K1 selects u94, its R0-dev estimate is {98*gpu94/3600:.2f} GPU-hours. T10, additional u94 and Part B receive no R0-dev compute.

The finalizer derives these estimates from review/RK_CHECK.json: mean CPU 32-frame time {mean32:.2f} seconds, mean CPU 64-frame time {mean64:.2f} seconds, and mean GPU 64-frame time {mean_gpu64:.2f} seconds. Their log2 timing ratio gives exponent {exponent:.3f}. Scaling that GPU time yields {gpu32:.2f} seconds for f32 and {gpu94:.2f} seconds for u94. Multiply by 110 K1 captures or 98 R0-dev captures and divide by 3,600. GPU_NEED.json records the inputs and unrounded values.

At the measured six-thread speed, two six-thread workers would take about {cpu12:.1f} elapsed hours and exceed this task's core cap. Ideal scaling to one eight-thread worker predicts {cpu8:.1f} hours, so the CPU fallback was not run. The scripts are `scripts/s1c_cpu.sh` and `scripts/s1c_gpu.sh`; OPERATOR.md provides their exact commands.

MISSING: VERIFIED kernel-selection evidence in `{W}/configs/KERNEL_PROVENANCE.json`; authenticated reader/checkpoint/frame evidence in `{W}/configs/READER_RECEIPT.json`; and an orchestrator-authored `{W}/configs/GO.json`. The reader sources are expected on trinity-3-30 at `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B/src/items/room134.json`, `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B5/ret/metadata/reads/0/metadata/journals/4/0/items.jsonl`, and `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A/src/tree`. No missing proof or manifest was invented.

Real GPU execution, physical-card validation and real S1c selection remain untested. Stub tests establish control-flow behavior only. dev-S1 remains diagnostic only; official benchmark items were not read. This task used zero GPU-hours, no network, SSH, Git, process termination or writes outside this workspace. A second-node mirror is MISSING under the no-network constraint.

The report retains selection-scope and source-evidence disclosures because they are required to audit the one-look ruling. It contains no project-revision narrative.
'''
(W/'out/ROOMKIT_REPORT.md').write_text(report)
inputs[str(W/'out/ROOMKIT_REPORT.md')]=sha(W/'out/ROOMKIT_REPORT.md')
write(W/'out/CPU_RUN_RECEIPT.json',dict(verdict='PASS',host=socket.gethostname(),stages={n:r['verdict'] for n,r in records.items()},tests=count,verified_distinct_inputs=len(verification),gpu_hours=0,network_used=False,selection='MISSING',r0dev_pricing='UNRUN',limitations=['real GPU untested','kernel provenance MISSING','reader evidence MISSING']),inputs)
status(f'CPU fixes complete: all {count} tests pass; S0, K1 reproduction and supplied-forward aggregation pass. The one-look runner, K1 selection scripts, UUID handling and interrupted-resume procedure are implemented. Real S1c selection and R0-dev pricing are unrun and blocked on missing selection/provenance and authorization. Deliverables are out/ROOMKIT_REPORT.md, out/GPU_NEED.json, and out/sb_rkfix.tar with SHA256. No GPU, network, SSH, Git, process termination or writes outside this workspace were used.')
print('CPU fixes PASS;',count,'tests;',len(verification),'distinct input digests verified; S1c and R0-dev UNRUN')
