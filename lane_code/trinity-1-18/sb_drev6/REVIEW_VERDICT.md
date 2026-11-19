# REVIEW_VERDICT: sb_rowD6 direction half-turn twins (reviewer sb_drev6, trinity-1-18, 2026-11-19)

**Verdict: REJECT.** One BLOCKER against the order's design goal. Every correctness check passes, so re-rendering the question text alone clears it.
Reviewed: out/sb_rowD6.tar sha256 265b03ac653b…7376 (recomputed; members match out/), NEW_ROWS.jsonl 8135c8d9…, SOURCE_MAP.jsonl 5a0f2f95…, store v7 210b2534… (recomputed), tree seal 8ea1fe6b.
Method: my own scripts here (rev_census.py, rev_verify.py, rev_balance.py, rev_claims.py, rev_wording.py); none imports sb_rowD* code. Evidence: work/VERIFY_REVIEW.json, work/BALANCE_REVIEW.json, work/WORDING_REVIEW.json, work/READ40.md.

## Findings
1. **BLOCKER: the clause can be predicted without reading it in the teaching subset.** All 8,000 new questions use a template no source uses ("At the X, face toward/away from the Y. Choose the direction of the Z relative to that heading."), while the 8,000 controls keep their v7 wording.
   Each feature alone is 50/50 by clause (opening, template, names, label, letter). Combined, they leak: template plus "all three names in the 73-name Seen-family set" predicts the clause for 95.95% of the 16,000 teaching rows.
   Within the 8,000 old-wording rows, the clause-masked wording alone predicts it for 93.1%: of 43 wordings, only one carries both clauses.
   In benchmark-style wording, Step-1-family items stay 100% toward (4,000 here; 49,901 in v7). Their only away examples use the new wording, so the shortcut the order targets ("neither opening nor name set predicts the clause") survives in the wording the evaluation uses.
   Fix: render each away twin by substituting the clause in the source's own question (the rows_r1 codeA/build_away.py pattern), then rerun the wording filter and validators. Answers, options, frames and traces stay as built. Rendered the same way, the (b) twins become copies of their v7 mates (finding 4), so their quota is better spent on more (a) rows or on new-template controls for the opposite clause.
2. **minor: the room PASS rests on sb_rowD2's tiered alias map, not N's.** I ran N's `Rooms` unchanged on build19's room_authority (alias pin c47c5fcd). It marks 7,901 of 8,000 new rows, and the same 7,901 sources, `unresolved` (scene ids such as d2/vbfd96742c82d), and `Rooms.admit` refuses unresolved rows; only 99 resolve.
   Under sb_rowD2's TIERED_ALIAS_MAP, all 16,000 rows resolve, rooms match SOURCE_MAP, and there are 0 hits on K1, R0, withheld-80 (634820b4), dev-S1 (969cdb56) or BENCH v2 (3119aa4a).
   REPORT.md says "All five room exclusions apply" without naming the substituted alias map. Binding must carry that map.
3. **minor: the remove lists come from N's build17 config (`w19/work/build17/inputs/config.json`), not build19's, which ships the sealed tree.** build19 adds w18/work/build18/inputs/u.json (2,637 keys, N's V7_K1_LIST). u_union (4,959 keys) contains all 2,637, so coverage is equal.
   With build19's list plus u_union, 0 new rows, 0 sources and 0 lineage keys match. `check_rows` admits 8,000/8,000 in each population, also with N's dev/benchmark scene filter. Provenance should cite build19.
4. **minor: every (b) toward twin re-templates an existing v7 row.** Each of the 4,000 has exactly one v7 Seen/toward mate with the same scene, frames, objects, options and answer letter, and shares its pair_id.
   So (b) adds new wording to existing toward items, not new toward geometry, and doubles the weight of those 4,000 items. REPORT.md says only that each twin "matches its stored toward mate".
5. **minor: VERIFY.json inside the tar still says manual_review "PENDING".** CHECKS.json (PASS, binding_ready true) and READ60_REVIEW.json supersede it. Separately, v7 rows carry no candidate_id, so "disjoint from v7" holds trivially.

## Checks that pass (all 8,000 new rows unless stated)
- (1) Truth. I recomputed 300 random rows (seed 20261119), then all 8,000: source label, then my half-turn table, then exactly one option letter, which equals the new answer.
  Options are byte-identical to the source and the option map is a bijection. I also derived each label from the source trace's relation phrase (6 phrases): the source answer agrees 8,000/8,000 and the new label 8,000/8,000. Each (b) label equals its stored v7 toward mate's.
- (2) Convention. derivgen_v7 calculator.py (sealed) defines u = F−S and v = Q−S, with left iff cross > 0 and front iff dot > 0, and refuses |θ| in {0, 90, 135, 180}. A half turn sends u to −u, which negates dot and cross.
  So each hard quadrant maps to its opposite (front-left↔back-right, front-right↔back-left), and easy left↔right is the swap. The hard question text states the same Cartesian convention.
  The stored v7 answers agree: 0 literal-flip disagreements on the 5,846 easy/hard opposite pairs and on 12,023 more Seen toward/away pairs. All 1,274 opposite-pair and 2,592 away-pair disagreements are medium; no medium row is emitted.
- (3) Trace, checked on all 8,000 and read in full on 40. Away rows copy the source's Step 2 line verbatim and state the half turn as its own "Step 3" line.
  Toward rows copy the Seen line, restate the source's "would be" relation and say "I keep that heading". No trace adds numbers or geometry. Question roles match the source: 7,999 by parser, and the remaining one by hand.
- (4) Kit. On 8,000 new rows and 8,000 sources, r2_contract.validate, trace_grammar.validate_row, r2_grammar.validate_direct and carrier_c1_routing.direct_row pass. I imported the real module with torch stubbed, and every imported file matches the seal.
  qids are unique and absent from v7. candidate_identity (kit formula) reproduces all 8,000 candidate_ids, and they are unique. Each source is used once.
  The field diff touches only qid, pool, answer, target, facing and student_input.question, and adds candidate_id, label_row_keys and provenance.sb_rowD6.
  Wording filter: 5,767 distinct questions against 927 wordings, none within 0.10.
- (5) Marginals. Each opening × clause cell has 4,000 rows; labels are 1,440/1,440 for easy and 280 per quadrant for hard in every cell. Clause accuracy from answer letter is 0.505, from dataset 0.50, and from opening plus label 0.50.
- (6) Claims backed. I confirmed: 29,124 medium rows refused, 2,665 medium pairs, 3,026 census exclusions (all via u_union), the 298-row Seen/away hard front-right cell, and the name counts 1,026, 953 and 73.
