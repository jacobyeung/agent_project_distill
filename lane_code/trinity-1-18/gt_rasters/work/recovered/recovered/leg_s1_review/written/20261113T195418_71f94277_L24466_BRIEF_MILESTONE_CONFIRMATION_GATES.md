<!-- recovered by seal_plan: transcript=71f94277 line=24466 utc=2026-11-13T19:54:18.020Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_review/BRIEF_MILESTONE_CONFIRMATION_GATES.md  -->
# Confirmation pass, third round: two gates added to already accepted evaluation readers, and the hardware evidence of the comparators

You are an independent reviewer from a different model family than the author. Two scopes of an evaluation chain were accepted an hour ago with receipts; the acceptance left two fixes owed on the direct scope before the decision read (F5, F6) and several low items. The author has now added them and re-pinned. Confirm the additions, check that nothing else moved, and issue new receipts if so. The decision read these readers serve arrives in under two hours, so be exact and brief.

## Material

- The accepted state (read first): `/scratch/jjyeung/orch_cd/leg_s1_review/CONFIRMATION_MILESTONE.md` and its brief `BRIEF_MILESTONE_CONFIRMATION.md` beside it (context and file locations). Accepted packet: `/scratch/jjyeung/orch_cd/evalx/work/milestone/SCOPED_REVIEW_REQUEST_REPAIRED.json` (direct 21 files, digest 682aaeaa...; routed 29 files, digest 21dd82dd...).
- New packet: `/scratch/jjyeung/orch_cd/evalx/work/milestone/SCOPED_REVIEW_REQUEST_GATES.json` (sha256 9e3461ac...): direct 23 pins, digest 8103266b...; routed 34 pins, digest 5939949b....
- Author's RESULT: `/scratch/jjyeung/orch_cd/evalx/events/20261113T1950Z_RESULT_done_layout_gates_and_hardware_evidence.md`.
- Comparator hardware record: `/scratch/jjyeung/orch_cd/evalx/work/milestone/COMPARATOR_HARDWARE.json` (sha256 6d0f213e...), which the decision code (`work/milestone/decision_fork.py`, accepted separately: `/scratch/jjyeung/orch_cd/leg_s1_review/CONFIRMATION_DECISION.md`) requires before an empirical read.

## Check, with file and line

1. **Pins and digests** of the new packet, both scopes.
2. **F5 (done record).** Admission parses the producer's native done record and binds object name, size and archive hash, through the producer's attestation, to the authorized artifact; four contiguous hashed part receipts must agree (names, offsets, sizes covering the archive exactly, no gap or overlap). A done record for another object, a wrong size, a missing or overlapping part, or a receipt whose hash disagrees must refuse; say which tests show each. The author states plainly that this does not download and rehash the payload; confirm that the wording in code and reports claims no more.
3. **F6 (layout gate).** Each direct read family has a CPU gate after binding and before generation that verifies the artifact's own frame layout (32 duplicated anchors), the bound request's protocol, the artifact identity and the verified-export marker; its receipt is required for completion and archived. A request with another layout (for example 32 spread frames) for the leg must refuse; f17 and the parent keep their own registered layouts. Check that the gate reads the layout from the artifact and not from a default.
4. **Low items of the last pass:** atomic, flushed replacement for `STATE.json` and `LAST_SAVE.json`; failed partial archives left intact and accounted; a `COMPLETE` and `FAILED` pair refused as success by whatever reads them; the four routed helper modules now pinned.
5. **The diff against the accepted packet:** anything beyond these items that can change which items are read, scoring, pairing, a denominator, the frame layout, the tool loop or the saves. The new pins (2 in direct, 5 in routed): what each is.
6. **Hardware record.** It binds the two Orchard comparator merges (parent and f17) by digest to job records showing the GPU type. Verify the digests against the merge files it names, that the GPU type comes from the jobs' own records and not from an assertion, and that the decision code refuses a merge with missing or different hardware evidence (run or read the relevant test). Reported reference values to check against the merges: parent 71.7964% primary with 40 answers continued under the bounded budget (36 + 4); f17 73.5564% primary with one output-cap hit.
7. **Tests:** run both suites from a private copy (CPU only) and report counts.

## Output

Write `/scratch/jjyeung/orch_cd/leg_s1_review/CONFIRMATION_MILESTONE_GATES.md`, at most 40 lines: one verdict line per scope (**ACCEPT**, **ACCEPT AFTER FIXES** or **REJECT**), one line per item with evidence, anything new, what you ran, what you did not check. For each scope whose verdict is ACCEPT, write a new receipt (do not edit the earlier ones): `/scratch/jjyeung/orch_cd/leg_s1_review/MILESTONE_DIRECT_RECEIPT_GATES.json` and `/scratch/jjyeung/orch_cd/leg_s1_review/MILESTONE_ROUTED_RECEIPT_GATES.json`, each `{"verdict": "ACCEPT", "reviewer": "<your model family and role>", "scope": "direct" or "routed", "code_pins_sha256": "<the digest you verified>", "packet_sha256": "<sha256 of the new packet>"}`. Return a summary of at most 10 lines.

## Bounds

Read-only everywhere except `/scratch/jjyeung/orch_cd/leg_s1_review/work_milestone_gates/` (private copies and tiny fixtures, at most 500 MB). No Git commands, no ssh, no network, no GPU, no agents, no deletion commands, and no names of deletion operations in any shell command text. Stay on `/scratch`; never read, search or list `/home` or `/data*`; no recursive search outside the folders named here. Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`.
