# sb_phfix: review sb_phrev's corrections applied to the phrase kit (CPU, report-level)

W1 remains the chosen eligible arm and passes both bars on the 1,012 decision rows: 60.7510 against A0's 56.9269, +3.8241 [2.1629, 5.6281]; safe rows +0.4751 [0, 1.2269] on 442. Every result is labeled "diagnostic pending orchestrator ruling on registration". The figures match the reviewer's to four decimals, and the 1,037-row figures stand beside them (W1 +3.7319 [2.0462, 5.4778]; safe +0.4605 [0, 1.2160] on 456). No score code, bar or policy changed: kit.py is byte-identical (5c75aa97...), and aggregate.py re-reads the copied work/caps2 and work/recall2 without recapturing.

1. Registration. BARS.json and DECISION.json record written_before_any_score = false, and the pre-score certification is gone. The new BARS.json `registration` block (written by registration.py) holds these facts, and the report states them for the reader to judge:
   - First spec, in/KIT_SPEC_mask_phrase.md: sha256 d35055c1c11245ff..., mtime 09:50:47Z. Same numeric bars, applied to P_cf.
   - Spec v2, in/v2/KIT_SPEC_mask_phrase.md: sha256 5f099b8314cb2199..., mtime 10:06:34Z (arrived 10:06:37Z). Same numeric bars, applied to the cross-fitted W arm.
   - The earliest score file is work/caps/arkitscenes__41048124.json.gz at 10:03:18.783Z: a v1 capture holding row predictions with labels. It predates the stale PER_ITEM.jsonl (10:11:28Z) that the review cited. The first aggregate, work/stale_v1_out/DECISION.json, dates from 10:11:27.615Z. BARS.json was written at 10:12:21Z (mtime 10:12:42.900Z).
   - In order: the first spec predates every score file, and v2's mtime falls between the first capture scores and the first aggregate.
   - registration.py asserts that every other BARS field equals the 150d16a2... version. The new sha256 is 3157ad3e46fc70f0...; the originals are kept in sb_mask_phrase/work/orig_out/.
2. W2. It is removed from shippable_passing (now ['W1'], from the eligible arms W1 and W2c). bars.W2.role and the report label it a tool-change diagnostic.
3. Wording. "W1 understates the alias called alone" now reads "W1 prices a deduplicated subset; the exact serving score is unverified (standalone rerun = part 2)", in the report and in DECISION.serving_score.
4. Withheld rooms. DECISION.population discloses 5 captures in 4 rooms, with 25 rows, 0 heater rows and 14 both-good rows.
   - Plain keys hold the 1,012-row decision population, fitted without the withheld captures; keys ending _1037 hold the all-row figures beside them. Exceptions: both_good_rows and worse_operand_table stay all-row figures, because part 2 and the design record read them.
   - No policy moves. PHRASE_SET.json is refit on 188 rooms and still maps heater -> radiator.
   - On the 1,012 rows: P0 56.93; W1 as above; W2c +1.12 [+0.04, +2.50], which fails phrase_worth.
5. Open until part 2: table/desk, chair/seat and bookshelf/shelf. On the 1,012-row fits the raw name beats the alias alone (33 vs 6 of 54 objects; 16 vs 8 of 32; 5 vs 1 of 10), but the IoU > 0.95 deduplication can't be told apart from a weaker alias.
   - Part 2's default pass skips these pairs. `sam3_pass.py pass --all-aliases` covers them with 2,004 calls instead of 1,540, about 1.15 GPU-h at the rate behind the 0.88 GPU-h estimate (hard stop 1.2).

Tests: 26/26 pass (out/TESTS.json). These are the 24 shipped tests and 2 new ones (the registration record, and the decision population recomputed from PER_ITEM). Of the shipped tests, test_bars_frozen_and_recorded is renamed test_bars_hash_recorded and now also checks the false flag, and both fold-choice tests now check both populations.
Part 2 suite (a compatibility check outside the gate): 12/14 pass. Both fixture tests look up pins by the copy's path, but the fixture pins the source-lane path. The pinned price.py hash equals the copy's (1a4574639fdf80e1), so this comes from the copy, not from a regression.
Other changes: run.sh, launch.sh and part2/launch_part2.sh used to cd into the source lane; they now cd into this copy.
Package: out/sb_phfix.tar (sha256 in out/sb_phfix.tar.sha256) holds this note, PROMPT.md and the rebuilt kit under sb_mask_phrase/. The kit's own out/sb_mask_phrase.tar is rebuilt as well (sha256 66a5e56055d0ecd6...).
