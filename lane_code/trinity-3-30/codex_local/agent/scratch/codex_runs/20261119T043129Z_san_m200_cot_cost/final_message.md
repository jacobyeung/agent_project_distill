**1. Scope.** At step 200, B2048 never scores below ON16k on the paired direct reads: it improves 63 of 4,320 items. Counting accounts for nearly all excessive generation. Scores below are percentages; numeric types use mean relative accuracy.
I read every returned item through `san_kit`: dev-S1 has 1,339 of 1,339 shared items, scoring **77.77 / 75.83 / 77.71** at steps **544 / 100 / 200**. The complete base dev-S1 file has 1,525 of 1,525 items and scores 70.83; its additional distance and room items are not in the continuation’s direct files. R0-dev has 1,781 of 1,781 items, scoring **56.01 / 60.98 / 62.14**. Away twins score **21.33 / 88.67**, forward twins **94.67 / 93.33**, each on 150 of 150 items at 544 / 200. VSTI scores **46.11 / 58.33** on 900 of 900; routed A scores **66.90 / 75.27** on 636 of 636; routed B scores **6.57 / 64.40** on 134 of 134.
Sources are under `/scratch/jjyeung/orch_n30/`: base B2048 files are `evalx27/work/pull/x27/res/e193/merged/{main,away,forward}/results/budget_2048/0/items_leg_m544_*.jsonl`; direct returns are `cont_ops16/work/c15/h1read/kit/build/{adff67f7ae9,a5d2d909067,a8102c3207b}/fetched/x/{main,a7}/a0/results/{0,budget_2048/0}/items_a0.jsonl`. Facing uses `h1face/kit/build/a2e46c0504e`; VSTI uses `h1vsti/kit/build/{acb2faedd41,a35f73e87f0}` with the same result suffixes. Routed sources are the `metadata/reads/*/metadata/journals/*/0/items.jsonl` files returned by the loader under `cont_ops16/work/c15/r1route/{out3s/bases/b1/work/ret,out3s/bases/b2/work/ret,out3/A4/ret,out3/B5/ret}`.

**2. Token distributions and stopping counts.** Each tuple is **median / mean / nearest-rank p90 / maximum**. Semicolons separate **544; 100; 200**, or **544; 200** where 100 is unavailable. `B+4` means every corresponding ON16k statistic equals the B2048 statistic plus four tokens. “Easy/medium/hard” denote object-relative direction; V1–V3 denote camera-object relative distance; LR/NF/UD denote object-object relative position.
`F` counts force-closed items, `H` counts ON16k cap hits, `L` counts detected loops, and `b` counts detected loops whose B2048 thinking is below 2,048 tokens. Unlisted available counts are **0 of the row’s N**. A loop means an identical, lowercase, whitespace-delimited eight-word sequence occurs at least ten times before `</think>`; overlapping occurrences count. This detects repetition, not necessarily erroneous reasoning.

