VERDICT: DONE All requested round-5 fixes pass CPU validation; GPU adoption remains gated.

**Measured validation: 102 workspace tests and 21 fresh-application tests pass.** Five patches apply with zero fuzz; all original reader bytes and complete OFF output bytes remain unchanged. The round-5 regressions produce 11 expected assertion failures on the reviewed implementation.

**Adopt only after the exact package/profile passes the zero-difference GPU gate.** Step 600 uses A4's 636-item schedule, one card, caches only, general/no-requeue. The all-cache allowance is 12 GiB; processor-only uses 4 GiB and must pass its own gate. No GPU or production launch ran here.

Set the roots and reviewed target binding using the [README](kit_parity50/README.md), then build:

```bash
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \
  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \
  --manifest "$DELIVERY/patches/MANIFEST.json" --extension-pins "$DELIVERY/kit_parity50/EXTENSION_PINS.json" \
  --export-binding "$STEP600_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/step600"
```

Add `--processor-only` for that profile. The README supplies executable binding, delivery, placement, fill, dry-check, allocated-proof, GPU-gate, submit, fetch and unpack commands. `prep_paths` supplies paths; preparation_sha256 supplies pins. The synthetic test binding is not production evidence.

The generated submit script requires CPU payload/plan/inputs/operator bindings, entry/bundle success, the exact cache allowance and fits=true, both dry checks, an empty general queue, and a return pool at most 75,000,000 bytes. The GPU gate binds A4 prepare output plus operator overrides. Require zero answer/trace byte differences, useful hits, lower total worker time and measured host/GPU headroom.

**Forecast scope:** Package D is the 580-item distance read, a B5 fork with 03:30 walltime; it has **no ON route** in a19. Its one-card **estimate** is 13,813.069 s (3 h 50 min), based on measured 23.600 s/item. For the **636-item** A4 read that a19 builds, the **estimate** is **7,351.824 s (2 h 02 min 32 s; 11.559 s/item)**, carrying forward A4's supplied total with zero assumed saving. Neither is a measured step-600 result; queue/staging time and target-specific cache costs are excluded.

A refused unpack leaves its tree behind. Scorers must use only unpack's **success output after exit status 0**; an existing directory proves nothing. The README's command chains that handoff with `&&`. Successful partial returns remain partial. Hard kills may require fresh journals.

## Review round 5: finding -> fix -> test

| Finding | Fix and test |
|---|---|
| 1 MEDIUM | Exact wrap_batch output includes exclusion, EXIT log and USR1 forwarding; the built package passes a/5.py's bundle guard. |
| 2 LOW | Pre-copy payload/operator/extension/alias pins; tampered inputs are refused before output. |
| 3 LOW | Executable binding/delivery/place/fill/dry/CPU/submit/fetch/unpack steps; actual submit preflight refuses incomplete memory evidence and an oversized pool. |
| 4 LOW | Gate derives and validates the built package's prepared per-read profile; both cache profiles pass, mismatches fail. |
| 5 INFO | Package D and A4 forecasts are separately scoped estimates; documentation tests require both. |
| 7 INFO | Refused trees remain unscoreable; documentation tests require the success-output handoff. |

All six findings have fail-before/pass-after regressions. GPU parity, real restore/storage/transport/requeue and a multi-card operator remain unrun or undelivered.

The workspace briefly exceeded 3 GB. Sharing identical fixture files preserved every path and byte. The report retains the failed resource check and corrected size.

Exact commands, outputs and limitations: [REPORT](REPORT.md). Pins: [MANIFEST](patches/MANIFEST.json).
