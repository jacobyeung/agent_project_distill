# Read-only review: routed package E (dev-S1 distance only, 150 items) forked from routed package A4, bound to export D0 step 200 (run 359fcc3c). GO / GO AFTER FIXES / NO-GO.

You change nothing. No ssh, network, Git or GPU. Search only inside the named directories. Final message at most 50 lines: each finding with file:line, why it matters, severity (blocker / fix before GPU / note).

Builder workspace: /scratch/jjyeung/orch_n30/cont_ops18/ebuild (REPORT_E.md first; build_e.py, build_support.py, bind_E200.json, o_build_E.sh, o_place_fill_E.sh, place_fill_e.py, dryres_e.py, o_cpu_E.sh, o_sub_E.sh, score_e.py, tests). All evidence (built delivery members, diffs, payload changes, test results) is in ebuild/evidence (INDEX.md with sha256; review_e.py reconstructs the delivery in memory). Source A4: /scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3/A4 (1.tgz dcff1068, package/, src/). Sibling package D, already reviewed GO and running: /scratch/jjyeung/orch_n30/cont_ops18/dbuild.

Check:
1. The diff against A4 holds only: token and derived hashes, 9.json (token, budget_gpu_seconds, export_binding), a/6.py (distance only: types [3], counts, schedule, rehearsal, summary), a/0.json, a/5.py, a/4.py REVIEWED_* lines, 3.py/SUBMIT walltime seal, BATCH.sh wrap_batch (EXIT trap, exclude orchard-community-2, USR1 forwarding) applied once.
2. The 150 distance items, their order and every serving pin equal A4's, so E pairs item-for-item with A4 (R1 step 200) and the step-544 baseline.
3. bind_E200.json: object q8/8865619b/359fcc3c_m200.tar, 21583032320 bytes, sha256 6bd9eb26e22c7bdd26fe6e5a932502fa7d1aebd57024861bca786b027ff7d61b, config_sha256 4bc5442c5c9ff12e7407c173c2d1bd6f8a87ab75a298ae71cabbe2053c42bf3c (= D0 s1_receipt config_sha256), preparation hashes config 79b834ee..., receipt d898614a..., data_receipt 7d290849...; and the base_identity argument (shared base snapshot). Does a/4.py fail closed if any of these is wrong?
4. Placement and fill pull each part once with no retries, and verify the whole archive sha256 before use.
5. o_sub_E.sh keeps every guard o_sub_D.sh has (CPU receipt, bundle guard, entry sequence, memory, rehearsal rows for E, no job of ours on general, return pool).
6. score_e.py: call rate (at least one tower call), MRA per unit, pairing against the two baselines, room bootstrap.
7. Python 3.6 compatibility of Orchard-side files.
