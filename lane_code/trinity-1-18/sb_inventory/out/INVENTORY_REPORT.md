All three evidence slots remain MISSING. This bundle supplies a complete G3T meta inventory and proves that N creates no GF-1 connector; it does not certify a production tower run or SAM3 cache generation. No registry was modified.

The source is sealed w19, tree `8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa`.
Archive: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/out/tree_rebuild_b19_8ea1fe6b.tar`.
Archive SHA256: `390ffc32e881fec212ed5973725b4c4f2eac9c1c98585a5b2a9051c6d1a3e179`.
All 933 source-tree files match `TREE_SEAL.json`. The w19 report says GO=false and reports a population-capacity refusal; it supplies no completed training inventory.
The inventory uses `work/build19/inputs/kit_config.json`, SHA256 `b2e23841aa3634bf581dd775b4b44d6d73b26832bfd497e769976ed47a5b91aa`.
The packaged `config.json` has identical bytes. The C-prime reference is the `6ed2c7aa` prepared `s1_receipt.json` under `inputs/p_runtime`; all four `inputs/p_configs` files are indexed.
The b18 comparison and every recovered literal release-pin occurrence appear in [release_pin_index.json](inventories/release_pin_index.json). Other-arm and synthetic-test pins remain labeled by their source paths.

| Component | Release and frozen evidence | Draft decision |
|---|---|---|
| G3T geometry tower | Full native architecture on meta: 1,472 tensors, 1,406,749,212 elements; all frozen, zero optimizer members. | GAP: no N runtime/manifest binding to the pretrained assets. |
| SAM 3 segmenter | Loader and receipt agree on revision and checkpoint; wrapper freezes its backend. No SAM3 module enters N training. | GAP: upstream architecture and N runtime/cache binding are missing. |
| GF-1 connector | N has no GF1 module, parameter or optimizer member. | GAP: the mandatory policy slot has no absent-component exemption or complete clean receipt. |

G3T is `thatbrguy/g3t`, revision `c55e91a04f1cbbad67359072536351201fd19e8b` (`student_pilot/c1r_ref.py:8`).
`tower_read.py:20` requires weight SHA256 `d460957bb1c8a8c228d83ab10bad8a6dbcf80b03f29d7fbebf9c0f2c1c25f702` and config SHA256 `5aeb2acd008d41a1cac52e10216fbf35e8dfeb2ce26b89bb24e7ccc4ee0817d7`.
The documented b04 artifact filenames are `g3t/model.safetensors` and `g3t/config.json`; N's training config supplies neither path.
The observed vendored-source digest matches loader pin `df1ea59a73b0ad08b51670bfa37da84eace99b9d0c45c8d270f7052b42e98701`.
The config fixes embed_dim=1024, image_size=518, patch_size=14 and enables depth, point and both camera heads. Config and weight hashes above are recorded pins, not hashes of assets loaded by this audit.
`FrozenG3TTower` is a plain object outside the student module tree. Its loader uses `eval().requires_grad_(False)` and its load/run methods use `torch.inference_mode()` (`tower_read.py:144–202`).
The meta probe executes the real attachment interface, then calls parent `train()` and rebuilds optimizer groups. Every tower submodule stays in eval mode, and the optimizer membership is unchanged.
The optional registered `G3TEncoder` can train aggregator parameters in finetune mode (`g3t_online.py:187`); `parameter_groups` would place them in `geometry_encoder`. N forbids that path. No tower parameter reached an optimizer group here.
Several vendored layers record Apache License 2.0; other files refer to a missing root LICENSE. The full G3T release/weight license is MISSING.

SAM 3's receipt records revision `5dd401d1c5c1d5c3eedff06d41b77af824517619` and checkpoint SHA256 `9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e`.
The recorded checkpoint is `/scratch/jjyeung/orch_cd/ttower/work/sam3_weights/sam3.pt`, with 3,450,062,241 bytes. This byte count comes from the receipt, not a checkpoint read.
`sam3_tower.py:150–187` checks that checkpoint, revision and six source-file hashes; it constructs the image model with eval_mode=True and freezes all backend parameters. `encode` and `_detect` use inference mode.
The wrapper's plain-object ownership excludes its parameters from parent traversal. This code property does not recover an actual SAM3 parameter list or certify mask-cache provenance.
`segmenter.json` lists all six expected source filenames and hashes. The builder is expected at `/home/jjyeung/agent_project/agent/third_party/sam3/sam3/model_builder.py`, or a matching staged local copy. The NFS origin was not accessed.
The supplied local sources contain the receipt but no upstream SAM3 model implementation. Parameter names/shapes remain null, explicitly MISSING; zero denotes only SAM3 membership in N's student optimizer.
The receipt explicitly does not certify working-tree cleanliness or cache-time revision. It records no SAM3 license.

N sets `geometry_connector=none` and omits `geometry_online`. `r1_training.validate` refuses any other setting; `CarrierC1` constructs GF1 only when `geometry_online` contains `gf1` (`carrier_c1.py:169–175`).
GF1 therefore loads no upstream weights and creates zero parameters for this configuration. Its implementation identity is the sealed N tree plus the hashed `gf1.py` and `gf1_config.py` sources.
Literally, `r2_policy.record` demands schema=`r2-component-evidence-v1`, component=`heads_gf1_connector`, component_class=`new_training`, phase=`both`, nonempty resolvable `inputs`, verdict=`PROVEN_CLEAN`, and `exclusions_complete=true`.
That parser does not inspect the truth of the exclusion claim. An absent module alone does not authenticate the lost clean receipt, so this audit cannot honestly assert exclusions_complete. The R1 training skip/deferral does not remove the strict official-read requirement.
For geometry_tower and segmenter, the same schema, matching component/class/phase and input pins are mandatory; class=`external_frozen`, verdict=`EXEMPT_FROZEN`, and frozen=true are required. Neither record is drafted without the missing production binding.

The CPU probe uses N's real CarrierC1 constructor and parameter_groups, C-prime camera/depth settings plus N overrides, a reduced native Qwen base, and full-size heads on meta. [optimizer.json](inventories/optimizer.json) lists every parameter name, shape, requires_grad flag and group.
The optimizer has llm=28 tensors (23,676 elements; LR 0.000006), heads=94 (4,782,403; LR 0.0001), and pose=81 (220,444,758; LR 0.00006). These are reconstruction counts, not production model sizes.
The student has 90 frozen tensors and 203 optimizer tensors. Its frozen base/private vision parameters are distinct from the external G3T tower.
The probe executes the real depth-loader freeze statement without loading its unavailable initialization weights. The pinned step-544 artifact has no head_init, so inherited_head_names yields an empty set.
No pretrained load, training step, FSDP initialization or historical-run verification occurred. The full G3T constructor uses the repository's scalar-schedule helper so meta initialization can read its scalar schedule.
Six direct probes of the unchanged strict policy refuse missing records or false required booleans. The existing policy tests were read; no full-suite result is claimed. No official benchmark items were read.

Reproduction commands, run from this workspace:
- `bash work/run_python.sh work/prepare_sources.py` selects w19 and produces the archive/tree checks in `out/PACKAGE.json`.
- `bash work/run_python.sh work/inventory_cpu.py` produces every parameter count, shape and optimizer group, plus the G3T vendor digest. The launcher masks CUDA, forces offline libraries, uses two threads and caps virtual memory below 40 GB.
- `bash work/run_python.sh work/build_report.py` collects release/config pins, compares b18, writes inventories and three GAP drafts, and produces the six policy refusals. SAM3 identity/byte values are copied from the hashed receipt.
- `bash work/run_python.sh work/package_report.py` validates input hashes, snapshots small evidence sources, writes this report and creates the archive. `sha256sum FILE` independently reproduces each file digest.

Every generated evidence JSON carries input path/SHA256 pins; each component claim also names its sources. [VALIDATION.json](VALIDATION.json) reports the final checks. External paths remain provenance references; small inputs are included in `work/source_snapshots` with an index.
The deliverable is `out/sb_inventory.tar`; its digest is in `out/sb_inventory.tar.sha256`. The archive excludes itself and its checksum sidecar. No output is bound to a component registry.
The no-archaeology skill governs report wording; no historical-process sentence needs an exception.
