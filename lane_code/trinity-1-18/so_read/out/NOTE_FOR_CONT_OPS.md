VERDICT: DONE All round-8 fixes pass 129 workspace and 48 fresh-application CPU tests; H100 byte parity remains required.

The kit binds **step 400 only**, read A/job **173060**, source package **a15_cot_apdc76460c3a164**, artifact SHA256 **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. a19 refuses any other reviewed identity/preparation before reading the base. Later exports are diagnostic and cannot authorize adoption.

Follow [README](kit_parity50/README.md): apply patches; build with `u0/a19.py --enable-extensions --manifest ... --extension-pins ...` and the delivered binding; generate operations; place; detached fill; CPU proof; gate; receipt handoff; submit; unpack. The build uses **A4's 636-item schedule**, one card, caches only, general/no-requeue. All-cache allowance is 12 GiB; processor-only is 4 GiB and needs its own gate. OFF reader bytes remain unchanged; synthetic CPU fixtures do not establish GPU parity.

The CPU job preserves in-tree symlinks in `$P/a/4.tar`, refuses escaping/broken/cyclic links and records archive hash/bytes before CPU.json. Tar stderr stays in `results/4.err`. Reserve **about 33 GB for the archive (estimate)** plus extraction/source/runtime space. The GPU host must provide the exact writable logical root outside bwrap. Asset aliases must be symlinks. README sets `READ_PYTHON="$GPU_LOGICAL/d/v/py"`, opaque cache roots and an executable torch/transformers/CUDA preflight. ENVIRONMENT.json is CPU-bound; ue.json and submit check its hash and exact versions.

Require **zero answer/trace byte differences**, useful cache hits, lower full-worker time and measured memory headroom before crediting savings. Submit also checks cont_ops' complete CPU assertions, dry proofs, empty general queue, return-pool bound, plan/profile/assets/device/environment and kit hashes. Device admission requires H100 80GB HBM3 and 132 SMs.

**Estimates with zero credited saving:** the 636-item schedule takes **7,351.824 s (11.559 s/item; 2 h 02 min 32 s)** if supplied throughput carries forward. **Package D**, the separate 580-item distance read, has **no ON route** in a19; its estimate is **13,813.069 s (3 h 50 min)** from the supplied measured 23.600 s/item. Neither measures step-400 GPU performance.

A refused unpack leaves its extracted tree behind. Scorers require **success output after exit status 0**; partial returns remain partial. Frozen weights remain required; raw writes restored between boundaries escape the guard.

## Review round 8: finding -> fix -> test

| Finding | Fix and test |
|---|---|
| 1. Archive links | Preserve links and refuse escapes; extracted absolute heads link passes real Artifact/load_native admission. |
| 2. GPU environment | Use d/v/py with cache roots and preflight; version/hash/CUDA mutations refuse in executable shell, gate, runtime and submit tests. |
| 3. Late export refusal | Bind step 400 at build; eleven identity/preparation mutations refuse before base access. |
| 4. Archive path alias | Resolve both operands; README validation passes through a symlinked parent. |
| 5. Handoff details | Symlink aliases, retained tar stderr and fresh a15_cot_ap token; error and command tests pass. |

All ten new tests fail before and pass after; exact outputs and older requested review sections are in [REPORT](REPORT.md). [MANIFEST](patches/MANIFEST.json) pins delivery bytes. Real GPU parity/performance/memory, large staging, host interpreter execution, transport/restore/requeue and a multi-card operator remain unrun or undelivered.
