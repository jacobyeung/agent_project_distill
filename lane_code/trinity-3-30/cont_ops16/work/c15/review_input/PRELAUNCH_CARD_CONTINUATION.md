# Pre-launch card: LEG-S1 continuation, steps 545 to 1,000 (kit 07ca49df, run 469ddece)

Lane cont_ops, trinity-1-3. Orchard facts read 2026-11-15 18:11Z to 18:25Z in five batched read-only calls (raw output: `/scratch/jjyeung/orch_n30/cont_ops/work/inv{1..5}.out` on trinity-1-3). Nothing was submitted; two `sbatch --test-only` calls created no job.

## 1. Question the run answers

Does the sealed LEG-S1 recipe, trained to its registered 1,000-step schedule, keep or raise the scores it reached at m400/m544, and what are its m600, m800 and m1000 exports worth as the sealed-grammar reference that the repair seal is compared against? The run completes the plan; it adds no new idea.

## 2. Verdict

The packet is ready to launch. Every byte the resume reads is checked inside the job before the first update. The run neither reads nor writes anything under the full Orchard `/home`. Two points remain unproven: semantic restore equality and a graceful stop. The job's own first three steps and `scancel` cover them (section 6). The main exposure is the 99%-full project filesystem (section 5).

## 3. Exact command (one submission, on ORCH GO only)

```
cd /home/jjyeung/okit && env -u TK_JOB_START sbatch -J a15_cot_ap0b0c99e1 -o /dev/null -e /project/community/jjyeung/okh7/x_07ca49df/o/%j.err /home/jjyeung/okit/j/07ca49df.sh
```
- Token `a15_cot_ap0b0c99e1` is recorded in `cont_ops/work/ORCHARD_LEDGER.jsonl`. `--test-only` of this exact line at 18:23Z gave `Job 169980 to start at 2026-11-15T22:59:04 on orchard-community-1` (about 14:59 PT).
- The line differs from 169097's line only in the name, `-o` and `-e`. The name is not bound by the kit; no kit file reads `SLURM_JOB_NAME`. Wrapper `j/07ca49df.sh` (sha 553f57e3) and `job.sh` (737849b3) are unchanged, and both hashes were re-verified on Orchard today.
- **Why `-o /dev/null`:** rank 0 calls `print(..., flush=True)` without a guard before every save and export, and the stdout of `tk_step` runs under `set -e`. On a full NFS filesystem either write can kill a rank or the persister. Sending stdout to `/dev/null` removes that crash path. Tracebacks and warnings still go to `.err` on project, where Python's warnings and a dying process tolerate a failed write. The cost: the trainer's stdout lines (disk-guard JSON, `row_skip` and warning lines) are not kept. Metrics, steps, the first-step report and gcs.log are separate files and are kept. Fallback if ORCH prefers 169097's behaviour: drop `-o/-e`; stdout then goes to `o/<job>.out` on project.

## 4. What it binds and does

- **Kit and identity:** kit 07ca49df (95-file manifest de6e7e0f), effective configuration 84ea03af, seed 17, world 4, offset 0, fixed-zero sampling, global 1,000-step schedule (warmup 0.05). There are no new resume flags. The native selector `r8.py` chooses `u` because a checkpoint is present after restore; `w.py` resumes from `latest`.
- **Resume source (verified today):** `r/5da50f2b/A.tar` holds 112,988,477,440 B at step 544 from job 169097. `A.json` is verified, its archive sha 22249bc7 equals `A.sha256`, and its manifest sha is 0450e3a3. `A.verify.part` reports world 4 and 9 payloads. There is no B.json. RUN.json gives first_job 169097. The binding mirror sha is 209bcf8a.
- **Allocation:** advanced, 4 H100, 48 CPU, 800G, 24 h, no requeue, `--signal=B:USR1@3600`. The trainer's own budget stops it at 23 h (`stop_before_seconds` 3600) with an `export_at_stop`.
- **Saves:** the first admitted resumed update, then every 7,200 s, then the final or guarded stop. All saves go to node `/tmp`; the trainer keeps the two newest. The only persistent state is the end slot (section 5).
- **Exports:** registered milestones m600, m800 and m1000 go through the numbered GCS route, `q8/8865619b/469ddece_m{600,800,1000}.tar`. All 12 part sessions exist in `sess.json` (names checked, no contents). A budget stop before 1,000 uses the unused `mstopB` generation; `mstopC` remains as a spare. Each export is 21.58 GB. Uploads measured 283 to 460 MB/s.
- **Sessions:** `sess.json` was last modified 2026-11-13 13:17Z. If these are GCS resumable sessions with a 7-day life, the m1000 session lasts until about 2026-11-20 13:17Z. That is an assumption and is unverified; the job should end around 2026-11-16 19:00Z.

