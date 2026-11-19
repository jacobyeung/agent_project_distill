# sb_rarev review of the sb_rowA held-out camera wording set (2026-11-19, trinity-1-18)

**Verdict: REJECT as delivered.** The 900 items are sound in meaning, schema, leakage and seeding, but the
package's scorer cannot measure call placement on 350 of the 450 reworded items, so a read would fail at merge
after spending its GPU time. Once the parser blocker (finding 1) is fixed, the set qualifies for ACCEPT WITH FINDINGS (2-6).
Reproduce with `scratch/check_all.py`, `leak.py`, `phrases.py` (system `python -B`) and `native_admit.py`, `score_rest.py`
(`/scratch/jjyeung/envs/p1cpu/bin/python -B`, CPU only). Paths below are relative to `out3/bases/b1/src`.

1. **Blocker: 17 of 24 held-out wordings fail the package's question parser.** `rows/expected_calls.py:10-14` accepts only
   "between frame(s) X and/to Y" or "from frame X to frame Y" and otherwise raises `camera_question_missing_explicit_frame_pair`.
   `h1eval/scorers.py:29` (`placement`, metric M1) calls it with no exception handling, inside `h1eval/runner.py:33` (`measure`), inside
   `h1eval/h10/merge.py:63`. The launcher journals outputs without scoring, so the GPU read completes and then the merge exits 2.
   I fed perfect stub outputs to `measure`. All 450 originals scored, but only 100 of 450 reworded items did: 17/150
   displacement, 56/150 rotation, 27/150 direction. Only displacement h02, rotation h01/h04/h05 and direction h02/h07 parse.
   HANDOFF step 4 says no question-parser relaxation is needed; that claim is false. `merge.py:40` pins the parser's SHA at launch,
   so the fix must land before the package is sealed. Preferred fix: have `placement` build the camera call from
   `display_frame_pair`. That reproduces the parsed call on all 450 camera originals, which I checked. It is a scoring change, so it
   needs one independent review plus a parity check on the 636 devs1_routed items. Rewriting the 17 wordings to say "from frame i to
   frame j" would copy the reserved training layout (`wordings.py:51,58,65`) and weaken the held-out contrast.
2. **The reserved training wordings have the same gap.** 80 of the 120 fail `expected_calls`. None of the 120 (and none of the 24
   held-out) match the generator's question-mode pattern "between frame i and frame j of 32" (`camera_rows.py:519-520`). The training-row
   build, now MISSING, needs a frame-binding path that does not parse the question.
3. **Meaning is preserved.** I read all 24 wordings and 66 instantiated pairs (22 per type, every wording at least twice). A script
   then checked all 450 pairs: the same frame pair with i before j, 32 frames, metres, left-positive (-180, 180], and an identical
   ordered option string (all 150 direction items use "A. backward; B. right; C. left; D. forward"). Labels, answers and clip fields are
   unchanged. **No direction wording changes which notion of direction is asked.** All eight keep "main / predominant / principal /
   dominant" plus "consistent / sustained", measured against the orientation at frame i. None says net, endpoint or final position.
   On items with two large displacement components, the gap between label and tool output therefore hits both twins alike.
   Advisories: every displacement wording says straight-line, net or magnitude, while the original "how far did the camera move" also
   reads as path length. That matches the move tool's endpoint distance (`camera_rows.py:276-280`), but it makes the reworded twin more
   explicit, so part of any twin gap may come from the clearer question rather than from wording robustness. Likewise, "yaw / heading /
   about the vertical axis" matches the tool's gravity-yaw (`camera_rows.py:283-284`) and is more specific than "signed camera
   rotation". The prompt appends options after the question (`tree/student_pilot/batches.py:109`), so both twins list the options
   twice; only the reworded inline copy carries letters. This is cosmetic.
4. **Schema passes.** In all 450 pairs, key sets and recursive value types are identical and only `id` and `question` differ. The
   originals equal the source items exactly. All 900 IDs are unique, and none collides with a source ID. The manifest digest matches.
   The 900 native task twins have unique IDs, and each differs from its `CAMERA_TASKS.jsonl` row (f59090ff…) only in `id` and
   `question`. **Torch is available on this node** (`/scratch/jjyeung/envs/p1cpu`, torch 2.11.0+cpu), so I ran the native loader
   that the builder recorded as NOT_RUN. `h1eval.items.load_manifest` admits the set (900 items, R0 found 0).
   `parity_adapter.map_items` with `tasks=[HELDOUT_NATIVE_TASKS.jsonl]` maps 900/900 items to 900 unique reader keys with frames staged.
   This needs `b/` ahead of `h1eval/reader_core` on `sys.path`, as the launcher sets it. `accuracy`, `benchmark` and `unit_factor`
   score all 900 items correctly.
5. **Leakage passes, with one advisory.** I recomputed similarity with a word-level normalisation: ASCII folding; punctuation, numbers and
   option lists removed; crude stemming; stopwords dropped. Measures were word edit distance, content-word Jaccard, bigram Jaccard and
   longest shared word run.
   - Against the 40 reserved wordings: minimum edit distance 0.61, maximum Jaccard 0.59, longest run 7 tokens (displacement h02,
     frame glue); the 8 unused candidates are similar. Against my own extraction from the same 58 dev/kit files (392 camera strings,
     13 forms) plus the generator templates: minimum edit distance 0.68, maximum Jaccard 0.41, longest run 4.
   - Closest pair: rotation h06 against the reserved "Report how much the camera turns about the vertical axis…" (shared
     "about the vertical axis", Jaccard 0.59). Read h06 per wording with that in mind, or swap it.
   - The direction wordings share the "main / predominant / dominant consistent" core with the training stems; meaning
     preservation forces this. Coverage gap: the legacy routing stream (`rows.sqlite`) is absent; the generator implies it uses the original template.
6. **The assignment is reproducible but lumpy.** I rebuilt the set in memory from the source file and `wordings.py`, and it
   reproduces `item_set_sha256`. The formula does not depend on Python's random generator. Items per wording range 16-22
   (displacement), 14-27 (rotation) and 13-25 (direction); chi-squared with 7 df is 1.4, 7.2 and 7.2, consistent with a uniform hash.
   The cells are small and uneven: direction h07 has no C answers, h02 has one, and displacement h06 is 15/19 ScanNet++. Paired twin
   deltas are unaffected, but comparisons across wordings are confounded, and intervals at n=13 are wide. Advisory: assign by hash rank
   within type, giving 18-19 items per wording, optionally stratified by answer and dataset.
7. **Side effect of this review.** My first parser test created `rows/__pycache__/` (3 `.pyc` files) in the b1 package. The
   directory is not a git tree, and `orchard_h10/build.py:33-35` skips `__pycache__` and `.pyc` files. I deleted nothing; the owner may remove it.
