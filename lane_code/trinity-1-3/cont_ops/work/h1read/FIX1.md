# Fix round 1 — local gate complete
All 87 candidate tests pass, including 53 ported readk tests and all four reviewer refute tests. The separate 53-test run and four-item runtime fixture pass. Two asset builds and two final seals produce identical hashes; all 146 checksum entries verify.

| Finding | Change file:line | Covering test |
|---|---|---|
| F1 | `kit/reader/x7.py:129,152` reuses the main cell and duplicates all 32 anchors and indices; evaluator layout code stays unpatched. | Refute layout test; `test_frame_loader_duplicates_exact_anchor_pixels_and_indices`; `tests/runtime_fixture.py`. |
| F2 | `h1pair.py:29,59` refuses unequal family/item membership with a nonzero CLI exit. | Both refute membership tests; `test_cli_membership_refusal_has_nonzero_exit_and_clear_message`. |
| F3 | `h1pair.py:52` restricts harm to main/r0dev. | Refute away test; `test_harm_is_scoped_to_main_and_extra_only`. |
| M1 | `tests/test_kit.py:59,207,230,264,285` ports intended pins, families, steps, runs and binding; `evidence/INTENDED_PORTS.md:1` is included in DIFF.md. | All 53 ported tests pass on the candidate; final-pin test passes after sealing. |
| M2 | `kit/launcher/orchard_launcher.py:186` uses a7; `evidence/FAMILY_ALIASES.json:1` stays local. | `test_bootstrap_and_payload_keep_alias_and_key_on_trinity`. |
| M3 | `kit/reader/x7.py:52` requires directory 0700 and files 0600; `UPLOAD_PLAN.md:4` specifies operator modes. | `test_asset_modes_refuse_before_hash_or_extract`; `test_successful_full_local_asset_staging`. |
| M4 | `tools/build_assets.py:27,31` salts room/frame/item IDs with the retained local random key and rebuilds both assets. | `test_ids_use_persistent_key_and_distinct_domains`; `test_pins_inventory_and_determinism`; `evidence/FIX1_DETERMINISM.json`; all 3,136 reserve frames verify. |
| M5 | `REPORT.md:50` records the stricter refusal/answer-cap scoring policy. | Existing numeric, option, refusal and cap tests pass; scorer behavior is unchanged in this fix. |

Asset tar SHA256: `2ad8c67c111d5f286aa96ea688efd5c88218e116a8c09ae1a9b4bc71be893a21` (797,685,760 bytes).
Item file SHA256: `1e57fc08a2b29c20c8a2061cdcd33f8ffdab922758157a955ee107167548f0f7` (5,728,183 bytes).
FINAL_PINS SHA256: `875f7730814a0b93b44326391fb3295c25f7e4da5028a1d888b0108c9fb97bb4`.
Evidence: `evidence/FIX1_TESTS.log`, `FIX1_READK_TESTS.log`, `FIX1_REFUTE.log`, `RUNTIME_FIXTURE.json`, `FIX1_RESERVE.json`, and `FIX1_SEAL_CHECK.json`.
`FIX1.md` and the post-seal verification receipts are excluded from FINAL_PINS to avoid circular hashes. Live GPU execution and remote submission remain untested.

## FIX1c
Rule: `20261116T2218Z_ORCH_RULING_r0dev_dup_qids.md`; all 2,169 rows retained, unique logical IDs, only the two registered second occurrences receive `#2`.
`tools/build_assets.py` salts logical IDs with the retained key; `tools/item_ids.py`, `unpack_return.py` and `h1pair.py` expose logical IDs and source provenance on Trinity.
Gate: all 91 tests (87 existing + 4 ID tests), separate 53 ported tests, 4 refute tests and the runtime fixture pass; two builds and two seals match.
Item SHA256: `1d8b29a7f7bb5c4e486f430b1128b9fa249de24ae7a3905b9bb0ccdd778c892b` (5,728,183 bytes).
Tar SHA256: `2ad8c67c111d5f286aa96ea688efd5c88218e116a8c09ae1a9b4bc71be893a21` (797,685,760 bytes; unchanged content and mtime).
FINAL_PINS SHA256: `c2bb6c9e0fdedec04a9dbd94f4afb7676ab04334cb008b9bf3b43be0f7af46ab`.
Evidence: `evidence/FIX1c_{TESTS,READK_TESTS,REFUTE}.log`, `FIX1c_IDS.json`, `FIX1c_DETERMINISM.json`, `FIX1c_SEAL_CHECK.json`; all 154 checksum entries verify.
