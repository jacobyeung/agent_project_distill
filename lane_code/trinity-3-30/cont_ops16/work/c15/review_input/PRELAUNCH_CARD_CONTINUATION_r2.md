# Pre-launch card: LEG-S1 continuation, steps 545 to 1,000 (kit 07ca49df, run 469ddece)

I am lane cont_ops on trinity-1-3. Between 18:11Z and 18:25Z on 2026-11-15 I read Orchard in read-only batched calls; the raw output is in `/scratch/jjyeung/orch_n30/cont_ops/work/inv{1..6}.out` on trinity-1-3. I submitted nothing; the two `sbatch --test-only` calls created no job. The independent review is in `REVIEW_VERDICT_CONTINUATION_CARD.md`, beside this card. This revision applies that review's findings.

## 1. Question the run answers

The run completes the registered 1,000-step plan of the sealed LEG-S1 recipe and adds no new idea. It answers two questions:
- Does training to step 1,000 keep or raise the scores the recipe reached at its step-400 and step-544 exports?
- What are the m600, m800 and m1000 exports worth as the sealed-grammar reference against which the repair seal is compared?

## 2. Verdict

**I can submit within minutes of a GO, but the GO has to accept two unproven gates.** Both are listed in the packet's `GATES.json`:
- **Restore equality.** No test has shown that restoring the real slot reproduces its optimizer, RNG and sampler state.
- **Graceful stop.** No graceful stop path has been verified; the only stop route is `scancel`, and no one has tested it on this job.

What the job does establish, before its first update:
- **Byte identity:** the restored files match the slot's records (section 6).
- **Slot selection:** the operator confirms that the job restored slot A, step 544 (section 6, check S).

Rule E is a gross-loss alarm only. Passing it does not prove restore equality.

If ORCH does not waive restore equality, the alternative is the CPU check on `general` (section 6). It costs 1.5 to 5 hours, and the advanced start slips by at least that much.

## 3. Exact command (one submission, on ORCH GO only)

```
cd /home/jjyeung/okit && env -u TK_JOB_START sbatch -J a15_cot_ap0b0c99e1 -o /dev/null -e /project/community/jjyeung/okh7/x_07ca49df/o/%j.err /home/jjyeung/okit/j/07ca49df.sh
```
- **Token and test run.** The token is recorded in `cont_ops/work/ORCHARD_LEDGER.jsonl`. A `--test-only` run at 18:23Z gave the estimate "job 169980 to start at 22:59:04Z on orchard-community-1" (`inv5.out`). That run used the `/home` alias of the same `-e` path, so the GO batch repeats `--test-only` with this literal line first.
- **What changed from 169097.** The line differs from 169097's only in the name, `-o` and `-e`. The wrapper `j/07ca49df.sh` (sha 553f57e3), `job.sh` (737849b3), `b/r.sh` and `b/c.sh` match their recorded hashes on Orchard today. The job's own `a.py` checks the full 95-file inventory at start. A grep of the fetched sources (`c.sh`, `r.sh`, `i.py`, `w.py`, `g.py`, `gcsput.py`) finds no `SLURM_JOB_NAME`; I have not grepped every kit file.
- **`env -u TK_JOB_START` is redundant but safe.** The wrapper sets a fresh `TK_JOB_START`, so the trainer charges restore, staging and admission against the allocation budget. The step counter and LR schedule come from the restored global step.
- **Effect of `-o /dev/null`.** It removes one crash path: rank 0's unguarded `print(..., flush=True)` before each save and export, and `tk_step`'s stdout `printf` under `set -e`. Neither can then fail on a full filesystem. No control path parses the batch stdout. The stall guard reads file sizes and mtimes; uploads read `gcs.log`, receipts, `.done` and `.claim`; rule E reads metrics. The cost is that the trainer's stdout lines are lost: disk-guard JSON, `row_skip` and warnings.
- **What `-o` does not remove.** Three writes still need project space:
  - The stall guard (`sg.py`) prints to stderr before it relays a stop.
  - `r.sh` appends `o/<job>.stop` under `set -e` before it forwards USR1.
  - Both paths run only on a stall or on USR1. A full project filesystem can break them.
