# Store room audit: PASS

The CLI normalizes every list through the selected tree’s `Rooms.room`, persists every row’s scene and room, and refuses unresolved tokens by default.
It reports list, tier, stream, and family marginals plus joint counts; each JSON result records its input SHA256 hashes.

Run commands from `/scratch/jjyeung/orch_n30/sb_auditfix`; `PY=/scratch/jjyeung/envs/p1cpu/bin/python`.

`$PY -s tests/test_store_room_audit.py` passed 8 tests.
The synthetic audit plants 7 rows, including both ScanNet++ spellings in BENCH v2 and a row in each other list; every planted row hits its required list.
The unknown-token test refuses with exit 2 and prints 1 unresolved token across 2 rows.
The opt-in test exits 0 but marks its unresolved result INCOMPLETE and its counts as lower bounds.
The selected-tree test changes a copied Rooms method and verifies that both stored rooms and source hashes follow that tree.
Successful test outputs: `out/regression-7kq_r7r_/TEST_RESULTS.json`.

`$PY -s store_room_audit.py --store /scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite --tree /scratch/jjyeung/orch_n30/tree_rebuild10_w/w18/work/tree_r1 --lists inputs/lists --out out/v7`

| List | Hits |
|---|---:|
| R0 | 0 |
| withheld-80 | 0 |
| BENCH v2 | 0 |
| dev-S1 | 0 |
| K1 | 4,959 |

The command resolves all 204,413 rows with 0 unresolved tokens or rows. K1 tiers: A 110, B 4,770, C 79.
Store SHA256: `210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443`.
`out/v7/rows.sqlite` preserves every row; `out/v7/audit.json` records counts, source hashes, and the row-database hash.

`$PY -s tests/check_v7.py --audit out/v7/audit.json --out out/V7_CHECK.json` verifies every persisted scene/room and all marginal and joint counts.
ARKit venue labels use witnessed captures from the pinned visits file; missing visits fail explicitly.
The audit checks scene identity, not frame contents. Imported proof tiers rely on the pinned reviewed alias map; its original witness archives are not reopened.
No required input is missing. No Git, network, GPU, SSH, process termination, or external writes were used.

`$PY -s package.py` produces `out/sb_auditfix.tar`, `out/PACKAGE_MANIFEST.json`, and `out/sb_auditfix.tar.sha256`.
`sha256sum -c out/sb_auditfix.tar.sha256` checks the archive.
The archive includes code, README, pinned inputs, successful tests, this report, and all persisted v7 row records; the source store is external.
Borderline historical wording retained: none.
