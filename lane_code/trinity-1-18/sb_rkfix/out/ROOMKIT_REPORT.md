# Room-kit review fixes: CPU delivery

The kit enforces one R0-dev comparison: the single K1-selected DA3 arm under R0 against direct. All 38 CPU tests pass. S0, stored-forward aggregation and K1 reproduction pass. S1c and real R0-dev inference remain unrun; no adoption decision exists.

## Review requirements

1. The runner captures one selected arm. price.py scores R0 only, produces no secondary comparison, and excludes T10 and Part B. u94 receives no additional look; it can be the sole arm only if K1 selects it. SETTINGS.secondary is null. The specification and operator guide state these limits.
2. S1c registers the exact 110 K1-train captures before inference. Its GPU and CPU scripts run 32-anchor DA3 and use reproduce.py's shared converter/kernel. Its fixed rule selects f32 unless dense-64 wins with paired 95% lower bound above zero. SELECTION.json must contain complete train rows, hashes and choice before R0-dev starts. The required real selection is MISSING at `/scratch/jjyeung/orch_n30/sb_rkfix/out/room_pricing/SELECTION.json`.
3. price.py exclusively creates DECISION_REGISTRATION.json before conversion or scoring. It binds the bar, arm, R0, decision and code digest. Existing registration, ROOM_PRED.jsonl or PRICING_TABLE.json blocks execution; a failed read also consumes the look. The scorer CLI rejects --pred.
4. The runner converts torch's bare UUID to GPU- plus the UUID. The integration fixture supplies a bare hexadecimal UUID and executes the actual authorization path.
5. DONE receipts retain host/card/run, while resume compares only prediction identity. A STARTED-only folder requires manual COST.json closure naming its interrupted run. The guide documents accounting and fresh GO requirements; corrupt or partial predictions remain blocked.
6. The sensor-depth label audit is described as proposed, unbuilt. Original mesh labels and native scale remain fixed.
7. The stub-backend integration tests execute gpu_run.py and price.py for both possible selections. They cover cross-host/card/run skips, OOM drop without fallback, missing selection, manual interruption recovery, registration-before-conversion and repeated-look refusal. Separate S1c tests price all 110 synthetic training rows and exercise both choice outcomes. Fixtures are synthetic and cannot establish real selection or GPU correctness.
8. No secondary memory probe or secondary pass remains. OOM terminates the selected-arm experiment without lowering resolution or pricing an incomplete set.
9. preauthorize runs before prerequisite hashing. The gate merges prerequisite digests, rejects conflicts and hashes each distinct path once. A behavioral test checks that order and deduplication.
10. env.sh preserves caller shell options; tests cover errexit/nounset/pipefail. S0.json records the exact s0.py hash.

## Commands and evidence

Run these commands from `/scratch/jjyeung/orch_n30/sb_rkfix`. `scripts/cpu.sh` disables CUDA and applies nice priority 10 with eight-thread limits.

- `bash scripts/cpu.sh scripts/s0.py > out/S0.log 2>&1`: COMPLETE; 18,556 input hashes, 15,228 R0 PNGs, 162 scenes, 98 room items. S0 hashes its own script.
- `bash scripts/cpu.sh scripts/reproduce.py > out/S1b.log 2>&1`: PASS; 134/134 stored areas and 24 K1-train table entries match. Held-out variants remain null.
- `bash scripts/cpu.sh scripts/summarize_s1.py > out/S1_summary.log 2>&1`: PASS; validates the six supplied CPU-forward receipts without launching a tower. K1 64-frame areas are 14.69 and 39.79 m² against 14.73 and 39.35; both meet the 5% check. These two captures do not select a frame budget.
- `bash scripts/cpu.sh tests/test_roomkit.py > out/TESTS.log 2>&1`: 38 tests PASS, zero failures and errors. The suite discovers all tests in tests/.
- `bash scripts/cpu.sh scripts/score_room_pricing.py --direct evidence/direct_m200_room134.json --self-test > out/SCORER_SELF_TEST.log 2>&1`: PASS using synthetic echo/oracle/refusal predictions.
- `bash scripts/cpu.sh scripts/make_go_template.py > out/GO_IDENTITY.txt`: writes NOT_GO with final code identity.
- `bash scripts/cpu.sh out/finalize_delivery.py > out/FINALIZE.log 2>&1`: verifies 19,179 distinct local input digests and produces this report, GPU_NEED.json and S1C_STATUS.json.
- `bash scripts/cpu.sh scripts/package.py`: creates out/sb_rkfix.tar and its SHA256 file; verifies all archive members against out/DELIVERY_SHA256.txt.

## Compute and remaining inputs

Request **S1c approximately 0.09 GPU-hours plus f32 R0-dev approximately 0.09 GPU-hours on one 48 GB card**, plus model-load/CPU-pricing overhead within the cumulative 1.5 GPU-hour cap. These are estimates from the review's stored timings, not measurements from this task. If K1 selects u94, its R0-dev estimate is 0.45 GPU-hours. T10, additional u94 and Part B receive no R0-dev compute.

The finalizer derives these estimates from review/RK_CHECK.json: mean CPU 32-frame time 519.13 seconds, mean CPU 64-frame time 1533.63 seconds, and mean GPU 64-frame time 9.13 seconds. Their log2 timing ratio gives exponent 1.563. Scaling that GPU time yields 3.09 seconds for f32 and 16.66 seconds for u94. Multiply by 110 K1 captures or 98 R0-dev captures and divide by 3,600. GPU_NEED.json records the inputs and unrounded values.

At the measured six-thread speed, two six-thread workers would take about 7.9 elapsed hours and exceed this task's core cap. Ideal scaling to one eight-thread worker predicts 11.9 hours, so the CPU fallback was not run. The scripts are `scripts/s1c_cpu.sh` and `scripts/s1c_gpu.sh`; OPERATOR.md provides their exact commands.

MISSING: VERIFIED kernel-selection evidence in `/scratch/jjyeung/orch_n30/sb_rkfix/configs/KERNEL_PROVENANCE.json`; authenticated reader/checkpoint/frame evidence in `/scratch/jjyeung/orch_n30/sb_rkfix/configs/READER_RECEIPT.json`; and an orchestrator-authored `/scratch/jjyeung/orch_n30/sb_rkfix/configs/GO.json`. The reader sources are expected on trinity-3-30 at `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B/src/items/room134.json`, `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B5/ret/metadata/reads/0/metadata/journals/4/0/items.jsonl`, and `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A/src/tree`. No missing proof or manifest was invented.

Real GPU execution, physical-card validation and real S1c selection remain untested. Stub tests establish control-flow behavior only. dev-S1 remains diagnostic only; official benchmark items were not read. This task used zero GPU-hours, no network, SSH, Git, process termination or writes outside this workspace. A second-node mirror is MISSING under the no-network constraint.

The report retains selection-scope and source-evidence disclosures because they are required to audit the one-look ruling. It contains no project-revision narrative.