- **Fallback.** Drop `-o/-e`; stdout then goes to `o/<job>.out` on project, as in 169097.

## 4. What it binds and does

- **Identity.** Kit 07ca49df (95-file manifest de6e7e0f), configuration identity a7ad7051 (effective 84ea03af), seed 17, world 4, offset 0, fixed-zero sampling, global 1,000-step schedule with warmup 0.05. The selector `r8.py` chooses `u` because a checkpoint is present after restore. The trainer resumes `latest`. No resume flag is new.
- **Resume source.** The records were read today; the payload was not re-hashed.
  - `r/5da50f2b/A.json` reports verified, step 544, job 169097 and 112,988,477,440 B.
  - The archive sha 22249bc7 equals `A.sha256`; the manifest sha is 0450e3a3. `A.verify.part` reports world 4 and 9 payloads.
  - There is no `B.json`. `RUN.json` names first_job 169097.
- **Allocation.** advanced, 4 GPUs (the H100 nodes of the earlier legs), 48 CPU, 800G, 24 h, no requeue, `--signal=B:USR1@3600`. The trainer's budget guard plans its stop from per-step, per-save and per-export allowances of 300, 600 and 600 s. It can call the stop around 22:15 to 22:35 of elapsed time, then save, export and upload.
- **Saves.** The first admitted resumed update, then every 7,200 s, then the final save. All go to node `/tmp`. Two checkpoints stay active; older ones move to `_superseded/` with their payloads. The only persistent state is the end slot.
- **Exports.** m600, m800 and m1000 go by the numbered GCS route `q8/8865619b/469ddece_m{600,800,1000}.tar`; all 12 part sessions are named in `sess.json`. A budget stop before step 1,000 uses the unused `mstopB` generation. Each export is 21.58 GB; uploads measured 283 to 460 MB/s.
- **Assumption: session lifetime.** `sess.json` was modified at 2026-11-13 13:17Z. If these are GCS resumable sessions with a 7-day life, the last one expires around 2026-11-20 13:17Z. Creation times and validity are not verified.

## 5. Where it writes, and what a full filesystem costs

| Writer | Path (resolved) | Filesystem | If full |
|---|---|---|---|
| Slurm stdout | `/dev/null` | none | n/a |
| Slurm stderr | `okh7/x_07ca49df/o/<job>.err` | project | traceback lost; the stall-guard print can fail before its relay (section 3) |
| Wrapper log | `o/<job>.w.steps` | project | lines lost (no `set -e`) |
| Kit step log | `o/<job>.steps` (`tk_step`, `|| true`) | project | lines lost |
| GPU samples; stop flag | `o/<job>.gpu`; `o/<job>.stop` | project | samples lost; the stop-flag write can abort the USR1 handler |
| Upload bookkeeping | `o/gcs.log`, `o/gcs_469ddece_m*.done`, `.claim`, `sess.json.receipts.jsonl` | project | see the list below |
| Metrics, attempt, first-step mirror | `okh7/x_07ca49df/runs/469ddece/{metrics,attempt}_<job>.*`, `inputs/first_step_<job>.json` (rsync every 600 s) | project | mirror goes stale; the node copy is intact until job end |
| End slot B | `okh7/r/5da50f2b/B.*.part`, then records | project | the guard skips B below about 133 GB free (checkpoint + inputs + binding + 20 GB); A is untouched; a failure mid-copy can leave `.part` files |
| Run state, staging, export tars | `/tmp/jjyeung/okit_8865619b/...` | node-local, private per job ("/tmp does not survive between jobs", wrapper line 9) | the wrapper refuses below 3.8 TB in its first minute |
| Trainer inside bwrap | `/home` is a read-only tmpfs; caches and TMPDIR are in `TK_JOBDIR` on `/tmp` | node | n/a |

