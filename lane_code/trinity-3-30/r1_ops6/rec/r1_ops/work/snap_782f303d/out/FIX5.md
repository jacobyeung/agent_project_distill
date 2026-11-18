Fix 5 delta against `/scratch/jjyeung/orch_n30/r1_ops/work/snap_a6b70ef2` (frozen config a6b70ef2).

Config identity: `782f303d81e300b1b24094863d6ce7d984690529f0e414474c3e693df87e19da`. Archive: `p_1130b378.tar`. SHA256: `42bbcbb218c982b4e33cc92c7be97f01359ae2e47cd20e387c0008edefc6b1cb`.

The full census checks 204,413 unchanged v7 rows. All 431 traced room rows are eligible. The room cell draws 1,720 rows over 1,000 steps (1.72/step), below the four-repeat cap of 1,724 draws. All one-line room rows and out-of-range-frame, missing-relation and numeric-think mutants are refused. See proof/ROOM_GRAMMAR.json and logs/tests.log.

The loader audit prints toward/away draw shares of facing, decoded back-answer share among away-hard draws (including back-left/back-right, with exact-back separately), cm/ft/in draws and eligible/drawn absolute-distance counts by scannetpp/, scannetppv2/, scannet and arkit prefix. Local routing counts are explicitly NOT_RUN/null; the production proof uses the same code on staged routing rows. Routing selection is unchanged.

Units remain unbound at zero dose and appear under absent_on_P. The local required-family check has no missing family; unavailable native camera populations remain NOT_RUN. Production CPU proof on Orchard, full RGB admission and independent review remain pending. All eight proof checks are exercised by the local proof fixture.

Draw breakdown: `{"away_hard": {"back_definition": "Decoded option contains the word back, including back-left and back-right; exact_back counts only back.", "back_draws": 2356, "back_share": 0.848397551314368, "draws": 2777, "exact_back_draws": 0, "exact_back_share": 0.0}, "facing": {"away": {"draws": 10838, "share_of_facing": 0.5964777105118327}, "toward": {"draws": 7332, "share_of_facing": 0.4035222894881673}}, "routing_absolute_distance": {"drawn": {"arkit": null, "scannet": null, "scannetpp/": null, "scannetppv2/": null, "unknown": null}, "eligible": {"arkit": null, "scannet": null, "scannetpp/": null, "scannetppv2/": null, "unknown": null}, "status": "NOT_RUN"}, "units": {"draws": {"cm": null, "ft": null, "in": null}, "status": "NOT_RUN"}}`.

Changed source/config files:

- `tools/admission_census.py`
- `tools/finalize.py`
- `tools/rebind.py`
- `tools/run_local_checks.py`
- `tools/selection_check.py`
- `tools/write_fix5.py`
- `tests/test_packet.py`
- `configs/diff_against_deployed.json`
- `configs/diff_against_h1_1.json`
- `configs/r1p.json`
- `work/tree/student_pilot/loader_audit.py`
- `work/tree/student_pilot/type_mix.py`
- `out/SAMPLER_REVIEW.patch`
- `out/DEPLOYMENT_REVIEW.patch`

Item 4 has not started; items 1–3 are delivered first.

Generated outputs bind the current identity: R1P_PACKET.md, REPORT.md, GATES.json, BINDING.json, MIX.md, SHA256SUMS and the operator archive. No Git, SSH, Orchard, GPU, deletion, full lane copy or write outside this lane was used. The requested snapshot delta is retained for review; packet prose describes current state.