## 5. Where it writes (ORCH's 18:06Z note)

| Writer | Path (resolved) | Filesystem | If that filesystem is full |
|---|---|---|---|
| Slurm stdout | `/dev/null` | none | n/a |
| Slurm stderr | `okh7/x_07ca49df/o/<job>.err` | project | traceback lost; no crash path |
| Wrapper log | `okh7/x_07ca49df/o/<job>.w.steps` | project | lines lost (no `set -e`) |
| Kit step log | `o/<job>.steps` (via `tk_step` with `|| true`) | project | lines lost |
| GPU samples, stop flag | `o/<job>.gpu`, `o/<job>.stop` | project | lost; the stop flag is only written on USR1 |
| Upload log, done, claim, receipts | `o/gcs.log`, `o/gcs_469ddece_m*.done`, `.claim`, `sess.json.receipts.jsonl` | project | **the upload is skipped while full** (the `>> gcs.log` redirect fails, so `gcsput` never runs) and retried every 600 s and once at exit; an export still unsent when the job ends is lost with node `/tmp` |
| Metrics, attempt, first-step mirror | `okh7/x_07ca49df/runs/469ddece/metrics_<job>.jsonl`, `attempt_<job>.json`, `inputs/first_step_<job>.json` (rsync every 600 s) | project | mirror stale; the node copy is intact until job end |
| End slot B | `okh7/r/5da50f2b/B.tar.part` and records | project | the wrapper's guard skips B (needs about 113 GB + 20 GB), A stays untouched, exports are kept |
| Run state, staging, export tars | `/tmp/jjyeung/okit_8865619b/...` | node-local ext4 (5.8 TB at 169097) | the wrapper refuses below 3.8 TB in its first minute |
| Trainer inside bwrap | `/home` is a read-only tmpfs; caches and TMPDIR are under `TK_JOBDIR` on `/tmp` | node | n/a |

**The run writes nothing under the real `/home`, but staging reads about 13.9 GB of pinned inputs there** (`okit/u/4d66fc2a/*`, `okit/i/eb3429c5`, `okit/i/c6f147a2`, the MDG raster directory). Reads work while over quota. Clearing the quota must not touch them (event `home_inputs_must_stay`). Every `/home/jjyeung/okit/{x/07ca49df,r,j}` path is a symlink to project, so `/home` staying over quota is not a blocker. The `.out` path in the wrapper's `#SBATCH` header also resolves to project and is overridden by `-o`.

**Project space now:** 215.6 GB free (99%) at 18:23Z. Free space has swung by 100 to 240 GB/h on other tenants' writes. Consequences:
- If the run reaches step 1,000, m1000 is on GCS and B is not needed for the plan.
- If the run stops early (node fault, OOM, cancel), all progress since 544 is lost except exports already on GCS. Only the end slot persists state.
- If project is full at m600/m800/m1000 and stays full until job end, that export is lost. A warm start from m800 is still possible.
- No in-job mitigation exists without a kit change.

## 6. Unproven points, proofs and stop rules

| Point | Status | Cheapest proof |
|---|---|---|
| Byte identity of the restored state | proven in-job before any update | The wrapper checks the archive sha against `A.sha256`, the manifest sha against `A.json`, and the binding and `inputs/`, then exits 3 with no retry. `r8.py` re-hashes all 9 payloads against `complete.json`, checks the binding mirror and refuses a restored step older than the newest slot. These gates cost minutes and no separate job. |
| Semantic restore (optimizer moments, scheduler step, RNG, sampler position) | unproven at production size; proven at small scale on CPU (4 ranks, 3 steps, 1e-6) | **The job's own steps 545 to 547, compared with steps 530 to 544** (rule E below). |
| Native first-step admission | in-job | Gate `all_rank_native_v1` at step 545 checks 4 ranks, stream and microstep counts, no skips or substitutions, finite losses and gradient norms. The trainer raises on failure. |
| Graceful stop on request | the budget stop is proven (it fired at 544 in 169097); the USR1 relay is unproven | For an alarm, use plain `scancel <job>`. The wrapper has no TERM trap, so the copy phase never runs, A stays intact and B is not written. Optimization stops at once; I verify it with `sacct` State=CANCELLED and no new metrics row after one persist cycle. Work since 544 is lost, and on an alarm it is unwanted anyway. |
| Gate EMA replay | known gap, no effect expected | `replay_gates` rebuilds the scheduled-sampling EMA from `metrics_*.jsonl` in the node run directory. The slot does not carry `metrics_169097.jsonl`, so the EMA restarts empty. With `exposure_probability` and `max_own_probability` both 0.0, no row changes. The m400 gate only fires when start<400, and geometry_online is off. |

