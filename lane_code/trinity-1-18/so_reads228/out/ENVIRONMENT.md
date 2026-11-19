# Runtime and archive mapping

The authoritative environment is the 359-byte `q/env.json` from staged `a3.tar`, SHA256 `e46a9a59e1de189ae736a5d4e94c7827eabfcfa695057fda9640e8120a54a81a`. Its bytes are copied to [evidence/q/env.json](evidence/q/env.json), and STAGE_PLAN records the complete receipt.

| Module | Receipt version |
|---|---|
| torch | 2.13.0+cu130 |
| torchvision | 0.28.0+cu130 |
| transformers | 5.19.0 |
| scipy | 1.14.1 |

These are read from the pinned receipt, not measured on Trinity. The CPU test environment uses torch 2.11.0+cpu and transformers 5.12.1. It cannot replace the production runtime.

| Local source on trinity-2-28 | Package destination/content |
|---|---|
| `reads228/dl/s4e0` through `s4e3` | `d/m400/`: artifact, heads, full weights. Concatenation SHA256 `dcd49569e1555e18c403207f429de7b352f806bb11827fb57aa9973f4ceec7b5`. |
| `reads228/dl/g0` | `d/g/`: G3T config and weights. |
| `reads228/dl/a2.tar` | `d/b/` base tokenizer/config, `d/f/` frames, SAM source, selector and other listed inputs. |
| `reads228/dl/a4.tar` | `d/v/py`, `d/v/boot.py`, `d/v/site/` overlay; no base Python/torch runtime in its supplied list. |
| `reads228/dl/a3.tar` | `d/q/`: environment and policy receipts, vnice and terminator copies. |
| `kit/A10b/package/a/6` | `d/p0/`: three pinned step-400 preparation files, 184,320 archive bytes. |
| Existing `d/k/` | SAM3 checkpoint and receipt, rechecked against package pins. |
| `reads228/dl/r0_0` … `r2_0` | Package runtime groups; exact 13 source/target paths, hosts, sizes and hashes are in MISSING.json. No parts or member lists are supplied here. |

All `d/` destinations above mean `/scratch/jjyeung/b01ec87a6f29b/d`. Archive parts remain on local scratch. Extraction verifies each part and the full concatenation when the package supplies a concatenation hash. Marker files supplied by the coordinator do not replace the kit's hash checks.

The runtime mapping follows the sealed job's `sj`, `m/ap`, and `fsw` namespaces. Only registered namespace members and safe links are accepted; unknown members fail instead of guessing their destination. Runtime expansion has an aggregate 40 GB allowance, which is an estimate and a hard extraction cap. Unresolved native-library dependencies or relocatability problems stop the import probe. There is no pip/conda or alternate-environment fallback.

`/usr/bin/python3` **3.6.8** executes only extraction, path relocation, and code installation. Those stdlib paths were exercised with the actual system 3.6.8 interpreter on trinity-1-18. Both the control process and GPU worker then use **`/scratch/jjyeung/b01ec87a6f29b/d/v/py`**, with the wrapper's sealed `-B -I` calling convention. Its relocated base environment is `/scratch/jjyeung/orch_n30/reads228/runtime/m/ap/19252904/e`; its standalone interpreter is `/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12`.

The original reader computes trusted interpreter roots from `sysconfig.get_paths()` in `A10b/src/b/e2e_reader/artifact.py:135`; it also accepts `settings.env_roots`, which remains the pinned `d/v/site` directory. The probe requires every imported framework module to resolve beneath these roots on local scratch. It records Python version, executable, prefix, base prefix, CUDA build version, module locations, and audit coverage. The sealed preparation writes the same env_roots into settings, and the stage check verifies them before the idle gate.

The target runtime import and full preparation have **not** run. They require the absent runtime bytes. Local fixture tests establish the extraction/relocation logic and preparation call order; they do not establish ABI compatibility or successful model loading on 2-28.
