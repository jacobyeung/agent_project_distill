C8 is DRAFT_NOT_ADMITTED. No whole-worker pass, seal, upload, or launch is claimed.
Code: `out/c8/code_c8.tar`, sha256 `d03de829ae52386f2d845400b2d423bdfdaa177ee6921ef4676d7906938359aa`.
Family: `out/c8/FAMILY_C8.json`, sha256 `3163e1aef6bcdbafe7843ccbc7c85d6666ed3deb4a42e5fd5cb2e308c3ab4f6c`.
Diff: `out/C8_DIFF_vs_pilot9.patch`, sha256 `03950bd46232152f1febdcfbaad318344841d6423f2f04512fbf3bdb7d16a08e`.
Core tests: 14 pass under system Python (`out/tests/core.log`); 14 numerical guard tests were not executed (`out/tests/test_guard.py`).
Pilot and full: 0 worker lines executed; production branch coverage is unavailable (`out/coverage/pilot/coverage.json`, `out/coverage/full/coverage.json`).
The conservative inventory has 6390 source lines not executed by either rehearsal or core tests (`out/coverage/UNEXECUTED.md`, `out/coverage/SUMMARY.json`).
Pins: 9 PASS, 37 N/E (`out/PIN_TABLE.md`, `out/PIN_AUDIT.json`).
Independent stdlib census: 84 real captures, 11 sealed refusals, 1 reviewed refusal: d3/41254810 (`out/GUARD_CENSUS.json`). The production guard wrapper was not executed.
The required Python target is inaccessible here. All streamed completion markers remain absent (`out/INPUT_WAIT_STOP.json`).
The local input monitor ended early; it did not reach its maximum wait. The governor and transfers were untouched (`out/INPUT_WAIT_STOP.json`).
The mask receipt has only a draft producer rebind; cache-bind has not run (`out/MASK_REBIND_STATUS.json`).
The operator must fill code-object generation and md5 after upload; both are PENDING_UPLOAD (`out/PACKAGE_STATUS.json`).
Open defaults and blockers: `out/DECISIONS.md`; required proofs and unvalidated harness limits: `out/DESIGN_RECORD_native_r2_c8_20261115.md`.
No GPU, network, Git, other-agent, official-item, or shared-storage write was performed.
