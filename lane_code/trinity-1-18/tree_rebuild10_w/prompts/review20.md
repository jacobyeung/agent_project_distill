# Independent review (read-only, once) of build 20 of lane tree_rebuild: the fixes for review 19's four findings and N's Orchard proof kit

You review; you do not fix or design fixes. You run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, each with file:line or artifact path and the command or reading that shows it. Your final message is the verdict.

## Context
Vehicle N is a ~9B spatial vision-language model whose chain of thought calls heads inside its own checkpoint and answers from what they print. N takes over from vehicle P's step-600 export (run 6ed2c7aa, lineage step 544 1d6eeb28) as init; its production proof runs first on P's step-400 export, which has no checkpoint (export-only binding, proof mode q only). Build 19 deferred nine lost component-evidence records only for R1-on-N configs whose init is an authenticated P export; every official read, official init selection and handover into one must refuse while any slot is DEFERRED (ORCH RULING `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/RULING_0344Z.md`).

## Inputs (READ-ONLY)
- Build 20 workspace `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w20`: `out/BUILD20_REPORT.md`, `out/TREE_SEAL.json`, `work/tree_r1/`, `work/build20/` (proofs, kits/q, UPLOADS.json, OPERATOR.md, native20.py, jobtest.py). Its prompt `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build20.md`; review 19's verdict `.../prompts/REVIEW19_VERDICT.md`.
- Build 19 workspace (the base) `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19`; diff the two trees (`w19/work/tree_r1` vs `w20/work/tree_r1`) to find the changed files and review those only, plus `work/build20/kits/q`.
- P's own Orchard kit scripts and pins (what N's job is modelled on): `/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/pwrap/`.

## Check, in this order
1. Each of review 19's four findings: is it fixed, without weakening any gate? (1) P's real pose receipt form authenticates by schema and bound hashes; (2) `selected_init(..., official=True)` returns only an identity whose artifact it verified and refuses DEFERRED; (3) the component guard refuses any altered, missing, extra or VERIFIED-without-record slot; (4) f7eaf7a7 and 43853165 are staged. For each, try one variant the build's tests do not cover.
2. Answer again: can any path produce an official-item number, a selection on official items, or a handover or export feeding such a read, from an export or init with a DEFERRED slot?
3. The Orchard kit `work/build20/kits/q`: read job.sh, b/*.py, b/*.sh and b/resolve.py end to end. Would it run as written on an Orchard GPU node (paths, the bwrap namespace modelled on P's `ext/pwrap/b/c.sh`, staging and sha checks, the resolver on P's step-400 files: h/RP/e/r.json, s.tar, GCS tar parts)? Does any job-visible string (path, name, argument, environment variable, log) carry a project, benchmark, dataset, model or method word? Can it write into P's kit or run? Does the report-only room count stay report-only?
4. Anything in the changed files that would stop or corrupt the real proof's production audit, final handover, N initialization or every-rank first forward and loss (the CPU fixture never reached those stages).
5. Say what you did not check.

## Rules
- Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. Search inside the inputs above freely. Do not run the build's confirmation commands (they write proof folders); in-memory Python calls that write nowhere are allowed.
- Verdict, first line: `GO`, `GO AFTER FIXES` (each fix MUST or SHOULD, with evidence) or `NO-GO` (with the blocking finding). Then at most 40 lines.
