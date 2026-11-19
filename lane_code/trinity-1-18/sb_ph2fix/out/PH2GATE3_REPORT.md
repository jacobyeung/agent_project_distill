PASS: gate.py refuses scored-output directories/FIFOs and capture refuses RUNNING without PASS_COMPLETE.json.
Final gate.py SHA256: `c0d31da6634267c85c647898bd6370cea65d3cdd547a8738731a64d8f19daef0`; command: `sha256sum sb_mask_phrase/part2/gate.py`.
Reviewer-only edit SHA256: `6dc58b25432a97bc6bd1ab6e9cb3bb34b293831cc190b6b17129e5671f027ffb`; command: `python -B work/gate3_finish.py` verifies the file with only the advisory line omitted.
Part 2: 31/31 PASS; command: `env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 bash sb_mask_phrase/run.sh ../work/gate3_suites.py part2`; log: out/gate3_part2.log.
Launcher: 25/25 PASS; command: `env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 bash sb_mask_phrase/run.sh ../work/gate3_suites.py launcher`; log: out/gate3_launcher.log.
Regressions refuse a directory/FIFO named DECISION_PART2.json, a capture .json.gz directory, and RUNNING without completion; snapshots verify zero writes. Completed pools and ordinary logs pass.
Fixture: 1,012 rows, 204 captures, 442 both-good; command: `env PART2_FIXTURE_DIR=work/part2_gate3_fixture OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 bash sb_mask_phrase/run.sh part2/price.py fixture-aggregate`.
Fixture diagnostics: 1,037 rows, 209 captures, 456 both-good; same command. Synthetic plumbing evidence only.
GPU archive unchanged: SHA256 `3440a9ff995e6420a345f848f2bb9a0aee5c23ef04b6d31f57e6712e437e3b94`; command: `env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 python -B work/gate3_archive_check.py`.
The archive comparison verifies all 32,749 staged rows; only gate.py and test_part2.py differ among them. All other archived members match except the required STATUS.md.
out/GATE3.patch changes only sb_mask_phrase/part2/gate.py and sb_mask_phrase/part2/test_part2.py; GPU inputs, launcher, pricing, bars, and manifests are unchanged.
Validation and input hashes: out/GATE3_VALIDATION.json; command: `env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 python -B work/gate3_finish.py`.
MISSING: /scratch/jjyeung/orch_n30/sb_ph2chk/logs/patch_check.txt; the supplied evidence was read at /scratch/jjyeung/orch_n30/sb_ph2chk/work/logs/patch_check.txt.
CPU only on trinity-1-18; no GPU, network, SSH, Git, process termination, or writes outside this workspace.
