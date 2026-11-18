<!-- recovered by seal_plan: transcript=71f94277 line=24551 utc=2026-11-13T20:00:26.207Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_gates_confirmation_ACCEPT_three_conditions.md heredoc_quoted -->
# ORCH: gates confirmation is ACCEPT for both scopes; three conditions and one small fix

Result: `/scratch/jjyeung/orch_cd/leg_s1_review/CONFIRMATION_MILESTONE_GATES.md`; receipts `leg_s1_review/MILESTONE_DIRECT_RECEIPT_GATES.json` (8103266b) and `MILESTONE_ROUTED_RECEIPT_GATES.json` (5939949b), packet 9e3461ac. All 57 pins match; F5 and F6 are fixed and tested; the low items are done; nothing else changed. The hardware record's evidence and merge hashes match; both comparator jobs' own nvidia-smi lines say H100 80GB; the reference values recompute (parent 71.7964% with 40 continued = 36 + 4; f17 73.5564% with one output-cap hit). Tests from the reviewer's private copy: milestone 106/106, native 74/74, its own 9/9 (`leg_s1_review/work_milestone_gates/`).

**Do now (minutes, CPU):**
1. **C3: run `layout_check` on the real step-1 `artifact.json` and on the step-50 one.** The gate reads `frame_layout` and `anchors` from the artifact with no default; if the real artifact does not carry `anchors`, every direct read refuses. Tell me the result at once either way.
2. **N1 (`decision_fork.py:240-246`):** the hardware check trusts the audit's `gpu_type` field and only hash-checks the evidence; the reviewer's test passes evidence that reads "A6000". Make the code parse the GPU model from the evidence text and compare, with that test inverted; re-pin the fork and tell me the new hash (I will have the one-function change confirmed, it does not hold the launcher).

**Conditions on the launcher you are building:**
3. **C1:** no pinned code refuses a `COMPLETE` and `FAILED` pair (`execute_chain.py:226-240` can still write both); the launcher must treat the pair as failed.
4. **C2:** Orchard output goes to job-local storage and is persisted off the node before the job ends, as you planned.

Send the launcher's pin when it is ready. It is 20:00Z; step 100 is due near 21:40Z.