# Runtime and archive mapping

The authoritative 359-byte `q/env.json` is an authenticated a3.tar member with SHA256 `e46a9a59e1de189ae736a5d4e94c7827eabfcfa695057fda9640e8120a54a81a`. Its [copied receipt](evidence/q/env.json) requires these versions:

| Module | Pinned reader version |
|---|---|
| torch | 2.13.0+cu130 |
| torchvision | 0.28.0+cu130 |
| transformers | 5.19.0 |
| scipy | 1.14.1 |

These versions come from the receipt. They are not target measurements. The dispatch's torch 2.11 CPU environment tests the adapter; the pinned reader runtime must pass its own import probe.

| Target source | Destination/content |
|---|---|
| `reads228/dl/s4e0` through `s4e3` | `d/m400/` export, heads and full weights. |
| `reads228/dl/g0` | `d/g/` G3T. |
| `reads228/dl/a2.tar` | Base assets, frames, SAM source/checkpoint, selector and other pinned inputs. |
| `reads228/dl/a4.tar` | Unchanged `d/v/py`, `d/v/boot.py` and `d/v/site/` overlay. |
| `reads228/dl/a3.tar` | `d/q/` environment and policy receipts. |
| `kit/A10b/package/a/6` | `d/p0/` step-400 preparation files. |
| `reads228/dl/r0_0` through `r2_0` | The 13 package-pinned runtime parts listed in MISSING.json; coordinator treats them as staged. |

Here `d` is the package-visible `/scratch/jjyeung/b01ec87a6f29b/d`, backed by this kit's private `reads228/private/b01ec87a6f29b/d`. All parts remain on local scratch. Input archives use `--skip-old-files` after authentication. Existing private members must match exactly; unexplained destination files refuse staging. The other lane's shared logical root is never used. Extraction logs go under `reads228/extraction_logs`.

The physical runtime mapping is:

| Archive namespace | Host source | Package-visible bind |
|---|---|---|
| `sj` | `/scratch/jjyeung` through `reads228/runtime/sj` | `/scratch/jjyeung` |
| `fsw` | `reads228/runtime/fsw` | `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung` |
| `m/ap` | `reads228/runtime/m/ap` | `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap` |
| logical root | `reads228/private/b01ec87a6f29b` | `/scratch/jjyeung/b01ec87a6f29b` (overlaid after sj) |
| uv CPython | `/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu` | `/home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu` |

The adapter calls the authenticated `orchard_h10/vendor/orchard_job.py:118` namespace function. It selects the coordinator-approved root-owned `/usr/bin/bwrap` 0.4.0 and appends one bind from the private logical root to the pinned logical path. NAMESPACE.json records the system binary's measured size/hash/version/owner, the package bwrap pin, the exact argv and the target probe result. The package pin is 72,160 bytes, SHA256 `e318903862396f96de3df57264e0158682b952fd3fb53ac23d876413e7b30f71`; the target system binary's hash is measured at deployment. LOCAL_RUN copies both identities and names the executed binary. No runtime relocation is available.

Bootstrap uses target `/usr/bin/python3` (3.6.8 in the supplied inventory). Control wrappers then use the staged native `uv-python/.../bin/python3.12`, for stdlib-only work. Import checks, sealed preparation and the operator execute the unchanged `d/v/py` inside bwrap with `-B -I`. The worker inherits the operator namespace and runs under the pinned `d/q/vnice.sh` prefix; it does not launch another bwrap. Absolute runtime symlink bytes and pyvenv.cfg remain unchanged. Host-side checks translate registered logical prefixes and preserved Python links to physical scratch paths; those translations do not edit files or settings.

Runtime members are unavailable in this build workspace. Extraction on 2-28 authenticates ordered parts, records all member names/types/sizes and file hashes, enforces the aggregate 40 GB expansion cap and refuses unsafe namespace members/links. STAGE_CHECK requires the wrapper, boot module, base interpreter, pyvenv.cfg, encodings and each framework module before preparation. The namespace import probe then checks Python 3.12, exact versions, CUDA build availability and each module's placement under sysconfig roots or the unchanged env_roots. Both successful and failed stage checks retain the enumerated runtime inventory.

Target namespace creation, pinned reader-runtime startup/imports and full preparation have not run in this workspace. CPU tests run the real sealed operator in a separate interpreter while the native controller runs without site-packages. Any failure stops before the card gate without a fetch, install or automatic retry.

The operator probe and run share `namespace228.operator_command`. The probe imports all five operator/summary dependencies before any card access or run directory. It records its exact argv, exit code and diagnostics in OPERATOR_PROBE.json. Package `job.py:194` supplies the `d/q/vnice.sh` prefix; `job.py:206–207` establishes namespace plus `d/v/py` as the operator execution path. The adapter retains that execution boundary and calls the unchanged sealed operator with its observation launcher.