**If the upload bookkeeping cannot be written:**
- If `gcs.log` cannot be opened, `gcsput` does not run.
- If a later write fails, the objects may already be uploaded with no record of it.
- The `.claim` and `.done` writes are unguarded under `set -e`, so a failed write can kill the background persister. Retries every 600 s continue only while the persister lives.
- **An export reaches GCS only if its upload and its `.done` both succeed.** Step 1,000 alone does not mean m1000 is on GCS.

**`/home`.** The run writes nothing to the real `/home`. Staging does read about 13.9 GB of pinned inputs there: `okit/u/4d66fc2a/*`, `okit/i/eb3429c5`, `okit/i/c6f147a2` and the MDG raster directory. Any quota cleanup must leave these alone (event `home_inputs_must_stay`). ORCH reported `/home` over quota at 17:22Z and writable again at 18:41Z. My `quota` call returned rc=1 and established nothing.

**Project space.** Free space was 217.3 GB at 18:11Z and 215.3 GB at 18:39Z (`inv1.out`, `inv6.out`), at 99% full. Other tenants' swings come from the save-window record (`ORCHARD_SAVE_WINDOW_169097.md`, a 71 GB drawdown) and from ORCH notes of 2026-11-13 (100 to 240 GB/h). This card did not measure them.

**Loss cases:**
- If m1000's upload and `.done` succeed, B is not needed for the plan.
- If the run ends early (node fault, OOM, cancel) or B is skipped, all exact-resume progress since step 544 is lost when node `/tmp` disappears. An uploaded export still allows a warm start, without optimizer or RNG state.

No in-job mitigation exists without a kit change.

## 6. Gates before and during training

| Gate | What it proves | When |
|---|---|---|
| Wrapper restore | archive sha = `A.sha256`, manifest sha = `A.json`, binding, `inputs/` present; exit 3 with no retry | first ~15 min |
| `r8.py` and `g.py` | every payload's size and sha against `complete.json`; binding mirror; restored step not older than the newest slot; no cold start | before admission |
| **Check S (operator, before any update)** | `w.steps` must show `restore: slot A step 544 into …`. The wrapper restores only when the node run directory holds no complete checkpoint, and node `/tmp` is private to the job, so this line means `checkpoint_000544_16d2a80a…` is the only checkpoint and `latest` must select it. If the line is missing, the operator cancels before training (admission takes about 2 h). Then `attempt_<job>.json` must show first_step 545 and a resume pin naming checkpoint A or manifest 0450e3a3; rule E also checks this. | restore line ~15 min after start; attempt record ≤10 min after training starts |
| Native step-545 gate `all_rank_native_v1` | 4 ranks, stream and microstep counts, no skips or substitutions, finite losses and gradient norms; the trainer raises on failure | step 545 |
| Rule E (gross-loss alarm) | see below | steps 545-547 |

**Not covered by any gate, and accepted only by the GO:**
- Semantic restore equality: optimizer moments, scheduler step, RNG, sampler position.
- CUDA RNG installation.
- Graceful stop.

The CPU proof would be the canary checker 026cb696: `general`, 16 CPU, 800G, 0 GPU, at most 5 h, 554 GB of private disk, duration unmeasured. It re-reads the 113 GB `A.tar`. `general` allows one running job per user, and per the brief evalx27 uses it today (my `squeue` did not show which job), so the proof waits for or displaces that job.

The small-scale proof is a 4-rank, 3-step CPU exact-resume run at 1e-6. It is recorded in `distill_design/LEG_S1_TREE_20261111.md`, not in `CPU_PROOF.json`.

**Rule E**

