Run the helper after n_review1c passes task A. Copy the selection SHA256 and `regenerated_sha256` from that reviewer's RESULT, and point `REVIEW_VERDICT` to the same RESULT file. These values must come from the independent review.

```bash
L=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24e
: "${REVIEWED_SELECTION_SHA256:?Set this to the selection SHA256 in n_review1c task-A RESULT}"
: "${REVIEWED_REGENERATED_SHA256:?Set this to regenerated_sha256 in that RESULT}"
: "${REVIEW_VERDICT:?Set this to the absolute path of that RESULT file}"
nice -n 10 bash "$L/work/build24m4f/run.sh" "$L/out/arm_routing.py" \
  "$L/work/build24m4d/lane_inputs/routing_selection.json" \
  "$L/work/build24m4d/lane_inputs/db_bytes.json" \
  --reviewed-selection-sha256 "$REVIEWED_SELECTION_SHA256" \
  --reviewed-regenerated-sha256 "$REVIEWED_REGENERATED_SHA256" \
  --review-verdict "$REVIEW_VERDICT" \
  --output "$L/out/routing_armed"
```

The output directory must not exist and must lie within L. The runner limits CPU threads and memory and uses a workspace-local temporary directory. If the selection names another already-staged routing-base receipt, append `--routing-base /absolute/path/to/receipt.json`; its exact hash must match the selection.

Both reviewed hashes are required 64-digit hexadecimal values. The RESULT text must contain both complete hashes and the word PASS. Before creating outputs, the helper checks the selection file against its reviewed hash, checks its `regenerated_sha256` against the reviewed regenerated hash, and requires that hash to equal `inputs_pinned.routing_database.sha256` and the matching SHA256 in `db_bytes.json.files[]`. The DB record must have one consistent positive integer size. Changed row counts or row-ID digests change the selection hash and refuse.

All existing selection shape, logical path, routing-base authentication, kit seal, staging and size checks remain. The selection must name `/tmp/q_22c714e1/p/q/selection`. The selected routing-base receipt must authenticate the same database and already belong to the staging inventory. The bundled production receipt lives under `work/build24m4d/inputs/`.

The helper creates fresh `out/routing_armed/kits/{q,n,n_go}` copies with GO=false, scans and reseals them, and checks their authenticated database staging closure. It prints all three armed seals plus `armed_n_go_config.payload_sha256` (SHA256 of the decoded k/c.json payload bytes) and `armed_n_go_config.file_sha256` (SHA256 of the capsule file). It records those values, the reviewed hashes, and the RESULT file hash in `UPLOADS_ROUTING_ARMED.json`.

`UPLOADS_ROUTING_ARMED.json` and `.list` describe the changed q/n files and selection upload under `out/routing_armed/upload/`. The already-staged DB at `/project/community/jjyeung/okh7/x_22c714e1/u/<database-sha256>` and the n_go copy are excluded. `SCAN_{q,n,n_go}.json.gz` and `PLANNER_CLOSURE.json` record the local checks. Runtime checks still authenticate the remote DB bytes and size.

Apply `UPLOADS_24M4E.json` before the armed delta. The source kits in 24m4f have the same seals as 24m4e; arm_routing.py is outside every kit. The unarmed GO manifest does not apply to armed seals. Arming grants no upload or launch permission; the independent in-job config review remains required.

`work/build24m4f/ARM_TESTS.json` and `REVIEW_AUTH_TESTS.json` record synthetic review fixtures, the matching-selection bind, decoded scans, complete native mode-q planner checks, and rejection controls. These tests do not represent a production review or verify remote DB availability.
