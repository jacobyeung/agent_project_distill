Packet A round 12 drivers use `p_9dd2fbb7.tar`, SHA256 `9dd2fbb77503ecee875d538ebaed933cc95ff286f76e5955fc2591f63e3f0192`. Config: `fac0705214fdecb53561c633d7d94642cd469b50b662c5de81f09d11891d115f`. Run: `673bc60f`. Job name: `a15_cot_ap673bc60f`. Bundle: `/project/community/jjyeung/okh7/i_69d2930d`. Kit: `/project/community/jjyeung/okh7/x_69d2930d`.

`m0.sh` has already completed. Start at `u1.sh`. Keep `m0.sh`, `m0.v1.sh`, and `m0.out` unchanged; their hashes are in `PRESERVED_R1DRV7.json`. Retain `i_69d2930d.f170956` and `x_69d2930d.f170956`: the CANARY gate authenticates job 170956's admission through that kit's receipt, log, manifest, config, and staging record.

The binding ruling is `events/r1_ops/20261118T0044Z_ORCH_RULING_canary_launch_parallel_proof.md`. Submit the CPU proof on **advanced**, then immediately submit training on **advanced** in canary mode. The proof requests one node, one task, 48 CPUs, 800G RAM, zero GPUs, and **06:00:00**. Both `general` and `advanced` pass the sealed proof binder and local argv tests. The six-hour limit allows time after admission for the loader audit. Training retains the sealed sbatch line: four GPUs, 48 CPUs, 800G RAM, **13:00:00**, steps 1–200. Live scheduler placement and resource availability require the operator's queue check; this build made no Orchard call.

Run the following commands from the work directory. `orch` below is an operator helper; this build did not execute it. Check the newest r1_ops INBOX and the queue before submission. Poll at most once per minute. Stop after a failed or uncertain operation and inspect retained evidence; do not automatically retry.

```bash
cd /scratch/jjyeung/orch_n30/r1_ops/work/drv_p5
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
PY=/scratch/jjyeung/envs/p1cpu/bin/python
EVENTS=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
orch() { timeout 300 bash "$OSSH" 'bash -s' < "$1"; }
sha256sum -c DRIVER_SHA256SUMS.txt
```

Every checksum must report `OK`. Check before running installer builders, which replace inert placeholders with independently supplied approvals or private sessions.

| Order | Command | Expected output or gate |
|---|---|---|
| 1 | `orch u1.sh` | `PASS outer SHA; 37 members; sums.txt exact inventory; files 0600`. |
| 2 | `orch q1.sh` | Native receipt reuse and `native_unit_regeneration_executed=true`; ordered indices and projection verified. |
| 3 | `"$PY" -B review_build.py` | `READY rv1.sh; eight-review chain pinned; final verdict GO`, or GO AFTER FIXES with only explicit LOW fixes. `PENDING` means stop here. |
| 4 | `orch rv1.sh` | `PASS installed eight-review chain; final review_r1p8 accepted for packet A; no production GO granted`. |
| 5 | `orch ev1.sh`, then `orch evp1.sh` | `STARTED e0`, then require `e0 rc=0`, correct REMOVE hash, and four evidence records verified. |
| 6 | `orch dv1.sh`, then `orch dvp1.sh` | `STARTED d0`, then require `d0 rc=0`, `status=READY`, exact config identity, and `missing_source_members=[]`. |
| 7 | `orch scan1.sh > scan1.out` | Exact packet/archive/run and MANIFEST SHA; inventory requests an independent complete content scan. |
| 8 | `"$PY" -B cert_build.py ANON_OK.json` | `READY sc1.sh; proof-2 classified scan and ORCH 1758Z exemptions pinned`. Supply the independent certificate and classified scan first. |
| 9 | `orch sc1.sh` | Independent CLEAN certificate installed, bound to the final manifest, archive and scan. |
| 10 | `bash L1_mint.sh` | `PASS 20 fresh create-only sessions; mode 0600; URI contents withheld`. |
| 11 | `"$PY" -B session_build.py`, then `orch si1.sh` | Private installer READY, then `PASS installed sess.json mode 0600; 20 fresh destinations; contents withheld`. |
| 12 | `orch pq.sh` | UTC queue snapshot. Read the newest INBOX before proceeding. |
| 13 | `timeout 300 bash "$OSSH" 'bash -s -- advanced' < pr1.sh` | Sealed-kit checks, CPU sbatch argv with `-t 06:00:00`, then `SUBMITTED job_id=…`. Save that exact ID as `PROOF_JOB`. |
| 14 | Run the canary command below immediately after proof submission. | GO written or byte-equal reuse; active proof and accounting checks; `Submitted batch job …`; `SUBMITTED canary training_job=… proof_job=… admission_job=170956`. |
| 15 | `orch pm1.sh` | Queue, bounded redacted proof and training tails, proof receipt when available, and the training/proof association. |
| 16 | `orch f2.sh` | Proof accounting and bounded proof receipt/log. Keep raw logs private. |

```bash
# Set PROOF_JOB to the exact job_id printed by step 13.
GO_SHA=$(sha256sum "$EVENTS/r1_ops/20261118T0044Z_ORCH_RULING_canary_launch_parallel_proof.md" | cut -d' ' -f1)
timeout 300 bash "$OSSH" "bash -s -- $PROOF_JOB $GO_SHA" < go_submit_canary_9dd2fbb7.sh
```

