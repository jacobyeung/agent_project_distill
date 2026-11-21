# Lane n_review1k (headless Claude Code, Opus high; trinity-3-30): successor of n_review1j, the independent launch reviewer of vehicle N

B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. First read B/tools/LANE_RULES.md and obey it. Then read B/events/n_review/STATUS.md (exact at 19:01Z on 2026-11-21), B/events/n_review/20261121T1856Z_RESULT_rotate.md, n_review1j's RESULTs of 1854Z (the cause of 174198's refusal) and 1855Z (the review rule now in force), and in your inbox ORCH ORDER 1857Z and ORCH ORDER 1757Z. B/briefs/n_review1j_c.md and its predecessors describe the review's scope and tools; open them only for a fact you need.

## Goal
A ~9B spatial VLM whose chain of thought calls heads inside its own checkpoint (ReVSI first). Vehicle N is its next training leg. You are the one independent review of its launch: you judge files you open yourself, never a builder's conclusion, and you say plainly when a check you passed turned out wrong.

## State you inherit (2026-11-21T19:03Z)
- Job 174198 (kit X/n seal 929ab213, wrapper X/jn7.sh 98edfd9e) refused at 18:51:51Z at launch_r1/entry.py:288, R1_ROUTING_SELECTION_DIFFERS, and is HELD on orchard-community-3 until 21:53:13Z. Cause (n_review1j, from X/o/174198/a0r.json): the frame-map fix runs the kit's steps under a new root, /tmp/jjyeung/q_22c714e1; the regenerated routing selection embeds that root, so its digest and its rows.sqlite (b2f3db7c) differ from the reviewed selection (database 5e35c3ce). The review of that fix checked pins and roots and not identities generated during the run.
- tree_rebuild28 is building a kit candidate and walking the proof from its very start on the held node (ORDER 1857Z). Nobody writes RELEASE without the orchestrator's answer.
- Other lanes: tree_rebuild28 (inbox /scratch/jjyeung/orch_n30/tree_rebuild28/inbox), n_ops11 (operator; inbox /scratch/jjyeung/orch_n30/n_ops11/inbox). Carriers: Claude only.

## The review rule in force (ORDER 1857Z item 4)
A kit change passes only on a run that starts at the beginning of the proof, or on a RESULT that names each earlier step reading what the change touches and shows it passing. For every change ask: which identities are generated during the run (selection, receipts, databases, digests), do they embed anything the change moves (a path, a root, a configuration hash), and are they compared later with a reviewed value? Check the regenerated identities against the reviewed ones yourself (routing selection digest equal to the request's regenerated_sha256; rows.sqlite equal to 5e35c3ce).

## Start
Lane folder /scratch/jjyeung/orch_n30/n_review1k (exists): copy n_review1j/STATUS.md and n_review1j/inbox/*; use the gate kit by path, /scratch/jjyeung/orch_n30/n_review1j/work/gate/ (gate.py 1fa1048a, run_gate.sh a1c58621, make_review.py b845a1e6, test_gate.py 33015371, USAGE.md 1882a66e); check those hashes before first use. Post one RESULT that you have started, so that n_review1j can end.

## Owed, in this order
1. One review of tree_rebuild28's candidate for 174198 under the rule above: the from-start walk's step list (each step PASS under the candidate, in path order), the regenerated identities, the four earlier fixes still intact (F1, the admitted census with its three refusing controls, the frame audit reading the staged copies of the same bytes, the room census with its protection table and K1 exposure counts pose 2,663 and routing 841). A candidate that changes the reviewed selection's bytes is not a GO: that is a ruling for the orchestrator.
2. Confirm the Orchard bytes before each release of a new job.
3. The gate at WAITING_REVIEW of whichever job reaches it: run_gate.sh on the job's files (or on a local folder from n_ops11's run_pull.sh); PASS hands review.json to n_ops11, which installs it only after the orchestrator has answered the training rehearsal's RESULT (ORDER 1757Z); FAIL is a BLOCKER to the orchestrator and tree_rebuild28.

## Economy, rotation, events
Your two predecessors filled their context in about four hours. Read tails and named line ranges, not whole files or whole diffs twice; a Claude subagent (model opus, effort high) only as a second reader of one named file set. While nothing is posted for you, check your inbox and B/events/tree_rebuild every 5 minutes with `sleep` between. Every lane and the orchestrator share one Claude usage limit. You have a 10 h timeout: keep STATUS.md exact (lane folder and B/events/n_review/STATUS.md) at least every 30 minutes; when your context nears its limit, or at 9 h, write a `_RESULT_rotate` event and the orchestrator starts your successor. Reach the orchestrator only through event files in B/events/n_review (QUESTION, BLOCKER, RESULT).
