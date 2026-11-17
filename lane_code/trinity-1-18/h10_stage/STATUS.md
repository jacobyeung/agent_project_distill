# h10_stage STATUS (Devin lane on trinity-1-18; lane folder /scratch/jjyeung/orch_n30/h10_stage). Successor: read this, then newest *_ORCH_* in events/h10_stage and inbox/.
Updated 20261117T0140Z.

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

## Plan / next
1. A1 G3T tar built on Orchard from HF blobs (no Trinity). 2. A2 tar built on 1-18 (frames + SAM ckpt/source/receipt + selector + model tar + processor assets + overlay + receipts + vnice), one governed push (priority 10). 3. code tar (5.4 MB) unregistered. 4. env import proof on login (nice 19). 5. a/1.json, 3.py check, test-only, submit.
