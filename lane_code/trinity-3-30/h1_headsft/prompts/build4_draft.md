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
REVIEW_FIXES

## Read plan of the H1-0 launcher (`K/h1eval/h10/`)
1. Each perturbation mode runs only on its own type: `scale_translation` on camera_displacement,
   `rotate_translation` on camera_movement_direction, `negate_turn` on camera_rotation, `scale_scene` on
   object_abs_distance. The own arm decodes every item once unperturbed (baseline) and each routed item once more
   under its type's mode. The tower arm decodes every item once, unperturbed, never per mode, and
   `--tower-from <dir>` reuses tower records of b04's parity read (same export, items and reader hashes; refuse on
   any mismatch) instead of decoding them again.
2. Print the read count before starting and in `RUN_H10.md`: dev-S1 routed 636 + 600 own decodes (+636 tower unless
   reused); ReVSI official999 999 + 283 own decodes. Expected card-hours = reads x measured seconds per read; the
   launcher measures seconds per read on its first 10 items and writes the projection to its log.
3. Tests: mode-to-type mapping, read counts for both sets, tower reuse refusal on a hash mismatch, resume.

## Finish
Append a "Build 4" section to `K/BUILD_REPORT.md` (every test command with pass/fail counts, size added, what is
unverified) and update `K/SHA256SUMS`.
