# Review of sb_auditfix store room-audit CLI: ACCEPT WITH FINDINGS

The fix does what sb_alrev required: it maps list rooms through `Rooms.room`, loads `Rooms` from `--tree`, persists every row's scene and room, and refuses unresolved rows. Store v7 reproduces exactly. My own plants found two fail-open gaps (findings 3 and 4). Neither touches v7, but both should be closed before the CLI audits a store from another producer.

Evidence lives in this folder. All runs used `/scratch/jjyeung/envs/p1cpu/bin/python -s -B` with the w18 tree and `sb_auditfix/inputs/lists`. `plant_review.py` (294cfcdc) writes `plant_out.json` and `plant_run.log`; it computes expected rooms with its own minting and list code and calls the CLI once per store. `v7_compare.py` writes `v7_compare_out.json`. The rerun itself is in `v7_rerun/` and `v7_rerun.log`.

1. **My plants are caught: 11 hits and 7 refusals.** Eleven rows sit in one store, run once as JSONL and once as SQLite, and each hits its own list in both runs (exit 0). The alias forms are three hashed `d1`/`d2` tokens whose own witness field (`provenance`, `gt_authority`, `ground_record`) names a `scannetppv2/`, `scannetpp/` or rescan `_02` spelling. These tokens are absent from the alias map, so they resolve only through the row. The other alias form is a literal map key, `d1/scannet/scene0000_00`, which lands in BENCH v2 as tier B. The rows cover R0 (`d1` rescan `_05`, `scannetppv2` native), withheld-80, dev-S1 and K1 (ScanNet++ native, ScanNet rescan `_07`). The venue-id variants also hit: an unlisted sibling video, 41069178, in K1 venue381810; a hashed `d3` video in BENCH venue484545; and a native video in dev-S1 venue472640. Seven single-row stores each exit 2 with REFUSED:
   - a row whose scene is resolvable only through a frame path, with an unmapped `d2` token and a `scannetpp/<bench id>` path;
   - a frame-path-only row with no dataset or scene;
   - `scene=venue484545`;
   - `dataset=ScanNet`;
   - a `d1` prefix on a ScanNet++ token;
   - R0's nonstandard label `scannetpp/511061232`;
   - an unmapped `d3` token.

   With `--allow-unresolved`, the frame-path row exits 0 and is marked INCOMPLETE.
2. **The v7 rerun matches sb_alias2 on every list and every row.** The rerun takes 13 s and finds R0 0, withheld-80 0, BENCH v2 0, dev-S1 0 and K1 4,959, with 0 unresolved of 204,413. K1 splits into tiers A 110, B 4,770 and C 79. Against `sb_alias2/out/ROOM_AUDIT_TIERED.json`, the hits match per list, by tier, stream and family, and in all 40 joint counts. Coverage (A 189,498, B 11,842, C 3,073) and the 1,659 rooms also match. Per row, all 204,413 rows have non-null scene and room. Each row matches the independent `sb_alrev/token_rooms.json` on scene, room and tier, and my own recount of list membership from the persisted rooms agrees for every row. The rows also equal the builder's `out/v7/rows.sqlite` in content.
3. **Gap: non-canonical native ids resolve to phantom rooms and pass.** `normalize_scene` accepts `scene\d+_\d+` and any `\d+`, and `Rooms.room` then derives a room that no list holds. Three single-row stores show this, each exiting 0 with PASS and no hit:
   - `scannet/scene806_00` becomes `scannet/scene806`, although `scannet/scene0806` is in R0.
   - `scene00806_00` behaves the same way.
   - `arkitscenes/048458732` becomes `capture048458732`, although video 48458732 belongs to BENCH venue484545.

   Fix: require `scene\d{4}_\d{2}`, and require every ARKit id to appear in the pinned visits table. This costs nothing on v7: all 54,020 ARKit rows are in the visits table, and no ScanNet id breaks the 4/2-digit form.
4. **Gap: a second, conflicting witness is ignored.** `resolve` checks only the first non-empty `canonical` in the order `Rooms.canonical` reads them (row, provenance, ground_record, gt_authority). A row with `provenance.canonical=scannet/scene0150_00` and `ground_record.canonical=scannet/scene0806_00` (R0) passes with no hit, whether its token is native or hashed. The README's claim that "conflicting row witnesses remain unresolved" holds only for a conflict between the witness and the token or the map. Fix: gather all four fields and refuse on disagreement. v7 is unaffected, because its only witness field is `provenance` (43,779 rows) and no row carries two.
5. **No row escapes as unresolved without failing the audit.** Every row is counted once, as either resolved or unresolved. `complete` is true only when the unresolved count is 0, and every unresolved plant exited 2. The escapes I found are false resolutions (findings 3 and 4), plus frame paths that contradict a row's resolvable scene. That last case is out of scope by the README: `scannet/scene0150_00` with a frame path naming `scene0704_00` passes. Exit 2 also covers CLI misuse, so callers should read `audit.json` `status`, not just the exit code.
6. **Every report claim is backed by a file.**
   - Tests: `out/regression-7kq_r7r_/TEST_RESULTS.json` reports 8 run, 0 failures, 0 errors. It pins the current tool (0a3af5d8) and test file (ccb9ad3a). My copy in `fixcopy/` also passes 8/8.
   - Archive: `sb_auditfix.tar` matches its sha256 sidecar (1d6badbe…), and all 57 entries in `PACKAGE_MANIFEST.json` match the tar members. The tar's 58 files equal the workspace files byte for byte.
   - Store: `out/v7/audit.json` pins the v7 store at 210b2534.

   Three minor points remain. An earlier failing run, `out/regression-t0kpto4o` (1 error, old test file be075c88, same tool bytes), is left unmentioned and is not in the tar. `check_v7.py` recomputes rooms with the tool's own `prepare`, so it is not an independent check; finding 2 is. The `rows.sqlite` file hash depends on the run (builder 7f26fd01, mine ed373bed, identical rows), because its metadata embeds the command and paths. A rerun therefore has to compare rows, not the file hash.
