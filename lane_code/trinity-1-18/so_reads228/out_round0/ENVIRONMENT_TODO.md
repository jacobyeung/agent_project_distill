# Runtime staging contract

The package's pinned environment receipt is `/scratch/jjyeung/b01ec87a6f29b/d/q/env.json`: **359 bytes**, SHA256 `e46a9a59e1de189ae736a5d4e94c7827eabfcfa695057fda9640e8120a54a81a`. The mirror contains its pin but not its bytes. It has no `CONFIG/env.json`; `package/CONFIG.json` contains only the public package descriptor.

The input archive `a3.tar` contains `q/env.json`, `q/policy.json`, and the policy scripts according to the mirrored `cont_ops17/work/dry2.py:54`. Its SHA256 is `05dc8f79707a51ec227f4bb875670a5d3b7cfa27271447783bf2f79b7474f5ae`, and its pinned size is 10,240 bytes. The two environment-overlay candidates are the pinned `a2.tar` and `a4.tar`; their member lists are unavailable here. The plan also lists all three template-runtime archive groups from `ORCHARD_ASSETS.json`, including every part's source, size, and hash.

The template recognizes `/scratch/jjyeung/envs/p1cpu/bin/python3.12` and its base-runtime target `/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12` (`A4/src/orchard_h10/vendor/orchard_stage.py:19`). A4 selects `/scratch/jjyeung/b01ec87a6f29b/d/v/py` and adds `/scratch/jjyeung/b01ec87a6f29b/d/v/site`. The exact launcher body and dependency closure cannot be reconstructed from their path names.

The coordinator must:

1. Download the pinned archives once through the authorized IO-governor stream.
2. Inspect the runtime member lists and launcher; map the Python environment to `/scratch/jjyeung/envs`, preserve required local aliases, and keep every environment/library read off `/home` and `/data*`. Do not blindly extract template `sj/`, `fsw/`, or `m/` prefixes into system directories.
3. Verify `q/env.json` against its pin, then require exact receipt versions for torch, torchvision, transformers, and scipy. A4 separately requires transformers >=5.12. Inspect the receipt's remaining dependency information; the source inventory identifies SAM dependencies including iopath, portalocker, ftfy, timm, pycocotools, and wcwidth.
4. Record the archive-to-installed-runtime member map and actual expanded size. The 40 GB allowance is provisional. Preflight rejects a total staged footprint that leaves less than 5 GB below 150 GB and rejects framework modules outside local scratch.
5. Run the sealed CPU preparation and preserve its log. Only then run the five-minute GPU idle check and first-50 OFF trial.

No command in this delivery downloads, installs, or guesses a production environment. These unresolved steps prevent a claim that the deployment is ready to execute.
