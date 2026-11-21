# Swarm rules (bind every swarm worker; 2026-11-20)

B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. R = /data2/jjyeung/agent_project_data/distill_design/swarm_20261120 (results). S = /scratch/jjyeung/swarm_20261120 on the node you run on (staged inputs, node-local).

## Why this swarm exists
The user's words (2026-11-20): "last day, let's use up all these credits for something useful ... analyze failures ... fix our codebase ... improve efficiency of experiments ... we can overhaul everything". Project goal: a ~9B spatial VLM, end to end from RGB, whose chain of thought calls heads inside its own checkpoint and answers from what they print; it must beat open 9B models on ReVSI, VSTI and VSI-Bench, then serve as a cheaper base for navigation fine-tuning. Every task serves one of: a bug that costs benchmark points or GPU hours, a cheaper or faster experiment, an explained failure on a development set, or experiment code built ahead of need.

## Hard limits (a violation can cost the user their cluster access)
1. Read B/tools/LANE_RULES.md first; it binds you.
2. Work only inside your task directory S/work/<task>. Inputs are the staged copies under S that your task names. Read nothing else on /home or /data* except files your task names by full path; never run find, du, ls -R or grep -r on /home or /data*. A read above 20 MB from /home or /data* is not allowed in a swarm task.
3. No ssh. No git command in any repository on /home or /data* (the staged copy has no .git; compare files with diff). No GPU, no Slurm, no Orchard, no paid inference API, no download above 20 MB. No deletion commands; list files you would remove.
4. The launch line is off limits: vehicle N launches tonight from sealed kits. Change nothing outside your task directory; nothing you write lands on main, in a kit, in an epoch checkout or on Orchard. Code changes are delivered as a unified diff against the staged copy plus tests, for the orchestrator to land at a training boundary after review.
5. Legality: official benchmark items (VSI-Bench, ReVSI, VSTI) are never read for analysis, design or training data. Failure analysis uses only the staged development reads. If you meet an official item, stop reading it and say where it was.
6. Load: prefix heavy commands with `nice -n 10`; at most 4 threads (OMP_NUM_THREADS=4); targeted tests only, never a whole suite; read large files as streams; stay under 5 GB of disk and 8 GB of memory.

## Cutoff
The credit that pays for you ends tonight. Write R/results/<task>.md within your first 30 minutes (even if it only lists what you have so far) and update it as you go, most valuable finding first. Assume you can be cut off at any moment after 2026-11-21T07:00Z (23:00 PT); whatever is not on disk under R by then is lost.

## Evidence standard
Every finding gives file:line, a concrete input that fails and the wrong output, a reproduction you ran (a test or a script, kept in your files), and a price: benchmark points on a named development set, GPU-hours per training leg, or minutes per job; write "unpriced" with the reason when no price can be had. Mark each finding CONFIRMED (you reproduced it) or SUSPECTED (reading only). State what you did not check.

## Deliver
- R/results/<task>.md, at most 60 lines: findings ranked by price, each with its evidence path; then what you did not cover.
- R/files/<task>/: diffs, tests, scripts and tables, each under 5 MB, at most 30 files.
- One line appended to R/DONE.txt: `<UTC from date -u +%Y%m%dT%H%MZ> <task> <CONFIRMED count> <SUSPECTED count> <one-line headline>`.
- Never write under B/events, and never message the orchestrator; the runner reports for you.
