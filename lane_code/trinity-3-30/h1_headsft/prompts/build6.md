# Build H1-kit-6: real-weight S1 first batch on fixture rows (CPU only)

You are a Codex builder for lane h1_headsft on Trinity node trinity-3-30. Workspace `K=/scratch/jjyeung/orch_n30/h1_headsft/kit`
(write only inside K). Read `K/BUILD_REPORT.md` sections "Build 4" and "Build 5" first and keep everything that passes.
Work autonomously; where something is ambiguous, choose the conservative option, record it in `K/BUILD_REPORT.md`
under a new section "Build 6", and continue.

## Rules for the build (binding)
- Trinity rules: never run recursive grep/find/du/ls -R or any search over `/home` or `/data*`; read named files there
  only, in bounded parts. No Git. No ssh/scp/rsync/network. No GPU (`CUDA_VISIBLE_DEVICES=""`). No deletion or
  modification outside K; inputs are read-only. Never kill processes.
- Disk: this node is at its 200 GiB floor. Put every temporary and pytest basetemp under ONE directory `K/tmp/b6/`,
  never copy the tree, a kit or model files, and add under 20 MB in total. Report the size you added.
- Python `/scratch/jjyeung/envs/p1cpu/bin/python -B` with `CUDA_VISIBLE_DEVICES= PYTHONPATH=K/tree:K`, at most 32 GB
  RAM and 16 threads here. Pytest: `-p no:cacheprovider -p tests.reader_plugin -p tests.build4_plugin --basetemp=K/tmp/b6/<name>`.
- No answer post-processing; faithful training rows keep the model's own answer (ORCH ruling).

## Why
H1-1 (S1 faithful own camera rows + S2 pose targets, `K/configs/h1_1.json`) launches on 4 H100 at 06:25Z. Its CPU first
batch has run only on the tiny model (`first_batch/run_first_batch.py`, `tests/first_step.py`). The orchestrator wants
the S1 path (own-head readout -> faithful row -> forward/backward) exercised with the REAL step-544 9B weights on every
rank before launch. D0's row databases are not on Trinity, so the diagnostic uses fixture rows with real frames and the
real processor. It proves the code path (loading, readout, faithful re-render, tokenisation, finite loss and gradients,
memory, time per microstep); it measures no accuracy.

## Deliver
1. `K/first_batch/real_fixture_batch.py` and wrapper `K/first_batch/real_fixture_batch.sh`. CLI:
   `--config` (default K/configs/h1_1.json), `--model-manifest` (p3-model-input-v1 model.json), `--receipt` (the lineage
   training receipt; used only for processor and model loading, as `real_first_batch.py` does), `--artifact` (step-544
   artifact.json; check its sha256 equals `cfg['init_artifact']['artifact']['sha256']`, 1d6eeb28...), `--frames` (a clip
   manifest of 32 real frames, the same schema as the fixtures' `K/tmp/manifests/*.json` clip manifest, or a builder
   option that binds one dev-S1 item's frames through b04's parity kit: read
   `/scratch/jjyeung/orch_n30/b04_e2ehook/parity_kit/{README.md,common.py,stage_restore.py}` and
   `/scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/parity.py` and reuse their binding; prefer whichever needs fewer
   new assumptions), `--frames-root`, `--ranks` (default 0,1,2,3), `--routing-per-rank` (default 2), `--force-pose-own`,
   `--threads`, `--output DIR`.
2. Rows: the 12 camera fixture rows `K/rows/camera_fixtures.jsonl` (+ the two a0 ground rows that `tests/first_step.py`
   adds, if the native path handles them) packed with the native packer (`routing.c1_row`) against the real clip, and
   batched through the SAME native batch builder the trainer uses for routing rows (`student_pilot/carrier_c1_run.py`
   `Rows.get` and what it calls), with the real processor. Do not use `tests/fixtures.routing_batch` (synthetic base).
   Also run one pose-stream microstep per rank if a native pose row can be built from a fixture row's GT pose; if not,
   record why and skip it.
3. Plan: the step-2 plan exactly as `first_batch/real_first_batch.py` builds it (mixed_indices, seed 17, world 4,
   `training_mode='final'`, cfg mix), map routing indices onto the fixture rows modulo their count, and take each rank's
   first `--routing-per-rank` routing microsteps. Decision `gates.decide(2, micro//factor)`; with `--force-pose-own`
   the pose decision is True. Call `R.own_values(model, rows, batch, audit, index, decision, cpu)` exactly as the trainer
   does, then `model.zero_grad(set_to_none=True)`, forward, check finite loss, backward, check every non-None gradient
   is finite. No optimizer state, no weight update.
4. Output: `DIR/real_fixture_batch.jsonl` (one record per microstep: rank, microstep, stream, decision, h1 audit
   values/refused/answer_differs/type, loss, components, trained tokens, seconds for readout / forward / backward,
   peak RSS) and `DIR/SUMMARY.json` (per rank own / gt / refused counts, refusal histogram, any non-finite, total
   seconds, pass flag). Pass = every rank has at least one own camera row under `--force-pose-own`, every loss and
   gradient finite. Exit non-zero on fail. Output must be under `--output`; refuse reads under /home, /data*, /lustre
   with an audit hook as `real_first_batch.py` does (code imports from the tree and K are allowed).
5. The wrapper takes the Python interpreter and an optional PYTHONPATH overlay as environment variables
   (`PY`, `PY_OVERLAY`), sets `CUDA_VISIBLE_DEVICES=`, offline HF flags, thread counts, TMPDIR under the output dir, and
   imposes NO 32 GiB address-space cap (the 9B load needs ~60-120 GB; the run host has 1 TB). It must not hard-code
   `/scratch/jjyeung/orch_n30/h1_headsft/kit`: derive K from its own path (the kit is extracted elsewhere on the run host).
6. Tiny proof here: a test `K/tests/test_build6.py` that runs the same script logic end to end on the tiny model through
   an injectable loader (tests/fixtures.tiny and its processor) with synthetic frames, both with and without
   `--force-pose-own`, and checks the records and pass flag. Also check that the real loading path (model manifest,
   receipt, artifact pin) is exercised up to file opening with the real JSON files in
   `/dev/shm/jjyeung/h1tmp/from118/` (copies of the run host's model.json, receipt.json, artifact.json, RESTORE.json;
   the weights are not on this node, so stop with a clear missing-file error and assert that error).
7. Rerun `tests/test_build4.py tests/test_review.py tests/test_reader_build4.py` and the nine Build-4 OLD files with
   basetemp under K/tmp/b6: all must still pass (Build 5: 91 passed). Write "Build 6" in BUILD_REPORT.md: files,
   commands, results, size, the exact command to run on the real host (variables for model.json, receipt.json,
   artifact.json, frames), and the expected time per microstep you estimate (state it as a guess).
