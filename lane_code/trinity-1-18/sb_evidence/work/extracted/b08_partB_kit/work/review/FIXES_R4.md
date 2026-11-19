# Fixes for REVIEW_R4 (Codex gpt-6-astra, NO-GO, 6 findings) — assign.py 16a84573..., mask_match.py 1efbf88b..., tests 23 OK
1. Every recorded call must fullmatch one of the sealed Session call forms (ground_v312 GROUND/GAP, ground_v313 INSTANCE/SURFACE/EXTENT, box_v313 GROUND/GAP/CAMGAP), else drop 'record_call_grammar'. Test test_review4.
2. A head record may not contain a failure status line or an operator-fault string in any response ('record_failure_in_head'). Test test_review4.
3. An option GT must name one of the item's options (sealed option_map), checked before the status branch ('gt_not_an_option'); malformed options drop. Test test_review4.
4. mask_match refuses a frame given twice under different spellings. Test test_match_and_threshold.
5. GT and selected instance ids must be non-empty strings; None or '' is unverified / mismatch. Test test_review4.
6. Failure status lines allow colons in the name ('[^\n<>]+: not seen'); the name is the text before the final ': not seen' and must equal the ground call's obj. Test test_review4.
