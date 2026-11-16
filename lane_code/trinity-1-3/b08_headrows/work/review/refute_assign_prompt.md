You are an independent, read-only refute reviewer. Do not edit files, do not run ssh, git, or any network command. Read only the files named here (no recursive search outside /scratch/jjyeung/orch_n30/b08_headrows and the two sealed-tree files named below).

Spec under review (brief 08 part B, both-path mix for SFT then RL): every training item of a type that a head inside the model can inform gets ONE form, assigned in hindsight from the deployed pipeline's response on that item:
- head row only when the response is right (numeric within 15% of GT; counts exact integer; options exact letter) AND every operand's accepted instance-id set equals the GT instance-id set (no extra operands);
- direct row when the response is wrong, masks mismatch, or GT instance ids are missing;
- recovery row (call, real runtime failure status, then direct answer) for a real failure status;
- drop: room size and appearance order (direct-only types), object size and direction easy (no ground grammar), operator faults (trace ruling: "Routed policy requires a fixed named candidate universe", form_requires_v3.13, frozen_fusion_requires_depth_cut_receipt, mask_source_unavailable_for_type), unknown statuses, responses without pipeline + sha256 provenance, and any dev-S1, benchmark or withheld room.
- No head row may copy a silently wrong response. Selection: only the minority family per type (head rows on direct-majority types counting, relative distance, direction medium/hard; direct rows on head-majority absolute distance) plus recovery rows, cap 2,000 per (type, form), at most 4 per (type, room, form), deterministic order.

Files:
- /scratch/jjyeung/orch_n30/b08_headrows/out/PARTB_PREP.md (sections "Built" and "Renderer and grammar coverage")
- /scratch/jjyeung/orch_n30/b08_headrows/code/headrows/assign.py, mask_match.py, tests/test_assign.py, tests/test_mask_match.py
- pins in /scratch/jjyeung/orch_n30/b08_headrows/work/auth/
- sealed code used: /scratch/jjyeung/orch_n30/rows_rebuild/work/tree/src/student_pilot/s1_exclusions.py and student_pilot/ground_rows.py
Tests run with: cd /scratch/jjyeung/orch_n30/b08_headrows/code/headrows && /scratch/jjyeung/envs/p1cpu/bin/python -B -m unittest tests.test_assign tests.test_mask_match

Task: try to refute that the code implements the spec and that the spec admits no silently wrong or ineligible row. Look for: correctness checks that accept wrong answers (tolerance edge cases, option letter parsing, string vs number answers, negative/zero GT, count formats like '3.0'), mask checks that pass wrong instances (empty sets, duplicates, operand name normalisation, 'unmatched'), statuses misclassified (a real failure regex matching an operator fault or a success text), eligibility gaps (dataset aliases, scene strings with/without prefixes, ScanNet++ / ARKitScenes naming, rooms vs scenes, exceptions swallowed), selection bias (per-room caps, determinism, cap per form), provenance gaps, and anything in the sealed ground_rows.pack/validate path that would make an assigned head row unpackable. Each finding needs file:line and, where possible, a concrete input that fails (you may describe a failing test; you cannot write files). Verified problems only; no style comments; do not propose redesigns.

Output: a verdict line "VERDICT: GO" or "VERDICT: GO AFTER FIXES" or "VERDICT: NO-GO", then numbered findings (severity, file:line, failing input, why it violates the spec), then a list of what you checked and found sound. At most 80 lines.
