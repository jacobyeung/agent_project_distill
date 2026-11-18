# Original-init metadata for warm-start staging

The required original-init artifact SHA256 is **c1a4258816b3f561c9891f74cc1138780900de5cd890320161d2c94c85a86f67**.
Its logical member is `ap/f2ad01ad/runs/49becb79/m200/artifact.json`.

Retention evidence: `/scratch/jjyeung/orch_cd/orchard_cp2/events/20261113T1003Z_RESULT_init_m200_mirror_rehash.md`.
The operator rehashed that artifact, its heads, the full-weights manifest and all six manifest-pinned files in workbench job 168962. The report names `/tmp/jjyeung/okit_8865619b/root/c7d31ddd/init/c1a4258816b3f561/`.
That `/tmp` mirror is job-private, not a portable location or a reusable verification flag. ORCH also confirms an independent Trinity CP1 m200 checkpoint copy in `inbox/20261113T1925Z_ORCH_NOTE_init_artifact_is_retained.md`.

**Seal-time check:** confirm the original-init artifact's full SHA256 at the path the new kit stages. The warm-start group-recovery check needs this metadata JSON, not another copy of the original-init weight payload.
This lane read the operator's evidence; it did not inspect or fetch those checkpoint payloads and did not change production.
