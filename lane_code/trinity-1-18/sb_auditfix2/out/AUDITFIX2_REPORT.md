# Store room audit fixes: PASS

The CLI refuses non-canonical ScanNet ids and ARKit ids absent from the pinned visits table. It gathers all four canonical witness fields (row, provenance, ground_record, gt_authority), normalizes dataset synonyms, and refuses disagreements before resolving a room. Explicit witnesses cannot hide invalid native ids.

Run the commands below from `/scratch/jjyeung/orch_n30/sb_auditfix2`; `PY=/scratch/jjyeung/envs/p1cpu/bin/python`.

`$PY -s -B tests/test_store_room_audit.py > out/REGRESSION_RUN.log 2>&1` passed 16 tests with 0 failures and 0 errors. Results: `out/regression-2j6ixaba/TEST_RESULTS.json`.
The tests include the existing eight, all five reviewer examples (scene806_00, scene00806_00, arkitscenes/048458732, native conflicting witnesses, hashed conflicting witnesses), all six witness-field pairs, agreeing synonyms, and invalid ids masked by witnesses.

`$PY -s -B store_room_audit.py --store /scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite --tree inputs/tree_r1 --lists inputs/lists --out out/v7-fixed > out/V7_RUN.log 2>&1`

| List | Hits |
|---|---:|
| R0 | 0 |
| withheld-80 | 0 |
| BENCH v2 | 0 |
| dev-S1 | 0 |
| K1 | 4,959 |

The audit resolves all 204,413 rows with 0 unresolved rows or tokens. K1 tiers are A 110, B 4,770, C 79. Store SHA256: `210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443`.

`$PY -s -B tests/check_v7.py --audit out/v7-fixed/audit.json --out out/V7_FIXED_CHECK.json > out/V7_CHECK_RUN.log 2>&1` validates every persisted scene/room and every count using the selected tree.

`$PY -s -B tests/compare_alias2.py --audit out/v7-fixed/audit.json --out out/ALIAS2_COMPARISON.json > out/ALIAS2_COMPARISON_RUN.log 2>&1` independently compares all 204,413 source rows with the pinned sb_alias2 map, derives rooms from the pinned visits table, and checks every persisted column and list membership: 0 row mismatches. All marginal counts and 40 joint counts match sb_alias2. Coverage is A 189,498, B 11,842, C 3,073 across 1,659 rooms. This comparator does not import the CLI or call its room methods. The sb_alias2 report and map are preserved under `inputs/comparison/`.

Callers must read the current invocation's `audit.json` status and completeness; the README explains why exit codes alone are insufficient. PASS certifies resolution and may include list hits. The audit checks declared scene identities, not frame contents; imported tiers retain the pinned map's evidence scope.

The copied earlier failing run `out/regression-t0kpto4o/TEST_RESULTS.json` records 8 tests, 0 failures, 1 error, and test-file hash `be075c88ffaddeb9e6cc95d5661bb7142a8b492d83c12ffb94713e78ea71deeb`. This retained result is disclosed in the README and packaged as historical evidence; it does not validate the current tool. No files were deleted. This historical wording is retained because the task explicitly requires disclosure.

`$PY -s -B package.py` creates `out/sb_auditfix2.tar`, `out/sb_auditfix2.tar.sha256`, `out/PACKAGE_MANIFEST.json`, and `out/PACKAGE_CHECK.json`. The packager verifies every archive member against its recorded SHA256. `sha256sum -c out/sb_auditfix2.tar.sha256` checks the archive digest. The package includes current source, README, pinned inputs, reviewer evidence, successful tests, this report, and all v7 persisted row records; the source store remains external.

Every new JSON result records SHA256 hashes for its inputs. No required input is missing. All writes stayed in this workspace; execution used local CPU and disk, with no network, SSH, Git, GPU, process termination, or deletion.
