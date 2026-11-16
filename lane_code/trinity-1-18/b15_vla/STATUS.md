# b15_vla STATUS (Devin lane on trinity-1-18, started 12:26Z; brief .../orch_n30/briefs/b15_vla.md -> queue brief .../briefs/qs/15_vla_kit_recover.md)
Updated: 2026-11-16 13:15Z. Lane folder /scratch/jjyeung/orch_n30/b15_vla (trinity-1-18). Events .../orch_n30/events/b15_vla/.

## Goal
Recover the VLA kits (LIBERO Test L kit; navrun for R2R-CE), re-run their CPU proofs, bind B1 (U1 blocked) to the step-544 export, write out/VLA_KITS_STATUS.md, mirror, RESULT event. CPU only, no GPU, no Git, no deletion, no Orchard job without ORCH GO. About 55% done.

## Done
1. Inventory (Claude lane): Orchard /project/community/jjyeung/vla_libero survives, kit KIT_SHA256 af43148989f7837e...; navrun has no copy anywhere. Lists in work/ORCHARD_LIST.txt, work/LIST_*.txt.
2. LIBERO CPU proofs re-run on orchard-login-001 12:31-12:57Z (ORCH ANSWER 1224Z): driver out/rerun_20261116/rerun_driver.sh (sha 39f111f7...) with shadow V (symlinks; outputs only under out/rerun_20261116/). Kit sha256sum -c: 0 failed. Results (pulled to work/rerun/pulled/, archive work/rerun/rerun_pull.tgz sha 188b09f9...): HOOK_OK, HOOK_RESUME_EXACT (step-3/4 losses and batch fps equal 11-11's), REPEAT_EXACT, ROTATE_TEST_OK (all 10 checks), T-4 PASS 19/20 fx<0 hand-eye t (0.050, 0.000, -0.097) residual 6e-8 m, T-5 PASS, T-6 PASS corr 0.932/0.970/0.962, closed loop random 0/10 and demo replay 10/10, parity: state wait10 max 0.0, orientation matches eval flip, 40/40 prompts match. Identical to the 11-11 record.
3. Tiny-model B1 first batch = cpu_hook's arm_testL run (full forward + backward on CPU, finite losses, step-0 head parity). Real-config (Qwen3.5-9B) batch NOT run: ORCH hold (Q2).
4. B1 bound to step 544: header check (work/rerun/b1_header_check.py; Orchard out/rerun_20261116/B1_BIND_544_HEADER_CHECK.json) of okh7/i_bb09a77d/m.tar (archive sha 3ed73aea..., artifact 1d6eeb28f516... verified): 760 tensors, names and shapes equal to base Qwen3.5-9B c2022362 (426 LM, 333 ViT, 1 lm_head), 48 F32->BF16 dtype diffs (as for m200), heads.pt (2.76 GB) excluded. Wrapper kit_bind/train_b1_544.sh (sha 647fc50c...) extracts full_weights + artifact into job /tmp, checks artifact sha, refuses heads.pt and non-B1 arms, then runs the sealed train_arm.sh with B1_SRC=dir:...; logic tested with a fake tar (pass, bad-sha refuse, U1 refuse). Needed because the archive keeps artifact.json under ap/93ccadab/m544/, not under the full_weights prefix that stage.sh tarparts: reads.
5. navrun inputs on 1-18: env /scratch/jjyeung/envs/nav_habitat024; R2R-CE + R2RIE-CE json in navrun_inputs/refs (sha work/IB_330.txt); scenes navrun_inputs/scenes/mp3d: glb+navmesh of 72 non-test scenes (4.8 GB) streamed over IB from 0-13 /scratch/jjyeung/mp3d/v1/tasks/mp3d_habitat.zip (sha256 470948ee... equals its .sha256), CRC-checked.

## In flight
- navrun build round 1 DONE (Codex 12:43-13:05Z, receipt .../codex_runs/20261116T124353Z_b15_navrun/): navrun/BUILD_REPORT.md; 105 unittest pass (I re-ran: OK, 1.5 s); oracle SR 1.000 SPL 0.9988 on 1,839; blind priors near record; oracle-click 0.665 vs record 0.802; src tgz c87cd202... (superseded by round 2).
- navrun round 2 (Codex Astra high, tmux b15_codex_navrun2, receipt .../codex_runs/20261116T131256Z_b15_navrun_fix1/, brief work/codex/navrun_fix1_brief.md, EXIT line in work/codex/dispatch_navrun_fix1.out): wire official VLN-CE GT (navrun_inputs/refs/r2r_vlnce_preprocessed/, from 0-13 /scratch/jjyeung/mp3d/datasets/R2R_VLNCE_v1-3_preprocessed.zip sha 3171f5be..., copied over IB) for tracks/rows/replay and dense nDTW; diagnose oracle-click gap and add a GT-locations lead-point variant. Do not re-dispatch while it runs.

## Findings to report
- Orchard naming: the kit dir, the SBATCH --output path and job logs sit under /project/community/jjyeung/vla_libero, which carries "vla" and "libero"; the Orchard rule forbids project/dataset words. Before any GPU launch, relocate or alias under an opaque path (ORCH decision).

## Open questions
- Q2 (answered: hold real-config batch). rand100 (MIP OpenNav-100) ids not recovered: DEFAULT mark BLOCKED, report oracle on full 1,839 and val_unseen_600.

## Next steps
1. When Codex finishes: read navrun/BUILD_REPORT.md, run the unittest suite and spot-check the oracle and blind-prior numbers myself (nav env, OMP 8, nice 19).
2. Write out/VLA_KITS_STATUS.md (survived/rebuilt/tests/hashes, costs from the brief, U1 BLOCKED on briefs 04/05, naming finding) and a design record + INDEX line under distill_design.
3. Mirror: tar kit_bind + work/rerun/pulled + navrun (src, out lists/tables) to trinity-1-13 /scratch/jjyeung/n30_mirror/b15_vla/ over IB, compare sha256 (scenes 4.8 GB stay out unless asked).
4. RESULT event; ask for a review only if a GPU run is proposed.
## Read first
Queue brief, records DD/VLA_LIBERO_KIT_20261111.md, VLA_NAV_RUNNER_20261111.md, this file.
