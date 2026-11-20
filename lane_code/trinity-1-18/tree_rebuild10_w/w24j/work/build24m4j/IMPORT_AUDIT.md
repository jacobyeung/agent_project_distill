P's reconstruction source directly imports six third-party top-level packages: `PIL` (Pillow), `numpy`, `scipy`, `tokenizers`, `torch` and `transformers`. `IMPORT_CLOSURE.json` records 67 P modules and the 75 explicit probe imports. `IMPORT_WALK.json` records the broader 206-module AST walk, including every nested import and dynamic-loader call found in those files.

The build path includes `s1_pool_relocate.relocate`, `s1_pool.selected_rows`, `ground_rows.validate`, generator/derivgen geometry validators, `s1_routing.build`, its `Frames` class, `carrier_c1_routing.suffix_tokens`, `batches.training_text`, and `carrier_c1_run.processor_for_receipt`. The audit follows lazy imports from these paths. `suffix_tokens` reaches Pillow and `transformers.video_utils` through `batches`; SciPy supplies `cdist`, `cKDTree` and `ConvexHull` through the geometry modules. The child also instantiates P's native processor from authenticated metadata before `build()` to test configuration-selected library imports.

The frozen P config has `training_mode=final`, `geometry_online=null` and `mdg=null`. The closure includes the optional token modules conservatively. The `Frames` class reads the frame map, plan and FPS authority; it does not decode pixels. The separate evaluation `frames.py` modules use `av` and Pillow, but reconstruction does not call those decoders. Generator backend creation in `ground_v312_io` and its external `rk`/backend loader are generation paths; reconstruction validates the recorded rows and does not invoke those loaders. The broader AST candidates `accelerate`, `av`, `fla`, `google`, `peft`, `pyarrow`, `safetensors`, `torchvision`, `triton`, `vggt` and internal script aliases are recorded rather than silently treated as required build imports.

The supplied kit's environment mapping is:

| Package | Orchard provider | Explicit package version | Local probe version (Trinity only) |
|---|---|---|---|
| PIL | staged venv/site paths | no individual version string in the supplied kit metadata | 12.1.1 |
| numpy | NumPy overlay | 2.2.6 | 2.2.6 |
| scipy | staged venv/site paths | no individual version string in the supplied kit metadata | 1.14.1 |
| tokenizers | staged venv/site paths | no individual version string in the supplied kit metadata | 0.22.2 |
| torch | staged venv/site paths | no individual version string in the supplied kit metadata | 2.11.0+cpu |
| transformers | staged venv/site paths | no individual version string in the supplied kit metadata | 5.12.1 |

`job.sh` starts system Python only to verify/bootstrap the kit. `b/x.py` calls `z.bootstrap`; `z.bootstrap` verifies and decodes `k/j.json`. That shell extracts the venv and invokes `/project/community/jjyeung/c7d31ddd/venvs/rwtrain_torch211_cu129/bin/python -B -s`. The exact Python minor version and each venv distribution version are not available in the supplied metadata; the `torch211_cu129` directory label is not an independently verified version string.

The shell puts fla first, then NumPy 2.2.6, the staged kit's `b/`, the closure root and its `site_alias` on `PYTHONPATH`. The venv adds its site directories. `b/ep.sh` and `b/pc.sh` run evidence publishers under system Python and do not provide reconstruction dependencies. qd has `ep.sh`; `pc.sh` is present in the training kit. The decoded qd shell and all other decoded shell variants are retained beside this audit.

The venv archive is pinned by `ffc81db4b3b1c3d1e42ac91159d504dc57b36eebfc75f537d15a426bbe6a8a22`; the NumPy overlay archive by `74b2d4607362f15b4e097f1507ed8eae39c30cd0cdac8028d6008ab454d67c4e`; the fla member manifest by `4e4a6ac51788f7dd1ca9e0fc68f95109a129a636ce5f763e5b4ef3c3109f91c8`; and the closure archive by `fa8681cba4c02d789bc60c09fac7a05936c5b1fde81d53f77830294ea7e7895c`. The pinned P preflight expects fla 0.6.0 and triton 3.7.1 for training. Reconstruction's direct imports do not require those two packages. The CPU job stages the same venv, NumPy and fla assets; it needs no training closure hooks.

`rb.environment()` snapshots the parent's effective import paths in order, excluding the active source tree, launcher and kit-code directories. The command binds the interpreter/base prefixes, those site/overlay paths and P's tree read-only. It then launches the same interpreter with `-I -s -S -B`; explicit paths restore the dependencies while `-S` prevents site startup hooks from patching P. The extracted P tree is first. The runtime probe rejects every top-level name collision across P's tree and environment paths with `R1_RECONSTRUCTION_MODULE_SHADOWED:<name>` and checks the loaded P module origins. Every required import fails by name with `R1_RECONSTRUCTION_IMPORT_MISSING:<module>` before reconstruction starts.

The local archive was reconstructed in the input package and has hash `e7c9a966…`, not the original `e5be8157…`. Its extracted file inventory exactly matches P's authenticated `b83a8a35…` seal, including all 204 implementation entries. No original-archive hash check was bypassed in the kit: Orchard must supply the original `e5be8157…` bytes, P selection `5db993b1…` remains pinned, and both full database-hash checks remain `4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84`.

The local import trace records successful transitive packages under the available p1cpu environment. Those package versions describe Trinity only; the Orchard probe records its own module origins and versions. Production row bodies and processor metadata are unavailable locally, so the complete production database was not reconstructed here.