The final review is `events/review_r1p8/REVIEW_VERDICT_R1P8.md`, accepted by the local builder at November 17, 5:34 p.m. PT (November 18 01:34Z). Its `Packet A:` line must contain one unambiguous GO or GO AFTER FIXES verdict. A's section must name the full archive SHA or config identity. GO AFTER FIXES permits only explicitly LOW, nonblocking fixes. Missing, negative, ambiguous, stale or above-LOW final reviews refuse; Packet B cannot authorize Packet A. All eight review texts and hashes are installed and independently revalidated by the evidence worker. R1P7 is an antecedent approving `a5dc8f30`; it cannot substitute for R1P8.

The independent scan must cover the gate and wrapper additions, including `go_submit_canary_9dd2fbb7.sh`, as well as `scan1.out` and the final kit. FIX12 requires a quick scan because the complete visible surface differs. `CERTIFICATE_REQUIREMENTS.json` lists the 37 required external member pins; it grants no CLEAN status. The certificate must bind the final archive, config, kit manifest, scan output, classified findings, reviewer, CLEAN status and integer zero hits. The existing ORCH 1758Z exemptions remain SHA-bound. Use `--scan-record CLASSIFIED.json` for a local classified record. Never display real sessions or `si1.sh`.

The canary wrapper writes `go.json` with boolean `production_go_granted: true`, `config_sha256`, `admission_contract_sha256`, `wrapper_sha256`, `manifest_sha256`, `authority: sha256:<GO_SHA>`, and boolean `canary: true`. Existing GO bytes must match exactly. It exports `ADMISSION_JOB=170956` and `PROOF_JOB`, requires the proof to equal `BUN/job.id`, and requires one PENDING/RUNNING queue row under the exact job name. The proof ID must also match the retained proof sbatch output and have a submission marker. A second queue snapshot requires a six-hour limit and no GRES, and prints the pending reason for the launch event. Held proofs and unsatisfiable dependencies refuse. These checks address R1P8's proof/training name-collision and pending-reason conditions using the requested six-hour limit. Any other same-name queued job refuses. Accounting must succeed and contain no other same-name allocation except admission 170956 and this proof.

A training lock serializes canary attempts. `training.started` is created exclusively before entering the sealed gate; any existing attempt, job record, transcript, or canary marker refuses another submission. The gate writes `KH/o/<PROOF_JOB>.canary.json`; the wrapper preserves it and records sbatch's training ID in `BUN/training.job.id` and `BUN/training.json`, with the marker and GO hashes. It retains `training.sbatch.out`. A gate failure, uncertain sbatch output, or missing marker leaves the attempt blocked for inspection.

The operator must enforce the ruling's kill conditions: stop training if its admission fails or its stream counts differ from 170956; if the parallel proof fails outside its own script; if loader counts, shares or bound traces violate the card (missing family, more than 5% relative cell deviation, or a ceiling breach); or if the first-step loss/camera checks fail. A failure confined to the proof script permits training to continue with a short CPU audit. Before training reaches step 1, compare admission rows per stream/family against the card and write `PRELAUNCH_CARD_R1.md`, `PRELAUNCH_ROWS_R1.md`, and the first-steps RESULT under events/r1_ops. The launch event must retain the printed proof limit/GRES/reason and training ID beside the gate marker path. This driver does not automate those decisions or cancel jobs.

For a later non-canary launch, obtain the appropriate written ORCH GO and use `go_submit_9dd2fbb7.sh` with a completed PASS proof and that GO file's SHA. It preserves the PASS-proof wrapper behavior, omits `canary`, and pins the new archive, gate, sums, and job wrapper. It is not a retry path for a canary attempt. Old named submit aliases refuse execution.

`archive_delta_p7.json` verifies exactly two changed members versus `p_a5dc8f30.tar`: `s.sh` and `sums.txt`. All other 35 members, including the proof and `jb.sh`, are byte-equal; the training sbatch line is byte-equal. The frozen `KIT_DIFF12.md` compares the packet against the scanned kit and reports no derived-kit differences. The gate SHA is `fbcbb76c43a3307a846eb2c73171dd3ae4f99da7ad273328ce3a1a2e53e7b847`; sums SHA is `23eb51a0f6863e1086365acb4b542b3f62d4e8c3ba15dbf0bae6890cfad37bd8`; `jb.sh` SHA is `b6a1e4c8f4c0a8fce029233575d082fae69ba018a311288dc8391493efa4648f`.

Current local evidence is in `*_p7.txt`, `archive_delta_p7.json`, and `PRESERVED_R1DRV7.json`. Tests use Slurm/gate stubs, synthetic approvals, and the retained READY fixture `tests_p5_lp0z7pgr/derived_ready`; they do not attest production data or scheduler capacity. Tests cover all requested canary cases, uncertain attempts, both proof partitions and resources, PASS-wrapper GO reuse, review isolation, certificate/session builders, packet pins, REMOVE corruption, and sealed switch checks. No SSH, Orchard call, Git, GPU use, deletion, real mint, submission, or external write occurred in this build.