**A separate CPU proof on `general`** would be the canary's checker 026cb696 (16 CPU, 800G, 0 GPU, up to 5 h, 554 GB private disk, about 90 min expected). It also re-reads the 113 GB `A.tar` from project. `general` allows one running job per user (`general_qos`: 1 job, 1 GPU), and evalx27 holds it today, so the proof would wait for evalx27 or displace it, and the advanced start would slip by its queue wait plus 1.5 to 5 h. If the resume is bad, rule E detects it about 3 h into the job, which costs about 12 H100-hours. **Recommendation: no separate CPU proof.**

**Stop rules, fixed before launch:**
- **A (admission).** Any wrapper restore refusal, `r8.py` refusal, admission failure or step-545 native gate failure ends the job by itself. There is no resubmission without ORCH.
- **E (early loss).** Read steps 545, 546 and 547 from the persisted `metrics_<job>.jsonl`. **ALARM** if the first step is not 545, steps are not contiguous, any of ranks 0-3 is missing, a rank's step disagrees, a loss is missing or nonfinite, or any microstep is skipped. Otherwise compute, for each stream, the median over the three steps of the four-rank mean of `stream_means`. ALARM if |median − baseline median| > max(0.5·|baseline|, 6·1.4826·MAD, 1e-6). The baselines from steps 530 to 544 of `metrics_169097.jsonl` (86,552,359 B, read today) are:
  - pose 0.16716 (MAD 0.0092, alarm outside 0.0836 to 0.2507)
  - vqa 0.10068 (MAD 0.00734, outside 0.0354 to 0.1660)
  - routing 0.0061 (MAD 0.00275, above 0.0306)
  - pointing 0.51085 (MAD 0.02317, outside 0.2554 to 0.7663)

  A cold-start resume would be caught: the parent's steps 1 to 3 give routing 1.13, vqa 0.21 and pose 0.26, all of which alarm. Tool: `cont_ops/work/early_loss_check.py`, tested on that cold case (ALARM), on baseline-like rows (PASS) and on partial input (PENDING). One or two valid steps are PENDING. **On ALARM the operator runs `scancel` at once** (this needs ORCH's GO to say so), preserves A and the evidence, and reports. Persist lag means the job runs up to about 5 more updates before the stop.
- **W (wall).** The trainer's budget stops it at 23 h with a stop export (mstopB), and the wrapper writes B if space allows.
- **Milestone reads.** Registered stop rules exist only for steps 100 and 200 (ORCH 2026-11-14), so m600/m800/m1000 are "REPORTED MILESTONE; no registered stop rule; decisions remain with ORCH". If ORCH wants an m600 rule, it must be written before launch.

## 7. Cost and timing (from 169097's measurements)

- Restore: A.tar was written at 253 MB/s and re-read at 245 MB/s, so restore takes about 8 to 12 min plus the `r8.py` re-hash on local disk.
- Admission: staging plus mode-p admission took 2 h 03 min in 169097 (15:25 to 17:28Z).
- Training: steps 530 to 544 took 131.1 s each on average (max 135.8), including data wait. 456 steps take 16 h 37 min. 8 periodic saves at about 75 s and 3 exports at about 4 min add about 22 min.
- End slot: write 447 s and verify 461 s, about 15 min.
- **Total: about 20 h of the 24 h allocation, about 3 h before the 23 h budget stop, which is about 80 H100-hours allocated.** Step 1,000 fits with margin.
- The brief's 226 s/step was the canary's rate with a save every step. Production measured 131 s; at 226 s, step 1,000 would not fit.
- Likely start: the 22:59Z estimate (14:59 PT), on orchard-community-1, which also hosts other tenants' preempt jobs. End: about 2026-11-16 19:00Z (11:00 PT).

