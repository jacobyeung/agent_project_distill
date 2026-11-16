# Lane: eval harness host authorization - add trinity-0-3 and trinity-1-3 to check_lease allowed_hosts (student eval lease admission)

Workspace: `/home/jjyeung/agent_project_distill`. Lane directory: `agent/scratch/devin_lanes/eval_harness_hosts_20260919/` (LANE; outputs to LANE/out, working copies to LANE/work). Run everything locally on this node: no ssh, no nohup, no detached processes. CPU-only lane; no GPU work. Never delete, rename, or edit any existing file outside LANE and your worktree; create new files only. Never switch or create branches in the existing checked-out worktree `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/worktrees/eval_sharding_20260918`: all git work happens in a fresh `git worktree` you create under `LANE/work/` from branch `eval-harness-sharding-20260918` (reviewed PASS at `cf738d18`) onto a new branch `eval-harness-hosts-20260919`. Never run `find`, `grep -r`, `du`, or `ls -R` outside ONE named directory (sweeping searches have crashed nodes). `PYTHONDONTWRITEBYTECODE=1` and `python -B` everywhere.

Liveness heartbeat (mandatory): within your first minute and at least every 5 minutes append `<UTC> | <step in <=12 words>` to `LANE/out/HEARTBEAT.log` and rewrite `LANE/out/PROGRESS.md` (done / doing / next / blockers). Finish with `LANE/out/REPORT.md` (<=30 lines, last line `DEVIN_LANE_DONE`), written even on failure.

## Problem

`check_lease` in `student_pilot/benchmark_eval/contracts.py` (function starts ~line 413) admits leases only from a hard-coded `allowed_hosts` set at line 414: `{'trinity-1-13', 'trinity-0-18', 'trinity-0-23', 'trinity-3-23', 'trinity-2-28'}`; any other host raises `ValueError('Supervisor lease must match an authorized evaluation host')`. Four Qwen VSTI shard workers launched on `trinity-0-3` exited at this check (log: `.../eval_sharding_20260918/artifacts/paper_eval/runs/qwen35_vsti450_base_sharded_20260919/logs/shard_0.log`). The cluster GPU map shows the only free GPUs are on `trinity-0-3` (eight) and `trinity-1-3` (six), neither authorized.

## Change (functional scope, nothing else)

Add `'trinity-0-3'` and `'trinity-1-3'` to the authorized host set. Leave unchanged: the hostname-equality check (`lease.get('host') != hostname.split('.')[0]`), the GPU index range check (`0 <= index <= 7`), and the `trinity-1-13` GPU0 SAM3 reservation (lines ~420-421). If the existing code shape makes it a small, low-risk change, let the set be overridable by an env var or a JSON file next to `contracts.py` (future nodes become data, not code) while the in-code default keeps the current seven hosts (five existing plus the two new); if it is not a small change, skip the override and just extend the literal set — do not force it.

## Tests

Existing `check_lease` tests live in `tests/test_benchmark_eval.py` (~lines 765-795) and are exercised indirectly by `tests/test_benchmark_sharding.py`; both must pass unchanged. `tests/test_admission.py` imports a *different* `check_lease` from `student_pilot.lease` (an unrelated admission/legality module) — do not touch it. Add: (1) a lease for `trinity-0-3` and one for `trinity-1-3` are each accepted; (2) an unlisted host (e.g. `trinity-9-9`) is still rejected; (3) a lease/hostname mismatch is still rejected. Run the full suite once for the record per the CLAUDE.md gate; list any pre-existing unrelated failures with their cause and do not let them block.

## Deliverables (LANE/out/)

Commit SHAs; `CHANGES.md` (diff summary); `REVIEW_PROMPT.md` for one independent reviewer confirming the change is limited to host membership and that no lease, GPU, or scoring semantics changed (CLAUDE.md: one review for changes touching admission, legality, or scoring); `TESTS.md`; `REPORT.md` ending `DEVIN_LANE_DONE`.
