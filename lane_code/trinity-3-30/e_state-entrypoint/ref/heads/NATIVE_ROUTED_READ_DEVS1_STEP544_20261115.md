# Native routed read of the LEG-S1 step-544 student on dev-S1 (2026-11-16)

## Question
On dev-S1 (636 items: absolute distance 150, room size 36, camera displacement, movement direction and rotation 150 each; 84 captures, 58 physical rooms), does the student's native routed read beat its direct answers? In the native read the student writes the program and its own heads and frozen towers serve it inside generation.

## Answer
The student's direct read cannot answer the question, because it is not a direct-answer baseline on any of the five types. The student was trained to emit programs on all of them, and its direct read leaves those calls unserved. Most of its distance and room answers therefore come from budget-forced closes, and 96 of its 450 camera answers fail to parse. Against that read, native routing wins every type. The camera wins are large and robust. The distance and room wins are unresolved under the capped rule: zeroing forced closes flips their intervals from including zero to excluding it.

The comparison the project cares about is native routing against a direct-answer model. It pairs against the parent on distance and room (next section) and is unpaired elsewhere. On camera types native routing is far above the parent and f17. On distance it is below both. On room it shows no resolvable difference from the parent and trails f17. The distance loss comes from units, not programs. The model copies the tool's metric output even when the question asks for centimetres, feet, inches or square feet. On metre-only questions native distance is 61.6, above the scripted arm.

| Type | Items / captures / rooms | Native % | Scripted % | Direct % (primary / capped_zeroed) | Native − direct pp, primary | Native − direct pp, capped_zeroed | Unpaired parent / f17 direct |
|---|---|---:|---:|---|---|---|---|
| abs distance | 150 / 60 / 46 | 29.867 | 54.667 | 18.200 / 4.133 | +11.667 [−1.229, +25.529] | +25.733 [+16.474, +35.723] | 38.9 / 43.2 |
| room size | 36 / 18 / 9 | 53.889 | 65.000 | 31.944 / 8.889 | +21.944 [−1.765, +44.474] | +45.000 [+22.353, +65.000] | 55.6 / 71.4 |
| camera displacement | 150 / 51 / 36 | 82.333 | 82.333 | 9.800 / 9.800 | +72.533 [+66.562, +77.926] | same | 13.5 / 34.1 |
| camera movement direction | 150 / 48 / 36 | 94.667 | 94.667 | 24.667 / 24.667 | +70.000 [+60.000, +78.788] | same | 22.0 / 53.3 |
| camera rotation | 150 / 49 / 34 | 75.667 | 75.667 | 6.467 / 6.467 | +69.200 [+63.268, +75.072] | same | 9.3 / 8.1 |

Intervals are paired percentile 95% intervals from a bootstrap over physical rooms (50,000 draws, seed 20261115), marginal across cells. Native scores are identical under both capped rules, because the native arm has no budget-forced close with an answer; only direct changes. Per capture group: d1 distance +8.333 [+2.667, +24.118] (8 rooms) excludes zero under both rules, while d2 and d3 distance are unresolved. Room items exist only in d1, and camera items only in d1 and d2. The full grid is in the detail file.

## Paired against the parent's direct answers (confirmed by reader review_pp, 2026-11-16T05:11Z)
The parent CP1 m200 direct read of dev-S1 (trinity-1-18 `/scratch/jjyeung/orch_cd/devs1_direct/out`, r5 merge, B2048) covers the 150 distance and 36 room keys of this read. Both reads use byte-identical task and frame files, the same 32 duplicated anchors with true timing, budget 2,048 and a 64-token answer cap. They differ in GPU type and backend (vLLM on a Trinity card against an Orchard H100) and, by design, in prompt and checkpoint. The parent has no forced close, cap or parse failure on these types, so both capped rules give the same numbers. The adapter `06_parent_adapter/out/parent_adapter.py` (sha256 1051a70c…) feeds the parent rows to the unchanged script 44468e72. The script's artifact line hashes the student's export artifact, so the parent's artifact is unverified; its identity rests on the kit summary (model cp1m200) and the request binding.

| Questions | Items / rooms | Native % | Scripted % | Parent % | Native − parent pp | Scripted − parent pp |
|---|---|---:|---:|---:|---|---|
| distance, all | 150 / 46 | 29.867 | 54.667 | 38.867 | −9.000 [−17.031, +0.234] | +15.800 [+8.000, +24.153] |
| distance, metres | 43 / 23 | 61.628 | 59.302 | 60.698 | +0.930 [−13.095, +14.146] | −1.395 [−15.870, +12.400] |
| distance, non-metre | 107 / 41 | 17.103 | 52.804 | 30.093 | −12.991 [−24.15, −0.26] | +22.710 [+12.31, +34.08] |
| distance, centimetres | 28 / 18 | 6.071 | 63.571 | 50.000 | −43.929 [−61.25, −25.00] | +13.571 [−7.60, +29.00] |
| distance, feet | 46 / 27 | 18.261 | 48.913 | 8.261 | +10.000 [+1.02, +21.89] | +40.652 [+27.35, +54.42] |
