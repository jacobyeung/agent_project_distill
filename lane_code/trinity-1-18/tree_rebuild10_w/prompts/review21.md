# Independent review (read-only, once) of build 21 of lane tree_rebuild (changed files only): review 20's kit fixes, the opener fix, real P receipts, the capacity fixture and the V2H slice

You review; you do not fix or design fixes. You run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, each with file:line or artifact path and the command or reading that shows it. Your final message is the verdict.

## Context
Vehicle N is a ~9B spatial vision-language model whose chain of thought calls heads inside its own checkpoint and answers from what they print. N takes over from vehicle P's step-600 export (run 6ed2c7aa, lineage step 544 1d6eeb28) as init; its production proof runs first on P's step-400 export, which has no checkpoint (export-only binding, proof mode q only). Build 19 deferred nine lost component-evidence records only for R1-on-N configs whose init is an authenticated P export; every official read, official init selection and handover into one must refuse while any slot is DEFERRED (ORCH RULING `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/RULING_0344Z.md`).

## Inputs (READ-ONLY)
- Build 21 workspace `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21`: `out/BUILD21_REPORT.md`, `out/TREE_SEAL.json`, `work/tree_r1/`, `work/build21/` (proofs incl. receipts, native/capacity fixture, v2h; kits/q; UPLOADS.json; OPERATOR.md). Its prompts `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build21.md` and `build21b.md`; review 20's verdict `.../prompts/REVIEW20_VERDICT.md`.
- Build 20 workspace (the base) `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w20`; diff `w20/work/tree_r1` against `w21/work/tree_r1` and `w20/work/build20/kits/q` against `w21/work/build21/kits/q`; review the changed files only.
- P's fetched receipts: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/preceipts/`; V2H records `.../ext/v2h/`, rows `/scratch/jjyeung/n30_mirror/dist_diag/coverage_v2h/`.
- P's own Orchard kit scripts and pins (what N's job is modelled on): `/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/pwrap/`.

## Check, in this order
1. Review 20's three kit findings: ANON_OK.json staged; the staged export layout loads through `full_ft.read_export` (try it in memory on the fixture's staged export); no project, benchmark, dataset, model or method word in any job-visible string of the decoded kit (paths, names, arguments, environment variables, logs), and the operator-made opaque links are checked by the job. Try one variant the build's tests do not cover for each.
2. The opener fix found by the capacity fixture: is it a real defect, fixed without changing P's trained opener rows at handover (routing_opener_init=keep) or the step-544 lineage path, with a failing-before test?
3. The fixture's stage tables at 400 (export-only) and 600 (checkpoint): do they show ADMIT with every rank's finite first-batch loss from the real producers, and are the stand-ins only at the frame-host, model-size and GPU boundary?
4. Real receipts: do the mode-q readers authenticate P's real receipts without any weakened check (compare to w20)?
5. V2H binding: rows bound by sha256, card cell and ceilings, the held-out-wording assertion over every bound N slice (and the planted-row test), u2 handling.
6. Answer again: can any path produce an official-item number, a selection on official items, or a handover or export feeding such a read, from an export or init with a DEFERRED slot?
7. Say what you did not check.

## Rules
- Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. Search inside the inputs above freely. Do not run the build's confirmation commands (they write proof folders); in-memory Python calls that write nowhere are allowed.
- Verdict, first line: `GO`, `GO AFTER FIXES` (each fix MUST or SHOULD, with evidence) or `NO-GO` (with the blocking finding). Then at most 40 lines.
