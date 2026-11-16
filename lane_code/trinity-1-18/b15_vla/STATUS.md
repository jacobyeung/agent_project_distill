# b15_vla STATUS (Devin lane on trinity-1-18, started 12:26Z; brief .../orch_n30/briefs/b15_vla.md -> queue brief .../briefs/qs/15_vla_kit_recover.md)
Updated: 2026-11-16 14:28Z. Lane folder /scratch/jjyeung/orch_n30/b15_vla (trinity-1-18). Events .../orch_n30/events/b15_vla/.

## Goal
Recover the VLA kits (LIBERO Test L kit; navrun for R2R-CE), re-run their CPU proofs, bind B1 (U1 blocked) to the step-544 export, write out/VLA_KITS_STATUS.md, mirror, RESULT event. CPU only, no GPU, no Git, no deletion, no Orchard job without ORCH GO. Brief and ORCH ANSWER 1328Z orders 1-3 DONE (100%). Lane exits.

## Done
1. Inventory (Claude lane): Orchard /project/community/jjyeung/vla_libero survives, kit KIT_SHA256 af43148989f7837e...; navrun has no copy anywhere. Lists in work/ORCHARD_LIST.txt, work/LIST_*.txt.
2. LIBERO CPU proofs re-run on orchard-login-001 12:31-12:57Z (ORCH ANSWER 1224Z): driver out/rerun_20261116/rerun_driver.sh (sha 39f111f7...) with shadow V (symlinks; outputs only under out/rerun_20261116/). Kit sha256sum -c: 0 failed. Results (pulled to work/rerun/pulled/, archive work/rerun/rerun_pull.tgz sha 188b09f9...): HOOK_OK, HOOK_RESUME_EXACT (step-3/4 losses and batch fps equal 11-11's), REPEAT_EXACT, ROTATE_TEST_OK (all 10 checks), T-4 PASS 19/20 fx<0 hand-eye t (0.050, 0.000, -0.097) residual 6e-8 m, T-5 PASS, T-6 PASS corr 0.932/0.970/0.962, closed loop random 0/10 and demo replay 10/10, parity: state wait10 max 0.0, orientation matches eval flip, 40/40 prompts match. Identical to the 11-11 record.
3. Tiny-model B1 first batch = cpu_hook's arm_testL run (full forward + backward on CPU, finite losses, step-0 head parity). Real-config (Qwen3.5-9B) batch NOT run: ORCH hold (Q2).
4. B1 bound to step 544: header check (work/rerun/b1_header_check.py; Orchard out/rerun_20261116/B1_BIND_544_HEADER_CHECK.json) of okh7/i_bb09a77d/m.tar (archive sha 3ed73aea..., artifact 1d6eeb28f516... verified): 760 tensors, names and shapes equal to base Qwen3.5-9B c2022362 (426 LM, 333 ViT, 1 lm_head), 48 F32->BF16 dtype diffs (as for m200), heads.pt (2.76 GB) excluded. Wrapper kit_bind/train_b1_544.sh (sha 647fc50c...) extracts full_weights + artifact into job /tmp, checks artifact sha, refuses heads.pt and non-B1 arms, then runs the sealed train_arm.sh with B1_SRC=dir:...; logic tested with a fake tar (pass, bad-sha refuse, U1 refuse). Needed because the archive keeps artifact.json under ap/93ccadab/m544/, not under the full_weights prefix that stage.sh tarparts: reads.
5. navrun inputs on 1-18: env /scratch/jjyeung/envs/nav_habitat024; R2R-CE + R2RIE-CE json in navrun_inputs/refs (sha work/IB_330.txt); scenes navrun_inputs/scenes/mp3d: glb+navmesh of 72 non-test scenes (4.8 GB) streamed over IB from 0-13 /scratch/jjyeung/mp3d/v1/tasks/mp3d_habitat.zip (sha256 470948ee... equals its .sha256), CRC-checked.

6. navrun rebuilt (Codex Astra high, 2 rounds, receipts .../codex_runs/20261116T124353Z_b15_navrun/ and 20261116T131256Z_b15_navrun_fix1/): navrun/BUILD_REPORT.md; src navrun/out/navrun_src.tgz sha256 496836be8e375da80b807a87a26d1e9899540ede18f42cdb9243061514d51328; 118 unittest pass (I re-ran: OK); oracle SR 1.000 SPL 0.9988 (1,839); blind priors near record; replay 10,819/10,819 vs official VLN-CE GT (navrun_inputs/refs/r2r_vlnce_preprocessed, from 0-13 zip sha 3171f5be...); oracle-click GT-lead 0.887 / geodesic 0.665 vs record 0.802.
7. out/VLA_KITS_STATUS.md written; design record DD/VLA_KITS_RECOVERY_20261116.md + INDEX line.
8. Mirror: trinity-1-13 /scratch/jjyeung/n30_mirror/b15_vla/b15_vla_mirror.tar sha256 3cdfbbc9a285705f8f980bbb0c0cbeffae0a3f555e10359cb0323852b3fb6253 (equal to local work/b15_vla_mirror.tar; holds STATUS, out, kit_bind, navrun, work/rerun, work/codex, refs; scenes 4.8 GB and env not mirrored; scenes re-derivable from 0-13 mp3d_habitat.zip, env on 3-30 and 0-13).

9. ORCH 1328Z order 1 (naming): Orchard root moved /project/community/jjyeung/vla_libero -> /project/community/jjyeung/45e92888780e (work dir 45e92888780e_w holds survey lists and pre_sed_backup.tar of the 246 rewritten files); 66 symlinks re-pointed; SBATCH output $ROOT/logs/j_%j.out; job names a15_cot_ap<hex>; project name out of kit comments; NEW KIT_SHA256 e6bccd3deea4d7ab1c342061a3f3130e3d24eb83f622f2159ab2aa829a5fb775 (198 files; sha256sum -c SEAL_OK); old seal in out/reseal_20261116/. Scripts work/reloc/{survey,apply}.sh, logs work/reloc/{SURVEY2,APPLY}.txt. B1 wrapper updated to the new root (sha cf047044...).
10. Order 2 (controller stall): Codex round 3 (receipt .../codex_runs/20261116T134204Z_b15_navrun_fix2/): navrun controller_v2 default for NU/oracle-click, 132 tests (102-episode stall replay fixture), stationary tails 118->0; logged deltas in BUILD_REPORT.md; navrun_src.tgz 4e85320b37314837c09eb77ac4049a57430e59cd795bfed28713ec05dc95c607.
11. Order 3 (rand100): Open-Nav OpenNav_R2R-CE_100 (Drive id 1SfrPWqCIiivwduCYPMe-Za1wOt4eU6G9, 1.85 MB, sha f4770f1b..., single file <20 MB, curl 8 MB/s) in navrun_inputs/rand100; 100/100 match val-unseen; oracle 1.00, blind 0.02/0.05/0.06.

12. Re-proof from the new root (13:59-14:22Z, out/rerun_20261116b, pulled work/rerun/pulled_b, archive sha e1141882...): all proofs pass; hook traces byte-equal to the pre-move run; cl_check rows differ only in seconds/video path. Wrapper copied to Orchard $ROOT/bind/train_b1_544.sh (sha cf047044...).
13. out/VLA_KITS_STATUS.md, DD/VLA_KITS_RECOVERY_20261116.md and its INDEX line updated; mirror trinity-1-13 /scratch/jjyeung/n30_mirror/b15_vla/b15_vla_mirror2.tar sha256 b7e54a251070c77c20c0f4fb08d69a32dce1412e2217d5c695a6e8f32d1accf3 (b15_vla_mirror.tar there is the earlier snapshot).

## In flight
Nothing: no tmux sessions of this lane's work, no streams, no Orchard processes or jobs.

## Next steps (only on ORCH order)
1. Real-config B1 first batch (held).
2. GPU work: Test L shake-down via bind/train_b1_544.sh; navrun GPU job (render, occlusion-tested oracle-click, rand100 harness check).
3. U1 after briefs 04/05.

## Findings to report
- Orchard login-node /tmp (6.3 GB tmpfs) is 100% full with this account's files from other lanes (/tmp/b01h_m50.tar, b01h2_m50.tar, b8.*.tar, jjy_fw.*): report to ORCH; not this lane's to remove.
- Residual framework/dataset words in arguments and log text (StarVLA keys, Qwen3.5 dir substring, LIBERO suite/package names): listed in out/VLA_KITS_STATUS.md section 3.

## Open questions
- Q2 (answered: hold real-config batch). rand100 (MIP OpenNav-100) ids not recovered: DEFAULT mark BLOCKED, report oracle on full 1,839 and val_unseen_600.

## Read first
Queue brief, records DD/VLA_LIBERO_KIT_20261111.md, VLA_NAV_RUNNER_20261111.md, this file.
