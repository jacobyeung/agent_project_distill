C8r is packaged; full validation remains pending.

Artifacts and hashes: `out/c8r/`, `out/PACKAGE_STATUS.json`. The archive reproduces byte-exactly (`out/PACKAGE_VERIFICATION.json`).

All 76 tests pass (`out/tests/RESULT.json`). Every C8r changed executable line is covered; 9 C8 changed lines and 26 full-worker statements remain unexecuted (`out/coverage/UNEXECUTED.json`). The coverage gate fails as required.

Pins: 15 PASS, 4 PASS-REHEARSAL, 27 ORCHARD-ONLY (`out/PIN_AUDIT.json`, `out/PIN_TABLE.md`).

The sandbox blocked bwrap before staging (`work/rh_pilot_01/RESULT.json`). The harness retains single-process serving and refuses unsupported sharding (`out/SHARDING.md`). Operator commands are in `out/rehearsal/RUNBOOK.md`.

Code generation and MD5 await upload; production authority, the new live return path, GPU execution, and completed full-mode evidence remain unchecked (`out/FINAL_RESULT.json`).
