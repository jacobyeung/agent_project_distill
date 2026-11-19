# Independent review (read-only, once) of builds 24d, 24e and 24f of lane tree_rebuild: vehicle N's launch kit and one tree change, changed files only, versus build 24c

You review; you do not fix or design fixes. You run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, each with file:line or artifact path and the command or reading that shows it. Your final message is the verdict. This review gates N's launch on 4 H100 for 24 h; prioritise problems that would let a wrong launch admit, a correct launch refuse, or a running launch lose its exports.

## Context
Base: build 24c (`/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/tree_rebuild_b24c_22859833.tar`, tree e1e64652, kit q edb324ff, kit n bff6d42c), reviewed (`codex_runs/*_tree_rebuild_rev24c`). Prompts and reports under `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build24{d,e,f}.md` and `w24/out/BUILD24{D,E,F}_REPORT.md`; packages `w24/out/tree_rebuild_b24{d,e,f}_*.tar`.
- 24d: kit n stages and requires no member produced after P's step 400; full decoded job-sequence look-ahead; `out/kit_n_go` (k/a.json GO=true).
- 24e: every host-path pin in the decoded configs of kits q, n and kit_n_go is localised to staged `u/<sha>` files; a look-ahead with /scratch/jjyeung, /data* and /home hidden; f.sh validates before mkdir; job.sh makes the request absolute.
- 24f: the only TREE change, in launch_r2/persistence.py (ORCH RULING 1752Z): when `r1_training` is in cfg and `r2_persistence` is absent, milestone() keeps a node-local receipt instead of refusing. Kit: 4 GPUs, 48 CPUs, 800G, 24:00:00 on advanced; TK_JOB_START; a 10-minute live copy (at most 50 MB) plus a TERM trap; exports to GCS through gcsput.py split against pre-minted sessions in $TK_KIT_HOME/sess.json with done markers; the stop checkpoint to /project after a free-space check, GCS as fallback.

## Check
1. Compare 24c with 24f (and the intermediate packages) member by member in memory (tarfile; write nothing). The tree differs from e1e64652 only in launch_r2/persistence.py and its tests; list every changed kit and generator file, and anything beyond the items above is a finding.
2. The tree change: the node-local path is taken only when r1_training is set and r2_persistence is absent; with r2_persistence present the behaviour is byte-identical; every other combination still refuses. It touches no admission, legality, trained-group or export-content code. Tests cover all three cases, and the export bytes and receipt fields are equal on both paths (hash in the test).
3. Kit n has no post-400 dependency (24d), and every pin and absolute path in the decoded configs resolves on an Orchard host with nothing from Trinity (24e). Grep the decoded configs and scripts once for /scratch/, /home/, /data and trinity, and check each remaining hit's stated reason.
4. The copier: runs in the background from job.sh, never exceeds 50 MB a copy, survives TERM and USR1 and copies once more from the trap; `#SBATCH --signal` reaches the batch shell; exports are verified by sha256 before the done marker; it carries no credential and no session URL in the kit; it cannot write into the kit dir or anywhere outside its stated targets; the free-space check works before the stop checkpoint copy.
5. TK_JOB_START reaches train() through bwrap and torch.distributed.run, so the trainer's self-stop (wall 86,400 s - 3,600 s) comes before Slurm's 24 h limit.
6. kit_n_go differs from kit n only in k/a.json GO=true and the reseal. Decoded scans PASS; each kit dir equals its SHA256SUMS plus BUILD.json and SHA256SUMS.txt; the guard is unchanged (e397ea70); resolver identity checks are unchanged; the upload diffs are pinned and complete.
7. Say what you did not check.

## Rules
Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. Any process runs under nice -n 10, at most 8 threads, under 20 GB RAM. Verdict, first line: `GO`, `GO AFTER FIXES` (each fix MUST or SHOULD, with evidence) or `NO-GO`. Then at most 30 lines.
