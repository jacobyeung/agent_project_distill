# Review (read-only): H read package rebound to run 6ed2c7aa step 400
Workspace /scratch/jjyeung/orch_n30/cont_ops20_b/hd400 on this node (read only; search only inside it). The build round's brief is BRIEF_HD400.md, its report REPORT_HD400.md, outputs under validation/, DIFF_H400_VS_H544.txt; hcam/ is the H build (reviewed GO for 200/544 before this change). Inputs in in/ (BIND400.json, A10b_INPUTS.json part pins, m400.done, A10b_export.json). No ssh, network, Git or edits; you cannot write files: your final message is the review.
Check only, with file:line evidence, the H part (ignore D):
1. Admission: bind_H400.json equals in/BIND400.json plus the A10b part pins; o_build_H.sh STEP=400 admits only this binding; place/fill for 400 requires the exact x_ee227714 done path, REUSE_PARTS_FROM parts matching the pins (bytes, sha) before linking, and preparation files matching preparation_sha256; every failure closes; nothing can be pulled or copied silently.
2. Identity: the 400 build differs from the 544 build only in token-derived bytes, export binding and derived pins (payload, operator, items, settings, walltime unchanged).
3. score_h.py EXPORTS[400]: a 400 return is accepted only for this export and package; 544 returns are refused as 400; the 400-vs-544 comparison works; tests exist and pass.
4. Executability on Orchard: python3.6, bash -n, the Orchard sequence in REPORT_HD400.md runs as written.
Verdict line first: GO, GO AFTER FIXES (list), or NO-GO (list).
