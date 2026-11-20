Run the helper locally after the independent routing review, with the reviewed `routing_selection.json` and the discovery job’s `db_bytes.json` in `work/build24m4d/lane_inputs/`:

```bash
L=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24c
nice -n 10 bash "$L/work/build24m4d/run.sh" "$L/out/arm_routing.py" \
  "$L/work/build24m4d/lane_inputs/routing_selection.json" \
  "$L/work/build24m4d/lane_inputs/db_bytes.json" \
  --output "$L/out/routing_armed"
```

The output directory must not exist. The helper writes only within L, uses the bundled scanners and unchanged tree, and makes no network call. The supplied runner sets CPU thread limits, the memory limit and a workspace-local temporary directory.

The selection must name `/tmp/q_22c714e1/p/q/selection`, a positive row count, a row-ID digest, and `inputs_pinned.routing_database`. The helper selects that database’s SHA256 and positive byte size from `db_bytes.json.files[].{sha256,size}`. It refuses missing or conflicting metadata. `regenerated_sha256` identifies the regenerated receipt; it is not treated as the database hash.

The authenticated selected routing-base receipt must name the same database and already belong to the kit’s staging inventory. The production receipt `ca0616db…` is bundled under `work/build24m4d/inputs/`. If the reviewed selection names another already-staged receipt, supply its local bytes with `--routing-base /absolute/path/to/receipt.json`; the helper verifies its exact hash.

The database must already exist on Orchard as `/project/community/jjyeung/okh7/x_22c714e1/u/<database-sha256>`. The helper lists this dependency in `already_staged`; it neither reads nor uploads the remote DB. The runtime planner and copier still authenticate its hash and size.

The helper emits:

- `out/routing_armed/kits/{q,n,n_go}/`: fresh, resealed routing-bound copies, all GO=false. The only GO=true template remains `out/kit_n_go`, which is not uploaded.
- `out/routing_armed/UPLOADS_ROUTING_ARMED.json` and `.list`, with stream root `out/routing_armed/upload/`: changed q/n files and the reviewed selection at `u/<selection-sha256>`. The DB bytes and n_go copy are excluded.
- `out/routing_armed/SCAN_{q,n,n_go}.json.gz` and `PLANNER_CLOSURE.json`: decoded scans and the authenticated routing receipt-to-database staging checks for each copy. Local checks establish inventory closure; the job verifies the remote bytes.

Apply `UPLOADS_24M4D.json` first: it diffs against 24m3 (`UPLOADS_24M3.json` applied on top of 24m2d). The armed delta then diffs against the 24m4d kits. Every manifest carries its applicable seals. `UPLOADS_24M4D_GO.json` applies only to its recorded unarmed n seal; it is not a GO delta for the armed kits. Arming grants neither upload nor launch permission, and the in-job identity-bound review remains required.

The end-to-end SQLite fixture, negative DB metadata/hash/size checks, missing-staging control, and actual mode-q planner results are recorded in `work/build24m4d/ARM_TESTS.json` and `ARM_MISSING_DB_TEST.json`. Production preparation and database availability were not tested here.
