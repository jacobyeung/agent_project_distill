"""Verify current CPU evidence and emit the sb_rkfix2 delivery reports."""
from common import *
from gates import run_code_hashes,merge_inputs,verify_inputs
import math,socket
records={n:read(W/f'out/{n}.json') for n in ['S0','DRYRUN','K1_REPRODUCTION','TESTS']}
assert all(r['verdict'] in ('PASS','COMPLETE') for r in records.values())
inputs={str(W/f'out/{n}.json'):sha(W/f'out/{n}.json') for n in records}
for p in [W/'review/RK_CHECK.json',W/'review/rkrev2_REVIEW_VERDICT.md',W/'OPERATOR.md',W/'KIT_SPEC_room_pricing.md',Path(__file__).resolve(),W/'configs/KERNEL_PROVENANCE.json',W/'configs/READER_RECEIPT.json',W/'configs/KERNEL_FROZEN.json',W/'configs/GO.template.json',W/'out/S1K_RESULTS.json',W/'out/KERNEL_PROVENANCE_REPORT.md']:
 inputs[str(p)]=sha(p)
merge_inputs(inputs,run_code_hashes());verification=dict(inputs)
for r in records.values():merge_inputs(verification,r['input_sha256'])
for name in ['KERNEL_PROVENANCE','READER_RECEIPT']:
 receipt=read(W/f'configs/{name}.json');assert receipt['status']=='VERIFIED';merge_inputs(verification,receipt['input_sha256'])
assert all(p.startswith('/scratch/') for p in verification),'verification must use local copies only'
verify_inputs(verification)
# S1k source snapshots account for every historical source digest without rewriting preregistration.
k=read(W/'review/RK_CHECK.json')['report']['S1']['k1'];mean32=sum(r['k1_32']['seconds'] for r in k)/len(k);mean64=sum(r['k1_64']['seconds'] for r in k)/len(k);gpu64=sum(r['gpu_seconds'] for r in k)/len(k)
exponent=math.log(mean64/mean32,2);gpu32=gpu64/2**exponent;gpu94=gpu64*(94/64)**exponent;cpu8=110*mean32*6/8/3600
immutable='Never edit a GO note, KERNEL_PROVENANCE.json or READER_RECEIPT.json after its first run; S1c receipts and SELECTION.json bind their hashes.'
command='bash scripts/s1c_gpu.sh --run-id <run_id> --go-file configs/GO_<run_id>.json --provenance configs/KERNEL_PROVENANCE.json --reader-receipt configs/READER_RECEIPT.json'
need=dict(status='BLOCKED: authorization pending; S1c and R0-dev inference unrun',cards=1,minimum_card_gb=48,measured_gpu_hours_this_task=0,cumulative_cap_gpu_hours=1.5,
 estimated_gpu_hours=dict(S1c=110*gpu32/3600,R0_dev_f32=98*gpu32/3600,total_f32=208*gpu32/3600,R0_dev_u94_if_selected=98*gpu94/3600),
 derivation=dict(k1_32_cpu_seconds_mean=mean32,k1_64_cpu_seconds_mean=mean64,k1_64_gpu_seconds_mean=gpu64,scaling_exponent=exponent,estimated_gpu_seconds_f32=gpu32,estimated_gpu_seconds_u94=gpu94),
 provenance=dict(reader='VERIFIED',kernel='VERIFIED',authorized_by='pending orchestrator'),
 missing=[dict(field='authorized_by (must identify actual approval)',expected_location=str(W/'configs/KERNEL_PROVENANCE.json'),current_value='pending orchestrator'),dict(field='immutable per-run GO authorization',expected_location=str(W/'configs/GO_<run_id>.json'))],
 unrun_outputs=[str(W/'out/room_pricing/SELECTION.json'),str(W/'out/room_pricing/PRICING_TABLE.json')],
 cpu_fallback=dict(script='scripts/s1c_cpu.sh',workers=1,threads=8,estimated_hours=cpu8,within_two_hours=False,executed=False),
 command=command,immutable_records=immutable,estimate_command='bash scripts/cpu.sh out/finalize_delivery.py',selection_note='--stage all generates SELECTION.json; it is not a prerequisite for that launch')
