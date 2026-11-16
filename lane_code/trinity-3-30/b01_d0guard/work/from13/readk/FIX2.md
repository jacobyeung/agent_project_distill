# Fix round 2
Authority: `/data2/jjyeung/agent_project_data/distill_design/D0_STOP_RULE_20261116.md`, amended items 1–3. All tests and binds run behind `tests/offline_guard.py`; publish/cloud paths are mocked.

| Clause | Code | Tests/evidence |
|---|---|---|
| Reads 100/200/400/600/800/final 1000 | `f1f2.py:15`, `:198`; `kit/launcher/orchard_launcher.py:146`, `:176`, `:380` | `test_cli_accepts_all_steps_and_prints_both_readings`, `test_prepared_bootstrap_entry`, twelve `FIX2_BIND_*.log` files |
| Step 100 reports metrics, verdict null, reason “step 100 gives no verdict” | `f1f2.py:101` | `test_step100_has_no_verdict` (F1 fails) |
| F1: seven types, upper bound <0 stops at 200/400/600/800; comparative count/size are information only | `f1f2.py:19`, `:107`, `:148` | `test_f1_upper_zero_and_just_negative_at_every_read`, `test_each_registered_f1_type_can_stop`, `test_f1_has_seven_types_and_extras_cannot_stop` |
| At 200, any away200 ≤ away544 stops; A must equal 38/20/6 | `f1f2.py:109`, `:155` | `test_step200_equal_one_level_stops_just_above_all_continues`, `test_baseline_544_must_be_38_20_6` |
| At 400/600/800, ≥2 strict declines and failing F2 stop; prev steps 200/400/600 and paired membership are required | `f1f2.py:114`, `:137` | `test_two_levels_below_with_f2_failing_stops`, `test_two_levels_below_with_f2_passing_continues`, `test_one_level_below_continues`, `test_two_levels_equal_continues`, all `test_prev_*` |
| F2: away lower bounds >54/40/36, alike ≤20%, toward upper bound ≥0 | `f1f2.py:159`, `:163`, `:165` | `test_f2_interval_and_alike_boundaries`, `test_alike_exactly_twenty_passes_above_fails`, `test_toward_interval_upper_zero_passes_negative_fails` |
| F2 alone never stops; point reading is information only; F3/F4 remain non-stopping | `f1f2.py:109`, `:115`, `:166`, `:179`, `:180`, `:189` | `test_step200_f2_failure_with_all_levels_above_continues`, `test_later_reads_f1_stops_independently_of_f2`, `test_point_reading_is_information_only` |
| Final leg has ended: FINAL, F2 PASS/FAIL, F1 and comparison to required prev 800 | `f1f2.py:103`, `:183`, `:186` | `test_final_export_gives_final_and_f2_decision`; F1 failure does not change FINAL |
| Every fired reason names types/levels and values; otherwise “no stop condition met”; --m100 removed | `f1f2.py:107`, `:112`, `:117`, `:120`, `:199` | `test_all_fired_rules_are_reported`, `test_step200_away_below_baseline_stops`, `check_later_facing` |

The cited config schedules final step 1000; the uploader names `gs://cmu-gpucloud-jjyeung/q8/8865619b/359fcc3c_m1000.tar` (four parts). `evidence/FINAL_EXPORT_SOURCE.txt` records source hashes, schedule fields and receipt naming; this is configured intent, not evidence of a completed upload.
Validation: 53 CPU tests in `evidence/FIX2_TESTS.log`; twelve binds at 600/800/1000, all four families, in `evidence/FIX2_BIND_*.log`. Every `kit/reader/` byte matches the snapshot (`evidence/FIX2_READER_CHECK.json`).
Updated superseded tests: `test_step100_has_no_verdict`, `test_cli_accepts_step400_and_prints_both_readings`, `test_step400_f2_alone_decides_and_reports_f1`, `test_point_reading_is_information_only`, `test_f2_fail_without_trend_stops`, `test_trend_extension`, `test_trend_strict_equalities_and_two_levels`. REVIEW.md maps renamed tests; the fixture supplies 38/20/6, and kit step coverage extends to all reads.
Old complete pins: `evidence/FIX2_OLD_PINS.json`; new complete pins: `evidence/FINAL_PINS.json`. Core SHA256 values follow:
| File | Old SHA256 | New SHA256 |
|---|---|---|
| `f1f2.py` | `b561041cb1007ed23d055eacfe81ed4fe0429158abf7ceedc0356f04f58dd9bb` | `15e66c8003f8afc888de5ea204e7262257c14ac18232b1d9490a52084554d116` |
| `kit/launcher/orchard_launcher.py` | `170e2faf803ecddc86748381dfca45aa73c0b6310b82f33079b5c94059144518` | `9068f83eb75168b7de8e4409bba01d8a12b8776d3bb5da08556827a955b745d3` |

`DIFF_FIX2.patch` covers changed files against snapshot SHA256 `34ccc385ec281ef27eb8e1153362255d4a81ac366f1343fedf08c6f5fcf10948`, excluding evidence/test_* and evidence/chain_*; it omits itself to avoid recursion. Live logs are captured at patch generation.
`DIFF_FIX1.patch` is reconstructed: ten code patches verify both transcript blob IDs; launcher/document edits are recovered separately. Unreconstructed generated evidence is named in its header and `evidence/FIX1_RECONSTRUCTION.json`.
Unverified: live Orchard export/upload completion, credentials/assets, GPU execution, PNG pixels, returns and timing. Unscheduled stop exports can use mstop aliases; the configured final read is 1000, and the strict receipt parser remains unchanged. No SSH, GPU, network, Git, deletion or Slurm command ran.
