VERDICT: DONE All round-7 fixes pass 119 workspace and 38 fresh-application CPU tests; production H100 byte parity remains required.

The gate defaults to **step 400**, read A/job **173060**, source package **a15_cot_apdc76460c3a164**, artifact SHA256 **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. `BOUND_EXPORT` selects the exact export pin; `EXPORT_BINDING` selects the matching build/fill binding. Other exports, including step 600, require explicit parameters. The supplied metadata and its provenance are in `operations/`.

Follow [README](kit_parity50/README.md) for the executable route: apply patches, build with `u0/a19.py --enable-extensions --manifest ... --extension-pins ...`, generate operations, place, detached fill, CPU proof, gate, receipt handoff, submit and unpack. The ON build uses a fresh token and **A4's 636-item schedule**, one card, caches only, general/no-requeue. All caches allow 12 GiB; `--processor-only` allows 4 GiB and needs a separate gate. OFF reader bytes remain unchanged. The synthetic CPU fixtures do not establish GPU equality.

The CPU-proof job archives its live namespace to **`$P/a/4.tar` before CPU.json**, which records its SHA256, byte count and logical root. This shared staging path is outside the capped return pool. The evidence archive includes the exact `a/1.json`; the gate checks its CPU-bound hash and export-pin bytes before GPU work. Reserve archive storage before the CPU job. On the H100 host, `/scratch/jjyeung` must physically exist and be writable outside bwrap; preserve the exact logical root. The README gives the one-GPU, eight-CPU, 200G, five-hour allocation command. Device admission requires **NVIDIA H100 80GB HBM3 and 132 SMs**.

Submit requires the complete cont_ops CPU receipt assertions, cache-memory allowance, both dry checks, an empty general queue, a return pool at most 75,000,000 bytes, and successful GPU evidence for the same plan/profile/assets/device. The receipt also binds the executing driver, comparator and sealed sample to MANIFEST-derived pins embedded in the package. Require zero answer/trace byte differences, useful hits, lower full-worker time and measured memory headroom before crediting savings.

**Estimates, with zero assumed cache saving:** the 636-item A4 schedule takes **7,351.824 s (2 h 02 min 32 s; 11.559 s/item)** if supplied throughput carries forward. **Package D**, the separate 580-item distance read, has **no ON route** in a19; its estimate is **13,813.069 s (3 h 50 min)** from measured 23.600 s/item. Neither measures the selected export's GPU performance.

A refused unpack leaves its extracted tree behind. Scorers consume only **success output after exit status 0**; successful partial returns remain partial. The README runs `-s -E -B` from the operator directory and gates handoff with `&&`. It writes the receipt archive to an H100-host path.

## Review round 7: finding -> fix -> test

| Finding | Fix and regression |
|---|---|
| 1. Private root disappears | Tar through the live namespace before CPU.json; fixture tar survives namespace loss, and the real CPU-proof fixture runs staging. |
| 2. Fill wait hangs | Guard PACKAGE_TOKEN; refuse a vanished PID without an exit receipt; stop after 14,400 seconds. Missing token, dead PID, timeout and exit 17 refuse; exit 0 passes. |
| 3. PCIe accepted | Require the exact HBM3 name and 132 SMs; PCIe/wrong-SM stubs refuse. |
| 4. Evidence and host nits | Bind kit/comparator/sample hashes, include a/1.json, use -s -E -B, and fix the archive host path. Byte mutations refuse; unpack ignores a polluted Python environment. |
| 5. Export selection | Default to the supplied step-400 pin; explicit selection supports other exports. Step-400 default and synthetic step-600 selection pass; mismatches refuse. |

Failed or interrupted fill/staging attempts require inspection and a fresh token, never automatic retry. Frozen weights remain required: raw writes restored between boundaries escape the guard. Real GPU parity/performance/memory, transport/restore/requeue and a multi-card operator remain unrun or undelivered. Exact tests, measurements and limitations: [REPORT](REPORT.md). Pins: [MANIFEST](patches/MANIFEST.json).
