All files remain in W5. No deletion ran or is requested by this delivery.

- `work/tmp/` and generated directories under `out/tests/` contain test fixtures; retain them while reviewing receipts that reference their paths.
- `work/existing_full/` and `work/pytest_tmp/` contain the legacy test harness and fixtures.
- `out/baseline/` is the read-only comparison snapshot copied into W5.
- `out/reader_repin/` and `out/orchard_h10/` are rebuild intermediates.
- Copied W4 implementation scripts in `work/` are provenance inputs, not W5 rebuild steps. Use only the rebuild and verification commands named in REPORT.md.

The user can remove these after review. The sealed archives, manifests, hashes, diffs, logs and evidence should remain together.
