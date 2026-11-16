# refute review-gate (#4), 2026-11-16, trinity-3-30
REFUTED as claimed.
- "7 second-readers found no new blocker" false: review_contracts2 RESULT 0024Z "ACCEPT AFTER FIXES. Two blocking defects" (H-1 box_v313.py:519, H-2 calculator.py:239); review_rows2 RESULT 2235Z "Fix (inherited, missed in round 1): 1,227 size -p1 rows".
- vsti2, d0r2, k1b3, k1b4 event folders are empty; no RESULT to support the claim.
- 25 min D0 read kit: process/NOTES.md line 21 "(off critical path; m100 ~13:55)".
- 45 min k1b3: includes the reader that had exited (29-45 min), already claimed by #6 orch-watch (synth/body_orch-watch.md line 9): double count.
- 50 min k1b4: confirmed a fix to launch failure FAILED 09:34 (anchors.members), no verdict finding bounds it -> fixcheck would say NEEDS_READER.
- 8 h contracts r1-r6: no source cited in record or notes.
- Replayed rounds touch admission/legality/labels -> protected list escalates them -> little saving.
- Zero-cost part (record item 2: drop "one more confirmation" from GO; reviewer stays alive 3 h) captures most of the real loss.
- Brief inputs (REF paths, INTERFACES orchkit-verdict-v1, skeleton) exist; executable.
