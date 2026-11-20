**GO AFTER FIXES — complete the naming boundary and reconcile the delivery identity before placement.**

Review returned inline because the sandbox is read-only. Paths below are relative to `r1/`; `D/` denotes `out/delivery.tgz`, and `P/` denotes its inner `0.tgz`.

1. **Prior finding 3 remains open: external inputs expose model names.** `D/a/1.json:136,141` names `/scratch/jjyeung/b01ec87a6f29b/d/k/sam3.pt` and `SAM3_RECEIPT.json`. Production staging extracts these archives and checks these paths (`P/orchard_h10/job.py:118–126`). The naming regression scans payload members and launch surfaces, but misses external archive contents (`tests/test_fixes.py:87–110`). Extend opaque staging and its test to every job-visible input path while preserving content authentication.

2. **The reviewed artifact differs from the requested identity.** `PLACE.md:3,16` and the delivery specify token `ab6ea69ea972b`, job `a15_cot_apab6ea69ea972b`; the request specifies `a09fdd101cc93`. Reconcile the placement handoff with the exact reviewed artifact. Current delivery: **2,668,881 bytes**, SHA256 `8dee5268e3fe2583a60464c57223d031a3153b3ab32e907095ffaeef8365b8ee`.

The other prior findings are fixed:

- **Finding 1 — staging size:** independently measured **16,501,670 expanded bytes**, below **33,554,432**. The production-stage regression checks installed payload hashes (`tests/test_fixes.py:40–62`).
- **Finding 2 — labels:** task whitelisting removes labels and reseals task bindings (`layout.py:26–38`). Independent payload JSON scans found no prohibited label keys; all **150 prompt/RGB bindings** match T1.
- **Finding 4 — deadlines:** worker termination reserves publication time (`D/a/6.py:108–124`); capture, normal publication, and fallback share bounded windows (`runtime/budget.py:46–68`). Recorded regressions cover slow transfers and worker reaping (`tests/test_fixes.py:153–213`).

Remaining checks:

- External input pins match T1. Resource arguments satisfy general, gpu:1, 16 CPUs, 200G, exclusion, and 40 minutes (`P/orchard_h10/common.py:62–71`); the worker cap is 30 minutes.
- All **270 retained sources** match parent bytes. Geometry construction precedes segmentation; the writer enforces one prefill and zero decode steps (`runtime/w.py:39–62`). The format preserves the **32×51×51** grid losslessly (`depth_format.py:13–44`).
- Independently recomputed bounds match all ten T1 repeats; all 149 calling-item geometries fit their 60 representatives (`build_depth.py:23–42`).
- Upload enforces the **1 GB cap** and verifies generation, size, and readback hash (`P/orchard_h10/job.py:138–174`). Failed camera parity retains the capture (`runtime/w.py:103–123`).
- The **0.00 m / 95% all-150 gate** precedes interventions (`relift.py:235–254`). Cells b–g match the stated definitions, including rank-3 transport (`relift.py:66–101,285–306`).
- Independently confirmed **56 eligible items / 28 captures**. Bootstrap uses 10,000 paired room draws, seed 20261120, with dataset splits (`relift.py:195–203`; `gbuild/round7_common.py:40–66`).

**Validation:** all listed checksums pass; eight read-only tests pass, including 20 real T1 gap checks. Recorded package regressions report 22 passes; write-dependent tests were not rerun. Full depth parity awaits the return. Dev-S1 remains a held-out diagnostic.