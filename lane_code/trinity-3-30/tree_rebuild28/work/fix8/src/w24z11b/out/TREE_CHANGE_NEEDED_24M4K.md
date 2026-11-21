Case b: `r1_handover.compare_configs` refuses the config-only candidate with `P_EXPORT_CONFIG_DIFFERENCE:max_pixels`. All eight real decoded N configs reproduce it with authenticated metadata. P's missing pixel fields compare as `None`; explicit integers do not compare equal, even when they describe P's effective encoder bounds.

`TREE_CHANGE_24M4K.patch` proposes two narrow changes and includes three portable unit tests:

1. `carrier_c1_run.processor_for_receipt` sets `_b7_layout` only for a nonempty `b7_inputs`. Legacy R1 receipts use P's existing default-pixel encoder path, with the same effective frame count and markers. This also avoids introducing B7's dense-row reserve and exact frame-count checks into that path.
2. `launch_r1.entry.admit` preserves the existing B7 check. For legacy R1 configs, it validates duplicate layout, markers and frame count using `pose_samples.DEFAULT_PIXELS`, while requiring raw pixel fields to remain absent or null. The explicit-pixel candidate is deliberately not accepted by this branch.

Both changes are necessary: admission currently calls `layout(cfg)` unconditionally before training on every rank. A processor-only patch would still refuse there. The handover comparison, source seals, routing-selection digest check, row exclusions, review gate and B7 processor behavior remain intact in the proposal.

Tree C and the four sealed kits are unchanged. The patch is **not applied**. ORCH's authorization and a tree review are required before applying, resealing and issuing new kits. The current kits still refuse N's mode r; this delivery does not authorize a retry.

`work/build24m4k/CONFIG_TESTS.json` and `COMPARE_TESTS.json` record the real config/layout comparisons. `PATCH_TESTS.json` records synthetic 32-frame encoder and admission-layout tests; `PATCH_UNIT_TESTS.json` records tests of the proposed function compiled in memory, including the 31-frame compatibility case. These tests do not grant full admission or establish that every production P row passes N's other checks.

The requested explicit-pixel candidates remain at `work/build24m4k/candidate/{q,n,n_go,qd}/{c,n}.json`. The mode-r planner fixture uses that candidate where possible; unavailable payload and refresh boundaries are explicitly listed in `MODE_R_PLAN_TEST.json`. The CPU helper runs the selected kit's own sealed config and never silently substitutes these candidates.
