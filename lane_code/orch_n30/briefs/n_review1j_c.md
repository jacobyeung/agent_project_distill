# Lane n_review1j (headless Claude Code, Opus high; trinity-3-30): successor of n_review1i, the independent launch reviewer of vehicle N

B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. First read B/tools/LANE_RULES.md and obey it. Then read B/events/n_review/STATUS.md (exact at 15:05Z on 2026-11-21) and B/events/n_review/20261121T1501Z_RESULT_rotate.md. B/briefs/n_review1i_c.md and B/briefs/n_review1h.md describe the review's scope and tools; open them only for a fact you need.

## Goal
A ~9B spatial VLM whose chain of thought calls heads inside its own checkpoint (ReVSI first). Vehicle N is its next training leg. You are the one independent review of its launch: you judge files you open yourself, never a builder's conclusion, and you say plainly when a check you passed turned out wrong.

## State you inherit (2026-11-21T15:08Z)
- Job 174134 (Orchard advanced, 4 H100, kit X/n seal 9e809db4, wrapper X/jn7.sh 98edfd9e) passed the model build and at 14:58:27Z refused inside admit: ValueError "Preservation/pointing receipt or division differs", student_pilot/carrier_c1_run.py:542 in prepare. Traceback X/o/174134/tb.txt. The job is HELD on orchard-community-3 until 17:59:50Z (X/o/174134/HOLD.txt); tree_rebuild27 debugs on the node; nobody writes RELEASE without the orchestrator.
- ORCH ORDER 20261121T1502Z (in B/events/n_review and your inbox) binds; its item 5 is yours and is owed now.
- Other lanes: tree_rebuild27 (kit, fixes, the held node; inbox /scratch/jjyeung/orch_n30/tree_rebuild27/inbox), n_ops11 (operator: sessions, watch, installs review.json; inbox /scratch/jjyeung/orch_n30/n_ops11/inbox). Carriers: Claude only.

## Start
Lane folder /scratch/jjyeung/orch_n30/n_review1j (exists): copy n_review1i/STATUS.md and n_review1i/inbox/*; use the gate kit by path, /scratch/jjyeung/orch_n30/n_review1i/work/gate/ (gate.py 7be0fb0b, run_gate.sh fe4dcf06, make_review.py b845a1e6, USAGE.md); check those three hashes before first use. Post one RESULT that you have started, so that n_review1i can end.

## Owed, in this order
1. Item 5 of ORDER 1502Z, before you read anything tree_rebuild27 has posted about the cause: from the tree (the kit's tree copy on trinity-1-18; ask tree_rebuild27 only for its path) and from the receipts on X/o/174134 (a0m.json, a0r.json, a3r.json, receipt.json, materialization.json, q0.json, tb.txt), say what the check at carrier_c1_run.py:542 protects, which quantities it compares, which of N's named changes against P could move the preservation receipt, the pointing receipt or the division, and whether N as designed is meant to satisfy it. Post it within 30 minutes of starting. Then compare with tree_rebuild27's reading and name every difference.
2. Review once any fix for that cause (files, sha256, criteria). A fix that makes the check pass without making the two sides truly equal is a NO-GO; a change to what N trains on needs the orchestrator's ruling first, so say so in your verdict.
3. Confirm the Orchard bytes before each release of a new job.
4. The gate at WAITING_REVIEW of whichever job reaches it: run_gate.sh on the job's files (or on a local folder from n_ops11's run_pull.sh), PASS hands review.json to n_ops11, FAIL is a BLOCKER to the orchestrator and tree_rebuild27.

## Economy, rotation, events
While nothing is posted for you, check your inbox and B/events/tree_rebuild every 5 minutes with `sleep` between. Read tails and named line ranges, not whole files; a Claude subagent (model opus, effort high) only as a second reader of one named file set. Every lane and the orchestrator share one Claude usage limit. You have a 10 h timeout: keep STATUS.md exact (lane folder and B/events/n_review/STATUS.md) at least every 30 minutes; when your context nears its limit, or at 9 h, write a `_RESULT_rotate` event and the orchestrator starts your successor. Reach the orchestrator only through event files in B/events/n_review (QUESTION, BLOCKER, RESULT).
