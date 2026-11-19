# Review of sb_posefam (pose-family exclusion proof for vehicle N): verdict

**ACCEPT WITH FINDINGS.** N's BENCH v2 filter rejects all 23 raw a2v3 rows on venue 381879, and I reproduce every count with my own code. "Admitted-order hash MISSING" is honest, but its stated reason is incomplete. The record text holds in substance; `RECORD_TEXT.md` here corrects the MISSING reason, names the earlier drop stage and adds the recovery locations.

Paths: T = `tree_rebuild10_w/w20/work/tree_r1/student_pilot` (all 934 files match seal 780ca7b4). My code is `notes/pfrev.py`, and its output is `notes/pfrev_out.json` (all input sha256 included). Run it with `OMP_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3 -B notes/pfrev.py`.

## Findings
1. **(Q1) The code path applies BENCH v2 to every pose row, through N's config.** The trace runs as follows.
   - `carrier_c1_run.prepare` (T:465) builds the filter only if the config names a scene list (`:477-479`) and applies it only if one was built (`:619-624`). The code does not force the filter.
   - N's three configs all bind BENCH v2 3119aa4a and dev a1869ae2 in final mode, with pose 8957d119: build 20 5257a297, n1fix2 8063ef04 and build 21 8c610a6e.
   - `c1_pose_mix.prepare` (`:131-238`) keeps rows that match the scene filter in `pose_mix_order` (`prepare_exclusions`, `carrier_c1_run:481-483`). `s1_exclusions.apply/selection` (`:334-346`, `:202-224`) then filters each mix source.
   - Before training, `prepared()` re-derives that selection and refuses any change (`carrier_c1_run:788-789`, `s1_exclusions.verify:349-376`). It also refuses a foreign BENCH pin (`:353-357`).
   - Posefam's trace omits the config guard, this re-verification, and two r1-mode steps (finding 5).
   - w21 is unsealed. Its tree differs from the seal in 9 files, all environment-variable renames (`STUDENT_*` to `Q_E*`); none is in the pose path, and all 27 pose-path files are identical.
   - Minor: `c1_pose_mix.prepare` starts at line 131, not 123.
2. **(Q2) My recomputation confirms all 23, by the BENCH v2 rung-1 token rule.**
   - I minted `v`+sha256('rung1 scene arkitscenes/<id>')[:12] myself: 41159526 gives `d3/vc6a4b809b958` (12 rows) and 41159521 gives `d3/vf3e2ed14c783` (11 rows).
   - Both tokens are in `rung1_tokens`, aligned with `scenes` (0 of 1,212 entries misaligned). BENCH `members` lists both captures under group venue381879 (VSI-Bench, ReVSI), and EVAL_ROOMS maps them to venue381879. No target matches dev.
   - The (qid, raw index, capture) set equals POSEFAM.json's, and it matches sb_recrev's 12/11 counts and example qids.
   - The venue's other captures (41159519, 41159525) have 0 rows, and a3v2 has 0 venue rows.
   - My rule reproduces the full census: BENCH/dev/overlap 5,039/5,618/0 on a2v3 and 22,160/13,440/0 on a3v2. The sealed `Exclusions` class, copied and seal-checked, agrees with my rule on all 270,454 rows.
3. **(Q2, new evidence) The projections are bound to the raw databases.** P's receipt 0664bb17 stores a census computed from the real rows. Restricted to P's mix indices, the projections reproduce its `indices_sha256`, `scene_ids_sha256`, distinct-scene count and row count for both sources (b32359ce, 0b95850a).
4. **(Q2) The first drop stage is derivable; posefam marks it MISSING.**
   - P used the same spec 8957d119, the same database b32359ce and the same `/data2/k7pd/` prefix.
   - Its a2v3 part records `count` 27,604, which equals the source-0 entries in `pose_mix_order` d8d33340, and `benchmark_rows_dropped` 0.
   - `c1_pose_mix.py` (aaf0d293) and `carrier_c1_sweep.py` (bd64b6a1) are byte-identical in P's seal b01ce449 and in T.
   - All 23 are absent from P's mix order, so each fails `_row_selected` (dense rows or frame prefix; which one stays unknown). N's identical code skips them at `c1_pose_mix:192`, and BENCH v2 is a second, independent barrier.
5. **(Q3) MISSING is honest, but the stated reason is incomplete.**
   - "Not recovered" implies an N order exists somewhere. N has not prepared, and its configs cannot. `r2_contract.preparation` (`:69-77`) calls `r2_scene_bindings.verify`, which loads `r2_scene_rebuild` (null; `pinned(None)` raises at `:205`). It also requires `r2_sampling`, which is absent under `r1_training`.
   - N's admitted order will be the reader-filtered `pose_order.json` from `r1_population.bind_prepared` (`:142-191`), a checked subsequence of `pose_scene_order.json` (`scene_receipt:195-214`). POSEFAM.json's MISSING entry names `pose_scene_order.json` instead.
   - The raw databases are absent only on Trinity. The attestation table posefam itself snapshotted (SOURCES_13.tsv rows 11-12) lists verified copies on Mind and GCS, but the MISSING entries name only Trinity paths.
6. **(Q3) The record text is correct and not overstated.** Its claims match the evidence, and the upper-bound order (224,197 = 56,277 + 167,920) is scoped correctly. What needs correction is the MISSING sentence (finding 5), plus the config condition (finding 1) and the first-drop stage (finding 4); see `RECORD_TEXT.md`.
7. **(Q4) The filter misses no pose row on the 146 frame-pool captures.**
   - All 146 capture tokens are BENCH v2 names. 144 captures carry 15,279 raw pose rows (5,039 a2v3, which is every a2v3 BENCH row, plus 10,240 a3v2), and every one matches BENCH. Per-capture counts equal FPJOIN's.
   - Room siblings (EVAL_ROOMS room members, plus ScanNet rescans _00 to _09) leave 0 survivors.
   - No other token family can slip past: sb_recrev resolved every pose row's scene to a rung-1 token (66,934/66,934 and 203,520/203,520).
8. **The package is intact.** `sb_posefam.tar` verifies against its sha256, the copied code matches the seal, the report has 48 lines and the record 10, and VALIDATION.json reads PASS_WITH_EXACT_N_ORDER_MISSING.
