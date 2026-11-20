Run this helper after an independent review passes. Use the exact selection, published native receipt, database metadata and RESULT from that review. The RESULT must contain the selection file SHA256, the generated database SHA256 and the word PASS.

```bash
L=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24l
: "${SELECTION_FILE:?Set the local path to routing_selection.json}"
: "${RECEIPT_FILE:?Set the local path to the published receipt.json}"
: "${DB_METADATA_FILE:?Set the local path to db_bytes.json}"
: "${REVIEWED_SELECTION_SHA256:?Set the independently reviewed selection file SHA256}"
: "${REVIEWED_REGENERATED_SHA256:?Set the independently reviewed generated database SHA256}"
: "${REVIEW_VERDICT:?Set the local path to the independent RESULT file}"
nice -n 10 bash "$L/work/build24m4l/run.sh" "$L/out/arm_routing.py" \
  "$SELECTION_FILE" "$DB_METADATA_FILE" \
  --regenerated-receipt "$RECEIPT_FILE" \
  --reviewed-selection-sha256 "$REVIEWED_SELECTION_SHA256" \
  --reviewed-regenerated-sha256 "$REVIEWED_REGENERATED_SHA256" \
  --review-verdict "$REVIEW_VERDICT" \
  --output "$L/out/routing_armed"
```

The output directory must be new and lie within L. The runner uses isolated Python, limits CPU threads and memory, and exposes only L as writable. Copy the evidence into L before running it. If the selected routing-base receipt differs from the bundled receipt, add `--routing-base /absolute/local/path/to/receipt.json`.

For a native selection, `regenerated_sha256` is the canonical digest of the generated receipt because tree C′′ compares that digest during admission. It is not a database hash. The helper authenticates the supplied receipt against `selection.regenerated_receipt.sha256`, recomputes its canonical digest, checks its stream and row count, and requires its database SHA256 to equal the independently reviewed generated database hash. The database metadata must contain a positive, consistent size for that generated database and for the input routing-base database. The input and generated databases may differ. The selected base receipt must authenticate the input database and already belong to the staging inventory.

The helper retains both independent review hashes and the RESULT hash. It rejects changed receipt bytes, fabricated receipt digests, mismatched database hashes, missing metadata and changed row counts. Selections without a native receipt retain the strict database-hash check used by the compact legacy fixtures. No helper check substitutes for the independent review of production rows.

The armed q/n delta uses the new 24m4l seals in `work/build24m4l/ARM_BASE_SEALS.json` and its matching file inventory. Apply `UPLOADS_24M4L.json` first. The helper explicitly carries `k/c.json`, `k/n.json`, `k/8.json` and `k/s.json`, and its delta replays to complete armed kits. The separate GO overlay is not part of the ordinary upload stream.

The helper creates `kits/{q,n,n_go}` with GO=false, scans and reseals them, and writes `UPLOADS_ROUTING_ARMED.json/.list`. It prints all three seals and the decoded-payload and capsule-file hashes of armed n_go `k/c.json`. The generated database is rebuilt during mode q; the input database must already be staged. Neither database nor the n_go copy enters the ordinary armed upload stream. Runtime checks still authenticate staged bytes and sizes.

The kit publishes the selected build's raw `materialization.json`, `receipt.json` and `refresh.json` under `o/<job>/`, including on a failing shell exit when those files exist. `a6.json` maps the additional neutral filenames to their source paths and SHA256 values; those include P's base/comparison receipts and both refresh paths. A build that fails before producing a receipt cannot publish that nonexistent receipt.

`work/build24m4l/NATIVE_ARM_TESTS.json` records a real helper run, decoded scans and tree C′′'s unchanged receipt-digest check with synthetic materialization. `ARM_TESTS.json`, `REVIEW_AUTH_TESTS.json`, `ARM_COVERAGE.json` and `ARM_MISSING_DB_TEST.json` record the other fixtures. These checks do not constitute a production review, upload, launch or full routing reconstruction.
