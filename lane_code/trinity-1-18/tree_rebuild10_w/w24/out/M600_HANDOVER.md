Run `out/fill_m600.py` from the extracted build24 package. The template remains unlaunchable until the handover is authenticated.

Plan A reads exact files under `okh7/h_6ed2c7aa/m600`: `h.json`, `RP.json`, `s.tar`, `DONE.json`.
Plan B reads exact files under `okh7/pb_a5416871`: `h.json`, `RP.json`, `pb_report.json`, then the receipt’s exact metadata paths.
Both branches require `p-handover-v1` at integer step 600 and checkpoint closure. Step 200 refuses as `E56:200`. Step 400 retains its export-only branch.

Create an opaque `l.json` with three fields:
- `objects`: ordered export-part records, each with `name`, exact `pool_path`, `bytes`, and `sha256`.
- `export`: the ordered `names`, combined `bytes`, and combined `sha256`. Export names contain `6ed2c7aa_m600.tar`.
- `metadata`: model metadata records with exact `path` or `pool_path`, `bytes`, and `sha256`.

`python3 out/fill_m600.py --plan A --handover-dir /project/community/jjyeung/okh7/h_6ed2c7aa/m600 --listing /project/community/jjyeung/okh7/l.json --output-kit /LOCAL/n600`

For plan B, change `--plan` and the handover directory. Use a fresh output directory. No source or training-input change is allowed during filling.
The script verifies P’s pinned source/runtime identities, checkpoint and export closure, export parts, model metadata and routing base; then it reseals the kit and emits the resolved config, filled-pin record and upload inventory.
`M600_PINS.json` names every pending pin. Recompute the upload diff for the filled kit’s changed capsules and seals before transfer.
The inherited identity checks and all production admission gates remain enforced. GO stays false. The n allocation requests four GPUs on advanced and runs its own canary proof; no submission is performed by this script.