| Set / type; N | B2048 think tokens, by step | ON16k output tokens, by step | Nonzero F/H/L/b counts |
|---|---|---|---|
| dev-S1 / absolute distance; 150 | 2048/1857/2048/2048; unavailable thereafter | unavailable | 544: F 134 of 150 |
| dev-S1 / counting; 150 | 119/187.3/273/2048; 39/413.1/2048/2048; 41/425.2/2048/2048 | unavailable; 43/3092.5/16384/16384; 45/3104.5/16384/16384 | 544: F 2 of 150, L/b each 5 of 150; 100: F/H/L each 28 of 150; 200: F/H each 28 of 150, L 25 of 150 |
| dev-S1 / easy; 150 | 56/57.3/59/63; 62/62.6/64/70; 62/62.7/65/71 | unavailable; B+4; B+4 | — |
| dev-S1 / hard; 150 | 57/58.2/60/64; 67/68.1/71/75; 68/68.3/71/75 | unavailable; B+4; B+4 | — |
| dev-S1 / medium; 150 | 65/65.5/68/72; 66/65.4/69/75; 66/65.5/69/76 | unavailable; B+4; B+4 | — |
| dev-S1 / relative distance; 150 | 76.5/76.7/79/84; 58/59.1/63/66; 58/58.1/62/72 | unavailable; B+4; B+4 | — |
| dev-S1 / object size; 150 | 39/39.4/41/73; 35/36.8/42/84; 35/36.6/41/84 | unavailable; 42/43.6/49/91; 42/43.3/49/91 | — |
| dev-S1 / relative count; 139 | 121/269.7/532/2048; 2048/1509.6/2048/2048; 499/1041.4/2048/2048 | unavailable; 16384/11734/16384/16384; 503/7729.2/16384/16384 | 544: F 5 of 139, L/b each 4 of 139; 100: F 100 of 139, H 99 of 139, L 97 of 139, b 1 of 139; 200: F 65 of 139, H 64 of 139, L 68 of 139, b 7 of 139 |
| dev-S1 / relative size; 150 | 66/66.8/72/122; 49.5/54.1/81/100; 41/44.4/63/100 | unavailable; B+4; B+4 | — |
| dev-S1 / room size; 36 | 2048/1625.9/2048/2048; unavailable thereafter | unavailable | 544: F 28 of 36 |
| dev-S1 / route planning; 150 | 1/1/1/1; 61/59.5/95/108; 61/59.8/96/108 | unavailable; B+4; B+4 | — |
| R0-dev / appearance order; 246 | 59/58.9/63/72; 59/59/63/72; 59/59.2/63/72 | B+4; B+4; B+4 | — |
| R0-dev / counting; 385 | 148/264/546/2048; 40/588.7/2048/2048; 43/483.3/2048/2048 | 152/537.8/551/16384; 44/4465.7/16384/16384; 47/3577.1/16384/16384 | 544: F 10 of 385, H 7 of 385, L 16 of 385, b 6 of 385; 100: F 105 of 385, H 104 of 385, L 103 of 385; 200: F/H each 83 of 385, L 78 of 385, b 1 of 385 |
| R0-dev / easy; 192 | 60/60.7/65/68; 69/76/97/103; 69/74.9/97/104 | B+4; B+4; B+4 | — |
| R0-dev / hard; 192 | 62/61.9/66/73; 73/81.2/103/111; 74/80.2/103/115 | B+4; B+4; B+4 | — |
| R0-dev / medium; 194 | 69/69.2/74/79; 72/78.9/101/110; 71.5/78.2/101/106 | B+4; B+4; B+4 | — |
| R0-dev / relative distance; 279 | 80/80/84/104; 62/61.8/66/72; 61/61.2/66/71 | B+4; B+4; B+4 | — |
| R0-dev / object size; 293 | 38/45/41/2048; 35/35.4/40/51; 34/41.9/39/2048 | 43/99.3/46/16384; 40/40.7/46/56; 40/96.2/45/16384 | 544 and 200: F/H/L each 1 of 293 |
| away / easy; 50 | 59/59.2/61/62; 94/94.4/98/102 | unavailable; B+4 | — |
| away / hard; 50 | 59/59.9/62/64; 99/99.3/102/113 | unavailable; B+4 | — |
| away / medium; 50 | 66.5/67.1/69/72; 96.5/97.2/102/105 | unavailable; B+4 | — |
| forward / easy; 50 | 57/57.2/59/59; 67/65.9/70/76 | unavailable; B+4 | — |
| forward / hard; 50 | 57/58.1/60/62; 69/70/74/82 | unavailable; B+4 | — |
| forward / medium; 50 | 65/65.4/67/70; 68/68.4/73/76 | unavailable; B+4 | — |
| VSTI / V1; 150 | 78/78.2/81/84; 131/130.9/136/144 | B+4; B+4 | — |
| VSTI / V2; 150 | 69/69.7/72/75; 110/110.1/114/120 | B+4; B+4 | — |
| VSTI / V3; 150 | 61/61.4/63/66; 89/89.6/93/99 | B+4; B+4 | — |
| VSTI / LR; 150 | 59/62.8/77/113; 87/87.7/92/102 | B+4; B+4 | — |
| VSTI / NF; 150 | 93/88.9/100/304; 89/89.1/93/98 | B+4; B+4 | — |
| VSTI / UD; 150 | 63/83.4/96/2048; 90/90.5/95/100 | 67/182.9/100/16384; B+4 | 544: F/H/L each 1 of 150 |
| routed A / camera displacement; 150 | **Routed output:** 166/164.1/166/166; identical at 200 | No paired arms | No detected loops |
| routed A / movement direction; 150 | **Routed output:** 202/203.6/206/206; identical at 200 | No paired arms | No detected loops |
| routed A / camera rotation; 150 | **Routed output:** 90/89.9/93/95; identical at 200 | No paired arms | No detected loops |
| routed A / absolute distance; 150 | **Routed output:** 318/353.6/343/2175; 309.5/354.5/338/2057 | No paired arms | L: 3 of 150; 10 of 150 |
| routed A / room size; 36 | **Routed output:** 66/189.3/196/2057; 64/65.2/70/71 | No paired arms | No detected loops |
| routed B / room size; 134 | **Routed output:** 64/234.6/296/2116; 66/66.7/71/88 | No paired arms | L: 2 of 134; 0 of 134 |

