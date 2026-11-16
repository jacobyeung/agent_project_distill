# C1 pose sweep: independent training review (Claude Opus, 2026-11-08 11:20Z)

**VERDICT: GO-AFTER-FIXES.**
- **Spread layout on trainer `1db21600` + kit `93197ab8` (trainer tar sha256 `c41e5a35…`, as smoked by 104301-104303): GO as is.** I found no blocking defect on this path.
- **Duplicate or paired layout on B42 `897665b8` (and B43, which builds on it): fix BLOCKING-1 before any submit.**
- **B43 is unreviewed.** Its working tree was still changing at 11:18Z; check its final delta against §4 before you submit it.

Scope: I read `work/repo_c1` (carrier_c1*.py, full_ft, fsdp_training, camera_head, decoupled_v/_resume, p3_provenance), the B42 diff (`h5/b42/repo` against 1db21600), and kit `aws_c1/kit/b` (w.py, i.py, r.sh, c.sh tk_env, b3301004/5.sh) with the three arm configs. I also read the AWS smoke reports `o/10430{1,2,3}.4.json` (one read-only ssh call) and the AWS storage (user quota 250 TB, 54 TB used; filesystem 57 TB free).

## 1. BLOCKING

**BLOCKING-1 (only for duplicate/paired): C1-b stops being "CAMs after the video".**
- Cause: `h5/b42/repo/student_pilot/carrier_c1_data.py:110` sets `append_all = carrier_placement == C1_B and frame_layout == 'spread'`. Lines 138 and 152 therefore insert B's 32 CAMs after each viewpoint's own patch, the same positions as C1-a. The docs state this choice explicitly (`docs/carrier_c1_memory_layout.md:41-42`, "non-spread layouts place CAMs locally").
- Effect: under duplicate or paired, C1-b becomes C1-a plus frame embeddings plus grid RoPE. The arm no longer tests its question, and a-vs-b measures only those two extras.
- Fix: set `append_all = carrier_placement == C1_B`, independent of layout. Lines 138/152 then give 32 contiguous CAMs after the last patch. `refs` (one per group, shift 0) already anchors CAM k to viewpoint k's patch through `frame_position_ids`. Update the doc table, and change `tests/test_carrier_c1_layout.py:97-114`, which currently asserts local CAMs for every arm including B. For C1_B it should expect positions == range(last_patch_end+1, +32) and rope sources == each group's first visual token.
- Re-prep for the new layout is already required, so this costs nothing extra.

## 2. Non-blocking (top 5)

1. **Restarting after an early crash fails.**
   - Cause: a fresh start writes `binding.json` with exclusive create (`carrier_c1_run.py:542` → `p3_provenance.py:49`).
   - Effect: a crash before the first resume state (step 100 in 1db21600; ~30 min in B43) leaves an output dir that a fresh restart refuses with FileExistsError. Then the 1101Z plan "fix it and resubmit at once" needs a new `output` (a new identity, so a re-prep) or a removal.
   - Fix (B43): accept an existing `binding.json` equal to `bound` when no complete state exists. B43's `existing_export` (line 576) also fails closed on an export interrupted mid-write, so a crash during an m-export blocks resume past that milestone; that is acceptable but worth knowing.
2. **Lever A is on by default for pose_only and has never run on GPU** (B42 `carrier_c1.py:90`, `259-261`).
   - Change: the lm_head FSDP unit is never called, its grad stays None, and AdamW skips its weight decay (negligible).
   - Risk: it was tested only on CPU (gloo skipped), so step 1 of the 800-step runs is its first FSDP test. A failure there would be loud, but turning the lever off afterwards changes the identity (another re-prep).
   - It is not needed: spread peaks at 33.2 GiB of 80. To keep the smoke-proven path, set `skip_unsupervised_lm: false` in the B43 configs during the re-prep that B43 already forces.
3. **The schedule spends about half of each 4-h allocation idle.**
   - Cause: the configs (`k/a14f07c2.json` etc.) plan `p95_step_seconds 60` and `startup_seconds 1800`. With these, `capped_steps` (`carrier_c1_sweep.py:10-38`) ends each leg at ~170-185 steps, which is ~1.7 h at the measured 32-35 s/step.
   - Effect: 800 steps take 6 legs (0→185→355→400 gate→585→765→800), and each leg adds a queue wait.
