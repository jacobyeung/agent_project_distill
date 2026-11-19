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

For an N export, construct and warm-start the native model, call `scale_donor.attach(model, binding)`, then call `carrier_c1_run.load_artifact`. The trainer's `load_model` attaches the donor from its prepared receipt. Readers that construct `CarrierC1` directly must warm-start its private visual and attach the pinned donor before loading the export. The separate runtime loader must first restore `depth.model.visual.*` from the export heads with `strict=True`, then freeze that visual with `requires_grad_(False)`, then attach the donor and perform the metadata and strict-load steps below. Its base-weight load does not restore the private visual, and it does not read `depth_init`. Preserve the native `r1_persisted.scope` when staged content uses different paths; do not rewrite authenticated artifact headers. The verifier rejects missing donor bindings, changed donor tensors, changed shared visual tensors, or mismatched artifact/head metadata.

For a baseline artifact that predates the donor, load that baseline first and then attach the same pinned donor. Verify its private visual hash equals the donor source's hash. If it differs, stop with a pin mismatch; do not silently replace the baseline's own depth path. Every tower-arm baseline must be read again under the chosen donor before any N export is read under it. Record checkpoint, FoV variant, shared visual, feature contract and frozen scale-rule pins in each read receipt; reject mixed bindings in a comparison.

The patched `HeadState(..., pose_source='tower')` calls the donor automatically. An external bridge can call `tower_read.apply_tower(heads, state, batch, scale_donor=model.auxiliary_heads.scale_donor)`. The bridge computes the unchanged median rule on the donor's `[32,51,51]` endpoint grid, scales raw G3T translations once, and replaces the tower readout's depth map with raw G3T depth multiplied by that same scale once. Its sampler uses endpoint-aligned bilinear interpolation. Do not multiply the metric depth or translations again. The own-arm `HeadState` never calls the donor.

For external routed-distance geometry, supply either unscaled G3T depth/poses plus this donor scale to the existing `scaled_g3t_depth` profile, or already scaled tensors to `scaled_g3t_metric`; preserve the profile's scale-count checks. Cached live-head scales are invalid under this binding.

Run `PYTHON=/path/to/python bash /absolute/path/to/donor3/out/REAL_WEIGHT_COMMAND.sh` from the patched tree with its required pinned input variables populated. If staged paths differ, set `N_REPLICAS` and `N_REPLICAS_SHA` to a pinned JSON containing `paths: {sha256: local_absolute_path}`; every consumed replica is rehashed. It checks the actual step-2 export against initialization without loading the LM, authenticates both K1 captures, and rejects donor drift or an unmoved live head/grid. It uses an explicit fixture image resolution and synthetic fixed tower depth/confidence; it does not measure K1 scale accuracy. N must produce the native step-2 export for this check. Full-resolution pricing and the frozen step-400 versus step-544 decision remain separate inputs.

## Byte-identical reader sources (M2)

`feature_contract` hashes all bytes of the nine files below, including comments. The training tree and reader tree must use byte-identical versions of these files. Any later edit locks N's exports out unless the reader repins through a matching, reviewed binding migration. A reader that merely recalculates `feature_contract_sha256` still fails `verify_export`, because its settings no longer equal the artifact's settings. Retain the original pinned reader tree to read existing exports; a migration must consistently rebind the trusted source and exported metadata. Fail-closed enforcement remains enabled.

All paths below are relative to `student_pilot/`. `scale_donor.py` is added by this overlay and is absent from base seal 57a1f14d; no base hash exists for it.

| File | SHA256 at base seal 57a1f14d | SHA256 in PATCH_DONOR3 |
|---|---|---|
| `decoupled_v.py` | `5f249ed8cf10949d64718012ff47d8af59aa5787a2867bd1fcff6e1198a74d49` | `5f249ed8cf10949d64718012ff47d8af59aa5787a2867bd1fcff6e1198a74d49` |
| `decoupled_vc.py` | `a88c1e9727608698052477f3324d60c5d587491c810676d737fbe11dfa66d5f7` | `a88c1e9727608698052477f3324d60c5d587491c810676d737fbe11dfa66d5f7` |
| `p3_heads.py` | `ef6c96dccd7389ffadecf465d18873cdbda57fa884e67ef26e20e3b331288f9d` | `ef6c96dccd7389ffadecf465d18873cdbda57fa884e67ef26e20e3b331288f9d` |
| `point_depth_head.py` | `960a4334fb50f39d394fafe59bda71a80abf6dc5fd42dc4ea1b17c2e16e5eb69` | `960a4334fb50f39d394fafe59bda71a80abf6dc5fd42dc4ea1b17c2e16e5eb69` |
| `carrier_c1_data.py` | `9ccee823404c8dc225c6f7d73a9f1c31d5b18cc40cd77a79c331c9021174b701` | `9ccee823404c8dc225c6f7d73a9f1c31d5b18cc40cd77a79c331c9021174b701` |
| `scale_donor.py` | `MISSING (absent at base seal)` | `1fca29c9211e19f91a04e72c41a77652a56f3dea363e58fdd71817fe7229a134` |
| `tower_read.py` | `2cd338e1935803fdd4784b1626095a88a7641a222b394984977b8ec47c674634` | `d3235c1fa3be07a04637049d266a8965a456ad6d5ea0d682ac96e9185f4643ee` |
| `_tower_native.py` | `c9107bce52184f68145018b0c2a0095dde59f5978508f7cb0043d81366c15102` | `c9107bce52184f68145018b0c2a0095dde59f5978508f7cb0043d81366c15102` |
| `fixed_readout.py` | `acf71b5dd3ffad1749ec3ddee39362baefb9aafa6b4df3ba78ac1b3ea00628ef` | `acf71b5dd3ffad1749ec3ddee39362baefb9aafa6b4df3ba78ac1b3ea00628ef` |

