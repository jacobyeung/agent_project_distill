R0: MISSING / withheld-80: MISSING / BENCH v2: MISSING / dev-S1: MISSING / K1: MISSING; unresolved: MISSING (room audit stopped).

The required D0 v5 base and rows_a2 builder are missing. The task explicitly requires stopping when build inputs do not survive. No whole-store room-hit counts are certified.

The verified store contains 204,413 rows; SHA256 `210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443`.
The provenance-only partial map contains 2,569 aliases with source-file hashes, row indices, row IDs, raw-row hashes and explicit `provenance.canonical` witnesses. Conflicts: 0.
The 41,259-row alias test set yields 30,989 agreements, 0 disagreements and 10,270 missing witnesses; coverage is 75.1085%. Missing witnesses do not count as agreements.
Of 938 d1/d2 tokens in v7, 855 have explicit source-row witnesses (91.1514%).
The partial map resolves 114,730 of the 119,375 unresolved canonical rows; 4,645 remain unresolved. These are alias-coverage counts, not room-list results.
`ALIAS_SELFCHECK.json` contains up to 20 disagreement, missing-witness and unresolved examples. The source scan found zero provenance canonical fields in either the v2 or v3 store.

A pinned copy of the original rows_a2 alias map survives in another lane’s archive:
`/scratch/jjyeung/n30_mirror/b08_headrows/b08_partB_kit.tar!work/auth/alias_map.json`.
Its SHA256 is `488480ab4b7f352eba9c81e99313c8bfcc247e9cc463a11620be087a42f579cf` and it contains 3,603 entries.
It agrees exactly with 1,850 overlapping witnessed entries; 0 disagree. Even adding this copy leaves 2,433 canonical rows unresolved.
`RECOVERED_ARCHIVED_ALIAS_MAP.json` preserves this recovery separately. Archived-map entries without source-row witnesses were not promoted into the rebuilt map.

The missing D0 database is expected at:
`/scratch/jjyeung/n30_mirror/rows_rebuild3/out/rows/d0_v5/vqa/rows.sqlite`.
Its recorded original path is `/scratch/jjyeung/orch_n30/rows_rebuild3/out/rows/d0_v5/vqa/rows.sqlite`.
Its required SHA256 is `4af43b409969c360d530fde01c044358b6089702a0f5aa8055896276a94deb59`.
The missing builder is expected at `/scratch/jjyeung/n30_mirror/rows_a2/work/build_a2.py`.
Its required SHA256 is `89b2203f7257ef1a23d3fb4783b142e8b63c3174a47d8dfd8aa8650c2dcdef9b`.
Both are named by `rows_a2/a2_vqa_v3/BUILD_MANIFEST.json`. The mirror inventory and 74 top-level archive inventories contain neither required input as a direct member; nested archives were not exhaustively searched.

The surviving token function is `carrier_c1_routing.py:830` under build 17’s `work/tree_r1/student_pilot/`.
It uses `v + sha256(('rung1 scene ' + native_dataset + '/' + scene).encode())[:12]`, with ScanNet++ named `scannetppv2`. The fixed prefix is the only salt in that function.
`rows_a2/v4/vsti/code/sources.py:73` loads aliases; `generate_fceb45e6.py:148–161` copies the alias and canonical into each row. Its separate qid hash does not mint scene tokens.

Commands that produce the counts: `python work/inspect_sources.py`, then `python out/build_missing_report.py` from the workspace. JSON `inputs` records bind every source used by these outputs.
The first command scans source rows; the second reproduces build 17’s exact canonical method, verifies the store hash and baseline counts, and computes the self-check and coverage. It refuses the list audit.
Package command: `python out/package_outputs.py`. Verification command: `sha256sum out/sb_alias.tar`.
The archive contains the JSON outputs, report and scripts. Its report omits the final archive digest; the adjacent report records it to avoid a self-referential hash.
Archive SHA256: `c87fd7bb46e068a2720f02f6216d7b33b43787b8a5d2d7b60814696858ed2a33` (`out/sb_alias.tar`).
