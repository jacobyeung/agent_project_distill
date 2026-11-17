# h10_stage STATUS (Devin lane on trinity-1-18; lane folder /scratch/jjyeung/orch_n30/h10_stage). Successor: read this, then newest *_ORCH_* in events/h10_stage and inbox/.
Updated 20261117T0313Z.

## Goal
Stage H1-0 (package b01ec87a6f29b, kit trinity-3-30 /scratch/jjyeung/orch_n30/h1_headsft/kit/orchard_h10; local copy work/kit) on Orchard, fill a/1.json, login 3.py check, SUBMIT.cmd --test-only, submit ONE general job (<=5 GPU-h), babysit, report M1/M2/M3.

## Findings (evidence in work/o/p*.out)
- Orchard work dir: /project/community/jjyeung/okh7/e6fc152498 (0700). Login /tmp tmpfs is 100% full: never use it.
- Export: Orchard /project/community/jjyeung/okh7/i_bb09a77d/m.tar 21,583,032,320 B; M544_SOURCE.json records archive_sha256 3ed73aea (= kit pin). Members m544/... match stage_restore layout. Rehash running (W/h.sh -> W/m.sha).
- G3T on Orchard HF cache: blobs d460957b... -> hub/blobs/59/594204ac.. 5,627,166,200 B (rehash -> W/g.sha); config blob fab524bc 149 B sha 5aeb2acd...d7d7 (verified).
- Template runtimes (W/g0,g1,g2.list): g1 = m/ap/19252904/e venv: torch 2.13.0, torchvision 0.28.0, transformers 5.19.0, numpy 2.3.5, triton 3.7.1; no scipy, no SAM deps. g0 = uv-python 3.12.13 + sj/envs/p1cpu (CPU torch 2.11, transformers 5.12.1, scipy 1.14.1). g2 = code only.
- Python plan: inputs.python = d/v/py (sh wrapper) -> g1 python -I -B d/v/boot.py; boot adds d/v/site (scipy 1.14.1 from 1-18 orch_cd/evalx/work/trin_vl/pyextra + iopath/portalocker/ftfy/timm/pycocotools/wcwidth from envs/sam3_capretry_native_v1) via site.addsitedir; env_roots=[d/v/site].
- SAM 3 on 1-18: ckpt /scratch/jjyeung/orch_cd/ttower/work/sam3_weights/sam3.pt 3,450,062,241 B sha 9999e234 (verified); source /scratch/jjyeung/orch_cd/evalx/work/trin_vl/sam3src (6 receipt files match); receipt b05_owngrd/code/owngrd/vendor/SAM3_RECEIPT.json sha 979e2f77 (1123 B).
- b04 small inputs copied to work/b04/ (selector json 63aa0a69, safetensors 6d97c524, model tar 8005668f, base_small.tgz daa1bb17 7,037,953 B).
- Frames: /scratch/jjyeung/devs1_frames (xx/<sha>.png, 6624 files, 1.7 GB) = FRAMES.json path layout.
- vnice.sh sha 3ab2b542 matches (k1/tools, /data3/shared/scripts/vnice). Terminator: template pins cbb91ba7; every terminator.sh found (Trinity) is 19727987/86e97b7e/f81f89f7. OPEN.
- Main queue (01:09Z): main has 8 advanced jobs PENDING, none on general.

