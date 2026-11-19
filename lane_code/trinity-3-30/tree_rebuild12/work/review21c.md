# Independent review (read-only, once) of build 21c of lane tree_rebuild: the narrow fix of review 21's one MUST (changed files only)

You review; you do not fix or design fixes. You run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, each with file:line or artifact path and the command or reading that shows it. Your final message is the verdict.

## Context
Build 21 (package `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/out/tree_rebuild_b21_b262e7a7.tar`, seal b262e7a7) was reviewed NO-GO with one MUST: decoded `work/build21/kits/q/k/p.json` staged `p_files["k/benchmark_scene_exclusions.json"]` verbatim (kits/q/b/z.py:234) and the scanner (`work/build21/naming21.py:30`) skipped decoded k/p.json. Build 21c (prompt `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build21c.md`, report `w21/out/BUILD21C_REPORT.md`, new package `w21/out/tree_rebuild_b21c_*.tar`) fixes it. Everything else in build 21 was reviewed (verdict `/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261119T085438Z_tree_rebuild_rev21/final_message.md`, read that one file).

## Check
1. Untar both packages into a temporary directory you create under `/tmp/rev21c_$$` (reading only), diff them, and review only the changed files.
2. The MUST: no job-visible name (staged, linked, written, logged, result-archive member, decoded map key or value, environment name or value, argument) carries a project, benchmark, dataset, model or method word in any case under the bound forbidden-word lists; the renamed file keeps its pinned content and sha256 and is authenticated as before; every consumer finds it. Try one variant the build's tests do not cover (e.g. a forbidden word in another decoded map, or mixed case).
3. The extended scanner: covers every decoded map the job reads; failing-before test real; mutation refuses by name.
4. Nothing else changed in admission, legality, P's opener rows (routing_opener_init=keep), the step-544 lineage path, or the DEFERRED component-evidence boundary; GO stays false. If the sealed tree changed, say which files and whether the capacity/staging evidence was rerun.
5. Say what you did not check.

## Rules
Read-only except your own `/tmp/rev21c_*` directory. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. Verdict, first line: `GO`, `GO AFTER FIXES` (each fix MUST or SHOULD, with evidence) or `NO-GO`. Then at most 30 lines.
