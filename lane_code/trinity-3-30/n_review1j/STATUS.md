# n_review1j STATUS (successor resumes from this file alone) — 15:30Z 2026-11-21
Lane n_review1j: headless Claude Code Opus, trinity-3-30, started 2026-11-21 15:08Z, 10 h timeout (rotate by ~00:00Z 11-22). Brief B/briefs/n_review1j_c.md. B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Predecessor state: /scratch/jjyeung/orch_n30/n_review1j/STATUS_n_review1i.md (copy of n_review1i STATUS 15:05Z).
Lanes: tree_rebuild28 from 15:25Z (inbox /scratch/jjyeung/orch_n30/tree_rebuild28/inbox; events B/events/tree_rebuild; tree_rebuild27 ending), n_ops11 (inbox /scratch/jjyeung/orch_n30/n_ops11/inbox). Carriers Claude only.

## Job
174134 (kit X/n 9e809db4, wrapper X/jn7.sh 98edfd9e) HELD on orchard-community-3 until 17:59:50Z after admit refused at carrier_c1_run.py:542. ORDER 1502Z binds. No RELEASE without ORCH.

## Done
- 1508Z RESULT started. Gate kit hashes checked: gate.py 7be0fb0b, run_gate.sh fe4dcf06, make_review.py b845a1e6 (kit by path /scratch/jjyeung/orch_n30/n_review1i/work/gate/).
- 1516Z RESULT item 5 reading: cause = vqa receipt e3ee51da pins division 0d28fdd4 under trinity path n1fix2/inputs/0d28fdd432b0.json; a3v2 f41d15aa names its parent 0d28fdd4 under /lustre/.../e84d901c/z/4c230a7e.json; whole-dict pin compare fails; class (a). Caveat: 601 v7 rows outside 0d28 train (474 A3-only, 127 neither), 0 in a3v2 held-out. Detail /scratch/jjyeung/orch_n30/n_review1j/READING_174134_542.md = evidence/n_review1j/READING_174134_542.md (341aad22).
- Comparison RESULT with tree_rebuild27 1511Z: same cause; differences = 601 rows, sha-only tree compare option (needs ORCH), my unverified "vqa is N's addition", expected :545 pointing target_filter refusal.
- Tree copy for reading: 1-18 /scratch/jjyeung/orch_n30/n_review/r1j/t (from kit tar t_e047002134f979bd.tar 5f2d77c4); divisions at 1-18 n_review/r1j/div; local copies /scratch/jjyeung/orch_n30/n_review1j/work/{r174134,u,kit_k/dec}.

- Correction RESULT 1523Z; QUESTION 1524Z (ORCH ruling 1523Z rested on the withdrawn caveat; recommend F1; default follow ruling): P had vqa ddff748d (lustre path); the 601 rows = removal file 02315a74 (N carries it), caveat withdrawn; F1 (re-pin division.path to P's e84d901c path) is the right fix shape; F1 criteria (i)-(vi) in that event. Design record updated.

- ORCH RULING 1527Z: take F1 (candidate 724 B sha a7682dae; streams.vqa + r1_training.store_parameter; rebuild k/c.json, k/n.json, k/p.json, seal); also fix every pin with a Trinity build path (e.g. sibling dc03d271); preflight runs lines 536-547 predicates on every stream receipt at build and after staging. I review once on my criteria (correction RESULT 1523Z item 4).
- tree_rebuild28 RESULT 1531Z: runtime order pointing,pose,routing,vqa; :546 compares the REBUILT pointing receipt (target_filter equal) so my item (vi) passes per their evidence (not re-run by me). Row rule kept 189,069 of a '212,384-row store' (ask at review: which store, and why not 204,413 / P's 185,933). F1 packet will be events/tree_rebuild/f1_review/ (build W/w30f1/n_go on 1-18 presumably).

## Owed
1. Review F1 when tree_rebuild27 posts it (they build in parallel, unsealed until ORCH GO); also any fix for the cause (files, sha256, criteria in READING file "What a true fix looks like"). Tree change or row removal needs ORCH ruling first.
2. Confirm Orchard bytes (X/n SHA256SUMS + named files; X/jn7.sh) before each release of a new job (template /scratch/jjyeung/orch_n30/n_review1j/work/o46-style: n_review1i/work/o46.sh).
3. Gate at WAITING_REVIEW: bash /scratch/jjyeung/orch_n30/n_review1i/work/gate/run_gate.sh <job> /scratch/jjyeung/orch_n30/n_review1j/gate_<job> [--local DIR]; PASS -> make_review.py <run dir> <kit8> /scratch/jjyeung/orch_n30/n_review1j/review_<job>.json, copy to n_ops11/inbox; FAIL -> BLOCKER.
4. Check inbox + B/events/tree_rebuild every 5 min.
