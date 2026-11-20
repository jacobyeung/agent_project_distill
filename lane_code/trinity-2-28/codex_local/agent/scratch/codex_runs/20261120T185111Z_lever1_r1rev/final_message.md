**GO AFTER FIXES — do not submit this delivery.**

Review is inline because the sandbox is read-only. Below, `P/` denotes members of `out/delivery.tgz → 0.tgz`.

1. **Staging deterministically fails.** The payload expands to **34,362,101 bytes**, exceeding the **33,554,432-byte** allowance at `P/orchard_h10/job.py:106`. The extractor rejects it at `P/orchard_h10/vendor/orchard_stage.py:65–67`; `g/8.json` crosses the limit. The CPU check also calls this staging function (`delivery.tgz → a/5.py:130`). Reduce the payload or update the authenticated allowance, then test the actual staging path.

2. **GT labels reach the GPU job.** `P/g/0.json:9–25` contains `answer`, `ground_truth`, and released answers; `P/items/devs1_routed.json:12–22` also contains labels. The worker loads these tasks and passes them to its factory ([runtime/w.py:72](/scratch/jjyeung/orch_n30/lever1_c/r1/runtime/w.py:72), lines 88–93). Although the prompt binder excludes answer fields, the job-readable payload violates the requested boundary. Strip labels and unused labeled assets, preserving and resealing the exact prompt/RGB bindings.

3. **The full naming requirement is unmet.** Orchard staging extracts descriptive model paths, including `tree/rk/sam3mask.py` and `tree/scripts/sam3_reference.py` ([BUILD.json:356](/scratch/jjyeung/orch_n30/lever1_c/r1/out/BUILD.json:356), line 380). [REPORT.md:54](/scratch/jjyeung/orch_n30/lever1_c/r1/REPORT.md:54) explicitly retains descriptive source paths. Opaque job names and suppressed stdout do not cover these paths. Remove unused members and make retained runtime paths comply before placement.

4. **Publication can outlast the allocation and lose the normal receipt.** The worker deadline reserves only 120 seconds ([build_depth.py:72](/scratch/jjyeung/orch_n30/lever1_c/r1/build_depth.py:72)), but upload/readback each allow 1,800 seconds plus a 60-second describe (`P/orchard_h10/job.py:156–167`). Normal publication runs afterward, at lines 255–262. Bound transfers and worker termination by the allocation deadline while reserving time for failure receipts.

Other checks passed:

- Delivery/package/payload hashes match. Resource arguments specify general, gpu:1, 16 CPUs, 200G, the required exclusion, and 40 minutes (`P/orchard_h10/common.py:62–71`).
- The writer retains the original prefill and geometry constructor, exports lossless 32×51×51 depth, and preserves camera/scale metadata ([runtime/w.py:35](/scratch/jjyeung/orch_n30/lever1_c/r1/runtime/w.py:35); [depth_format.py:13](/scratch/jjyeung/orch_n30/lever1_c/r1/depth_format.py:13)). Reference geometries within each capture satisfy the derived repeat bounds.
- The 0.00 m, 95% parity gate precedes interventions; cells b–g implement the reported operations ([relift.py:235](/scratch/jjyeung/orch_n30/lever1_c/r1/relift.py:235), lines 285–306).
- Independently passed seven read-only tests and 20/20 real T1 gap checks. The funnel confirms **56 eligible items / 28 captures**; bootstrap uses 10,000 paired draws over 46 rooms, seed 20261120.
- Full depth-based parity remains untested until a return exists. Dev-S1 results must remain diagnostic.