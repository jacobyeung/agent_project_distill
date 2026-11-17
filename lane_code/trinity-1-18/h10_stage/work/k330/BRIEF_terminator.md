# Task: repin one vendor hash in H1-0 package b01ec87a6f29b, rebuild, rerun the suite (CPU only)

Workspace: /scratch/jjyeung/orch_n30/h10_stage/work/k330 on trinity-1-18 (K = k330/kit, a copy of the H1-0 kit; k330/tests = reviewer tests).
Hard rules: no git, no ssh/scp/rsync/network, no GPU, no process kills, no deletion. Write only inside k330 (and /dev/shm/jjyeung_h10t if a test needs tmp). Never search outside k330.

## Change (only this)
The package's vendored `orchard_h10/vendor/ORCHARD_ASSETS.json` (inside K/orchard_h10/package/0.tgz; source copy K/tmp/b8/readk_tmpl/launcher/ORCHARD_ASSETS.json) pins
`terminator_sha256 = cbb91ba7455d15007bd3affeb358dc5693f3845949ee0abacf892a4402748b94`, a file that exists nowhere. ORCH ordered the repin to the cluster's official terminator:
`19727987d5517c0e2549e1205e55f4bcc87f34dafe66c96bdf90233305942e5d` (/data3/shared/scripts/vnice/terminator.sh; you may sha256 that one file to confirm, read-only).
job.py stage() compares the staged terminator against this pin; nothing else may change.

## How
1. Do NOT run build.py's sources(): its B=/scratch/jjyeung/orch_n30/b04_e2ehook differs on this node. Instead write K/orchard_h10/repin_terminator.py that rebuilds from the existing package:
   - payload = every member of the old K/orchard_h10/package/0.tgz except 9.json, bytes unchanged, except orchard_h10/vendor/ORCHARD_ASSETS.json where the old hex string is replaced by the new one exactly once (byte replace, no JSON re-serialization).
   - cfg = old 9.json with only payload_pins['orchard_h10/vendor/ORCHARD_ASSETS.json'] updated (sha256, bytes). Keep template_pins as is (it records the unmodified transport source) and token b01ec87a6f29b.
   - Produce 0.tgz, 0.json, CONFIG.json, BATCH.sh, SUBMIT.cmd, 3.py, INPUTS.example.json, PACKAGE.json with exactly the same functions/format build.py uses (import build.py's batch(), use vendor orchard_launcher.tar_bytes, same helper text, same write()).
   - Self-test first: with no replacement, your rebuild must reproduce the old 0.tgz sha 4847ad12194edae7f3d573baef4bff8120db89b4495e7e54bcf474d5caf90676 and old PACKAGE.json byte-for-byte. Only then apply the change.
   - Keep the old package as K/orchard_h10/package_cbb91ba7/ (copy) and write the new one to K/orchard_h10/package/. Update K/orchard_h10/TOKENS.json only if build.py would.
2. Verify: every payload member except that one file is byte-identical; 9.json differs only in that pin; new plan_sha256 = canonical(cfg); 3.py-style load_helpers + verify_config pass on the new package; common.opaque passes for every public file.
3. Run the full suite with the command in K/BUILD_REPORT.md "Validation commands and results" but LANE_TEST_OUTPUT="$PWD/tmp/t10" and --basetemp "$PWD/tmp/t10/full", log to K/logs/t10/full.log; then the reviewer tests in k330/tests (t_*.py, run them the way their headers say, with bash cpu.sh). Update any test that hard-codes the old package/plan hashes only if it pins the package digest; report each such edit. Pre-existing failures that come from this node (missing /dev/shm fixtures, B paths) go in the report with cause; do not chase them.
4. Write k330/REPORT_terminator.md (<=40 lines): old/new 0.tgz sha+bytes, plan sha, PACKAGE.json file hashes, member diff proof, test counts (pass/fail/skip with causes), and the exact list of files you changed.
