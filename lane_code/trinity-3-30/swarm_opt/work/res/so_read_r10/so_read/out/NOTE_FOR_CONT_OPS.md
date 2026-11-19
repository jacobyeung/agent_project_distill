VERDICT: DONE Round-10 fixes pass 147 workspace and 66 fresh-application CPU tests; H100 byte parity remains required.

The kit binds **step 400 only**, read A/job **173060**, artifact **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. Follow [README](kit_parity50/README.md): apply patches; build with `u0/a19.py --enable-extensions --manifest ... --extension-pins ...`; obtain CPU proof; gate, seal, stage-kit and transfer before salloc; stage the host, run parity, return the receipt, then submit/unpack.

All **13 runtime parts plus bwrap** in [RUNTIME_PINS](kit_parity50/RUNTIME_PINS.json) remain exact-path Orchard prerequisites; their bytes are not supplied. Reserve **about 33 GB for 4.tar (estimate)** plus extraction/runtime space. The host hashes 4.tar once while extracting it. It enters A4's namespace for script preflight and parent; workers call the wrapper directly with J.environment, including HOME/TMPDIR/OPENBLAS=1.

Require **zero answer/trace byte differences**, useful hits, lower full-worker time and measured memory headroom before crediting savings. OFF bytes remain unchanged. A4's 636-item, single-card cache-only route allows 12 GiB for all caches or 4 GiB for processor-only with its own matching gate. No multi-card A4 operator is delivered.

CPU checks use torch 2.11.0+cpu / transformers 5.12.1; production requires torch 2.13.0+cu130 / transformers 5.19.0. The production guard must detect add_, copy_ and load_state_dict before readers. A miss fails ue.json and submit. Models must remain frozen; raw writes restored between boundaries can escape detection.

**Estimates with zero credited cache saving:** A4's 636-item schedule takes **7,351.824 s (11.559 s/item; 2 h 02 min 32 s)** if supplied throughput carries forward. The separate 580-item distance Package D has no ON route in a19; its estimate is **13,813.069 s (3 h 50 min)**. Neither measures step-400 performance. Scorers require successful unpack output after exit status 0; partial returns remain partial.

## Review round 10: finding -> fix -> test

| Finding | Fix and test |
|---|---|
| 1. Wrapper rejects -c | Pinned u0/u5.py script; exact boot bytes reject -c and execute preflight through the wrapper double; tampering refuses. |
| 2. Missing aliases | One table generates PRIVATE_ALIASES and seven host symlinks; staged fixture resolves all 12 paths; missing nested settings path refuses before self-test. |
| 3. Nested bwrap | Direct wrapper argv inside U0_ROOT; J.environment assertions pass. |
| 4. Repeated reads | One extraction/hash stream; measured one open/read and wrong-hash refusal. |

All seven new regressions fail before and pass after. Both supplied wrapper hashes match the coordinator prefixes and listed sizes; prior MANIFEST had no independent full wrapper-member hashes. [REPORT](REPORT.md) records exact hashes, outputs and that limitation. [MANIFEST](patches/MANIFEST.json) pins the delivery. Real H100 namespace/runtime execution, GPU parity/performance/memory, transfer and submit remain unrun.
