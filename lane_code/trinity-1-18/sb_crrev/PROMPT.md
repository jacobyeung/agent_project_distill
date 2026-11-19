# Task sb_crrev: independent review of the call-rate and usage reader (read-only verdict)
You are a reviewer on trinity-1-18 (CMU Trinity). Workspace: /scratch/jjyeung/orch_n30/sb_crrev (write only your verdict and scratch here). Read AGENTS.md in this folder first and obey its cluster rules (no recursive search or bulk reads on /home or /data*, no Git, no deletion, no ssh, no GPU, no killing processes, no tmux changes). You get no replies.

## What to review
A Codex builder wrote callrate.py in /scratch/jjyeung/orch_n30/sb_callrate (read out/CALLRATE_REPORT.md, README.md, the code, tests, reproduce.py; inputs under in/ are copies of routed-read returns: step 200 in/cont_ops/work/r1route/out3/A4/ret and B5/ret, step 544 registered reads in .../out3/bases b1/b2; the prior scorer in/cont_ops16/work/c15/r1route/out3s/score_r5.py and classifier in/dist_diag/work/q1/classify.py). Its job: for each routed type, call rate, capped rate, usage (final answer follows the head's printed response), answer rate, score, by unit and by wording, paired A vs B with the room bootstrap; room MRA split dev-S1 vs R0-dev; a --summary mode. An operations lane will paste its output into results at steps 400 and 600 and the orchestrator will make training decisions from it.
Check, with evidence (file:line, a command you ran and its output):
1. Correctness of each metric's definition against the trace format (read 20 real items' traces from the returns yourself): call detection per type, capped, usage tolerance and unit handling, answer extraction, room area parsing. Find any item it misclassifies.
2. Independent recomputation: write your own minimal script (do not import theirs) and recompute call rate, capped and score for distance and room134 at step 200 and 544, and the room MRA split; compare.
3. Robustness for steps 400/600: a new return root with the same layout, a partially complete return, a different package token; does it refuse rather than silently mis-pair?
4. Anything reported that its files do not back.
Deliver REVIEW_VERDICT.md (at most 60 lines): ACCEPT, ACCEPT WITH FINDINGS or REJECT, then numbered findings with evidence and severity.