## Staged on Orchard (W=/project/community/jjyeung/okh7/e6fc152498; all sha-verified on Orchard)
- archive 0 export: W/e/0..3 (GCS generation-pinned parts, 4x5,395,758,080 B, part shas = TRANSPORT.json; whole 3ed73aea). NOTE i_bb09a77d/m.tar is NOT the pin (sha 42457dbd, repacked members).
- archive 1 G3T: W/g/0 6a53059f 5,627,176,960 B (g/model.safetensors d460957b, g/config.json 5aeb2acd), built on Orchard from HF cache.
- archive 2: W/a2.tar 1de93f61 5,257,369,600 B (f/ frames 6624 verified, k/sam3.pt, k/SAM3_RECEIPT.json, s/ SAM source, h/ selector, o/ model tar, b/ processor assets). Governed push h10_stage_a2 done 02:02Z.
- archive 3: W/a4.tar c867d40a 145,274,880 B (v/py wrapper, v/boot.py, v/site overlay). Governed push h10_stage_a4 done.
- archive 4: W/a3.tar 05dc8f79 10,240 B (q/env.json e46a9a59, q/policy.json a95a881c, q/vnice.sh 3ab2b542, q/terminator.sh 19727987).
- a/1.json sha 7757209963ac (local copy work/stage/1.json). Env proof (work/proof/run.out): torch 2.13.0+cu130, torchvision 0.28.0+cu130, transformers 5.19.0, scipy 1.14.1; SAM deps, sam3, reader code import OK; fla absent (as in b04's Trinity parity).
- Package /project/community/jjyeung/b01ec87a6f29b: terminator repin (ORCH 0154Z, Codex receipt agent/scratch/codex_runs/20261117T021027Z_h10_terminator, k330/REPORT_terminator.md): 0.tgz ecfad90f, plan 5ef2094e, PACKAGE.json ba178d46. Old files in W/pkg_old.
- Login check with new package: passed (1 GPU, 05:00:00). test-only FAILED: operator submit() PATH=/usr/bin:/bin, sbatch is /usr/local/bin -> Codex fix running (tmux h10_codex2, brief k330/BRIEF_sbatch_path.md).
- CPU rehearsal of job action 0 (prepare) running on login: W/rh_setup.sh -> W/rh.done, W/rh.out.

## Job history
- Orchard 170620 (a15_cot_apb01ec87a6f29b, general, 1 GPU x 05:00:00), package 0.tgz 2dd91b3b / plan 8b89141f: RUNNING 02:35:23Z on orchard-community-4, FAILED 02:41:06Z (5m43s): every input hash passed in-job, then bwrap "Can't find source path <root>/fsw" at action 0. Return: pool okh7/ae71c903/b01ec87a6f29b00029a7c (+GCS q8/ae71c903/...), extracted at W/ret1. BLOCKER 0242Z sent. NEVER resubmit without the user's yes (OPERATIONS.md: failed allocation needs the user's answer).
- h1read assets for cont_ops STAGED: /project/community/jjyeung/okh7/af83c921/{d81f4a26.tar 2ad8c67c 797,685,760 B, e52a690b.jsonl 1d8b29a7 5,728,183 B}, dir 0700, files 0600, sha verified on Orchard (governed push h10_stage_h1read done).
- Mirror: trinity-0-13:/scratch/jjyeung/n30_mirror/h10_stage/mirror_h10_0245Z.tar sha 21d06478 (kit orchard_h10 + reports + 1.json + small stage files).

- Orchard 170631 (same job, package 0.tgz e82ac329 / plan 1de19b86 / PACKAGE.json 27b287a9, fsw fix per ORCH 0242Z): RUNNING since ~03:01:35Z on orchard-community-1; worker type 0 started 03:07:35Z; ~7 s/read; RESULT first_reads sent. Return token b01ec87a6f29b00029a87 -> pool okh7/ae71c903/b01ec87a6f29b00029a87 (+GCS). End of allocation ~08:01:35Z; returns by ~07:41Z.
- Faithful rehearsal root W/r2 (from empty) passed action 0. Lesson in H1 record; OPERATIONS.md (k330 copy) rule updated.

## Next
1. Babysit 170631 every 10 min: work/o/m.sh (squeue, sstat, pool dir) + work/o/prog.sh (srun --overlap 1 CPU/1 GB: per-type items.jsonl line counts, STEPS tail). 1-min on regression. NEVER resubmit 170631; a cluster kill waits for the user.
2. On return: 3.py fetch on Orchard into W/fetch_<token>, pull 0.tgz (<=90 MB) to 1-18 (governed if >20 MB), merge with h1eval.h10.merge --type-layout (k330 kit, p1cpu), compute M1/M2/M3 per type, RESULT complete; clean partial -> resume plan (pin return in a/1.json resume, same 1 GPU).
3. Mirror final kit + results.
