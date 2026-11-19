# Read-only review: routed package H (900 camera items: 450 held-out reworded + 450 originals) forked from routed package A4, at steps 544 and 200. GO / GO AFTER FIXES / NO-GO.

You change nothing. No ssh, network, Git or GPU. Search only inside named directories. Final message at most 50 lines: findings with file:line, why it matters, severity (blocker / fix before GPU / note).

Builder workspace /scratch/jjyeung/orch_n30/cont_ops18/hcam: REPORT_H.md first, then build_h.py, heldout_h.py, bind_H200.json, bind_H544.json, o_build_H.sh, o_place_fill_H.sh, place_fill_h.py, o_cpu_H.sh, o_sub_H.sh, score_h.py, tests. Evidence in hcam/evidence (INDEX.md; `python3 -B review_h.py` reconstructs both deliveries in memory). Inputs: hcam/in (HANDOFF_cont_ops18.md, held-out items/twins/tasks, SCORER_PATCH with CHECKS.json; the patch already passed an independent review). Source A4: /scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3/A4 (1.tgz dcff1068, package/, src/). Reviewed siblings: /scratch/jjyeung/orch_n30/cont_ops18/ebuild (E, A4-derived) and dbuild (D).

Check:
1. Diff against A4 holds only: token and derived hashes; payload additions (three held-out files under items/), the scorer patch (h1eval/scorers.py d032f969 only), build.py sources/settings for the new items, 9.json (token, budget, evaluator digest, export binding for 544); a/6.py camera-only (types 0,1,2; COUNTS (300,300,300,0,0); expected 900; rehearsal/summary); a/0.json, a/5.py; a/4.py REVIEWED_* only for 544; 3.py/SUBMIT sealed walltime; BATCH.sh wrap_batch once.
2. Every original item equals A4's item and every reworded twin reads its original's frames and labels; question and display_frame_pair agree; patched scorer scores originals exactly as before (parity 636/3,816).
3. Serving equals A4's (tower G3T camera, candidates_argmax, memo, call caps).
4. Bindings: 200 unchanged from A4; 544 equals dbuild/bind_D544.json (469ddece mstop 3ed73aea...).
5. o_sub_H.sh keeps every guard o_sub_E.sh / o_sub_D.sh has that applies.
6. score_h.py: call rate, patched answer metric, reworded-minus-original pairing, step comparison, identity binding of returns.
7. Python 3.6 compatibility of Orchard-side files.
