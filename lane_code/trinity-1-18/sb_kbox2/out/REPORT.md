The kit is BLOCKED: deployed StageOne matches 4/5 labelled-table choices (80%; required >=95%).
No full training pricing, rule selection, selector fitting, or held-out evaluation ran. Every decision bar is MISSING.
The ARKitScenes TV changes from table candidate tv:002 (four frames) to deployed tv:000 (five frames).
The deployed scale is 2.2971098979; the table scale is 2.7102517570. The adapter reproduces both ARKitScenes table feature vectors exactly under the table geometry.

Commands: `bash run.sh prepare.py`; `bash run.sh prepare_pinned.py`; `bash run.sh replay_check.py`; `bash run.sh diagnose_replay.py`.
Pricing/checks: `bash run.sh dryrun.py > out/box_ladder/dryrun.log 2>&1`; `bash run.sh -m unittest -v test_box_math`.
All means, paired bounds, denominators, diagnostics, and archive: `bash run.sh finalize.py`.
Dry run: 71.586 seconds; peak RSS 706.219 MiB; CPU-only, nice 10, eight numerical threads.
Replay check: 6.493 seconds / 446.574 MiB; diagnosis: 5.119 seconds / 366.836 MiB.
PRIMARY_296 pins 1,037 train distance rows / 192 rooms; raw-name tables cover 883 / 173 rooms. All primary train rasters exist.
The dry run prices 92 records on four distance rows in two training rooms. It cannot choose a rule.
Checks: stored-label S4 parity 4/4; copied-reader A0 row parity 4/4; single-frame fusion checks pass; GT fused answers 4/4; eight numerical and decision-boundary tests pass.
Every MRA below uses corrected labels. Paired bootstrap: item-weighted, physical rooms, 10,000 draws, seed 20261119.

| Dry arm | MRA | Delta vs A0 [paired 95%] | Delta vs A2 [paired 95%] |
|---|---:|---|---|
| A0_deployed | 85.00 | +0.00 [+0.00, +0.00] | -5.00 [-6.67, +0.00] |
| A2_gt_masks | 90.00 | +5.00 [+0.00, +6.67] | +0.00 [+0.00, +0.00] |
| A3_gt_fused_allspread | 82.50 | -2.50 [-10.00, +0.00] | -7.50 [-10.00, -6.67] |
| A3_gt_fused_trim | 92.50 | +7.50 [+0.00, +10.00] | +2.50 [+0.00, +3.33] |
| A3_gt_fused_vote2 | 95.00 | +10.00 [+0.00, +13.33] | +5.00 [+0.00, +6.67] |
| A3_gt_fused_vote2_best | 97.50 | +12.50 [+0.00, +16.67] | +7.50 [+0.00, +10.00] |
| A6_gtgeo_fused | 92.50 | +7.50 [-20.00, +16.67] | +2.50 [-20.00, +10.00] |
| A6_gtgeo_single | 87.50 | +2.50 [+0.00, +3.33] | -2.50 [-3.33, +0.00] |
| DRY_A4_gathered_allspread | 87.50 | +2.50 [-10.00, +6.67] | -2.50 [-10.00, +0.00] |
| DRY_A4_gathered_best1 | 85.00 | +0.00 [+0.00, +0.00] | -5.00 [-6.67, +0.00] |
| DRY_A4_gathered_trim | 90.00 | +5.00 [+0.00, +6.67] | +0.00 [+0.00, +0.00] |
| DRY_A4_gathered_vote2 | 87.50 | +2.50 [-10.00, +6.67] | -2.50 [-10.00, +0.00] |
| DRY_A4_gathered_vote2_best | 90.00 | +5.00 [-10.00, +10.00] | +0.00 [-10.00, +3.33] |
| DRY_A7_da3_allspread | 72.50 | -12.50 [-13.33, -10.00] | -17.50 [-20.00, -10.00] |
| DRY_A7_da3_best1 | 92.50 | +7.50 [+0.00, +10.00] | +2.50 [+0.00, +3.33] |
| DRY_A7_da3_trim | 95.00 | +10.00 [-10.00, +16.67] | +5.00 [-10.00, +10.00] |
| DRY_A7_da3_vote2 | 97.50 | +12.50 [+0.00, +16.67] | +7.50 [+0.00, +10.00] |
| DRY_A7_da3_vote2_best | 95.00 | +10.00 [+0.00, +13.33] | +5.00 [+0.00, +6.67] |
| DRY_A7_pi3x_allspread | 70.00 | -15.00 [-20.00, +0.00] | -20.00 [-26.67, +0.00] |
| DRY_A7_pi3x_best1 | 92.50 | +7.50 [-10.00, +13.33] | +2.50 [-10.00, +6.67] |
| DRY_A7_pi3x_trim | 92.50 | +7.50 [-20.00, +16.67] | +2.50 [-20.00, +10.00] |
| DRY_A7_pi3x_vote2 | 95.00 | +10.00 [+0.00, +13.33] | +5.00 [+0.00, +6.67] |
| DRY_A7_pi3x_vote2_best | 95.00 | +10.00 [+0.00, +13.33] | +5.00 [+0.00, +6.67] |
GT-geometry fusion increment (A6 fused minus A6 single): +5.00 [-20.00, +13.33]; this is distinct from either arm minus A2.
Dry gather precision: 21/25; unmatched seed objects: 1/5. Full diagnostics: DIAGNOSTICS_DRY.json.