write(W/'out/GPU_NEED.json',need,inputs)
write(W/'out/S1C_STATUS.json',dict(status='MISSING',expected_output=str(W/'out/room_pricing/SELECTION.json'),reason='Real S1c forward unrun: CPU estimate exceeds two hours; GPU prohibited in this task',gpu_script='scripts/s1c_gpu.sh',cpu_script='scripts/s1c_cpu.sh'),inputs)
result=read(W/'out/S1K_RESULTS.json');winner=result['result_table'][result['winner_index']];old=next(r for r in result['result_table'] if r['constants']==dict(height_margin_m=.10,cell_m=.05,min_votes=2,closing_m=.20));count=records['TESTS']['tests'];dry=records['DRYRUN'];rep=records['K1_REPRODUCTION']
report=f'''# Room kit: CPU delivery

The four requested review edits are implemented and all {count} tests pass. Both launch provenance records are VERIFIED. Kernel authorization remains **pending orchestrator**, and the gate rejects it. Real S1c and R0-dev inference remain unrun. This delivery authorizes no GPU launch.

## Resume and one-look controls

The runner requires `configs/GO_<run_id>.json` before authorization or CUDA. Stub integration tests execute S1c under run 1 followed by R0-dev under run 2, and interrupt `--stage all` during S1c before a manual closure and resume. They verify that completed captures are skipped, the interrupted capture resumes, and the first GO file remains unchanged.

{immutable}

COST.json preserves prior records, including manual closure, authorization, accounted run IDs and evidence hashes, in history. STARTED.json embeds previous_started on recomputation. Predictions pass through pred.npz.part and os.replace. An interrupted partial file requires manual closure; a pred.npz without DONE remains blocked.

price.py checks prediction completeness using only receipts and hashes before its exclusive decision registration. An incomplete set consumes no look; conversion failure after registration consumes it. load_selection requires the S1c registration, f32 and dense predictions and DONE files, verifies their hashes, checks training-row identities, and recomputes every delta and the seeded bootstrap interval. Tests reject missing evidence and altered statistics.

## Reader receipt

`configs/READER_RECEIPT.json` verifies 98 frame lists against the routed item manifest, journal mapping and kit manifest. It replays all 134 direct-answer rows and scores from the accepted journal. Each value cites a file, field and SHA256. The checkpoint identity is the accepted reader's recorded export digest (sorted relative paths and file SHA256s); the receipt does not claim a local checkpoint-weight rehash.

Source: `/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/`, including `B/src/items/room134.json`, `B5/ret/metadata/reads/0/metadata/journals/4/0/`, and reader source under `A/src/tree` and `A/src/h1eval`/`B/src/h1eval`. Command: `bash scripts/cpu.sh scripts/reader_receipt.py > out/READER_RECEIPT.log 2>&1`.

## Frozen kernel

S1k selected the constants from a preregistered 16-candidate Cartesian grid on exactly 110 K1 training captures. The grid covers margin {{0.05, 0.10}} m, cell {{0.05, 0.10}} m, votes {{1, 2}} and closing {{0.10, 0.20}} m. It maximizes mean K1-train MRA, with refusal zero and ties resolved by grid order. Stored dense-64 DA3 predictions supply the 32 anchors through the kit conversion; no tower forward ran.

The winner is a **0.05 m cut below the first percentile, 0.10 m cells, two votes, and 0.20 m closing**. It scores **{winner['mra']:.6f} K1-train MRA**, versus {old['mra']:.6f} for the legacy tuple. Selection took {result['cpu_seconds']:.2f} CPU-seconds and {result['wall_seconds']:.2f} elapsed seconds, with eight-thread limits. These training scores choose constants; they establish no held-out improvement.

The cited design records describe a rule selected on 88 official VSI-Bench ScanNet items and do not establish an independent origin for each legacy constant. S1k selects the deployed constants anew on K1 train. K1 labels still inherit the legacy rule, and the grid includes its tuple. These required disclosures remain in `relation_to_benchmark_rule`; `benchmark_selected: false` describes the new selection only. Authorization remains pending orchestrator.

`configs/KERNEL_FROZEN.json` binds the winner to `vendor/room_kernel.py`; both S1c and R0-dev pricing call it through `kernel.pipeline`. Legacy reproduction remains a separate consistency check. `out/S1K_REGISTRATION.json` and `out/S1K_RESULTS.json` preserve the grid, row scores, timing and input hashes. `evidence/s1k_execution_code/` preserves the source bytes used during selection; the provenance record maps historical source paths to these hashed snapshots.

Commands: `bash scripts/cpu.sh scripts/s1k.py > out/S1K.log 2>&1` and `bash scripts/cpu.sh scripts/kernel_provenance.py > out/KERNEL_PROVENANCE.log 2>&1`. S1k is already frozen and refuses a second selection. The short provenance report is `out/KERNEL_PROVENANCE_REPORT.md`.

## Validation

All commands run from `{W}`. `cpu.sh` disables CUDA, uses nice priority 10, and caps OMP/MKL/OpenBLAS at eight threads.

- `bash scripts/cpu.sh scripts/s0.py > out/S0.log 2>&1`: COMPLETE; {records['S0']['verified_files']} input files, {records['S0']['room_items']} room items. S0 binds its own script.
- `bash scripts/cpu.sh scripts/reproduce.py > out/S1b.log 2>&1`: PASS; {rep['rebuilt_equals_stored'][0]}/{rep['rebuilt_equals_stored'][1]} legacy areas and {len(rep['train'])} training-table entries reproduce.
- `bash scripts/cpu.sh scripts/summarize_s1.py > out/S1_summary.log 2>&1`: PASS; six stored CPU-forward receipts checked. Legacy K1 64-frame areas are {dry['k1'][0]['k1_64']:.2f} and {dry['k1'][1]['k1_64']:.2f} m², within 5% of 14.73 and 39.35. DRYRUN also records the frozen kernel's areas.
- `bash scripts/cpu.sh tests/test_roomkit.py > out/TESTS.log 2>&1`: {count} tests PASS; zero failures/errors. Real-data tests verify the frozen kernel against selected K1 rows; CPU stubs verify GPU-runner control flow only.
- `bash scripts/cpu.sh scripts/score_room_pricing.py --direct evidence/direct_m200_room134.json --self-test > out/SCORER_SELF_TEST.log 2>&1`: synthetic scorer checks.
- `bash scripts/cpu.sh scripts/make_go_template.py > out/GO_IDENTITY.txt`: NOT_GO with current code/settings/provenance/reader hashes.
- `bash scripts/cpu.sh out/finalize_delivery.py > out/FINALIZE.log 2>&1`: verifies {len(verification)} distinct local evidence hashes and computes GPU_NEED estimates from review/RK_CHECK.json.
- `bash scripts/cpu.sh scripts/package.py > tmp/PACKAGE.log 2>&1`: writes out/sb_rkfix2.tar and its SHA256, and verifies every archived member against out/DELIVERY_SHA256.txt.

## Launch state

MISSING: actual approval in `configs/KERNEL_PROVENANCE.json.authorized_by` and an orchestrator-authored `configs/GO_<run_id>.json`. S1c selection is an unrun output, not an input to `--stage all`. The orchestrator's launch command after approval is:

```bash
{command}
```

The estimate is {110*gpu32/3600:.3f} GPU-hours for S1c plus {98*gpu32/3600:.3f} for f32 R0-dev on one 48 GB card. If K1 selects u94, its R0-dev estimate is {98*gpu94/3600:.3f} GPU-hours. The cumulative cap is 1.5 GPU-hours, including loads and authorized retries. The eight-thread CPU S1c fallback estimate is {cpu8:.2f} hours and was not run. GPU_NEED records the timing inputs and formula.

The single K1-selected arm receives the only R0-dev comparison. T10, an additional u94 pass and Part B are forbidden. The sensor-depth label audit is proposed, unbuilt. This task used zero GPU-hours, no network, SSH, Git or process termination, and wrote only in this workspace. Real CUDA execution remains untested. No R0-dev tower prediction or one-look registration was created outside synthetic test fixtures.
'''
(W/'out/ROOMKIT_REPORT.md').write_text(report)
inputs[str(W/'out/GPU_NEED.json')]=sha(W/'out/GPU_NEED.json');inputs[str(W/'out/ROOMKIT_REPORT.md')]=sha(W/'out/ROOMKIT_REPORT.md')
write(W/'out/CPU_RUN_RECEIPT.json',dict(verdict='PASS',host=socket.gethostname(),stages={n:r['verdict'] for n,r in records.items()},tests=count,verified_distinct_inputs=len(verification),gpu_hours=0,network_used=False,reader_receipt='VERIFIED',kernel_provenance='VERIFIED',authorized_by='pending orchestrator',selection='MISSING',r0dev_pricing='UNRUN'),inputs)
status(f'CPU delivery validated: {count} tests pass; S0, K1 reproduction and stored-forward checks pass. Reader and new K1-train kernel provenance are VERIFIED, but kernel authorization remains pending orchestrator and no per-run GO exists. S1c and R0-dev inference are unrun. Deliver out/ROOMKIT_REPORT.md, out/GPU_NEED.json, out/KERNEL_PROVENANCE_REPORT.md and out/sb_rkfix2.tar with SHA256. No GPU, network, SSH, Git or process termination was used.')
print('PASS',count,'tests;',len(verification),'verified local hashes; authorization pending orchestrator')
