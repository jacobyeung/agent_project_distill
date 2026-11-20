**GO AFTER FIXES — the time target and exhaustive GPU-import coverage remain unresolved. Do not submit yet.**

Review returned inline because the sandbox is read-only. Paths below are relative to `r1/`.

1. **Budget target remains unmet.** Forecast: **23.75 worker / 37.75 allocation minutes**, leaving only **2.25 allocation minutes**. The seven-minute increase is 360 seconds for shared loading plus 60 seconds for staging/telemetry; neither allowance is measured. Meeting 34 minutes requires saving **225.01 seconds**. The explanation is candid, but no reduction was implemented ([out/BUDGET_CHECK.json:4](/scratch/jjyeung/orch_n30/lever1_c/r1/out/BUDGET_CHECK.json:4)). Resolve this before submission and validate any rebuilt delivery.

2. **The import inventory is selective, not exhaustive.** It imports all 26 vendor files plus nine explicitly named modules; it does not establish every deferred GPU-path import or explain every exclusion ([tests/check_imports.py:26](/scratch/jjyeung/orch_n30/lever1_c/r1/tests/check_imports.py:26)). Complete that audit. I found no missing vendor file, but cannot certify the requested “every module” condition from this evidence.

The other two priority checks pass:

- **Exact delivery validation:** independently verified delivery, package, payload, evidence and test-log hashes. Token **`a784b94c2e6af`**, **3,704,563 bytes**, SHA256 **`fba95b8b0b00c87ec7900817a0977084e18efed504b8918e24eccf9224302974`**. Recorded results show **36/36 tests**, two fresh-process import checks and two CPU rehearsals passing ([out/VALIDATION.json:2](/scratch/jjyeung/orch_n30/lever1_c/r1/out/VALIDATION.json:2)).
- **Production failure fetch:** the injected worker exception uses real local pool publication and the unchanged production fetch block, including the delivered numeric fetch entry. I independently decoded the fetched archive’s **13-line traceback** and verified its hash. Four negative authentication checks pass ([tests/test_failure.py:156](/scratch/jjyeung/orch_n30/lever1_c/r1/tests/test_failure.py:156)). Bounds are **200 lines × 2,048 characters** (`runtime/e.py:10`).

Remaining checks:

- **Sources:** all **296 retained serving sources** match the authenticated T1 delivery byte-for-byte. All **26 vendor files** are present; the vendor digest matches `df1ea59a…e98701` (`runtime/s.py:7`).
- **Rehearsal gaps:** vendor `dependency/{__init__,distortion}.py` and `utils/{__init__,geometry,load_fn,pose_enc,rotation}.py` are retained for the complete source pin and deferred preprocessing/pose conversion. The separate fresh-import check covers them. Deferred `g/m.py` and `orchard_h10/s.py` provide telemetry and staging; they are also included and separately checked.
- **Capture ordering:** capture 1’s tower runs before carrier loading; its output is reused, and its depth record is flushed before later RGB extraction ([runtime/w.py:119](/scratch/jjyeung/orch_n30/lever1_c/r1/runtime/w.py:119)). Shared archive staging still precedes it. **Failure within one–two minutes of allocation start remains unverified** (`REPORT.md:13`).
- **Telemetry:** returns include elapsed seconds, sampled capture RSS peak, cumulative process RSS high-water and GPU peak allocation, including incomplete captures (`runtime/m.py:17`).
- **Execution:** nine external file pins and five archive specifications match T1. Resource checks cover general, GPU:1, 16 CPUs, 200G and the exclusion (`tests/test_all.py:159`). The 40-minute allocation, 30-minute worker cap, publication deadlines and **1 GB cap** remain enforced (`build_depth.py:97`; `runtime/budget.py:46`; `depth_format.py:55`).
- **Serving fidelity:** one prefill, zero decoding, applied scale, cameras, intrinsics and canvas mapping remain enforced. The format restores exact **32×51×51** depth values (`runtime/w.py:66`; `depth_format.py:31`). I independently recomputed all five T1 repeat bounds; they match.
- **Naming and legality:** delivery member names and raw JSON pass the deny-list; decoded payload JSON has no GT/label/answer keys. REPORT, PLACE and BUILD agree. The authenticated rehearsal evidence scans every produced file (`tests/test_all.py:190`; `layout.py:26`).
- **Relift:** the **0.00 m / 95% all-150 parity gate** precedes interventions. Cells a–g match the brief; the recorded cohort is **56 items / 28 captures**, with 20 portrait objects censored. Paired room bootstrap uses 10,000 draws, seed 20261120, with dataset splits ([relift.py:214](/scratch/jjyeung/orch_n30/lever1_c/r1/relift.py:214); `out/COHORT.json:2`). Dev-S1 remains a held-out diagnostic.

No GPU, remote operation or write ran. Writer-dependent tests were inspected through authenticated evidence, not rerun.