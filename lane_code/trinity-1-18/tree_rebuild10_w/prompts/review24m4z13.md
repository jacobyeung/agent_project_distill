# Narrow review (read-only, once) of vehicle N's launch wrapper jn4.sh (lane tree_rebuild, build 24m4z13)

You review; you do not fix. Run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, with file:line and evidence. Your final message is the verdict.

- Build: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z13/` (prompt `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build24m4z13.md`; out/jn4.sh sha256 80c80de7..., out/JN4.diff against `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/out/jn3.sh` 90ba5540, out/BUILD24M4Z13_REPORT.md, out/T_JN4_USAGE.md, work/build24m4z13/). The reviewer finding it answers: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/n_review/evidence/n_review1h/ITEM6_7_FINDINGS_0135Z.md` (Item 7). The kit it launches: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/out/kit_n` (read-only).
- Verify, each with evidence:
  1. The diff is only: one EXIT trap that runs the j2 publisher once and preserves the exit status, and removal of the old final publish; nothing else (header, job name a15_cot_apb2edfac4, ROOT, child job.sh, TERM/USR1 forwarding, node-local logs) changes.
  2. Every exit path (fewer than 4 H100, b/v.py refusal, resolve|l.py refusal under pipefail, normal child exit, TERM, USR1, publisher failure) publishes exactly once with the refusal line by name in the screened tail, and the exit status is the original one; the trap is installed before the first possible early exit; it cannot recurse or hang the job past Slurm's grace (bounded publisher).
  3. Under the TERM@600 signal path, the forwarding trap and the EXIT trap interact correctly (child receives TERM, wrapper waits, EXIT trap publishes once).
  4. The local tests in work/build24m4z13 ran on these bytes and show fail-before on jn3.sh and pass-after on jn4.sh for each early exit.
- Also list what you did not check.

Rules: Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data* (read only the named files there). nice -n 10, at most 8 threads, under 20 GB RAM. First line `GO`, `GO AFTER FIXES` or `NO-GO`; at most 12 lines.
