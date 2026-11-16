C8r is PACKAGED_FULL_VALIDATION_PENDING (`out/FINAL_RESULT.json`).
Code: `out/c8r/code_c8r.tar`, SHA256 `f4535bc015da4a6e7f0d99e6db17a39fd49aa8d78dcf0a47d0aa5241b507f134`.
Family: `out/c8r/FAMILY_C8R.json`, SHA256 `618e1b5298dde2c82738590ea23438b3923e8a5ae06174bf686644688e980b40`.
Diff against C8: `out/C8R_DIFF_vs_C8.patch`, SHA256 `4ee0c813df8d07cf15a498a24fc252d6957e701c88b50dbc353224f7703546cf`.
Diff against pilot9: `out/C8R_DIFF_vs_pilot9.patch`, SHA256 `53edc10421f80f1176559f8c72e11c1316b99526d8692e8e5061b0e226dd50af`.
Exact receipt: `out/c8r/sources/sj/orch_cd/evalx/work/milestone/orchard_native/MASK_CACHE_C8_BOUND.json`, SHA256 `3be02a82ed2983715db108fe0326dea59ccd1571bae3d6ae476c27074ba06f8e`.
Tests: 76 passed, no failures or errors (`out/tests/RESULT.json`, `out/tests/results.log`).
Pins: 15 PASS; 4 PASS-REHEARSAL; 27 ORCHARD-ONLY (`out/PIN_TABLE.md`, `out/PIN_AUDIT.json`).
The deterministic archive and all source/member pins match (`out/PACKAGE_VERIFICATION.json`).
All C8r changed executable lines are covered by tests (`out/PACKAGE_VERIFICATION.json`).
Coverage gate FAIL: 9 C8 changed lines and 26 full-worker statements remain unexecuted (`out/coverage/UNEXECUTED.json`).
The pilot review maps only identical C8 source lines; no C8r whole-worker pass is claimed (`out/coverage/UNEXECUTED.json`).
Namespace blocked before staging: bwrap could not create its route socket (`work/rh_pilot_01/RESULT.json`).
Pilot command: run the exact operator command in `out/rehearsal/RUNBOOK.md` with `--mode pilot --shards 1 --dest "$PWD/work/rh_pilot_operator"`.
Full command: run the exact operator command in `out/rehearsal/RUNBOOK.md` with `--mode full --shards 1 --dest "$PWD/work/rh_full_operator"`.
Sharded command: `--mode full --shards "$N" --dest "$PWD/work/rh_full_sharded"`; unsupported counts refuse before staging (`out/rehearsal/RUNBOOK.md`, `out/SHARDING.md`).
Coverage uses parallel filenames and combine with input preservation; no sharded serving merge occurred (`out/rehearsal/RUNBOOK.md`, `out/tests/RESULT.json`).
Defaults: independent verified return channels, bounded anonymous pool probe, exact mask bytes, read-only shared inputs, single-process serving (`out/DECISIONS.md`).
Durable return-proof sidecars carry generation and SHA256 evidence; cloud tests used an offline CLI (`out/tests/results.log`).
Owned bytes: 58340122; build cap: 4000000000 (`out/STORAGE.json`).
Code generation and MD5 remain PENDING_UPLOAD (`out/PACKAGE_STATUS.json`).
Not checked: live Orchard quota/write probe, real GCS credentials, GPU/runtime/base/export tensor checks, new production authority, and completed full rehearsal (`out/FINAL_RESULT.json`).
No network, remote session, GPU job, Git operation, other agent, or write outside this build was used.
