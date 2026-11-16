# Build H1-kit-4: review fixes and the H1-0 read plan (CPU only)

You are a Codex builder for lane h1_headsft on Trinity node trinity-3-30. Workspace `K=/scratch/jjyeung/orch_n30/h1_headsft/kit`
(write only inside K). It holds builds 1-3: read `K/BUILD_REPORT.md` first and keep everything that passes. Work
autonomously; where something is ambiguous, choose the conservative option, record it in `K/BUILD_REPORT.md`, continue.

## Rules for the build (binding)
- Trinity rules: never run recursive grep/find/du/ls -R or any search over `/home` or `/data*`; read named files there
  only, in bounded parts. No Git. No ssh/scp/rsync/network. No GPU (`CUDA_VISIBLE_DEVICES=""`). No deletion or
  modification outside K; inputs are read-only.
- Disk: this node must keep 200 GiB free and has about 3 GiB of headroom. Put every temporary and pytest basetemp under
  ONE directory `K/tmp/b4/`, never copy the tree, a kit or model files per test, and add under 100 MB in total. Report
  the size you added.
- Python `/scratch/jjyeung/envs/p1cpu/bin/python -B` through `K/cpu.sh`; at most 32 GB RAM and 16 threads.
- No answer post-processing: the model converts units and formats numbers itself.

## Fixes
The cross-family review (verdict `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/h1_headsft/REVIEW_VERDICT_H1KIT.md`,
read it in full first) found seven defects; the orchestrator ordered all seven fixed. Copy the reviewer's failing tests
`/scratch/jjyeung/orch_n30/review_h1kit/work/kit/tests/test_review.py` into `K/tests/test_review.py` (record its sha256;
adapt only import paths, never the assertions' intent). All seven must pass, and every earlier test must still pass.
1. Stop rule (registered): an own camera row's faithful answer DIFFERS from GT when the option changes (movement
   direction), when the relative difference exceeds 10% (displacement), or when the wrapped absolute difference exceeds
   10 degrees (rotation). All-reduce the counts across ranks every step; if the share over steps 1-50 exceeds 0.35, the
   leg exports m100, writes a stop record naming the rule, and stops at step 100. Log the share per step.
2. S1 at the first batch: the CPU first-batch tools (tiny and `real_first_batch`) run step 2 (the first step that draws
   pose-own under seed 17) or force pose-own, so faithful rows pass the full forward and backward on every rank; print
   the own-row count per rank (must be > 0 on every rank).
3. Every per-row S1 failure (MaterializeRefusal, RenderError, ValueError, KeyError, StopIteration, IndexError) becomes a
   counted refusal that trains the GT row; add the sealed path's all-reduced failure flag so no rank can diverge from
   the others at a collective.
4. Modes match the registration: `rotate_translation` 180 degrees; `scale_translation` and `scale_scene` run at both
   k = 0.5 and k = 2; modes are keyed by name plus parameter everywhere (runner, statistics, pair, curve, CLI).
5. M1 and M2 bars computed with pass flags (registration in `/data2/jjyeung/agent_project_data/distill_design/H1_GT_HEAD_ROUTING_SFT_20261116.md`,
   section "Registration"): M1 call rate >= 98% and exact sequence >= 95% per routed type, answer-before-first-call
   <= 1%, false calls <= 2% overall and <= 5% per direct type, ReVSI distance call rate >= 95%; M2 own-minus-tower
   per-item paired difference per type with the room bootstrap, adequate when the lower bound is above -5.
6. Each mode runs only on its own type (see the read plan below).
7. Faithful-identity gate wired into preparation: a preparation step runs `rows/faithful_check.py` logic over the packed
   camera rows of the routing receipt the config binds, writes the identity rate and refusal histogram into the
   preparation record, and refuses the launch with S1 on when identity < 95%. Provide `rows/faithful_gate.py <rows>`
   for an operator to run the same check on a rows file or SQLite receipt on any CPU host.
Minor items from the verdict: compare the R0 pin with R0_SHA256 in `h1_r0.py`; make the H1 stop report a distinct
status (not `stopped_for_resume`) so no wrapper requeues it.
Item payloads: `devs1_direct` becomes ready with the 300 facing twins now on this node:
`/scratch/jjyeung/orch_n30/h1_headsft/work/items_in/DEV_BACKDIR/TASKS.jsonl` (sha256 730ed5363f91a19c99de6f903b947066f5da3b19c42e70f095fa518ac54c5f15, away)
and `/scratch/jjyeung/orch_n30/h1_headsft/work/items_in/DEV_FORWARD_TWINS/TASKS.jsonl` (sha256 4d6c3a9411d091d1f583a9e308525ca08dec55df05fe7c0a1c7c39e8043239af, forward);
the 1,825 IDs must equal the e193 inventory (1,525 main + 150 away + 150 forward); rerun the R0 check.

## Read plan of the H1-0 launcher (`K/h1eval/h10/`)
1. Each perturbation mode runs only on its own type: `scale_translation` on camera_displacement,
   `rotate_translation` on camera_movement_direction, `negate_turn` on camera_rotation, `scale_scene` on
   object_abs_distance. The own arm decodes every item once unperturbed (baseline) and each routed item once more
   under each of its type's modes. The tower arm decodes every item once, unperturbed, never per mode, and
   `--tower-from <dir>` reuses tower records of b04's parity read (same export, items and reader hashes; refuse on
   any mismatch) instead of decoding them again.
2. Print the read count before starting and in `RUN_H10.md`: dev-S1 routed 636 + 900 own decodes (+636 tower unless
   reused); ReVSI official999 999 + 566 own decodes. Expected card-hours = reads x measured seconds per read; the
   launcher measures seconds per read on its first 10 items and writes the projection to its log.
3. Tests: mode-to-type mapping, read counts for both sets, tower reuse refusal on a hash mismatch, resume.

## Finish
Append a "Build 4" section to `K/BUILD_REPORT.md` (every test command with pass/fail counts, size added, what is
unverified) and update `K/SHA256SUMS`.