Tool: `cont_tools/early_loss_check.py METRICS ATTEMPT`. It exits 0 for PASS, 3 for PENDING and 2 for ALARM, and has 14 local cases (`test_early_loss_check.py`). The baselines come from steps 530 to 544 of `metrics_169097.jsonl` and were fixed before launch. Each value is the four-rank mean, median (MAD):
- pose 0.16716 (0.0092)
- vqa 0.10068 (0.00734)
- routing 0.0061 (0.00275)
- pointing 0.51085 (0.02317)

The check reads the first three complete lines of the new attempt's file in file order.

**ALARM** fires on any of these:
- the steps are not exactly 545, 546 and 547 in order (duplicates, gaps, reordering);
- a step key is missing;
- ranks are not exactly 0 to 3;
- a rank's step disagrees;
- a stream is missing or nonfinite;
- any microstep is skipped;
- the attempt record is missing while rows exist, or names a wrong first step or resume pin;
- for any stream, |median of three − baseline| > max(0.5·|baseline|, 6·1.4826·MAD, 1e-6).

An unterminated last line counts as an in-flight write: PENDING, not ALARM.

**What rule E catches:**
- A cold start: the parent's steps 1 to 3 give routing 1.13, vqa 0.21 and pose 0.26, which all alarm.
- A wrong resume pin or first step, through the attempt record.
- It does **not** reliably catch a lost optimizer state, a wrong RNG state, a wrong LR position or replayed rows with correct labels.
- All 23 overlapping three-step windows in steps 520 to 544 pass. That shows a low false-alarm risk; it is not a calibrated rate.

**Stale-row rule.** If 50 minutes after the native first-step report appears (about 3 h after job start) no row 547 is persisted while the job runs, raise a BLOCKER. If the job has exited, report its exit.

**On ALARM** (the GO authorizes this per ORCH 18:28Z): run `scancel <job>`, keep A and the evidence, and report.
- I expect `scancel` to stop optimization and to leave B unwritten: the wrapper has no TERM trap, so the copy phase does not run. This follows from the code and is untested.
- I verify the stop with `sacct` showing CANCELLED and no new metrics row after one persist cycle.
- **Lag:** a 600 s persist interval plus a 60 s watch means up to about 7 updates of about 131 s each run before detection.

**Rules W and A.**
- **W (wall):** the trainer's budget stop, with a stop export, after which the wrapper writes B if space allows.
- **A (admission):** any refusal by the wrapper, `r8.py` or admission ends the job by itself, with no resubmission without ORCH.

**Milestones.** Registered stop rules exist only for steps 100 and 200 (ORCH ruling 2026-11-14, recovered as `evalx/written/20261114T041230_…_milestone_step_set_everywhere.md`). m600, m800 and m1000 are reported milestones with no stop rule. Any m600 rule must be written before launch.

## 7. Cost and timing (from 169097's measurements)

| Component | Estimate |
|---|---|
| Staging and mode-p admission to the first trainer launch (169097: 15:25 to 17:28Z) | 2:03 to 2:07 |
| Restore of A.tar (written at 253 MB/s, re-read at 245 MB/s); not measured as a restore | 0:08 to 0:12 |
| `r8.py` and `g.py` re-hash 113 GB of local checkpoint up to 4 times, plus state loading; unmeasured | ~0:10 to 0:30 (guess) |
| 456 updates × 131.12 s, the mean of steps 530-544 (rank-0 step time, excluding checkpoint and export durations) | 16:36:29 |
| Extra cost of the first update | ~0:05 |
| First resumed save + ~8 periodic + final, at ~76.6 s each | ~0:13 |
| 3 exports at ~4 min (export, tar, upload) | ~0:12 |
| End slot (write 447 s + verify 461 s) | 0:15 |
| **Total** | **~19:40 to 20:10**, against a budget stop near 22:15 to 22:35 and the 24 h limit |

