VERDICT: DONE Round-9 fixes pass 140 workspace and 59 fresh-application CPU tests; production adoption still requires the pinned runtime and the H100 byte gate.

The kit binds **step 400 only**, read A/job **173060**, source package **a15_cot_apdc76460c3a164**, artifact SHA256 **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. Follow [README](kit_parity50/README.md): apply patches; build with `u0/a19.py --enable-extensions --manifest ... --extension-pins ...`; place, fill and obtain CPU proof; run the private gate, seal, stage-kit and transfer **before salloc**; stage the H100 namespace; run parity; return the receipt; submit and unpack.

**Prerequisite:** all 13 runtime parts and bwrap in [RUNTIME_PINS](kit_parity50/RUNTIME_PINS.json) must be reachable at their exact Orchard paths. Their bytes are absent from the supplied files. REPORT lists every path, byte count and hash. The helper reuses A4's runtime staging block and maps the archive into root/sj/<logical>/d. Preflight, parent and workers use `J.namespace(root) + [inputs['python'], '-B', '-I', ...]` and J.environment, including HOME/TMPDIR/OPENBLAS=1. Fresh opaque tokens isolate kit/source roots. Reserve **about 33 GB for the asset archive (estimate)** plus extraction/runtime space.

The CPU environment is torch 2.11.0+cpu / transformers 5.12.1; production is torch 2.13.0+cu130 / transformers 5.19.0. The production interpreter must detect add_, copy_ and load_state_dict mutations before reader work. A miss writes failed ue.json and starts no workers; submit requires all three checks. The real production self-test remains unrun.

Require **zero answer/trace byte differences**, useful hits, lower full-worker time and measured memory headroom before crediting savings. A4's **636-item** single-card cache-only route allows 12 GiB for all caches or 4 GiB for processor-only, each with a matching gate. OFF remains byte-identical. Models must remain frozen; raw writes restored between boundaries can escape detection.

**Estimates with zero credited saving:** A4's 636-item schedule takes **7,351.824 s (11.559 s/item; 2 h 02 min 32 s)** if supplied throughput carries forward. **Package D**, the separate 580-item distance read, has **no ON route** in a19; its estimate is **13,813.069 s (3 h 50 min)**. Neither measures step-400 performance. A refused unpack leaves its extracted tree behind; scorers require **success output after exit status 0**, and partial returns remain partial.

## Review round 9: finding -> fix -> test

| Finding | Fix and test |
|---|---|
| 1. Namespace | A4 staging, namespace and wrapper commands; authenticated extraction and all launch sites pass. |
| 2. Version gap | Production guard self-test and submit evidence; each injected miss fails closed with a recorded receipt. |
| 3. Idle allocation | Gate/seal/stage-kit/transfer precede salloc; exact extraction commands execute on fixtures. |
| 4. INFO | Fresh token, J.environment, labelled logs and explicit guard limits; all regressions pass. |


All 11 round-9 tests fail before and pass after. Eight carried round-7 applied logs are labelled under checks/round7/. [REPORT](REPORT.md) contains exact outputs, all prior required review sections and the remaining production prerequisites. [MANIFEST](patches/MANIFEST.json) pins the delivery. GPU parity/performance/memory, real namespace/runtime execution, transfer/submit and persistent requeue remain unrun; no multi-card A4 operator is delivered.
