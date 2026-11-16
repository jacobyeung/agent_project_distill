# Analysis review fixes are implemented and validated
- Script: `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/native_vs_direct.py`; sha256 `44468e7201200d611eddef7449ead57ccb7c3be32ed2230a2bc747801070c8d8`.
- Original: `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/native_vs_direct.orig.py`; sha256 `64ac19a6c91e361a7fa482d63d6a5629ef1ecccc6b7cb55ae5d0a09d9b726f4a`.
- Unified diff: `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/FIX_DIFF.patch`.
- Tests: 49 passed, no failures/errors/skips; `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/tests/RESULTS.json`; log `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/tests/full_validation.log`.
- Mutants: all 13 killed; source digest is recorded in `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/tests/MUTATION_RESULTS.json`.

| Mutant | Result | Evidence |
|---|---|---|
| M01_pairing_shift_direct | KILLED | `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/work/mutations/M01_pairing_shift_direct/out/tests/RESULTS.json` |
| M02_denominator_drop_no_answer | KILLED | `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/work/mutations/M02_denominator_drop_no_answer/out/tests/RESULTS.json` |
| M03_sensitivity_keeps_direct_refused | KILLED | `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/work/mutations/M03_sensitivity_keeps_direct_refused/out/tests/RESULTS.json` |
| M04_primary_drops_refused | KILLED | `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/work/mutations/M04_primary_drops_refused/out/tests/RESULTS.json` |
| M05_resample_items_not_rooms | KILLED | `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/work/mutations/M05_resample_items_not_rooms/out/tests/RESULTS.json` |
| M06_resample_captures_not_rooms | KILLED | `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/work/mutations/M06_resample_captures_not_rooms/out/tests/RESULTS.json` |
| M07_percentile_90 | KILLED | `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/work/mutations/M07_percentile_90/out/tests/RESULTS.json` |
| M08_unpaired_bootstrap | KILLED | `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/work/mutations/M08_unpaired_bootstrap/out/tests/RESULTS.json` |
| M09_bootstrap_room_weighted | KILLED | `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/work/mutations/M09_bootstrap_room_weighted/out/tests/RESULTS.json` |
| M10_refusal_direct_zeroed | KILLED | `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/work/mutations/M10_refusal_direct_zeroed/out/tests/RESULTS.json` |
| M11_callrate_all_items | KILLED | `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/work/mutations/M11_callrate_all_items/out/tests/RESULTS.json` |
| M12_label_answer_for_primary | KILLED | `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/work/mutations/M12_label_answer_for_primary/out/tests/RESULTS.json` |
| M13_drop_capped | KILLED | `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/work/mutations/M13_drop_capped/out/tests/RESULTS.json` |

- Fixture: 636 items, PLUMBING; `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/fixture/NATIVE_VS_DIRECT.json`. Runtime 26.004 seconds with 50000 draws; `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/fixture/RUNTIME.json`.
- Real pilot: 10 pairs, PLUMBING; `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/work/pilot/PILOT_CHECK.json` and `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/pilot/NATIVE_VS_DIRECT.json`.
- Independent bootstrap: 196 populated arm/cells; point estimates agree; maximum endpoint gap 0.636364 pp from independent random draws; `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/tests/INDEPENDENT_BOOTSTRAP.json`. These are plumbing checks, not model scores.
- Metre-only counts: distance 43, room 29; `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/fixture/NATIVE_VS_DIRECT.json`.
- Raw direct: `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/in/direct_raw/items_leg_m544_main.jsonl`; sha256 `c0cb8a6bd316327c66a94d5f227ac3af666125f6863258fefe6515cf8f99d661`.
- Raw direct: `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/in/direct_raw/items_leg_m544_camera.jsonl`; sha256 `8cedf7c631cfa8a7389ec122606885bfa34f85941cc444c283b7e86309177b38`.
- Decisions: parsed forced closes retain recorded scores; missing final answers require zero; capped and producer-error sensitivities are paired; claims are per type; `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/DECISIONS.md`.
- Artifact identity: native digests match the expected export; direct evidence is absent locally, so cross-arm identity is PARTIAL; `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/VALIDATION.json`.
- Not checked: real full-read performance, scorer execution, frame equality, weight bytes, job admission, independent room identities, and supplied training/parent/guard context; `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/VALIDATION.json`.
- The required sealed-guard fallback retains “pilot-era replay”; parent camera means are explicitly unsourced. See `/scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/RUN.md`. Orchestrator confirmation remains required before a real model claim.