Routed call distributions, in the same tuple order: each camera type is **1/1/1/1** at both steps; absolute distance is **3/3/3/3; 3/1.76/3/3**; room A is **2/1.8/2/2; 0/0/0/0**; room B is **2/1.9/2/2; 0/0/0/0**. Every camera and distance read finishes `eos`, including 150 of 150 distance items at each step. Room A finishes `max_calls` on 29 of 36 and `eos` on 7 of 36 at 544; room B does so on 115 of 134 and 19 of 134. At 200, room A and B finish `eos` on 36 of 36 and 134 of 134. Routed F/H flags and exact think-token counts are unavailable.

**3. Score, length, token efficiency, and trace-form census.** Short/long scores use the lowest/highest third after excluding both force-closed and detected looping items; ties sort by item ID. The parenthesis gives each third’s membership in the retained population. `T; Δ; T/pt` gives total step-200 think tokens, score change from 544, and tokens per gained percentage point. A negative Δ is a regression, not useful token efficiency. Routed T uses output-token records.
Census cells give the three most frequent **exact normalized strings**, in descending frequency, as **signature: n of N @ score%**. Object names and numeric values become placeholders; whitespace and case are normalized; answers and printed tool-response bodies are excluded. Signatures below summarize those strings: “angle” is the old measured-angle form; “keep,” “away,” and “opposite” name the facing clause; “then” names the alternate object-list wording. Counts retain differences in sentence wording, relation, unit, and list length.
At step 200, ON16k scores equal B2048 everywhere except the three explicit B/ON cells below. B2048 wins on **3 of 150** dev-S1 counting items, **48 of 139** relative-count items, and **12 of 385** R0-dev counting items; ON16k wins on **0 of 4,320** paired items. At 100, B2048 wins on **69 of 139** relative-count items, scoring 64.03 versus 14.39, and **8 of 385** R0 counting items, scoring 46.68 versus 45.09. At 544, ON16k wins on **1 of 385** R0 counting items, scoring 51.04 versus 50.78; B2048 wins on **1 of 293** R0 size items, scoring 59.08 versus 59.04. All other available paired scores agree item by item.

