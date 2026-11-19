VERDICT: DONE All round-6 fixes pass 111 workspace and 30 fresh-application CPU tests; production GPU validation remains required.

Adopt the **636-item A4 read**, one card, caches only, general/no-requeue, after its **H100 80 GB** gate reports zero answer/trace byte differences. All-cache allowance is 12 GiB; processor-only uses 4 GiB and needs its own gate. The synthetic CPU fixture is not production evidence.

Follow [README](kit_parity50/README.md) for authenticated patch application, binding, build, detached fill, CPU proof, exact asset staging, GPU gate, receipt handoff, submit and unpack. Build with:

```bash
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \
  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \
  --manifest "$DELIVERY/patches/MANIFEST.json" --extension-pins "$DELIVERY/kit_parity50/EXTENSION_PINS.json" \
  --export-binding "$STEP600_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/step600"
```

Add `--processor-only` for that profile. Submit requires the complete cont_ops CPU receipt checks, cache-memory allowance, both dry checks, an empty general queue, a return pool at most 75,000,000 bytes, and successful GPU evidence for the same plan/profile/assets/device. Require useful cache hits, lower full worker time and measured memory headroom before crediting savings.

**Estimates, with zero assumed cache saving:** A4’s 636-item schedule takes **7,351.824 s (2 h 02 min 32 s; 11.559 s/item)** if supplied throughput carries forward. **Package D**, the separate 580-item distance read, has **no ON route** in a19; its estimate is **13,813.069 s (3 h 50 min)** from measured 23.600 s/item. Neither measures step 600.

A refused unpack leaves its extracted tree behind. Scorers consume only **success output after exit status 0**; successful partial returns remain partial. The README’s `-s -B` command gates that handoff with `&&`.

## Review round 6: finding -> fix -> test

| Finding | Fix and regression |
|---|---|
| 1. Unpack import | Run from the operator directory without `-I`; the actual README subprocess accepts an authenticated fixture. |
| 2. Foreground fill | Nohup, permanent attempt lock, PID/log and exit file; success/failure receipts pass and duplicate launches refuse. |
| 3. Weak CPU check | Embed cont_ops’ assertions verbatim; altered batch, guard, dispatch, events and memory refuse. |
| 4. Missing pins | Authenticate every copied A4 member, batch and bootstrap before output; mutations refuse. |
| 5. Checkpoint/device | Bind CPU restore/manifest receipts and export identity; changed assets, wrong step and non-H100 properties refuse. |
| INFO: whitespace | Compare three split fields; tabs/newlines pass and extra fields fail. |
| INFO: GPU handoff | Require a bound successful GPU receipt; failed or mismatched evidence refuses. |

Failed fill attempts require a fresh token. `done`/`prep_paths` remain authenticated operation metadata. Frozen weights remain required: raw writes restored between boundaries are outside guard coverage. Real GPU parity/performance/memory, transport/restore/requeue and a multi-card operator remain unrun or undelivered.

Exact outputs and limitations: [REPORT](REPORT.md). Delivery pins: [MANIFEST](patches/MANIFEST.json).