| Decision bar | Verdict | Train / paired bounds / held-out |
|---|---|---|
| replace_box | MISSING | MISSING / MISSING / MISSING |
| fused_path | MISSING | MISSING / MISSING / MISSING |
| gather_safe | MISSING | MISSING / MISSING / MISSING |
| selector_worth | MISSING | MISSING / MISSING / MISSING |
| selector_adopt | MISSING | MISSING / MISSING / MISSING |
| size_screen | MISSING | MISSING / MISSING / MISSING |
| first_seen_screen | MISSING | MISSING / MISSING / MISSING |
| tower_challenger | MISSING | MISSING / MISSING / MISSING |

Deviations and limits:
- V2 was absent when checked; SPEC_APPLIED.md lists all five required corrections. F32/F32_fused aliases are MISSING from v1; no alias mapping was invented.
- Held-out is report-only. No early five-capture replay, held-out score gate, size gate, or external split was used.
- A1/A5 labels are MISSING because candidate IDs can denote changed members under GD; A8 fitting is deferred behind the parity gate.
- A4 and A7 dry outputs enumerate all fusion rules; no winner exists. The full coordinator remains unfinished behind the failed prerequisite.
- Size uses the exact capture/instance audit join and full extents; unknown conventions remain MISSING. Basket is unknown in the ScanNet++ dry capture.
- Gather seeds match only manifest-listed same-name GT instances; IoU ties use count, summed IoU, then instance ID. Unmatched seeds remain MISSING.
- The expected top-level tree is MISSING; the harness-resolved b04host3 tree is used read-only. Remote R1 source equality is MISSING because SSH is prohibited.
- Harness declarations are AST-loaded with workspace bindings; GTGeometry receives C=c2w for frame_count. Vendor bytes remain unchanged.
- Mixed input containers were hashed and train records filtered. No held-out capture, cached output, raster, or table was evaluated.
- No GPU, network, SSH, Git, tmux, process termination, external write, install, or deletion ran. Local tar transfer was omitted as required.
Edited files and exact line spans: box_ladder/EDITED_LINES.json; executable/source hashes: box_ladder/CODE_SHA256SUMS.
Input hashes accompany every output JSON and per-item record. Historical copied outputs are isolated in out/inherited and excluded from the archive.
Archive: out/sb_kbox2.tar; SHA256: out/sb_kbox2.tar.sha256. No rasters, tower caches, or inherited archive is included.
No borderline revision-history prose was kept.
