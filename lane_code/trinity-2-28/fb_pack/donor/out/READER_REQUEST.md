# Reader binding for cont_ops21

Bind the tower arm to `auxiliary_heads.scale_donor`. The own arm keeps the live point-depth and pose heads.

The N kit must include an explicit `scale_donor` block with these exact fields:

- `schema`: `tower-scale-donor-v1`.
- `checkpoint`: the source C1 export artifact's absolute `path` and full `sha256`.
- `fov_source`: `V1` for checkpoint-private FoV or `V2` for frozen G3T intrinsics. There is no default.
- `visual_sha256`: `scale_donor.visual_identity(model.auxiliary_heads.depth.model.visual)`.
- `feature_contract_sha256`: `p3_provenance.digest(scale_donor.feature_contract(model.auxiliary_heads.depth))`.

The kit must authenticate the source checkpoint and compute these pins before training or reading. V1 also freezes the private frame queries, which feed the FoV module. V2 reads `TowerState.raw_pose9[TowerState.anchor_slots, 7:9]`; authenticate cached tower outputs against the frozen G3T source, weights, preprocessing and frame indices. Exports record those G3T identities. Neither variant may read live pose-head FoV for scale.

Use the step-400 source unless the frozen K1 decision rule selects step 544. Step-400 artifact SHA256 is `5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd`; heads SHA256 is `e72208ac55e342a3ac7972383f63740be323eba28d6c3bd293da1ad47743d4a7`. The real heads and the final V1/V2 decision are MISSING in this delivery. Do not treat a fixture binding as production admission.

For an N export, construct and warm-start the native model, call `scale_donor.attach(model, binding)`, then call `carrier_c1_run.load_artifact`. The trainer's `load_model` already attaches the donor from its prepared receipt. Readers that construct `CarrierC1` directly, including the separate runtime loader, must add the attach call themselves. Keep the existing private visual copy frozen. Preserve the native `r1_persisted.scope` when staged content uses different paths; do not rewrite authenticated artifact headers. The verifier rejects missing donor bindings, changed donor tensors, changed shared visual tensors, or mismatched artifact/head metadata.

For a baseline artifact that predates the donor, load that baseline first and then attach the same pinned donor. Verify its private visual hash equals the donor source's hash. If it differs, stop with a pin mismatch; do not silently replace the baseline's own depth path. Every tower-arm baseline must be read again under the chosen donor before any N export is read under it. Record checkpoint, FoV variant, shared visual, feature contract and frozen scale-rule pins in each read receipt; reject mixed bindings in a comparison.

The patched `HeadState(..., pose_source='tower')` calls the donor automatically. An external bridge can call `tower_read.apply_tower(heads, state, batch, scale_donor=model.auxiliary_heads.scale_donor)`. The bridge computes the unchanged median rule on the donor's `[32,51,51]` endpoint grid, scales raw G3T translations once, and replaces the tower readout's depth map with raw G3T depth multiplied by that same scale once. Its sampler uses endpoint-aligned bilinear interpolation. Do not multiply the metric depth or translations again. The own-arm `HeadState` never calls the donor.

For external routed-distance geometry, supply either unscaled G3T depth/poses plus this donor scale to the existing `scaled_g3t_depth` profile, or already scaled tensors to `scaled_g3t_metric`; preserve the profile's scale-count checks. Cached live-head scales are invalid under this binding.

Run `bash out/REAL_WEIGHT_COMMAND.sh` from the patched tree with its required pinned input variables populated. If staged paths differ, set `N_REPLICAS` and `N_REPLICAS_SHA` to a pinned JSON containing `paths: {sha256: local_absolute_path}`; every consumed replica is rehashed. It checks the actual step-2 export against initialization without loading the LM, authenticates both K1 captures, and rejects donor drift or an unmoved live head/grid. It uses an explicit fixture image resolution and synthetic fixed tower depth/confidence; it does not measure K1 scale accuracy. N must produce the native step-2 export for this check. Full-resolution pricing and the frozen step-400 versus step-544 decision remain separate inputs.
