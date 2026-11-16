# Re-freeze pre-registration, amendment 1: which ground-truth rasters the K1 kill test uses (written 2026-11-15T21:24:11Z, before any K1 output was scored)

## Question
The K1 kill test and selector refit (step P1 of REFREEZE_PREREGISTRATION_20261115.md) score the deployed mask backend against ground-truth rasters of 300 training captures, each pinned by sha256 in the kit's CAPTURES.json. The original rasters were lost with trinity-2-18. A clean-room builder reproduces 259 of them byte for byte; 41 do not reach their pin. What does K1 use?

## Answer
- Primary analysis: the 259 captures whose rebuilt raster equals its pin (ScanNet 51 of 51, ScanNet++ 86 of 87, ARKitScenes 122 of 162; K1 train 215 of 242, K1 held-out 44 of 58). Every registered statistic, mark and decision rule is unchanged and is computed on these captures.
- Sensitivity analysis, reported beside it: all 300 captures, with the builder's best rebuilt raster for the 41 that miss their pin, marked as unpinned.
- If the two analyses give the same pass or kill verdict on every registered mark, the primary stands. If any mark differs, no verdict is declared: the orchestrator rules, and the default is to wait for the original rasters (trinity-2-18) or for a builder that reaches the remaining pins.
- A raster that reaches its pin later moves into the primary set; the primary set never shrinks and no capture is dropped for any other reason.

## Why
- A pin-equal raster is the original file, so the primary analysis uses registered inputs only. The subset is fixed by raster availability at 2026-11-15T21:24:11Z, before the K1 GPU phase finished and before any score existed; it does not depend on model output.
- The subset is not random: the 40 ARKitScenes captures that miss carry more annotated boxes (median 17 against 10), so they are probably harder scenes. That is why the full-set sensitivity analysis is mandatory and a disagreement blocks the verdict.
- Evidence: orch_n30/events/gt_build/20261115T2116Z_RESULT_rasters_built.md, PIN_CHECK.tsv and VARIANTS.md there; record K1_GT_RASTER_REBUILD_20261115.md. State of K1 when this was written: phase tower_sam launched 21:19Z (orch_n30/events/k1_ops3/20261115T2120Z_RESULT_tower_sam_launched.md); phases own and convert, tables, render and report not run.

## Options rejected
- Waiting for trinity-2-18 before any analysis: the node has been down since 10:00Z with no date; the user ruled that its work moves.
- Re-pinning the 41 rebuilt rasters as registered inputs: their difference from the originals cannot be measured without the originals.
- Dropping the 41 captures silently: it would bias the test toward easier scenes without saying so.

## What might not work and how we would notice
The 41 missing captures could carry the failures K1 is meant to find. The sensitivity analysis shows it: a mark that passes on 259 and fails on 300.

## Other disclosures that go with every K1 result
2,204 of 14,304 pinned frames are the pinned PNGs fetched from the Orchard frame store (the local decode differs by one grey level in 1 to 13 pixels); K1 runs without fallback traces; the report's import path was restored from the kit's pinned files; MRA statistics are also given under the benchmark authority's scorer; the own phase runs on Orchard.

## Primary set as of 2026-11-15T22:27Z
Lane gt_build2 reached 37 more pins with one rule set that also reproduces every earlier match, so the primary set is 296 captures (ScanNet 51 of 51, ScanNet++ 86 of 87, ARKitScenes 159 of 162). Four captures remain unpinned and enter only the sensitivity analysis: ARKitScenes 41125829, 42899325, 45261532 and ScanNet++ ef69d58016. Evidence: orch_n30/events/gt_build2/20261115T2227Z_RESULT_37_more_rasters.md, PIN_CHECK.tsv and RULES_R1.md there. No K1 score existed at this time (phase tower_sam run 2 started 22:21Z).

