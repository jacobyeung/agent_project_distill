# PH2FIX2
CPU checks PASS; fresh strace MISSING because the sandbox denies ptrace. No GPU, SSH, network, tmux, Git or process termination ran.
Fix 1: `sb_mask_phrase/part2/vendor/terminator.sh:33` and `vendor/PINS.json:4,8` pin `19727987d5517c0e2549e1205e55f4bcc87f34dafe66c96bdf90233305942e5d`; `test_launcher.py:172` permits only `/tmp/terminator/$USER-<pid>` outside the pool. The monitor was not executed.
Fix 2: `sb_mask_phrase/part2/launch_gpu.sh:4` and `launch_gpu.py:89` set payload OPENSSL_CONF and PATH=/usr/bin:/bin; `test_launcher.py:182` passes.
Fix 3: `sb_mask_phrase/part2/price.py:226,292` separates decision fits from `_1037` diagnostics with the corresponding fold_choices; `test_part2.py:174` passes.
Population: 1,012 rows / 204 captures / 442 both-good; diagnostics: 1,037 / 209 / 456. The synthetic fixture reproduces W1 +3.82 [+2.16, +5.63]; it is not a GPU result.
Population command: `PART2_FIXTURE_DIR=work/part2_aggregate_ph2fix2_verified bash sb_mask_phrase/run.sh part2/price.py fixture-aggregate`; evidence: that directory's `aggregate/DECISION_PART2.json`.
Hole 1: `sb_mask_phrase/part2/gate.py:11` rejects dangling and existing file symlinks; `test_part2.py:271` passes.
Hole 2: `sb_mask_phrase/part2/gate.py:11,45` rejects directory and ancestor symlinks before traversal; `test_part2.py:274` passes.
Hole 3: `sb_mask_phrase/part2/gate.py:55` matches score suffixes case-insensitively; `test_part2.py:277` passes for uppercase JSON.
Hole 4: `sb_mask_phrase/part2/gate.py:55` covers CSV, TSV, JSONL, JSON, gzip and temporary suffix chains; `test_part2.py:280` passes for CSV.
Exclusive outputs: `sb_mask_phrase/part2/price.py:39,44,299` uses x/xt for JSON, gzip and per-item output; `test_part2.py:200` preserves existing files and dangling targets.
Guard command: `env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 python -B work/guard_ph2fix2.py`; all 159 applicable attack-entry pairs refuse with 0 writes. Clean gates and legitimate aggregate capture inputs remain controls.
Suites: part 1 26/26, part 2 26/26, launcher 25/25; dry-run steps 1–4 PASS; CPU STEP5 refuses CUDA as required.
Suite commands: `bash sb_mask_phrase/run.sh test_kit.py`; `bash sb_mask_phrase/run.sh part2/test_part2.py`; `bash sb_mask_phrase/run.sh part2/test_launcher.py`; `bash sb_mask_phrase/run.sh dryrun.py report`. Evidence: `out/CPU_VALIDATION.json`.
Fresh strace command: `env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 python -B work/strace_ph2fix2.py`; PTRACE_TRACEME returns Operation not permitted.
MISSING: fresh trace at `work/ph2rev_probes/strace_fixed/imports.strace`. The supplied reviewer's fixed trace has 0 /home or /data* touches; actual payload ssl/hashlib/torch imports and launcher bootstrap pass without tracing.
Trace evidence command: `env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 python -B work/strace_evidence_ph2fix2.py`; `out/STRACE_PH2FIX2.json` distinguishes supplied trace evidence from fresh checks.
GPU estimate: default 1.229 GPU-h exceeds the 1.2 stop; the ten-capture projection drops new phrases (W_new MISSING), projecting 0.922 GPU-h. All-aliases projects 1.425, dropping to 1.118.
Estimate command: `bash sb_mask_phrase/run.sh ../work/estimate_ph2fix2.py`. With detect d=0.064/(1+6.5/19), seconds=32*d*(6.5*captures+calls); the drop estimate includes new calls already spent in ten captures. Loading and STEP5 add time within the hard stop.
Staging: 32,749 files, 13,216,850,605 bytes = 13.216851 GB. Command: `bash sb_mask_phrase/run.sh part2/staging.py`; `out/STAGING_PART2.tsv/json` pin all staged inputs.
Production preflight command: `env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 python -B work/finalize_ph2fix2.py`; PASS without probing a GPU.
Transfer from trinity-1-18 after selecting the GPU node: `cat /scratch/jjyeung/orch_n30/sb_ph2fix/out/sb_ph2fix2.tar | ssh trinity-X-Y.ib 'mkdir -p /scratch/jjyeung/orch_n30/sb_ph2fix && tar xf - -C /scratch/jjyeung/orch_n30/sb_ph2fix'`.
Launch on that GPU node (replace index 0 with the chosen idle >=48 GB card): `tmux new -s p2 'env PATH=/usr/bin:/bin bash /scratch/jjyeung/orch_n30/sb_ph2fix/sb_mask_phrase/part2/launch_gpu.sh --node-local 0'`.
Return from the GPU node: `cd /scratch/jjyeung/orch_n30/sb_ph2fix/sb_mask_phrase/out && tar cf - pool_part2 | ssh trinity-1-18.ib 'cd /scratch/jjyeung/orch_n30/sb_ph2fix/sb_mask_phrase/out && tar xf -'`.
Price on trinity-1-18, where all 209 K1 caches remain: `cd /scratch/jjyeung/orch_n30/sb_ph2fix/sb_mask_phrase && bash part2/launch_part2.sh capture && bash run.sh part2/price.py aggregate`.
Package: `bash package.sh`; verify every staged member with `env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 python -B out/check_archive_ph2fix2.py`. SHA256: `out/sb_ph2fix2.tar.sha256`.
The reviewed archive remains byte-identical: `nice -n 10 sha256sum -c out/sb_ph2fix.tar.sha256`; expected SHA256 `38620df42faf70dcf6d030a8995e9a9d0415671980528c80e0c1f458efb671b9`.