## 8. Confounds

1. **Trace grammar breach.** Every continued step trains on the sealed rows, which the 2026-11-15 ruling rejects. Of 288 rows per step, 192 are language rows (128 VQA, 64 routing). Of those, 15.3 are answer-only (empty think) and 95.0 state a measurement in prose: 110.3 of 192, or 57%. Over 456 steps that adds about 7,000 answer-only rows and 43,300 stated-measurement rows. m1000 measures the sealed recipe at full schedule; it cannot serve as a grammar-compliant model. It is a clean control for the repair seal only if the repair seal uses the same parent, schedule and steps.
2. **Split allocation.** The resume runs on a different node with CUDA RNG re-installed, nondeterministic kernels and an empty gate EMA (no effect at probability 0). m1000 is not bit-equal to an uninterrupted run, so any comparison should say "two allocations".
3. **Schedule position.** m600 and m800 are read mid-decay at a higher LR than m1000. Compare milestones of this run with the same-step exports of other legs, not across steps.
4. **Untrained types** (zero language rows in this leg) keep drifting from the parent and stay labeled "untrained in this leg".

## 9. Row mix per step

288 rows per step: pose 64, VQA 128, routing 64, pointing 32, with no MDG stream (mix `[pose, vqa, vqa, routing, pose, vqa, vqa, pointing, routing]`, weights pose 1.5, depth 0.25, depth_fov 0.05, others 1.0). Of the 192 language rows, 110.3 breach the grammar (section 8) and 81.7 do not.

## 10. Reads that follow, and the other lanes while 4 advanced GPUs are taken

- **The QOS is per user.** `adv_4gpu_qos` gives at most 4 GPUs on 1 node and 6 jobs per user jjyeung. This job takes **all four advanced GPUs for about 20 h**. No other advanced job of this user runs meanwhile, including main's.
- **Main's `jjy_*` jobs** are 5 chained 1-GPU jobs of 3.5 h each (167857→…→167861), behind 167894, which main holds. 168278, 167894 and 167739 are held. None is eligible now; I did not touch them. If main releases 167894, its chain (about 17.5 GPU-h) waits until this job ends. **ORCH must ask main before GO.** Main has priority, and its jobs share our 4-GPU cap.
- **native_r2** needs 1 advanced GPU for a pilot and a read. Option 1: it submits first, and our 4-GPU job starts when its GPU frees; the estimated start is already 22:59Z, so a short pilot before then costs nothing. Option 2: it waits about 20 h. **Default: native_r2's pilot first, if it is ready to submit before about 21:30Z; otherwise it waits.**
- **evalx27** stays on `general` (1 job per user), unaffected.
- **Milestone reads during the run:** m600 lands about 3.5 h after the first step (about 2026-11-16 04:00Z) and m800 about 7.5 h later. They cannot use advanced while this job runs. Run them on `general` after evalx27, or on Trinity 49 GB cards via the GCS export (21.6 GB through the head node, IO governor). Otherwise they wait for m1000, which lands about 2026-11-16 18:40Z.
- **Order:** m1000 first, then m800 and m600, read with the same reader and rules as m400.

## 11. On GO (one batched call), then watch

1. Recheck: wrapper and job.sh shas; `A.json` and `A.sha256` unchanged (22249bc7); no `B.json`; no job of ours named for this run; main's advanced jobs not eligible-pending (held or Dependency only); project free ≥ 50 GB.
2. Write test: one new 64 KiB file `okh7/x_07ca49df/o/.wtest_cont_<stamp>` with fsync and read-back sha. The file stays and goes on the removal list.
3. Submit the line in section 3 and record job id, stdout, queue line and project free space in `cont_ops/work/SUBMISSION.json`.
4. Watch every minute until running and `w.steps` shows the restore line, then every 5 min until step 547 is persisted, then every 10 min. Each watch is one batched `ossh` call. RESULT events go out for: start; restore OK; admission passed; step 545; rule E verdict; m600, m800 and m1000 uploaded; end. A BLOCKER goes out at once for any refusal, alarm, a step slower than 450 s or a failed upload.