- **Margin:** about 2 to 2.5 h. That is an estimate, not a guarantee. The packet's conservative scenario totals 20:25. About 80 H100-hours are allocated.
- **Brief's 226 s/step.** That figure was the canary's rate with a save every step. It is not in the lane folder, and at that rate the updates alone would need 28:37, so the plan could not finish in one allocation.
- **Likely window:** start around 22:59Z (14:59 PT) per the test-only run; end around 2026-11-16 19:00Z (11:00 PT).

## 8. Confounds

1. **The data breaches the trace grammar.**
   - Every continued step trains on rows the 2026-11-15 ruling rejects (`distill_design/TRACE_RULING_20261115.md`, lines 16, 26 and 47-50).
   - Each step holds 288 rows, 192 of them language rows (128 VQA, 64 routing). Of those, 15.3 are answer-only and 95.0 state a measurement in prose: 110.3 of 192, or 57%. Over 456 steps that is about 7,000 and 43,300 more such rows.
   - So m1000 measures the sealed recipe at full schedule. It is a clean control for the repair seal only if that seal uses the same parent, schedule and steps.
2. **Split allocation.**
   - The run spans two allocations: CUDA RNG is re-installed, some kernels are nondeterministic, and the node may differ.
   - The gate EMA replay starts empty. `replay_gates` reads `metrics_*.jsonl` from the node run directory, and the slot does not carry them. With exposure and own probabilities of 0.0, no row changes.
   - There is no resumed-versus-uninterrupted comparison. Label results "two allocations".
3. **Schedule position.** m600 and m800 sit at a higher LR than m1000. Compare same-step exports across legs.
4. **Untrained types** stay labeled "untrained in this leg".

## 9. Row mix per step

Each step draws 288 rows: pose 64, VQA 128, routing 64 and pointing 32, with no MDG.
- Mix: `[pose, vqa, vqa, routing, pose, vqa, vqa, pointing, routing]`.
- Weights: pose 1.5, depth 0.25, depth_fov 0.05, all others 1.0.
- Of the 192 language rows, 110.3 breach the grammar (section 8).

## 10. Reads, and the other lanes while 4 advanced GPUs are taken

- **The QOS is per user.** `adv_4gpu_qos` allows at most 4 GPUs on one node, and 6 jobs, per user jjyeung. This job takes all four for about 20 h. No other advanced job of the user runs meanwhile, main's included.
- **Main's `jjy_*` jobs.** Five 1-GPU jobs of 3.5 h each are chained 167857→…→167861 behind 167894, which main holds; 168278, 167894 and 167739 are held. None is eligible, and I touch none. ORCH is asking main (18:28Z).
- **native_r2.** If its pilot is ready first, it goes first (ORCH 18:28Z). That delays our start by the pilot's length.
- **Milestone reads during the run** cannot use advanced. They can run on `general` after evalx27, or on Trinity 49 GB cards from the GCS export (21.6 GB through the head node, IO governor), or wait for m1000.

## 11. On GO (one batched call), then watch

1. Recheck:
   - wrapper, `job.sh`, `r.sh` and `c.sh` shas;
   - `A.json` and `A.sha256` unchanged (22249bc7); no `B.json`;
   - no job of ours for this run in the queue;
   - main's advanced jobs not eligible-pending;
   - project free space ≥ 150 GB;
   - `--test-only` of the literal line.
2. Write test: one new 64 KiB file `okh7/x_07ca49df/o/.wtest_cont_<stamp>`, with fsync and read-back sha. The file stays; it goes on the removal list.
3. Submit, and record the job id, stdout, queue line and free space in `cont_ops/work/SUBMISSION.json`.
4. **Watch:**
   - every minute until the job runs and check S passes;
   - every 5 minutes until rule E's verdict;
   - then every 10 minutes.

   Each watch is one batched `ossh` call.
5. **Events.**
   - A RESULT for each of: start, check S, admission passed, step 545, the rule-E verdict, each of m600, m800 and m1000 with upload and `.done`, and the end.
   - An immediate BLOCKER for any refusal, ALARM, missing restore line, a step slower than 450 s, a failed upload or a stale row.