| Set / type | 200 score: B / ON if unequal | Short / long score; each third | T; Δ; T/pt | 544 top skeletons | 100 top skeletons | 200 top skeletons |
|---|---|---|---|---|---|---|
| dev-S1 / absolute distance | unavailable | unavailable | unavailable | Repeated gap prefix: 10 of 150 @0; answer tag: 9 of 150 @22.2; attributed answer tag: 7 of 150 @0 | unavailable | unavailable |
| dev-S1 / counting | 56.33 / 55.53 | 81/52; 40 of 122 | 63,782; −6.47; no gain | Match frames4/5/9: 10 of 150 @94; 8 of 150 @81.2; 6 of 150 @90 | List2: 26 of 150 @89.6; locate2: 15 of 150 @81.3; list2-right: 15 of 150 @86 | List2: 31 of 150 @84.2; list2-right: 14 of 150 @82.9; list2-left: 8 of 150 @85 |
| dev-S1 / easy | 93.33 | 98/90; 50 of 150 | 9,406; +2.00; 4,703 | Angle right-front/left-front/left-behind: 62 of 150 @93.5; 61 of 150 @93.4; 17 of 150 @94.1 | Locate, relation-before-heading right: 42 of 150 @90.5; heading-first left/right: 41 of 150 @92.7; 30 of 150 @90 | Find keep-right/keep-left/then-left: 46 of 150 @93.5; 46 of 150 @93.5; 14 of 150 @92.9 |
| dev-S1 / hard | 82.67 | 86/82; 50 of 150 | 10,250; −1.33; no gain | Angle left-front/right-front/left-behind: 67 of 150 @80.6; 54 of 150 @87; 16 of 150 @87.5 | Locate FL; relation-first FR; heading-first FR: 33 of 150 @72.7; 33 of 150 @81.8; 23 of 150 @69.6 | Find keep-FL/keep-FR/then-FL: 33 of 150 @81.8; 29 of 150 @82.8; 17 of 150 @94.1 |
| dev-S1 / medium | 88.00 | 92/90; 50 of 150 | 9,824; −1.33; no gain | Angle left/right/back: 80 of 150 @90; 67 of 150 @89.6; 3 of 150 @66.7 | Relation-first slight-left/out-left; heading-first slight-left: 17 of 150 @94.1; 14 of 150 @85.7; 14 of 150 @100 | Keep slight-left/out-left/out-right: 17 of 150 @94.1; 17 of 150 @94.1; 15 of 150 @86.7 |
| dev-S1 / relative distance | 73.33 | 80/72; 50 of 150 | 8,713; +2.67; 3,267 | Metric list, location variants: 30 of 150 @70; 25 of 150 @80; 12 of 150 @58.3 | Order, frame/left/right location: 53 of 150 @67.9; 13 of 150 @84.6; 9 of 150 @55.6 | Order, frame/left/right location: 48 of 150 @79.2; 14 of 150 @71.4; 9 of 150 @77.8 |
| dev-S1 / object size | 69.40 | 68.4/66; 50 of 150 | 5,484; +0.67; 8,226 | Box/inches, first-image/kitchen/frame: 6 of 150 @58.3; 5 of 150 @80; 5 of 150 @52 | Frame estimate cm/inches/m: 14 of 150 @77.1; 11 of 150 @73.6; 9 of 150 @82.2 | Frame estimate cm/m/inches: 10 of 150 @74; 6 of 150 @75; 6 of 150 @71.7 |
| dev-S1 / relative count | 64.75 / 30.22 | 50/54.55; 22 of 67 | 144,760; +2.88; 50,304 | Visible strings tie: match/equal, compare/outnumber, longer match list; each 1 of 139 @0/100/0 respectively | Unfinished left/time/right lists: 37 of 139 @73; 10 of 139 @90; 3 of 139 @66.7 | Unfinished left/frame-left/frame-right lists: 10 of 139 @100; 8 of 139 @50; 7 of 139 @85.7 |
| dev-S1 / relative size | 90.00 | 92/94; 50 of 150 | 6,663; −1.33; no gain | Box-m shorter/box-m longer/box-cm longer: 7 of 150 @85.7; 2 of 150 @100; 2 of 150 @50 | Longer+conclusion/relation only/repeated relation: 24 of 150 @83.3; 9 of 150 @100; 6 of 150 @66.7 | Longer+conclusion/compare instruction/largest selection: 15 of 150 @80; 12 of 150 @83.3; 11 of 150 @100 |
| dev-S1 / room size | unavailable | unavailable | unavailable | Point+area: 4 of 36 @50; scalar-only text: 2 of 36 @10; area/box prefix: 1 of 36 @10 | unavailable | unavailable |
| dev-S1 / route planning | 80.67 | 90/74; 50 of 150 | 8,974; +2.00; 4,487 | Empty think: 150 of 150 @78.7 | One-turn right/left/back: 24 of 150 @79.2; 24 of 150 @91.7; 13 of 150 @92.3 | One-turn right/back/left: 29 of 150 @82.8; 17 of 150 @94.1; 15 of 150 @93.3 |
| R0-dev / appearance order | 62.20 | 64.63/63.41; 82 of 246 | 14,560; +5.69; 2,558 | Four frames, then order: 246 of 246 @56.5 | Same: 246 of 246 @59.3 | Same: 246 of 246 @62.2 |
| R0-dev / counting | 53.74 / 51.71 | 73.2/50.2; 100 of 301 | 186,089; +2.96; 62,846 | Match frames3/4/2: 18 of 385 @73.3; 18 of 385 @68.9; 17 of 385 @83.5 | List2/locate2/count-once instruction: 75 of 385 @85.7; 59 of 385 @82.7; 36 of 385 @38.3 | List2/locate2/unfinished frame list: 109 of 385 @85.8; 24 of 385 @52.9; 10 of 385 @0 |
| R0-dev / easy | 78.65 | 79.69/84.38; 64 of 192 | 14,379; +13.02; 1,104 | Angle left-front/right-front/right-front facing variant: 45 of 192 @80; 33 of 192 @72.7; 26 of 192 @57.7 | Locate keep-right/keep-left/away right-to-left: 52 of 192 @69.2; 37 of 192 @83.8; 33 of 192 @54.5 | Find keep-left/keep-right/away right-to-left: 43 of 192 @83.7; 36 of 192 @66.7; 23 of 192 @69.6 |
| R0-dev / hard | 57.81 | 56.25/65.62; 64 of 192 | 15,390; +11.98; 1,285 | Angle right-front/left-front/left-front facing variant: 52 of 192 @73.1; 51 of 192 @58.8; 31 of 192 @9.7 | Locate FR/relation-first FR/FL: 34 of 192 @70.6; 29 of 192 @65.5; 22 of 192 @63.6 | Away FL-to-BR/toward FL/away FR-to-BL: 21 of 192 @76.2; 20 of 192 @55; 17 of 192 @70.6 |
| R0-dev / medium | 64.95 | 53.12/62.5; 64 of 194 | 15,165; +15.98; 949 | Angle right/left/right facing variant: 67 of 194 @56.7; 56 of 194 @71.4; 36 of 194 @25 | Relation-first out-right/away slight-right/away out-right: 23 of 194 @69.6; 22 of 194 @86.4; 15 of 194 @33.3 | Toward out-right/away slight-right/away out-left: 21 of 194 @47.6; 15 of 194 @93.3; 15 of 194 @53.3 |
| R0-dev / relative distance | 67.38 | 69.89/69.89; 93 of 279 | 17,063; +2.51; 6,801 | Metric-list variants: 33 of 279 @66.7; 33 of 279 @75.8; 24 of 279 @58.3 | Frame-closest/frame-farthest/left-closest: 80 of 279 @63.7; 37 of 279 @67.6; 15 of 279 @60 | Frame-closest/frame-farthest/left-closest: 84 of 279 @69; 40 of 279 @80; 13 of 279 @46.2 |
| R0-dev / object size | 58.29 | 57.84/55.15; 97 of 292 | 12,291; −0.78; no gain | Box-cm, frame/first-frame/object location: 69 of 293 @63.9; 38 of 293 @64.2; 19 of 293 @70.5 | Estimate-cm, frame/left/right: 102 of 293 @63.8; 34 of 293 @54.7; 13 of 293 @56.9 | Estimate-cm, frame/left/first-frame: 98 of 293 @61.2; 33 of 293 @46.7; 15 of 293 @72 |
| away / easy | 94.00 | 81.25/100; 16 of 50 | 4,721; +56; 84 | Angle right-front/left-front/right-behind: 22 of 50 @45.5; 19 of 50 @31.6; 6 of 50 @50 | unavailable | Away left/right; opposite-right: 19 of 50 @89.5; 11 of 50 @90.9; 10 of 50 @100 |
| away / hard | 82.00 | 87.5/87.5; 16 of 50 | 4,966; +76; 65 | Angle left-front/right-front/right-behind: 25 of 50 @4; 16 of 50 @12.5; 3 of 50 @0 | unavailable | Away FR/FL; opposite-FL: 17 of 50 @76.5; 14 of 50 @85.7; 5 of 50 @80 |
| away / medium | 90.00 | 93.75/87.5; 16 of 50 | 4,858; +70; 69 | Angle right/left/right variant: 25 of 50 @28; 19 of 50 @10.5; 3 of 50 @0 | unavailable | Away out-left/slight-left/out-right: 11 of 50 @100; 9 of 50 @88.9; 7 of 50 @85.7 |
| forward / easy | 98.00 | 100/100; 16 of 50 | 3,297; 0; undefined | Angle left-front/right-front/left-behind: 22 of 50 @95.5; 20 of 50 @100; 6 of 50 @100 | unavailable | Seen keep-right/keep-left; find keep-left: 12 of 50 @100; 11 of 50 @90.9; 8 of 50 @100 |
| forward / hard | 86.00 | 87.5/75; 16 of 50 | 3,498; −6; no gain | Angle left-front/right-front/left-behind: 19 of 50 @94.7; 17 of 50 @88.2; 8 of 50 @87.5 | unavailable | Toward FL/then keep-FL/then toward-FR: 6 of 50 @83.3; 5 of 50 @100; 4 of 50 @75 |
| forward / medium | 96.00 | 100/100; 16 of 50 | 3,419; +2; 1,710 | Angle left/right/back: 29 of 50 @96.6; 19 of 50 @94.7; 2 of 50 @50 | unavailable | Seen toward out-left/slight-left/slight-right: 10 of 50 @90; 6 of 50 @100; 5 of 50 @100 |
| VSTI / V1 | 38.00 | 36/30; 50 of 150 | 19,629; +13.33; 1,472 | Metric nearest/equal: 149 of 150 @24.8; 1 of 150 @0 | unavailable | Locate+order; “frame N of N” twice/once: 143 of 150 @37.8; 6 of 150 @50; 1 of 150 @0 |
| VSTI / V2 | 37.33 | 44/24; 50 of 150 | 16,510; +5.33; 3,096 | Metric nearest: 150 of 150 @32 | unavailable | Locate+order; “frame N of N”: 149 of 150 @36.9; 1 of 150 @100 |
| VSTI / V3 | 59.33 | 68/54; 50 of 150 | 13,444; +4; 3,361 | Metric nearest: 150 of 150 @55.3 | unavailable | Locate+order; “frame N of N”: 147 of 150 @59.2; 3 of 150 @66.7 |
| VSTI / LR | 70.00 | 88/60; 50 of 150 | 13,152; +16; 822 | Angle right-behind/left-front/stand-right-behind: 7 of 150 @71.4; 7 of 150 @14.3; 6 of 150 @16.7 | unavailable | Viewpoint-right/left/right with “of N”: 104 of 150 @66.3; 38 of 150 @84.2; 5 of 150 @60 |
| VSTI / NF | 62.67 | 54/70; 50 of 150 | 13,358; +11.33; 1,179 | Box-distance far/box-gap far/box-distance near: 7 of 150 @57.1; 6 of 150 @33.3; 4 of 150 @75 | unavailable | Nearer relation, farther/nearer conclusion; nearer with “of N”: 94 of 150 @66; 54 of 150 @55.6; 2 of 150 @100 |
| VSTI / UD | 82.67 | 82/84; 50 of 150 | 13,570; +23.33; 582 | Angle-right/metres-above/angle-right concluding up: 5 of 150 @20; 4 of 150 @75; 3 of 150 @66.7 | unavailable | Horizon higher/lower/lower with “of N”: 88 of 150 @77.3; 54 of 150 @90.7; 3 of 150 @100 |
| routed A / displacement | 81.87; no ON comparison | 85.2/83; 50 of 150 | 24,608; −0.47; no gain | Preamble, move, copy-distance: 150 of 150 @82.3 | unavailable | Same: 150 of 150 @81.9 |
| routed A / movement direction | 94.67; no ON comparison | 94/92; 50 of 150 | 30,541; 0; undefined | Move+component maximum forward/left/backward: 41 of 150 @90.2; 37 of 150 @97.3; 36 of 150 @94.4 | unavailable | Same memberships and scores |
| routed A / rotation | 76.27; no ON comparison | 53.4/93; 50 of 150 | 13,490; +0.67; 20,235 | Turn, “degrees”/“degree”: 145 of 150 @77.5; 5 of 150 @20 | unavailable | Turn, “degrees”/“degree”: 143 of 150 @79.2; 7 of 150 @15.7 |
| routed A / absolute distance | 50.27; no ON comparison | 40.22/54.35; 46 of 140 | 53,179; +22; 2,417 | Ground-ground-gap metres/inches/gap-wording: 106 of 150 @25.8; 11 of 150 @29.1; 11 of 150 @11.8 | unavailable | Ground-ground-gap metres/feet/inches: 48 of 150 @46.2; 29 of 150 @63.4; 9 of 150 @68.9 |
| routed A / room size | 66.94; no ON comparison | 57.5/70; 12 of 36 | 2,349; +55.28; 42 | Ground-area/point-gap/point-area: 6 of 36 @0; 5 of 36 @0; 5 of 36 @60 | unavailable | Landmarks-between metres/feet; landmarks-side metres: 23 of 36 @63.9; 4 of 36 @65; 3 of 36 @66.7 |
| routed B / room size | 64.40; no ON comparison | 63.41/65.68; 44 of 134 | 8,933; +57.84; 154 | Ground-ground/point-ground-box/mode-gap: 16 of 134 @0; 13 of 134 @0; 9 of 134 @0 | unavailable | Landmarks-between/side/“among these landmarks”: 70 of 134 @63.6; 36 of 134 @61.7; 10 of 134 @64 |

