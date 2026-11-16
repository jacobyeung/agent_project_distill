# Restoration admission

The candidate training closure is missing. An export contains the artifact and tensors; it does not supply the authenticated preparation configuration and receipts that this backend requires. The direct-reader completion receipt authenticates transport, not the missing training metadata.

| Check | Accepted value | Candidate requirement |
|---|---|---|
| Artifact file SHA256 | `1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef` (`BASELINE_CONFIG.json`) | Derived after complete tar verification; exact step/run and artifact pin required |
| Prepared config file SHA256 | `78341acb36ffd03b9cec6de65effc9fafcbe8bccdc1dfb43e9da7bd88af47560` (`BASELINE_CONFIG.json`) | Candidate config file, not a path substitution into accepted bytes |
| Canonical training config identity | `84ea03af6049a179bf4a44619b1534fdcb528b5511544189236254b5d66842cb` (`BASELINE_prepare_config.json`) | Recompute with the unchanged trainer.identity; equal artifact and preparation config_sha256 |
| Production data receipt SHA256 | `ebc2983ef7ba33e2e77f4435fff7a031b633a449ef9311622ecab653ea759f40` (`BASELINE_CONFIG.json`) | PREPARED, nonsynthetic, real frames verified; exact config/preparation pins |
| Preparation receipt SHA256 | `34cf26a691728802db8d47766c42bd4045c5481fe1f27c09a486abafaec1a3d6` (`BASELINE_prepare_config.json`) | Verify architecture, streams, layout, route policy and scene exclusions against candidate config |
| Source seal file SHA256 | `c82c2da1a0933207fbf60ba82f6c5172509c96d715620efe7495d0014c9aeaf9` (`BASELINE_prepare_config.json`) | Authenticate actual staged source files and candidate seal bindings; fixed backend source cannot drift |
| Run seal SHA256 | `89690a76b141c43debcbbbf567e69331e2ced6608f6af2d594df4a12668ef80b` (supplied `work/from113/work/obj/m544_artifact.json`) | Check candidate source-seal/config binding and export seal unchanged |
| Init specification | Derived by `evalpath/runtime.py:30` in supplied trainer | Bind candidate artifact and every trained group; exact trained tensor loading remains required |
| Own-head scale and gravity | Accepted manifest in `BASELINE_CONFIG.json` full projection | Recompute through the unchanged geometry kernel with the candidate heads; publish the new manifest and receipts |

`guard_backend.authenticate_candidate` retains `read_runtime.prepared` and `runtime.check_init_spec`. `Session` uses the authenticated C8r restore, parity and geometry functions. Each checkpoint needs a fresh process because the sealed gravity guard installs once and tracks capture verdicts. The production process coordinator is not implemented.

`guard_export.stage` first binds the plain-text completion record to the prepared plan, checks whole-archive size and digest, normalizes only the record container to JSON, then calls the unchanged reviewed `stage_export` with full checking. The reviewed file and checker are shipped byte-for-byte. The candidate wrapper is not yet connected to C8r job staging.

C8r can validate ordinary milestone member roots and whole archives. Its production transport descriptor, prepared configuration, artifact pin and ancillary receipts are fixed to the accepted run. The reviewed stager admits the candidate milestone layout, but its namespace/checker bootstrap must be connected to the new job; copying that module alone does not finish the integration.

`PIN_CLASSIFICATION.json` records the baseline values. No candidate hash, config identity, source seal, init specification or prepared geometry value has been invented. They remain unavailable until the candidate closure and export are admitted.
