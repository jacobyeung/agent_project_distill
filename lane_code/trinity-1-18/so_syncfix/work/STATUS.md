Time: Thu Nov 19 18:17:24 UTC 2026
Status: DONE. All requested round-three fixes delivered in out/.
Preserved delivery: out_round3/; its payload checksum manifest still verifies. Preimage remains syncin, scanner f9460a5e3e23e5f2765e454824645d8970b333817518d626847a5e0cba46fabb.
Functional suites: Python 3.6.8, 83/83 in 75.539s; Python 3.12.13, 83/83 in 68.904s.
Before regressions: all 11 methods fail with 22 assertions on each interpreter. The rollback probe republishes stale bytes before the fix and preserves the current clone after safe disable.
Patch replay: four numbered patches, 38 files; tools-only patch, 7 files; byte-identical, zero fuzz/offsets, syntax OK on both interpreters.
Final sealed bundle: all 80 payload entries and bundle checksum verified; delivery audit 3/3 on each interpreter. Exact sealed-audit logs: work/tmp_fix3_sealed36.txt and work/tmp_fix3_sealed312.txt.
Bundle SHA256: 4a6d754942480eb990b1434c1477341ff33e486a0a3c37f775d61e0108b62de3  so_syncfix_bundle.tar.gz
Visible workspace apparent bytes: 1511086941; du excludes permission-restricted existing reviewer fixtures, as recorded in work/tmp_fix3_workspace_final_bytes.stderr. No fixtures were deleted or chmodded.
Decisions: disable retires stage before the flag while holding the lock, preserving activation if stage retirement fails. Rollback retains that lock, extracts only on scratch, verifies PREIMAGE, replaces complete tools with the driver last, and verifies installed PREIMAGE. Local legacy stage failures conservatively count because their messages omit rc; thresholds apply per node. Manual timeout overrides retain ordering-only enforcement, with margins explicitly documented.
Production installation, calibration, activation, first hourly run, and real OpenSSH checks remain owner work. No real SSH/Git, network download, GPU, paid API, live tool change, deletion, or stopping of another job occurred. Completed before the 2026-11-19T18:49:23Z deadline.
