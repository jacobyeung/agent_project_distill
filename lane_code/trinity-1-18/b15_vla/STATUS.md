# b15_vla STATUS (lane on trinity-1-18; brief .../orch_n30/briefs/b15_vla.md -> queue brief .../briefs/qs/15_vla_kit_recover.md)
Updated: 2026-11-16 12:00Z. Lane folder /scratch/jjyeung/orch_n30/b15_vla (trinity-1-18). Events .../orch_n30/events/b15_vla/.

## Goal
Recover the VLA kits (LIBERO Test L kit; navrun for R2R-CE), re-run their CPU proofs, bind B1 (and U1, blocked) to the step-544 export, write out/VLA_KITS_STATUS.md, mirror, RESULT event. CPU only, no GPU, no Git, no deletion, no Orchard job without ORCH GO.

## Done (step 1: inventory) — about 15% of the brief
- Orchard /project/community/jjyeung/vla_libero SURVIVES. kit/KIT_SHA256 = af43148989f7837ef8e137453096f6a67fb366242a6f16fa454544ac55303897 (= sha256 of kit/SHA256SUMS); `sha256sum -c SHA256SUMS` on Orchard: all 199 lines OK (one stale __pycache__ pyc aside, excluded locally). Sizes: envs e_sv 7.0G, e_lb 2.2G, e_tool 201M; data/lerobot 1.8G (4 suites), data/hdf5 1.2G; work/tiny_Qwen3.5 114M; src 573M (starVLA 985c2238 + pilot overlay, LIBERO, LIBERO-plus); osmesa 367M; cache 5.4G; dl 2.6G. Listing: work/ORCHARD_LIST.txt, work/ORCHARD_KIT_SZ.txt.
- Local copy of kit code + proof logs (436 KB): work/orchard_kit/ (pull.tgz). 11-11 proofs ran on the Orchard LOGIN node (no srun), logs: out/cpu_hook/log.txt (HOOK_OK, HOOK_RESUME_EXACT), out/cpu_rotate/log.txt (ROTATE_TEST_OK), out/conformance/T4-T6.
- navrun: NO surviving copy (record VLA_NAV_RUNNER_20261111 says only 2-18). trinity-3-30 orch_cd/nav_build is the 11-06 student repo, not navrun (work/LIST_3_30*.txt). Rebuild inputs found: env /scratch/jjyeung/envs/nav_habitat024 (habitat-sim 0.2.4, py3.9; on 3-30 and 0-13); R2R-CE v1-3 train/val_seen/val_unseen/test + R2RIE-CE 1_3_v1 json at 3-30 /scratch/jjyeung/orch_cd/nav_survey/refs (13.6 MB); MP3D zip 0-13 /scratch/jjyeung/orch_cd/mp3d_dl/dl/tailprobe.zip (16,085,306,031 B, unverified); 3 extracted val-unseen scenes 0-13 /scratch/jjyeung/mp3d/e0_scenes/mp3d (8194nk5LbLH, pLe4wQe7qrG, zsNo4HB9uLZ); 0-13 /scratch/jjyeung/mp3d/datasets/R2R_VLNCE_v1-3_preprocessed.zip. (work/LIST_0_13*.txt)
- vla_heads and vla_where sources survive inside the Orchard kit (kit/ext_v2/vla_heads, kit/ext_where/vla_where); navrun's nav codec / ClickTranslator come from them.

## In flight
Nothing running. No tmux, no streams, no Orchard jobs.

## Open questions (event 20261116T1157Z_QUESTION_orchard_cpu_proofs.md)
Q1 rerun LIBERO CPU proofs on Orchard login node as 11-11 did — DEFAULT yes (nice 19, OMP 4, outputs vla_libero/out/rerun_20261116/).
Q2 real step-544-config B1 first batch — DEFAULT hold (needs ORCH GO for an Orchard general CPU job, or a governed stream); tiny-model B1 batch only.

## Next steps
1. Re-run LIBERO CPU proofs on Orchard (kit scripts cpu_hook.sh, cpu_rotate.sh, repeat_check.sh, parity_check.py, conformance.sh, cl_check.sh random+replay 10 eps) into out/rerun_20261116; run detached (nohup setsid) and poll via ossh.sh every 5-10 min.
2. navrun rebuild on trinity-1-18 under /scratch/jjyeung/orch_n30/b15_vla/navrun: copy env + R2R json over IB from 3-30; extract val-unseen (and train) scene glb+navmesh from the 0-13 zip by an IB stream; rebuild package from record VLA_NAV_RUNNER_20261111.md (episode loop, metrics, 5 formats, lists, row builder), 58 tests, oracle on rand100.
3. Bind B1/U1 (U1 BLOCKED on briefs 04/05), write out/VLA_KITS_STATUS.md, mirror to second node, RESULT.
## Read first
Queue brief, records DD/VLA_LIBERO_KIT_20261111.md, VLA_NAV_RUNNER_20261111.md, VLA_ACTION_HEAD_DESIGN_20261111.md §4-5, this file.
