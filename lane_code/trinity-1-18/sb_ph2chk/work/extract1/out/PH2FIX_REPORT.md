# PH2FIX report
CPU-VERIFIED LAUNCH-READY. No GPU inference, network, SSH, Git, process termination or external writes ran.
Tests: part 1 26/26; part 2 20/20; launcher 23/23; CPU dry-run steps 1–4 PASS.
Test command: `env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 nice -n 10 python -B verify_cpu.py`; CPU_VALIDATION.json records child commands and evidence hashes.
placement and one 48 GB card off trinity-0-13: sb_mask_phrase/part2/launch_gpu.py:54; PASS — small-card, placement and identity tests.
two empty nvidia-smi readings 300 seconds apart: sb_mask_phrase/part2/launch_gpu.py:144; PASS — fake nvidia-smi: busy first/second, graphics process, 1024 MiB boundary; wait argument 300.
vnice: sb_mask_phrase/part2/launch_gpu.py:161; PASS — command vector and tampered-vendor tests; local vnice and monitor pinned.
timeout at remaining budget: sb_mask_phrase/part2/launch_gpu.py:152; PASS — fake pass: 4320 s then 4308 s; clean resume subtracts 12 s.
1.2 GPU-hour hard stop: sb_mask_phrase/part2/watchdog.py:9; PASS — stalled-call and remaining-budget tests; outer SIGKILL timeout bounds native stalls without a grace period.
KILLED never rerun: sb_mask_phrase/part2/launch_gpu.py:35; PASS — RUNNING, STOP, KILLED, unmarked partial and nonzero-exit tests; clean-end receipt precedes marker rename.
writes only under GPU output directory: sb_mask_phrase/part2/launch_gpu.py:85; PASS — fake pass write-tree check; TIMING_RECEIPT, logs, caches and vnice control stay in pool_part2.
bars-first and existing score refusal: sb_mask_phrase/part2/launch_gpu.py:125; PASS — missing/altered bars and planted score tests; gate.py and BARS bytes unchanged.
STEP5 gates the pool pass: sb_mask_phrase/part2/sam3_pass.py:292; PASS — part 2 suite and expected CPU CUDA refusal; default launcher runs STEP5 then pass under one budget.
Watchdog: sb_mask_phrase/part2/sam3_pass.py:148; load, encode, detect and STEP5 reader calls use min(300 s, remaining budget). Python alarms interrupt cooperative stalls; outer timeout bounds native stalls.
Timeout exits were simulated with a fake pass; no live process was killed during CPU validation.
Output path: sb_mask_phrase/part2/sam3_pass.py:313; all GPU JSON receipts pin their direct controls and the staging manifest, which pins the payload.
Bars SHA256: 166be15bcd56f303b9b032bab84712264a687bc073b791251b57b814e515d774; guard SHA256: f40b93d12e79768eea1ee6b2b2911695fcc64b4f935e9c4589bcd8b20a5a8368; command: `sha256sum sb_mask_phrase/part2/{BARS_PART2.json,gate.py}`.
Pinned vnice SHA256: 3ab2b542726f32dbecdbe30104f903aa2bef3526a9257013fd5f8bcc99461c6b; command: `sha256sum sb_mask_phrase/part2/vendor/vnice.sh`; vendor/PINS.json also pins the confined monitor.
Staging: 32,742 files, 13,216,814,799 bytes = 13.216815 decimal GB; STAGING_PART2.tsv/json lists source paths, staged paths and SHA256.
SAM3 environment: /scratch/jjyeung/orch_n30/sb_ph2fix/payload/environment; 25,594 files, 7,910,122,788 bytes. The staged environment includes SciPy 1.14.1 from p1cpu; the editable SAM3 import resolves inside payload; Linux/NVIDIA driver and shell utilities remain host prerequisites.
Staging commands: `env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 python -B stage_payload.py`; `python -B relocate_environment.py`; `env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 python -B supplement_environment.py`; `bash sb_mask_phrase/run.sh part2/staging.py`.
Staged smoke PASS: 209 captures, 32 decoded frames; external application inputs and network blocked; exact command in STAGED_SMOKE.json.
Default GPU need: one >=48 GB bf16 card; 1,540 calls × 32 frames × 0.064 GPU-s / 3600 = 0.876089 GPU-h.
--all-aliases GPU need: same card; 2,004 calls × 32 × 0.064 / 3600 = 1.140053 GPU-h; command producing both estimates: `bash sb_mask_phrase/run.sh part2/staging.py`.
Both estimates exclude loading, STEP5 and encoding; the shared 1.2 GPU-h hard stop includes them. Projection may drop new phrases or stop; completion within budget is not claimed.
Exact launch command on the authorized GPU compute node: `bash /scratch/jjyeung/orch_n30/sb_ph2fix/sb_mask_phrase/part2/launch_gpu.sh --node-local 0` (add `--all-aliases` if required).
The default command runs STEP5 then pass. A clean `--mode step5` may continue with `--mode pass`; STOP, KILLED, orphan RUNNING and completed passes refuse nonzero.
Package command: `bash package.sh`; out/sb_ph2fix.tar contains the staged payload; out/sb_ph2fix.tar.sha256 records its SHA256.