## Separate runtime load sequence (M3/M4)

After the runtime constructs `CarrierC1` and `full_ft.load_export` restores the base tensors, execute the following block in place of its head load. `binding` is the authenticated `scale_donor` configuration; `artifact` and `heads_path` come from the authenticated export. Preserve the existing bundle authentication and relocation scope.

```python
from student_pilot import scale_donor

heads = torch.load(heads_path, map_location="cpu", weights_only=True)
visual = model.auxiliary_heads.depth.model.visual
prefix = "depth.model.visual."
visual.load_state_dict({key[len(prefix):]: value for key, value in heads.items()
                        if key.startswith(prefix)}, strict=True)
visual.requires_grad_(False)
scale_donor.attach(model, binding)
metadata = heads.pop("_scale_donor", None)
if metadata != artifact.get("scale_donor"):
    raise ValueError("Scale donor artifact/head metadata differs")
scale_donor.verify_export(model, heads, metadata)
model.auxiliary_heads.load_state_dict(heads, strict=True)
```

Only keys starting with the exact prefix `depth.model.visual.` enter the visual load; strip that prefix and require complete, strict coverage. Keep those keys in `heads` for the final strict load. The private visual starts as a trainable deep copy of the empty base. Loading base tensors alone does not initialize it, and the standalone runtime skips `depth_init`. Restore the visual and freeze it before attaching: `attach` still authenticates it against `binding['visual_sha256']`. A changed visual must fail at attach. `_scale_donor` is metadata and must be removed, compared with `artifact['scale_donor']`, and verified before the full strict head load.

`test_mdg_runtime_strict_load_requires_reader_metadata_steps` executes a test adapter inserted at the strict-load site of the actual `mdg_runtime.load_runtime` function body. The runtime constructs the real `CarrierC1` on a differently initialized tiny Qwen base and calls the real `full_ft.load_export`; the test never substitutes `CarrierC1` or supplies an already attached model. It loads a native fixture export after two optimizer steps and checks every exported head tensor for byte identity. Negative cases reject the old attach-first order, freezing alone, loading without freezing, a tampered or incomplete visual, unpopped metadata, inconsistent metadata, and a changed donor tensor.

The test substitutes bundle authentication, processor/token setup and the tiny empty-base boundary, and isolates `r2_policy.unsupported_entry`. It checks the proposed reader sequence; it does not install it in the shipped runtime, validate a production bundle, or run real pretrained weights. Production still requires an authenticated R2 reader adapter. The legacy-reader guard remains enabled.

## Preparation and checkpoint boundary (S1)

S1 remains documented, not implemented. Bind the donor before producing N's preparation. `prepare` includes it in the receipt and `prepared` rejects an existing receipt that omits it with `C1 preparation frame layout/LM lever differs`. A fresh receipt is required under this patch.

Treating the donor only as a preparation-free lever would not satisfy the requested native checkpoint-resume proof. `identity(cfg)` includes `scale_donor`; `train` binds that identity into the resume binding, and `restore` rejects a pre-donor checkpoint under the changed binding. The only existing config-rebind exception is the GX policy, whose `gx_rule_rebind` also rejects donor changes. The native checkpoint regression demonstrates refusal under the new binding and successful restore under the unchanged binding with an attached frozen donor. Extending that identity/rebind policy changes resume legality, so this lane stops S1 at the requested boundary. The existing `r1_handover.compare_configs` allows adding a pinned donor at an independently admitted initialization boundary; it does not authorize an in-place resume or bypass preparation.

## Source loading and real-weight command (S2/S3)

Rank zero attaches with `verify_assets=True` and authenticates the source heads. After the trainer's existing startup agreement, follower ranks attach with `verify_assets=False`, preserving `r1_persisted` relocation. The source artifact, feature contract, tensor content and visual identity checks remain enforced. Heads use memory mapping; ranks still construct their private frozen modules, so this does not claim zero per-rank loading or production throughput. The source must stay immutable on local storage throughout launch.

`N_DONOR_BINDING` must name a pinned JSON object with a top-level `scale_donor` key: `{"scale_donor": { ...the exact fields above... }}`. Set `PYTHON` to the environment's interpreter; the command has no hard-coded Trinity interpreter path. Real step-400 heads remain MISSING at `/scratch/jjyeung/b01ec87a6f29b/d/m400/heads.pt` (SHA256 `e72208ac55e342a3ac7972383f63740be323eba28d6c3bd293da1ad47743d4a7`). Step-544 heads have no supplied location, and the production FoV/source decision remains MISSING.
