# Fix round 2 (one item, CPU only, local only)
Same scope and limits as FIX_BRIEF_R1.md (work only in this folder; no ssh/network/Orchard/GPU/Git/deletion).
Round 1 changed the Slurm job name to `a_5ee9da63`. That is wrong: the account's admission rule REQUIRES every job name to be exactly `a15_cot_ap` + opaque hex, so the name must be `a15_cot_ap5ee9da63` (as ids.json/REPORT.md had before round 1). The fixed prefix `a15_cot_ap` is the mandated opaque prefix, not a method word; allow exactly that prefix in tests/test_visible_names.py (only as the job-name prefix) and keep every other forbidden-word check.
- Restore `-J a15_cot_ap5ee9da63` in payload/s.sh and everywhere the job name appears (REPORT.md table and step 8, ids/tokens, go.template, tests).
- Rebuild every pinned artifact this touches deterministically; update SHA256SUMS.txt, payload sums, UPLOAD.json, evidence/hash_changes_fix1.json (or a fix2 file), DIFF.md, REPORT.md.
- Do not touch tests/RERUN_CHAIN.sh's refusal logic; do not create chain_r1.
- Rerun all local tests (the 4 originals, test_stop_bridge, test_fix1, test_visible_names, tests/review/*) and report results in FIX2.md (<= 20 lines).
