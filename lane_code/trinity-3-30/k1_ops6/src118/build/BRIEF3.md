# Codex build 3: fix the trinity-1-3 namespace rehearsal harness only (no package, job or kit change)

Model gpt-6-astra, effort high. BRIEF.md's rules still hold: write only in this workspace (/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build), no Git, ssh, network, GPU, kill or deletion; bounded reads; nice 19, one thread. Read rh_prepare.py, build_rh.py and the 1-3 result first.

## What happened
The operator extracted rh/RH_1_3.tar under /scratch/jjyeung/orch_n30/k1_partb_rh on trinity-1-3 and ran `bash run_rh.sh` (bwrap exists there: /usr/bin/bwrap). Result (copied back, extracted at ../rh13_out/out/: namespace.log, ARGV.json, RESULT.json):
  bwrap: Can't mkdir parents for /scratch/jjyeung/orch_n30/k1_partb_rh/out/stage_f4fd0dcd/sj/a7e31d84: Read-only file system
Cause: the namespace ro-binds stage/sj onto /scratch/jjyeung, which hides every later bind destination under /scratch/jjyeung, including the stage itself and the package root (`--bind root root`). On Orchard the stage lives under the job-private /tmp, so this clash is a rehearsal-layout artifact.

## Fix (harness only)
Make the rehearsal emulate Orchard's job-private /tmp while keeping every physical write inside /scratch/jjyeung/orch_n30/k1_partb_rh (the orchestrator allows nothing else on 1-3):
- run_rh.sh (written by build_rh.py) starts ONE outer bwrap that binds the host filesystem as-is (`--dev-bind / /` or equivalent), binds <rh>/jt (created inside the rh dir) onto /tmp, and makes the package visible at a path under /tmp (e.g. bind <rh> onto /tmp/<opaque>), then runs rh_prepare.py from there. The stage root, cache, temp and home must then be under /tmp, exactly as batch_entry/stage_job place them on Orchard; the inner namespace argv must come from the unchanged NS.namespace builder.
- Keep the fallback: if the outer bwrap itself fails, record its stderr in out/ and still write out/RH_RESULT.tar (the result tar must always reach the operator). If nested user namespaces are refused, record that clearly as the reason.
- Do not change stage_job.py, batch_entry.py, phase_worker.py, job_support.py, phase_support.py, the source bundle packet/d6e92a81.tar, the batch packet/a7e31d84.sh, manifest v2 or any kit file. If the fix truly needs one of them changed, stop and say why in REPORT3.txt instead.
- Rebuild rh/RH_1_3.tar with `build_rh.py --pack-env` (the operator authorizes this local /scratch write; the env trees are on local /scratch). inputs/model.tar (sha 8005668f) and ../meta/e10fbb95.tar are present; the real prepared check now passes locally (evidence/v2_976f8c0488).
- Run run_rh.sh locally as far as bwrap allows (local bwrap fails on NETLINK_ROUTE; that is known) and show it still writes out/RH_RESULT.tar.
- Make the results tar include rehearse_v2's own evidence run (coverage, unexecuted lines) from inside the namespace, so the operator can credit 1-3-executed lines.
## Deliver
REPORT3.txt (short, no-archaeology): the change (diff of rh_prepare.py/build_rh.py), the new RH_1_3.tar bytes and sha256, the exact operator command for 1-3 (unchanged: extract under /scratch/jjyeung/orch_n30/k1_partb_rh, which the operator will first move aside by renaming, then `cd /scratch/jjyeung/orch_n30/k1_partb_rh && bash run_rh.sh`), and the local run output. Note: the operator will extract into a fresh directory name /scratch/jjyeung/orch_n30/k1_partb_rh2 if the old one cannot be renamed; make the harness independent of the exact directory name.
