# Refute review: R0 reserve-scene exclusion proof (read-only)

You are an independent reviewer. Try to REFUTE the claim below. Report only verified problems, each with file:line or data evidence and a concrete failing example (capture id + authority + matching key). Do not design fixes. Do not edit any file. No git, no ssh, no network. Never search recursively under /home or /data*; read only the named files. Everything you need is under /scratch/jjyeung/orch_n30/b10_reserve (call it LANE).

## Claim
Every capture in LANE/out/R0_SCENES.json (sha256 f7c45817...; 372 captures, 272 rooms) is outside every training stream of the student lineage (T0 -> CP1 -> LEG-S1 -> D0), outside every benchmark room/venue (VSI-Bench, ReVSI, VSTI and the rest of BENCH v2), outside dev-S1 and WITHHELD_ROOMS_80, at physical-room level (ScanNet: sceneNNNN with all rescans; ScanNet++: scene id; ARKitScenes: venue). R0-dev (100 rooms) and R0-rl are disjoint.

## Evidence to check
- LANE/code/census.py (builds the universe from single-directory listings in LANE/in/*.txt and LANE/in/arkit_metadata.csv, resolves each authority's keys through alias token families, writes LANE/out/CENSUS.json and CENSUS_PER_CAPTURE.json). Authorities and sha256 are in CENSUS.json "inputs" (kit07 metadata copy under LANE/in/kit07/pull: m3/a3v2_division.json, m3/frame_map.jsonl.gz, m/k/frame_rates.json, m/k/benchmark_scene_exclusions.json, m/k/{99e6eed6,932c0c4e,dafa4a9c,600ef69d}.json, m/k/dev_scene_exclusions.json; LANE/in/WITHHELD_ROOMS_80.json; LANE/in/stream_scenes/{d0v5_vqa,legs1_mdg_rasters}.txt).
- LANE/code/build_r0.py (selection + split), LANE/code/test_exclusion.py (independent substring test; run it: `cd LANE && python3 code/test_exclusion.py`, ~2 min).
- Other kit07 files that may list scenes of training streams: LANE/in/kit07/pull/m/k/*.json, *.tsv, m/BUILD.json, m/sess.json, prep/*. Check whether any of them names an R0 capture or room in any form (native id, 'v'+sha256(...)[:12] tokens of families 'rung1 scene <ns>/<id>', 'rung2 scene', 'v590kgt scene', with ns in scannet, scannetpp, scannetppv2, arkitscenes).

## Known gaps (assess each: does it make the claim false or unproven?)
1. Separate T0 and CP1 stream scene lists were not found; the census assumes kit07 frame_map + division A3 cover every ancestor stream.
2. ScanNet++ has no cross-scene physical-room key; two ScanNet++ scene ids may be the same room (one in R0, one trained).
3. The Qwen3.5 base model's pretraining exposure is unknowable.
4. Unknown token families: an authority key that resolves to nothing would be silently ignored if census.py's unresolved counts were wrong; verify the unresolved counts (CENSUS.json unresolved_counts all 0) yourself for at least two authorities.

## Output
A verdict line `VERDICT: REFUTED|UNREFUTED|UNPROVEN`, then numbered findings (severity, evidence, failing example), then what you checked and found clean. At most 60 lines.
