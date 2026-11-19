The 23 venue-381879 qids cannot pass N's mandatory BENCH filter. The exact N admitted-order hash remains MISSING.
This is a complete exclusion proof for those qids, but it does not close the entire data_rows_r2 record.

Evidence binds sealed build 20 `780ca7b446a578c83a1b1a398a8d54c0503a7cca26309bae6a1b60f85ef2a278` and config `5257a29705d1eb6a8c6cb2604eb7c6a3af74483438964921f084dcdc3864699d`.
Build 21 carried the inherited build-20 seal when inspected; its discovered capacity fixture is a different population.
The copied code files match their entries in TREE_SEAL.json; execution imports only workspace copies.

Code path (paths are relative to `work/code/`, with original sealed line numbers):
- `student_pilot/carrier_c1_run.py`, `prepare`, 464–505: load filters and pose mix; `prepare_exclusions`, 481–483, defers scene matches to the final filter.
- `student_pilot/c1_pose_mix.py`, `_row_selected`, 66–73, and `prepare`, 123–238: dense/frame-prefix selection, division validation, legacy exclusions, then source-index order.
- `student_pilot/carrier_c1_run.py`, `prepare`, 619–624: apply BENCH/dev scene exclusions to every stream, including pose.
- `student_pilot/s1_exclusions.py`, `Exclusions`, 42–128, `selection`, 191–224, and `apply`, 334–345: filter pose sources and write `pose_scene_order.json` while preserving order.

The pose receipt is `8957d119bfa6776efe776816675da6d0f610a6e8c336acd66c297f29cf4e7e0f`; its sources pin a2v3 `b32359ce256a567912d6436fac95dcab78bcef3bb2e1154cabdca57bacdc5320` and a3v2 `0b95850a2dec57ec6702ca72cd198eb5afdcdcdd5f711a76a878104e30ec3571`.
Source receipt `30612832` agrees with P's rc3 SHA256SUMS.txt; the a3v2 receipt is `1e7b491b`.
BENCH v2 is `3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970`; N's dev list is `a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5`.

The CPU scan covers all 66,934 a2v3 and 203,520 a3v2 projected rows (270,454 total).
All 23 target qids reject on BENCH alone: 12 on d3/41159526 and 11 on d3/41159521; no target matches dev or the reserve rule on its projection.
Each target token is independently minted from its capture and checked against BENCH membership and EVAL_ROOMS venue381879.
The independent scene census matches N's filter counts for both sources.
On the full projected sources, BENCH drops 5,039 / 22,160 rows and dev drops 5,618 / 13,440 rows, with zero overlap.
The 224,197 survivors form only a scene-filter upper bound; its native-array SHA256 is `15f2b4fe5959a4c3e1d708471a731f688946c610dc41bd44086fa49cc89a6a74`.
Its filename explicitly says `raw_scene_filter_upper_bound_order.txt`; no production preparation receipt is fabricated.

P's authenticated mix/admitted orders contain 229,924 / 194,987 rows and zero target qids in either order.
Thus the 23 were already absent before P's final scene filter; P's broad BENCH drop count is not their removal count.
Applying N's final scene rule to P's preselection gives 185,667 rows, SHA256 `e6325e792ae81614b10bdc3920d411ec073ff920ba93ff2352276a12314003d5`.
That conditional replay differs from P's order and cannot establish N's initial selection.
The build-21 capacity fixture admits 16,000 rows and joins to zero target qids, but its pose receipt is `d548daf8` and its databases differ from a2v3/a3v2.

Room-rule scope: BENCH physical groups and explicit capture tokens apply to pose (`s1_exclusions.py:74–104`); ScanNet room prefixes are also inferred.
The scene filter does not infer arbitrary ARKit capture-to-venue links. These two captures have explicit BENCH tokens, so their rejection needs no inferred mapping.
`carrier_c1_run.excluded_row:340–348` invokes the reserve rule; `Rows.row:1104–1128` rechecks it for r1_training.
The separate `r1_rooms.Rooms.admit` call is in routing `compose:53–90`; `r1_rooms.verify_audit/census:86–175` covers routing slices and VQA, not all pose rows.

MISSING: full raw `ap/f02f16ad/s/a2v3/rows.sqlite` and `ap/f02f16ad/s/a3v2/rows.sqlite`; exact production/recovery paths and receipt hashes are in POSEFAM.json.
MISSING: N-bound `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/469ddece/pose_scene_order.json` and its preparation receipt; the inherited output path alone is not authentication.
Scene projections omit the dense-row targets, frame-prefix paths, and full-row reserve fields. The first actual removal stage and exact N order therefore remain MISSING.
The copied preparation code proves a mandatory final rejection for every target even if an earlier stage would remove it.

Commands (run from `/scratch/jjyeung/orch_n30/sb_posefam`):
`python3 work/stage.py` snapshots the inputs and verifies each copied code hash against the seal.
`OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3 -B work/prove.py` produces every row count, qid join, order hash, filter census and missing-input result above.
`OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3 -B work/finish.py` checks the result and line limits, writes VALIDATION.json, and packages/verifies every archived member.
`sha256sum -c out/sb_posefam.tar.sha256` checks the deliverable archive; FILES.sha256 covers its members.
The archive contains the report, record paragraph, per-qid proof, copied source, input snapshots, commands, and explicitly scoped derived orders.
No borderline chronology sentence was retained. No BLOCKER.md was required: no target survives the mandatory filter.