Only **appearance order, 246 of 246**, and **camera displacement, 150 of 150**, have one exact step-200 skeleton under this normalization. Every other type has a second string; many differences are wording or relation values, not a second reasoning method. VSTI V1–V3 mainly differ by whether the frame denominator is repeated. The routed distance direct alternative copies relative-distance ordering; its detected loops occur on **10 of 150** items, all without calls. At 544, VSTI LR/UD contain direction-angle forms, and NF contains absolute-distance box-gap forms. These are observable cross-type similarities; their training provenance is a **HYPOTHESIS**, not established by string matching.

**4. Loops and their cost.** The table gives verbatim beginnings or repeated spans; ellipses truncate long physical lines. Most counting loops occupy one line, so three distinct loop lines do not exist. For relative count’s terminating example, the first three lines are shown with `⏎`.

| Looping type | Two trace excerpts and the repeated content |
|---|---|
| Counting | R0-dev 200 `022bf0575cbf5e5bdd69bde9`: “Step 1: locate each distinct shelf at its first appearance: frame 87.4; frame 87.4; frame 87.4; …”; `028611c66f4e3d25d3a857f2`: “Step 1: locate each distinct box at its first appearance: frame 10; frame 10; frame 10; …”. The instance-list entry repeats. |
| Relative count | dev-S1 200 `vsi590k_087487`: “Step 1: list the distinct chair instances by first appearance: left; left; left; …”. `vsi590k_087614`: “Step 1: list the distinct chair instances by first appearance: 26.0 s (right); 26.0 s (right); … ⏎ Step 2: list the distinct trash bin instances by first appearance: 2.6 s (right); 26.0 s (right); … ⏎ Step 3: compare the counts: chair count is greater than trash bin count.” The latter finishes after 519 think tokens and scores 1. |
| Object size | R0-dev 200 `16884daee5676e0113e6102a`: “Step 1: find the keyboard, first seen in the left view of the left view of the left view …”; R0-dev 544 `296abef79d35976277095e10`: “Step 1: find the windowsill (first seen in the first seen in the first seen …”. The location clause repeats. |
| VSTI UD | At 544, `419285d69ea5a66222d6e0b4` repeats: “Step 7: the box distance is 6.66 m. Step 8: the box distance is 6.66 m; the box gap rule says …”. Only **1 of 150** items supplies a detected loop, so no second example exists. |
| Absolute distance | Routed A 200 `vsi590k_042644` repeats the nearest-to-farthest list containing “then shower curtain, then bathroom vanity, then bathtub, …”; `vsi590k_044622` repeats “then dresser, then computer tower, then floor lamp, then shelf, …”. These are candidate-list loops, not repeated tool calls. |
| Room size | Routed B 544 `r0_40cd47aa64e896c97bb6` repeats XML-like blocks including `<state a="wall" b="wall" c="wall" d="wall" rule="box_grid_5cm"/>`; `room_scene0587_01` repeats blocks including `<box x="-2.00" y="0.50" z="1.25" mode="room">` and `<grid x="-2.00" y="0.50" z="1.25" rule="box_grid_5cm">`. |

At 200, force-closed counting contributes **17.87 type points** of error on dev-S1, with imperfect scores on **27 of 150** items; relative count contributes **11.51 points**, on **16 of 139**; R0 counting contributes **19.53 points**, on **78 of 385**; R0 size contributes **0.34 points**, on **1 of 293**. These are error masses, not recoverable gains. Detected loops contribute respectively **15.93, 11.51, 18.49, and 0.34 points**; routed-distance loops contribute **2.47 points**. Do not add loop and force-close costs: their memberships overlap. Longer non-runaway traces score worse for counting, route planning, VSTI V1–V3 and LR; R0 directions, VSTI NF, and several routed types show the opposite association.

**5. Three changes for vehicle N.** Only the existing B2048-versus-ON16k comparison establishes an accuracy-preserving reduction; the wording changes below require an ablation.
1. **Keep the 2,048 close and teach bounded counting traces.** At 200, **176 of 4,320** direct items hit ON16k’s cap. Closing them saves approximately **14,336 tokens per capped item**, less the short forced answer, without observed score loss at this checkpoint. Reinforce the kept family `object_counting|r1g|rows_rebuild_d0_v1`: its sample target says, “locate the distinct instances of box; count each once across the frames.” The census reports **2,617 of 9,253** rows kept. **HYPOTHESIS:** bounded instance evidence prevents recurrence; removing list rows alone has not established that effect.
2. **Compress VSTI Locate lines while retaining every cited frame.** Rewrite “Step 2: locate the stool, first seen in frame 2” as “stool: frame 2,” and keep the viewpoint and relation. Apply to the six `*|vsti_rel_v4|None` families, with **11,799 of 11,926** rows kept. **Estimated** savings are **38/28/18 tokens** per V1/V2/V3 item and **19/18/19** per LR/NF/UD item. These estimates scale removed characters by each trace’s observed token density. The sampled targets explicitly repeat this Locate sentence. **HYPOTHESIS:** preserving its information preserves accuracy.
3. **Remove camera explanations that precede the executable call.** Retain `<move>`/`<turn>`, printed responses, sign conventions where needed, and option mapping. Current prefixes explain the pose head and then restate the frame pair. **Estimated** savings are about **102/104/46 tokens per displacement/movement/rotation item** if the entire prefix is removed; retaining a short convention statement reduces those savings. The traces use the same camera forms at both checkpoints. This is the least certain accuracy-preserving change: identical wording does not prove the preamble is causally unnecessary, and the supplied v7 family samples do not identify its training quota.

**6. Label or scoring defects.** None established. A correct B2048 answer beside an unfinished ON16k trace is not itself a scoring defect: they are different arms. For example, relative-count item `vsi590k_087487` has B2048 score 1 despite the ON16k list loop. Base direct dev-S1 also has missing thinking prefixes on **56 of 150** distance, **2 of 150** counting, **5 of 139** relative-count, and **20 of 36** room items; their visible answers are not complete trace skeletons.

**8. Not established.** Length correlations do not show that shortening reasoning improves answers; question difficulty, subtype, units, and option structure can explain them. Exact tokenizer savings and accuracy after rewriting require paired generation with the revised traces. Routed `tokens` are output records, not isolated think-token counts, and their `eos` flags do not exclude long repetitive generation. Base missing prefixes make its loop counts lower bounds. The census normalizes names recognized from questions, options, and trace syntax; unusual aliases can split otherwise equivalent forms. No official benchmark items were used.

**Appendix — CLASSIFIER**

```python
# Run with /scratch/jjyeung/envs/planner_local_v1/bin/python.
import os, sys, math, statistics as S, resource
from collections import Counter
os.environ["OPENBLAS_NUM_THREADS"] = "1"
sys.dont_write_bytecode = True
resource.setrlimit(resource.RLIMIT_AS, (3500 * 1024**2,) * 2)
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K

def distribution(values):
    v = sorted(x for x in values if x is not None)
    if not v:
        return None
    return [round(S.median(v), 1), round(S.mean(v), 1),
            v[math.ceil(.9 * len(v)) - 1], max(v)]

def looping(r):
    words = (r["text"] or "").split("</think>")[0].lower().split()
    counts = Counter(tuple(words[i:i+8])
                     for i in range(max(0, len(words) - 7)))
    return max(counts.values(), default=0) >= 10

for name in ["dev-S1", "R0-dev", "away", "forward", "vsti", "A", "B"]:
    steps = [544, 100, 200] if name in ["dev-S1", "R0-dev"] else [544, 200]
    for step in steps:
        run = "S1" if step == 544 else "R1"
        if name in ["dev-S1", "R0-dev"]:
            rows = K.direct(run, step, name)
        elif name in ["away", "forward"]:
            rows = K.facing(run, step, name)
        elif name == "vsti":
            rows = K.vsti(run, step)
        else:
            rows = K.routed(step, part=name)
        for typ in sorted({r["type"] for r in rows}):
            rs = [r for r in rows if r["type"] == typ]
            n = len(rs)
            ls = [r for r in rs if looping(r)]
            count = lambda k: f"{k} of {n}"
            result = dict(set=name, step=step, type=typ, N=count(n),
                          loop=count(len(ls)))
            if name in ["A", "B"]:
                result.update(tokens=distribution(r["tokens"] for r in rs),
                              calls=distribution(r["ncalls"] for r in rs),
                              finish={k: count(v) for k, v in
                                      Counter(r["finish"] for r in rs).items()})
            else:
                on = not (step == 544 and name in ["dev-S1", "away", "forward"])
                result.update(B=distribution(r["think_tokens"] for r in rs),
                              ON=distribution(r["out_tokens"] for r in rs) if on else None,
                              forced=count(sum(bool(r["forced_close"]) for r in rs)),
                              cap=count(sum(bool(r["hit_cap"]) for r in rs)) if on else None,
                              loop_below=count(sum(r["think_tokens"] is not None and
                                                   r["think_tokens"] < 2048 for r in ls)))
            print(result)
```