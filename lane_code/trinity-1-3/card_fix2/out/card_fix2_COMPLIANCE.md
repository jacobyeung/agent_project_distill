# card_fix2 compliance list: where card v3 and the record implement each amendment (2026-11-17)
`C:n` = line n of `events/next_leg/R1_CARD_v3.md` (sha256 c83f0dc5); `D:n` = line n of `distill_design/NEXT_LEG_DECISION_20261117.md` (sha256 dab4486e). Evidence: `events/next_leg/card_fix_a3_evidence.tgz` (47b1b97f), `events/next_leg/card_fix2_b5_evidence.tgz` (9278860b).

## Adjudication 2 (binding)
- **B1** estimates, nominal bound, evidence by sha, 0.186 withdrawn: C:2 (every probability is a conditional simulation estimate), C:24 (nominal 0.025 + 0.025, 0.00625 + 0.00625, 0.0875 over four looks), C:25-26 ("estimated"), C:33 (evidence sha256); D:81, D:93. The 0.186 figure appears in neither file.
- **B2** object size protected under H1, not a gate; toward-facing and relative size protected, HOLD then STOP: C:19, C:20; D:73, D:76. The gate tables hold no size row (C:36-42; D:99-105).
- **B3** VSTI gate with the type clause; unit gate over all 107 items; each gate read once, once more only after a HOLD: C:38, C:40, C:34; D:101, D:103, D:97, D:109.
- **B4** baselines bind the first read, not the launch; registered by sha256; a missing baseline is HOLD: C:7, C:4 (launch waits for no baseline); D:112, D:202.
- **B5** a population under 60 is a mark; the 49 twins print; the facing gate is the 150 away twins; each gate states its minimum detectable improvement: C:34, C:39, column MDI of C:36-42; D:97, D:101-105. Computed: facing +3.9 to +8.9 points (step 544's paired room distribution); unit and recovery on the own arm's read, registered values from the tower-arm read; VSTI and room from their baseline reads, with a planning value for VSTI.
- **B6** recovery rows not a hard requirement, P may carry the leg; capped reads at most 5 of 150 on the claimed arm at every boundary, by room bootstrap; recovery rows enter with N's continuation proof; gate only at 60 or more status reads, else the mark: C:20, C:41, C:61, C:4; D:77, D:104, D:250.
- **B7** unit rows required from launch in faithful form; P binds the slice whose answers equal the label; a unit under 100 eligible rows is named missing: C:62, C:65, C:40, C:4; D:249, D:244, D:201. Slot UNIT-P is filled from `events/rows_r1/20261117T1539Z_RESULT_units_p_slice.md`: 1,224 rows (ft 1,130, in 94, cm 0), cell 2.87, inches and centimetres named missing on P.
- **B8** room call-rate marks by bootstrap over physical rooms; ceiling exactly 4 x eligible / 1,000 (1.876 at 469 rows): C:42, C:58, C:49; D:105, D:107, D:239.
- **B9** spending rule, step-400 stop at about 83 H100-hours, a restart needs a new card: C:45, C:47; D:109, D:114, D:135.
- **B10** five launch gates; N takes over only at a boundary where its continuation proof has passed: C:4; D:202, D:258, D:15.

## Adjudication 1
- **A1** official reads report-only, no routing rule on a benchmark item: C:2, C:47; D:212, D:114.
- **A2** only traced room rows; room programs removed: C:58; D:239, D:253, D:107.
- **A3** family-wise harm rule on dev-S1, mean rule, R0-dev stops nothing alone, one decision per boundary, false stop and power stated: C:18-19, C:24-28; D:70, D:73-74, D:81-87, D:93.
- **A4** one efficacy gate per repair, paired and room-aware, denominators stated, every boundary priced: C:34-42, C:68-73; D:97-105, D:134-138.
- **A5** marks recalibrated: 33 of 150 = 22.0%, SE 3.4; room mark on 36 + 98 items; unit baseline recounted on unperturbed reads (22 of 107, exact on the own arm): C:40, C:41, C:42; D:103, D:104, D:105.
- **A6** camera types 47.2 / 75.3 / 42.7 against 82.3 / 94.7 / 75.7, unpaired, G3T serves: D:34 (the card carries no camera comparison); the paired join is the tower-arm baseline, C:7, D:112.
- **A7** S2 off at launch, every weight from step 544: C:10; D:116-117.
- **A8** size family follows lane size_diag's verdict: C:55, C:66; D:254, D:231.
- **A9** effects as upside scenarios with no predictive interval: C:77; D:141.
- **A10** each cell at most 4 x eligible / 1,000; VSTI doses per type; camera-object absolute distance excluded: C:49, C:57, C:59; D:225, D:248, D:240, D:252.
- **A11** no GO without the loader audit inside the proof: C:4; D:201.
- **A12** pins per boundary; exposure per arm, rooms apart from exact items: C:79; D:258.

## Rulings and notes applied with them
- ORCH_RULING_card_v2 item 3, pooled R0-dev rule with its validity conditions: C:8; D:113. Item 4, unit cell from the faithful slice of all 10,945 rows: C:62, D:244, D:249. Items 5 and 6, vehicles across boundaries and the selector pin: C:79; D:258.
- Store v7's review (`events/rows_r1/REVIEW_VERDICT_V7.md`, ADMIT WITH CONDITIONS, landed 15:50Z): C1, ReVSI's away wording disclosed as a training template with no transfer claim: C:16, D:69. C2, contamination flag on any K1 held-out number: C:79, D:258. C3, room traces locate but do not derive: the orchestrator's to accept, named at C:81 and D:253.
- ORCH NOTE 1523Z, slot SIZE-V = verdict (b), cell 0, split by metric and imperial items, what H1 does with a drift of 0 to -6: C:55, C:66, C:20, C:29; D:254, D:95.

## Readings the amendments left open (lane card_fix2's choice; the orchestrator confirms or strikes)
1. B6 names no consequence and no test for "at most 5 of 150 ... by room bootstrap". Card: a count above 5 is a HOLD, a second one a STOP; the count decides and its room-bootstrap interval is printed (C:20, D:77). The other reading, a breach only when that interval lies wholly above 5, would let counts of about 6 to 11 pass.
2. B6 and B7 remove recovery from the definition of a passing boundary. Card: a passing boundary is a PASS with the unit gate passed (C:44, D:109).
3. B3 gives each gate one read and one more after a HOLD. Card: the room gate's 5% call-rate bound at E + 400 is a printed mark, not a third read (C:42, D:105).
