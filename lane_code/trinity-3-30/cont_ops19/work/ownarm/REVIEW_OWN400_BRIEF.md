# Review (read-only): own-arm camera kit rebound to run 6ed2c7aa step 400

Workspace (read only): /scratch/jjyeung/orch_n30/cont_ops19/work/ownarm. Write only REVIEW_OWN400.md there. No ssh, no network, no Git, no edits to code. Search only inside this directory and /dev/shm/c19o/w (the extracted trees out/pkg/r400/package and src link there).

The kit (kit/, step-200 proof build out/pkg/b200, earlier review GO AFTER FIXES) forks routed package A4 and changes the operator to read the 450 dev-S1 camera items with tower and own arms. It was bound to run 673bc60f. The new change rebinds it to continuation run 6ed2c7aa at step 400 (BRIEF_OWN400.md states the task; REPORT_OWN400.md the result; DIFF_R400_VS_B200.txt the full diff; TEST_RESULTS_OWN400.txt the tests; pin400.json the binding; ref_build_r10.py and ref_o_place_pull_fill10.sh show how the routed A/B packages were rebound to the same export and ran on Orchard).

Check only, and report verified problems with file:line evidence:
1. Admission: the derived o_pullfill.sh / o_pullfill_resume.sh / o_place.sh fail closed on a wrong receipt, wrong object/bytes/sha, wrong preparation file sha (config, s1 receipt, data receipt), wrong run/step in the artifact; nothing in the pin can be silently ignored; the receipt path / run pairing whitelist is exact.
2. Identity: r400's payload, operator, tower settings and scorer bindings equal b200's except token, export binding, REVIEWED_* constants and the derived hashes; no other byte moves (compare with DIFF_R400_VS_B200.txt and the packages themselves).
3. Fill parity with the routed A/B rebind that ran (ref_o_place_pull_fill10.sh): same a/4.py arguments (--config/--receipt/--data-receipt/--lineage/--step), same export part handling (four parts, no retries), same dry checks.
4. Executability on Orchard: python3.6-compatible helpers, bash -n, paths that exist in the Orchard layout named in the scripts.
5. Scorer (kit/ownread.py): its export-pin check now compares against the 400 binding; partial returns still refuse.
Verdict line at the top: GO, GO AFTER FIXES (list), or NO-GO (list). Do not design fixes beyond naming the defect.
