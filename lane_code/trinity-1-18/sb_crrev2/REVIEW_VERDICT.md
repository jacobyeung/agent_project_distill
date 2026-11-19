# Review verdict 2: sb_callrate after the review fixes

**ACCEPT WITH FINDINGS.** The builder fixed or documented all ten first-review findings, nothing that passed before regressed, and a `--summary` run with default flags is safe to paste at steps 400 and 600. My step-400/600 evidence comes from synthetic returns, because no real ones exist yet. The new findings are LOW or INFO and need no rerun. Fix new finding 1 or 2 before anyone pastes an `--allow-subset` or `--strata` run.

Evidence is in `scratch/`. `probes.sh` and `probes.out` hold the first review's 13 probes plus 19 new ones, with outputs in `probes/`. `dist10.py` and `distall.py` check traces without importing the reader or scorer. `recompute.out`, `unit_tests.txt` and `repro.txt` hold the reruns, and `steps/` holds the synthetic step-400/600 packages, which are A4 and rob/t2 copies with the step relabelled.

## First-review findings
1. Fixed. A partial `--summary` (t2, t2b, a partial B side, a partial step 400) exits 2 with empty stdout and a one-line reason on stderr. With `--allow-partial --allow-subset`, stdout opens with `PARTIAL:` and per-type SETS lines. Every row then shows n/expected (distance 100/150, room 20/36), and both marginals use the shared IDs.
2. Fixed. A4 vs B5 (t4) and step 400 vs B5 both exit 2 with "ID sets differ". With `--allow-subset`, room B MRA is 68.89 on the 36 shared IDs, where it was 64.40 on 134.
3. Fixed. The reader now reports three exclusive categories (follow_converted, copied_unconverted, other) plus conversion_failure. Usage now means follow_converted + copied_unconverted (see new finding 4).
4. Fixed. Room36 primary uses b1/read 0: B 0.116667, capped 29/36, delta 55.28 [38.82, 70.39]. A labelled secondary row prints b2/read 0 (55.83 [39.50, 70.50]).
5. Fixed. t3 reproduces t0 per item with the default `--original-root` and with `/nonexistent_prefix`. Only missing link targets relocate.
6. Fixed. Room rows name their source reads, so `dev-S1 [A=A4/read 0; B=b1/read 0]` and `[A=B5/read 0; B=b2/read 0]` no longer share a label.
7. Fixed. b1/read 1 answers 147/150, and 161821, 161827 and 161834 count as not_seen. The b2 room36 answer rate falls from 25.00 to 22.22 because room_scene0587_01 answers with a `<cover …>` tag.
8. Addressed. The summary drops trace-wording rows, the table and README call them diagnostics, and `--strata` takes external labels.
9. Partly open, with no effect today. A synthetic test now exercises `room_v314.parse_response`. `<area>` and mode-less `<ground>` still do not count as room calls, and `--b` still scores B with A's scorer, which the README states.
10. Fixed. All 56 tests pass in my separate copy, whose `in/` is a symlink. Fixtures now go to `scratch/tests` (see new finding 5).

## Regressions and recompute
- The first review's `recompute.py` gives byte-identical output today, and the new reader matches it. Camera deltas are -0.47, 0.67 and 0.00; distance is 22.00 [13.15, 29.61]; room134 is 57.84 [50.75, 64.68]. Room MRA is dev-S1 68.89/11.11 (57.78) and R0-dev 62.76/4.90 (57.86), and room36 is as in item 4 above.
- t1, t2e, t3, t3n and the synthetic s400 and s600 returns equal t0 per item. The authentication refusals (t1b, t2c, t2d, t2f, t3b, t3c, and step 400 labelled 600) still exit 2, and the camera rows equal the old summary.
- `reproduce.py`, rerun from my copy, gives 190 PASS, and its strata example equals the shipped one. The tar's SHA-256 (ba53f025…) matches, and all 14 of its files equal the working tree.

## Distance usage split
- I read 10 traces covering m, cm, ft and in and every category: 042674, 042715, 042717, 045546, 163095 and 256028 from A4, and 042581, 042584, 042632 and 042645 from b1/read 1. All 10 verdicts are right, including 042632, where 107.9 in is within 5% of 107.48.
- I reclassified all 300 items independently from the raw `gap` responses, and every item agrees. A4 gives 73/12/0 of 85 eligible and b1/read 1 gives 72/70/0 of 142, with conversion failure 12/50 and 70/100. All 10 called-but-ineligible items got `not seen` from `gap`.

## New findings
1. LOW: `--allow-subset` on complete but different sets reports success. t4_sub exits 0 with JSON status OK, and its room row reads `36/36 / 36/36` although B planned 134. Only the SETS banner shows the difference. Fix: give subset results their own status, such as SUBSET.
2. LOW: an incomplete `--strata` file yields a normal-looking summary. With 140 of 150 distance IDs labelled, stdout holds the full table and stderr is empty. Only the exit code (2), the JSON status (MISSING) and the `stratum=MISSING` rows show the gap. Missing population membership reports its reason only on stderr (code reading). Fix: print a MISSING banner on stdout, or refuse as for PARTIAL.
3. LOW: A4's own outcomes define the shipped strata example. A4's call rate is exactly 0% or 100% in all 19 strata, so its step-200 stratum call deltas (0 or -100) hold by construction. The labels say TRACE_A4 and the README warns, but those step-200 stratum rows should never be pasted.
4. INFO: "usage" has a new meaning. It now reads 100/100 at both steps, and the old 85.88/50.70 is now follow_converted. Relabel any usage row pasted before the fix.
5. INFO: `--allow-partial` alone always fails when one side is partial (t2_ap gives "ID sets differ"), so both flags are needed, as the README says. Test temp dirs pile up in `sb_callrate/scratch/tests` (73, never cleaned), and the 68 old ones remain in `tests/artifacts`. The tar excludes both.
6. INFO (pre-existing): the synthetic step-400/600 returns loaded after I edited the step in `READ_PLAN.json`, `EXPORT_PIN.json` and the journal bindings together. Authentication therefore rests on those three agreeing, because the reader never hashes `READ_PLAN.json` itself.
