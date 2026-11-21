# Independent review: rank 1 gate amendment (read-only)

You run on trinity-2-28 for lane lever5. Check `hostname -s` prints trinity-2-28 (stop if `trinity`).

## Rules (binding)
- /home/jjyeung/.claude/CLAUDE.md section "Key Trinity Cluster Rules" and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md bind you.
- Every stream over 20 MB that crosses the head node or touches /home or /data* registers with the IO governor first; Orchard calls keep the spacing LANE_RULES states. For you: no stream, no copy, no ssh, no Orchard, no Git, no GPU, no deletion.
- READ ONLY. Do NOT execute relift.py, run.py or anything that computes a cell (a)-(g) or a BOX score: no cell value may become visible to you. You may run static checks (diff, sha256sum, python -c "import ast; ...") that compute no score.
- Write only /scratch/jjyeung/orch_n30/lever5/r1p/REVIEW_AMENDMENT.md.

## Files (read only these; nothing else)
- /scratch/jjyeung/orch_n30/lever5/r1p/AMENDMENT.md (the amendment text)
- /scratch/jjyeung/orch_n30/lever5/r1p/r1/relift.py (amended) and /scratch/jjyeung/orch_n30/lever1_c/r1/relift.py (original); diff in /scratch/jjyeung/orch_n30/lever5/r1p/relift.diff
- /scratch/jjyeung/orch_n30/lever5/r1p/boxdev/run.py (BOX check code) and /scratch/jjyeung/orch_n30/lever5/r1p/boxdev/SOURCE_PINS.json; originals in /scratch/jjyeung/orch_n30/lever1_c/boxdev/{run.py,SOURCE_PINS.json}; /scratch/jjyeung/orch_n30/lever1_c/r1/SHA256SUMS (the r1 kit's seal)
- /scratch/jjyeung/orch_n30/lever5/r1p/HISTORY_DIAG.txt (the evidence for the amendment)
- /scratch/jjyeung/orch_n30/lever5/r1p/PLAN_RANK1.md (the registered plan's rank 1 section and its results entry)

## Criteria (judge each PASS/FAIL with file:line evidence)
1. Cell (a) and cells b-g share the same dump, the same item set and the same code path (fit_lift on the same restored geometry g; same refs; same exclusions), so every versus-(a) difference is paired inside one dump.
2. Nothing in the amendment selects items or captures after the fact: the item set, exclusions, censoring and bootstrap are unchanged from the original; the amendment only removes the two STOP returns and adds report-only fields.
3. The amended relift still raises on a depth-free gap mismatch, an incomplete or salvaged return, a binding mismatch, and every other original integrity check.
4. The BOX check executes the amended prefix unchanged otherwise, checks base == relift cell (a) per item, and its pins resolve to the files named (the depth_format.py pin change is justified by the r1 kit's seal).
5. The amendment's stated reason follows from HISTORY_DIAG.txt, and the amendment text matches the code.
6. No cell value was visible to the lane or to you (the amended code has never been run; check the r1p tree holds no output of it: no r1p/r1/out, no r1p/boxdev/out).
Verdict: GO or NO-GO, with any required fix. Deliverable: REVIEW_AMENDMENT.md (<= 50 lines). Final message: the verdict and one line per criterion.
