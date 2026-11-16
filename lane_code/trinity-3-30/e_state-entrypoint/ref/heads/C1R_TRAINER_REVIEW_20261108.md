# C1-r trainer: independent training review (Claude Opus, 2026-11-08 11:40Z)

**VERDICT: GO-AFTER-FIXES.** This covers trainer commit `5cbc49c4` (worktree `c1r/work/repo_c1r`) and kit config `kit/k/b4254f7a.json`.
- I found no blocking defect in the training mechanics. Train mode, checkpointing, gradients, head init, the alignment target, frame identity and the loss all check out (§4).
- Two blocking items sit in the launch configuration and the kit. A third sits in the readout. The readout item does not block the training submit, but it blocks trusting the m100 canary and the m400 gate.

Scope: c1r_run, c1r_align, c1r_data, c1r_dense (plan, load_clip, read_record, teacher forward), c1r_resume, c1r_targets, carrier_c1 / carrier_c1_data / carrier_c1_run / carrier_c1_sweep, camera_head (init, head, loss), plus kit `w.py`, `i.py`, `k/8.json` and `b4254f7a.json`. I made 2 read-only code-aws calls: one fetched C1-b's prepared camera block, the other listed `$X` and checked path resolution.

## 1. BLOCKING

**B1 (submit): the kit config `b4254f7a` is not the C1-r P0.5 dense run.**
- What the config contains:
  - `frames.layout: "spread"`.
  - `streams` holds only the legacy F1 per-clip plan `z/a0170001.json`. It has no `dense_plan`.
  - It has no `resume_every_seconds` and no `milestones`.
- Failure if submitted as is:
  - `ClipRows` takes the legacy path (`c1r_data.py:225,244-256`). That path waits for `$X/binding.json` plus `f/` and `g/` per-clip files, which the dense materializer never writes.
  - Each rank then blocks in `wait_for_files` for up to 45 min (`c1r_data.py:120-129`). The NCCL watchdog's default 10-min timeout (`c1r_run.py:223`, no timeout passed) kills the job at step 1.
  - Even with a legacy cache, the run would train spread rather than P0.5. It would also save every 100 steps and export no m100.
- Minimal fix (I1b's NOTES give the same list):
  - `frames = {layout: "paired", pair_gap_seconds: 0.5, pixels_per_frame: [16384,147456]}`.
  - `streams.clips_plan` = the gunzipped B2 paired JSONL, `$X/p10/02.jsonl`. LAYOUTS order is 01 spread, 02 paired, 03 paired-1, 04 duplicate, 05 paired-16. Only the `.gz` copies exist on AWS now.
  - `streams.dense_plan` = `$X/p10/a0.json`, sha `147ce9f8…`.
  - `cache_root` = `$X`. This already matches the materializer's `--out` in `k/8.json`.
  - `resume_every_seconds: 1800` and `milestones: [100,200,400,800]`.
  - Then re-prepare. The identity changes.

**B2 (submit): the kit cannot authorize a dense-plan training job.**
- Cause: modes s, t and u call `coverage_check` (`kit/b/i.py:42-53`, called at `:102` and `:115`). It needs a `c1r-coverage-v2` report whose `plan` equals `cfg.streams.clips_plan`.
- The only producer is `c1r_clips.coverage` (`c1r_clips.py:916-940`). It validates a legacy per-clip plan and its worker receipts. It cannot read the B2 JSONL or the dense shard indexes, and I1a states that trainer modes were left on their old interfaces.
