The driver adapts dev-S1 rows to the frozen tree's native evaluator. It can bind four matched arms on 600 items and three free-generation arms on all 1,525 items. Full registered R1/R1b/R2 qualification remains blocked by unsupported scripted forms and unqualified prompt controls.

The selected source is the archive named by `leg_s1_tree/events/20261112T1046Z_NOTE_tree_frozen.md`: `t_04c4a166e33308b7.tar`, SHA256 `c78cb0c9e12985978c0caf4d7109dd24bd4e0754aea98fe0100a9ddb3655b983`. `work/tree_final` preserves its files. Bindings pin every source file. The live `PRELAUNCH_CARD.md` currently says HOLD because the released training design lacks the registered route-table and mixed flagged/unflagged behavior. A newer training release requires a new source review and bind; this package does not qualify that future release.

The built entry points are `routed.py bind`, `run`, and `merge`. `geometry.py tower` generates frozen raw G3T caches; `geometry.py prepare` derives scale and gravity from the exact LEG checkpoint. Neither GPU command ran here.

| Arm | Inputs to native generation | Items |
|---|---|---:|
| forced_route | Development instruction to use spatial tools | 600 or 1,525 |
| scripted | Same prompt as forced_route; native `ReferenceChoice` supplies call-choice tokens, heads supply responses, model supplies final answer | 600 |
| forced_direct | Development instruction to answer without tools; any actual call refuses the cell | 600 or 1,525 |
| unflagged | Original question and options | 600 or 1,525 |

These two English instructions are explicit development interventions, not trained flag tokens. They must not be interpreted as the registered forced-path controls. The report labels their numerical checks UNQUALIFIED. The training owner must first deliver the matched flag contract; then this adapter must bind those actual controls. No accuracy threshold has been added to the registered rules.

All arms use greedy native generation, thinking enabled, 32 duplicate frames and the tree's minimum 16,384-token cap. The native evaluator refuses a 2,048 generation cap. Routed R2 compares its own native forced-direct arm at the same cap; it does not compare a routed ON16k result with the vLLM B2048 arm. The reviewed direct cells separately derive B2048 from ON16k.

The adapter preserves every source index, timestamp, actual FPS, total frame count and PNG hash. It assigns a declared PNG-clip digest, rather than inventing an MP4 hash. Only question/options enter the model row. Ground-truth answers, source roles and label metadata do not enter generation. Failures and typed refusals remain in denominators; replay mismatches invalidate the cell.

Masks come from the checkpoint's native MDG head through `s1_grounding.build_backend` and `NativeMDG`. Each object query gets the isolated prompt-plus-call query pass. Candidate names come only from the question/options. The fixed `routed_default_v1` acceptance/merge policy remains bound. No SAM cache or ground-truth mask is substituted. Forced-route and scripted arms must have identical prefills, artifact and geometry identities; the merger checks these facts.

Predicted geometry uses G3T pose, FoV and depth, the frozen scale estimator applied to this checkpoint's private depth grid, and this checkpoint's gravity. `geometry.py prepare` uses one deterministic question per capture to obtain those own quantities and records that question and prefill hash. It shares the resulting geometry across arms. The full MDG query still uses each arm's actual prompt.

The raw tower contract is `legs1-raw-g3t-cache-v1`, with a capture-to-NPZ pin map. Each NPZ carries `raw_pose`, `depth_grid`, `depth_conf_grid`, `frame_indices`, `anchor_slots`, `grid_uv`, and `source_hw`. Dense counts are the capture's g3s32 or g3s64 group; its 32 LM anchors must match exactly. Native depth/confidence grids are 32×51×51. `geometry.py tower` accepts `legs1-dense-frames-v1`: `captures[native]` contains `frames` entries `{path,sha256,index}` and 32 `anchor_slots`. All 152 captures are required. The provided dev PNG plan has only the LM anchors; additional dense RGB inputs must come from the producer. Do not approximate 64 frames with duplicates.

Frozen G3T pins, checked by the native loader:

- Revision: `c55e91a04f1cbbad67359072536351201fd19e8b`.
- Weights: `d460957bb1c8a8c228d83ab10bad8a6dbcf80b03f29d7fbebf9c0f2c1c25f702`.
- Configuration: `5aeb2acd008d41a1cac52e10216fbf35e8dfeb2ce26b89bb24e7ccc4ee0817d7`.
- Scale rule: `460231adeda2b7ce4b8065f22df1556e0a00b31ca3e489d571a2d4c8b9b49d4e`.

The prepared manifest retains schema `s1-predicted-geometry-v1`, pins every geometry NPZ, and adds the exact checkpoint pin and producer hash. Geometry uses the native explicit `scaled_g3t_depth` profile: unscaled depth/translation, one recorded scale, exactly one application. Native loading tests verify this arithmetic. An old, unbound, empty or differently produced manifest refuses. The available `devs1_tower/exports_r2` archive has already combined G3T with older own depth/gravity and lacks raw confidence grids. It cannot supply the new checkpoint's geometry. `work/geometry/GEOMETRY_CHECK.json` retains the unsuccessful admission evidence; it is not a production manifest.

Fusion is `fit_gbox_policy_voteb5_best1_v1`: erosion and P10/P90 ±0.15 m interior trimming; largest view for absolute distance; 5 cm two-frame votes plus largest view for other boxes; room floor-cell vote. The VSI freeze was re-derived on dev-858 after earlier test-scene exploration, and lacks dev evidence for size, easy direction, counting and room. It is explicitly not a VSTI policy. The separate VSTI table routes only camera displacement and movement direction; this package does not claim VSTI coverage. Dev-S1 R1b uses the training route table, with absent types direct as the trainer specifies.

`SCRIPTED_REFERENCES.json` contains 150 absolute-distance, 150 relative-distance, 150 medium-direction and 150 hard-direction references. The adapter checked source question/options and selected only literal object names present there. The native API supports their box-gap and three-point-angle forms. It does not provide reference executors for counting, relative count, room, easy direction, size, relative size or route planning. These account for the other 925 main items. `scripted --scope main1525` refuses; it never inserts an answer or reuses a priced ground-truth program. Full-table certification requires native script support for each routed type. The 600-item report remains explicitly incomplete.

Before the first scored native cell, `run` loads the real export and performs prompt/pixel, teacher/cache and own-head replay parity using a camera-call probe. Trace 3.14 receives a real native backend. Scored grounded traces replay through the 3.14 audit runtime. A failed gate produces retained evidence and no COMPLETE receipt. `--first-minute` runs those checks and one item; it is a first-item check, not a promise to finish in 60 seconds. Use a fresh bind/output for the full cell afterward.

First-item checks requiring a real export/card: complete trained-group restoration; config/source/base admission; frozen tower and MDG asset loading; model/tokenizer/device compatibility; actual PNG and dense-anchor parity; real v3.14 call/replay; MDG query masks and candidate coverage; forced-control behavior; native throughput and peak memory. Controlled tiny random CPU heads prove execution and refusal mechanics, not these production properties or learned accuracy.
