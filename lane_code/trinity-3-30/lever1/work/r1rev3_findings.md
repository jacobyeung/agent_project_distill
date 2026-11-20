**GO AFTER FIXES — close the CPU-rehearsal naming leak before placement.**

Review returned inline because the sandbox is read-only. Paths below are relative to `r1/`; `P/` denotes `out/delivery.tgz → 0.tgz`.

1. **Naming remains incomplete.** `P/orchard_h10/runner.py:44–52` reads item JSON through the decoding loader, then writes those decoded bytes directly into `metadata/a/3.json`. The Orchard CPU rehearsal calls this function (`delivery.tgz → a/6.py:69–72`). The final-plan test artifact visibly contains `scannet` and `vsi590k` identifiers at [3.json:4](/scratch/jjyeung/orch_n30/lever1_c/r1/tests/case_mhonlzcw/r/metadata/a/3.json:4). This violates `BRIEF_R1FIX2.md:4`’s explicit restriction on job-written JSON. Preserve opaque storage during this copy and extend the regression to inspect files produced by the actual rehearsal.

The four original findings now stand as follows:

- **Staging size: fixed.** Independently measured **29,515,745 expanded bytes**, below **33,554,432**. Production staging enforces that limit (`P/orchard_h10/job.py:101–105`).
- **Labels: fixed in delivered data assets.** Independent decoded-JSON scans pass; all **150 prompt/RGB bindings** match T1 (`layout.py:26–38`).
- **Naming: partially fixed.** External segmentation/selector inputs are removed (`external_inputs.py:8–24`); the generated-JSON leak above remains.
- **Deadlines: fixed.** Worker termination and publication have separate bounded windows (`build_depth.py:85–90`; `runtime/budget.py:46–68`).

Other required checks passed:

- Final identity agrees: **`a49a2224fff01`**, job **`a15_cot_apa49a2224fff01`**, **3,486,735 bytes**, SHA256 **`5662faa050c165d3e6cd3252820a6c9f75b4968a66b05d375746556e8b65c4db`**.
- All delivery hashes pass. Nine retained external file pins and archive pins match T1. Resources satisfy the requested partition, GPU, CPU, memory, exclusion, and 40-minute allocation (`P/orchard_h10/common.py:64–73`).
- Upload checks the **1 GB cap**, generation, size, and readback hash; failed camera parity retains the capture (`P/orchard_h10/job.py:140–175`; `runtime/w.py:103–123`).
- All **270 retained sources** match parent bytes. Geometry precedes segmentation; the writer enforces one prefill and zero decoding. Depth round-trips exactly at **32×51×51** (`runtime/w.py:39–62`; `depth_format.py:13–44`).
- Independently recomputed all ten repeat bounds; all 149 recorded calling-item geometries fit their capture representatives (`build_depth.py:23–42`).
- The **0.00 m / 95% all-150 gate** precedes interventions. Cells b–g, rank-3 pose transport, and paired room bootstrap match the specified operations (`relift.py:69–104,198–205,238–319`).
- Independently confirmed **56 eligible items / 28 captures**. Dev-S1 remains diagnostic (`REPORT.md:20`).

**Validation:** eight independent read-only checks and **20/20 real T1 gap checks** passed. Write-dependent package tests were inspected, not rerun. Live GPU numerics and remote publication remain untested.