# Fix round 1

All six review items are implemented. The authoritative F2 verdict follows TRACE_RULING 2.7.

| Item | Fix | Evidence |
|---|---|---|
| A1 | Bootstrap accepts `a2` and `build-integrity-v1`; preparation re-pins launcher bytes. | `test_prepared_bootstrap_entry` reaches mocked execution at 100/200/400 and rejects tampering; `test_failure_return_uses_mock_publisher` covers failure return. |
| A2 | Returns retain all families’ raw journals at ON16k/B2048/B4096; gzip level 6 and both size caps apply. | `test_return_retains_all_raw_journals` checks every archived byte. |
| A3 | Strict one-line bucketless object/bytes/SHA receipt; expected run and step; fixed bucket URI; four ordered parts; whole-tar size/hash before extraction. | `test_done_sample_and_strict_identity`, `test_wrong_done_refused_before_cloud_or_disk_reservation`, `test_ordered_cloud_stream_requires_whole_digest_before_stage`, and `test_digest_before_extraction`; uploader source in `evidence/UPLOADER_FORMAT.txt`. |
| B1 | Seven registered F1 types decide; relative count and relative object size are information only. | `test_f1_has_seven_types_and_extras_cannot_stop`; `test_each_registered_f1_type_can_stop`. |
| B2 | Lower-bound reading decides; point failures and alternate verdict print as information only. | `test_point_reading_is_information_only` checks disagreement at 60/46/42 and equality at constants. |
| B3 | Kit and CLI accept 400; F2 decides STOP/CONTINUE at 400, with F1 reported. | `test_step400_f2_alone_decides_and_reports_f1`, `test_cli_accepts_step400_and_prints_both_readings`, bootstrap entry and three step-400 binds. |
| Test guard | Every test entry denies real process creation and socket operations; execution boundaries use mocks. | `test_offline_guard_blocks_real_commands_and_network` includes bare/absolute gcloud and shell bypass attempts. |
| Pins | Final code, tests and review documents are re-pinned; fresh batches embed current launcher pins. | `test_final_pins_match`; `evidence/FINAL_PINS.json`. |

Validation: 40 tests pass in `evidence/FIX1_TESTS.log`. Eight binds pass in `evidence/FIX1_BIND_*.log`: all families at 100, main at 200, and main/away/forward at 400. Prompt inventories match accepted bytes.
No live publish, network, SSH, GPU, Git, deletion or Slurm command ran. Live milestone execution and its embedded artifact path remain unverified. `REVIEW.md` gives file:line references for each item.
