The audit found 224 never-proposed operand instances among 1056 in 93 GT-covered captures. They occur in 2249 questions, including 337 of the directly paired questions.

An operand instance is (capture, queried name, annotation instance ID). Names follow the existing executor’s vocabulary, so a broad query can require several annotated subcategories. Physical IDs are also counted below. A question with a missing instance is potentially affected; its answer is not necessarily wrong. Only the grant experiment measures its score effect.

Physical (capture, ID) instances: 1047; never for at least one queried name: 223. The other 59 cached captures have no aligned GT and cannot enter this recall audit.

Matching uses the baseline route tool’s greedy one-to-one IoU > 0.5 rule, on masks downsampled by two to the GT raster. Any nonzero GT area counts as visible; ≥154 GT pixels counts as usable by the frozen program. Largest-view areas below use GT pixels; the input-image equivalent is four times larger. Every visible frame has its best IoU, conditional score, joint score, SAM presence, retained count and match flag in PER_INSTANCE.jsonl. A score is null when no retained proposal overlaps at all; discarded masks are unavailable.

Acceptance means that the selector’s exported unique/counting mask set overlaps this instance above IoU 0.5 in at least one frame. It is a geometric acceptance measurement, not a claim that a linked track has pure identity. Non-counting questions may remain answerable with another instance of the same name.

The cache retains joint score ≥0.2, at most 10 proposals per phrase/frame. The linker separately requires conditional score ≥0.3. All 200 conditional scores remain cached, but discarded masks do not. Therefore a low score is evidence of censoring, not evidence that an unseen mask would match.

The groups below are mutually exclusive diagnostics, in this precedence: no visible pixels; largest area <154; at most two usable views; non-exact prompt/label relationship; SAM presence <0.2 on every visible frame; unresolved. Lexical mismatch can coexist with size or sparse visibility and appears separately in the marginal tables. No group establishes a causal explanation from pixels.

| Diagnostic group | Never instances | Questions / paired questions | Abs grant pp [95% CI]; share of loss | Count grant pp [95% CI]; share of loss |
|---|---:|---:|---|---|
| no_visible_pixels | 22 | 281 / 33 | +0.00 [+0.00, +0.00]; 0.0% | +0.00 [+0.00, +0.00]; 0.0% |
| below_program_size | 23 | 330 / 46 | +0.00 [+0.00, +0.00]; 0.0% | +0.00 [+0.00, +0.00]; 0.0% |
| few_views | 74 | 1199 / 162 | +8.82 [+3.17, +14.24]; 31.2% | +8.57 [+3.87, +14.56]; 37.0% |
| lexical_mismatch | 13 | 496 / 77 | +1.84 [+0.00, +5.29]; 6.5% | +0.00 [+0.00, +0.00]; 0.0% |
| presence_gate | 11 | 440 / 58 | +1.84 [+0.00, +3.98]; 6.5% | +1.10 [+0.00, +4.05]; 4.7% |
| unresolved | 81 | 986 / 162 | +14.34 [+6.84, +21.98]; 50.7% | +12.31 [+7.16, +17.87]; 53.1% |

| Grant group | Paired questions whose score improves | Whose score worsens |
|---|---:|---:|
| no_visible_pixels | 0 | 0 |
| below_program_size | 0 | 0 |
| few_views | 76 | 0 |
| lexical_mismatch | 13 | 0 |
| presence_gate | 14 | 0 |
| unresolved | 93 | 1 |

Each grant starts from gt_ever_proposed and adds only that group’s full GT masks. It then runs the unchanged frozen programs and route-table pairing, with 10,000 physical-room bootstrap draws. These are ideal-mask recovery ceilings for the specified group, not predicted deployment gains or mathematical score bounds. Groups can interact; their effects and loss shares need not sum to 100%. GT masks can also hurt a score.

The reference never-proposed contrasts are 28.29 pp on absolute distance (76 GT-covered pairs) and 23.19 pp on counting (91 pairs). They are not averages over all 150 pairs of each type. The audit reproduced both GT endpoints on 6846 per-item/arm rows with zero prediction or score mismatches.

The grant route JSONs in analysis/ retain the full direct pairing, substituting the diagnostic arm only where GT exists. CAUSE_CONTRASTS.json isolates each group against gt_ever_proposed on the correct GT-covered denominator. They are counterfactual tables, not routing decisions.

| Dataset | Ever recall | Usable frame recall | Proposal precision | Unique accepted / count accepted |
|---|---:|---:|---:|---:|
| All | 78.8% | 60.7% | 30.4% | 337 / 601 |
| arkitscenes | 79.9% | 57.8% | 31.2% | 175 / 270 |
| scannet | 91.6% | 66.7% | 34.0% | 77 / 178 |
| scannetppv2 | 66.3% | 54.3% | 24.4% | 85 / 153 |

Proposal precision counts retained proposals overlapping a queried annotated instance above IoU 0.5. It is annotation-relative: incomplete labels can classify a real object as unmatched. Frame recall uses one-to-one matching, while precision counts all matching proposals.

The retention audit finds extra score-eligible candidates at floor 0.05/cap 30 in visible frames of 178 never-proposed instances. 41 have at least one cap-clipped visible frame. For 24 visible misses, even the maximum raw joint score stays below 0.05 in every visible frame, so that dense setting alone cannot add any mask there. These figures measure eligibility only; discarded masks have no stored geometry.

The GT matcher has a concrete semantic error: 13 instances for query ‘ceiling light’ bind to annotation ‘ceiling’. tplib.match_labels falls back to substring containment, so it treats the room surface as the lamp. These targets touch 433 questions (69 paired). Ten lie in lexical_mismatch and three in few_views. All +1.84 pp of the lexical group’s paired absolute-distance gain comes from two such questions, vsi590k_163060 and vsi590k_161427. That is a measurement artifact, not a justified synonym-recovery ceiling. The three remaining lexical misses (two table→desk and one counter→kitchen counter) recover 0.00 pp on the paired absolute-distance and counting sets. Do not add ‘ceiling’ as a lamp prompt to optimize this metric.

Excluding every paired question exposed to this suspect mapping leaves the never-proposed contrast at 28.77 pp on object_abs_distance (73 pairs; 95% CI [17.00, 38.29]); 23.79 pp on object_counting (87 pairs; 95% CI [16.15, 32.71]). This changes the denominator; it is a sensitivity check, not a replacement of the baseline route table.

Dataset

| Group | Instances | Never proposed | Never % | Questions with a miss |
|---|---:|---:|---:|---:|
| arkitscenes | 368 | 74 | 20.1 | 506 |
| scannet | 323 | 27 | 8.4 | 249 |
| scannetppv2 | 365 | 123 | 33.7 | 1494 |

Queried category

| Group | Instances | Never proposed | Never % | Questions with a miss |
|---|---:|---:|---:|---:|
| backpack | 5 | 0 | 0.0 | 0 |
| basket | 1 | 0 | 0.0 | 0 |
| bathtub | 15 | 0 | 0.0 | 0 |
| bed | 25 | 4 | 16.0 | 182 |
| blanket | 7 | 2 | 28.6 | 20 |
| bookshelf | 5 | 0 | 0.0 | 0 |
| bowl | 8 | 1 | 12.5 | 10 |
| bucket | 1 | 1 | 100.0 | 24 |
| ceiling light | 13 | 13 | 100.0 | 433 |
| chair | 336 | 48 | 14.3 | 277 |
| clock | 3 | 0 | 0.0 | 0 |
| closet | 1 | 0 | 0.0 | 0 |
| coat hanger | 1 | 1 | 100.0 | 81 |
| computer mouse | 8 | 0 | 0.0 | 0 |
| computer tower | 3 | 1 | 33.3 | 18 |
| counter | 3 | 1 | 33.3 | 60 |
| cup | 2 | 1 | 50.0 | 96 |
| cutting board | 1 | 1 | 100.0 | 70 |
| desk | 11 | 2 | 18.2 | 2 |
| dishwasher | 2 | 0 | 0.0 | 0 |
| door | 70 | 16 | 22.9 | 155 |
| exhaust fan | 2 | 2 | 100.0 | 74 |
| fireplace | 5 | 0 | 0.0 | 0 |
| guitar | 1 | 1 | 100.0 | 39 |
| headphones | 2 | 1 | 50.0 | 84 |
| heater | 18 | 18 | 100.0 | 459 |
| keyboard | 10 | 0 | 0.0 | 0 |
| lamp | 16 | 5 | 31.2 | 22 |
| laptop | 6 | 1 | 16.7 | 25 |
| microwave | 4 | 0 | 0.0 | 0 |
| mirror | 4 | 2 | 50.0 | 40 |
| monitor | 15 | 0 | 0.0 | 0 |
| nightstand | 1 | 0 | 0.0 | 0 |
| paper bag | 2 | 2 | 100.0 | 121 |
| pillow | 16 | 6 | 37.5 | 103 |
| plant | 21 | 8 | 38.1 | 56 |
| power strip | 1 | 1 | 100.0 | 42 |
| printer | 2 | 0 | 0.0 | 0 |
| radiator | 1 | 1 | 100.0 | 22 |
| refrigerator | 23 | 0 | 0.0 | 0 |
| shoe rack | 2 | 1 | 50.0 | 31 |
| shoes | 29 | 12 | 41.4 | 181 |
| slippers | 6 | 1 | 16.7 | 73 |
| sofa | 54 | 3 | 5.6 | 29 |
| stool | 18 | 5 | 27.8 | 72 |
| stove | 21 | 5 | 23.8 | 35 |
| suitcase | 4 | 1 | 25.0 | 24 |
| table | 122 | 31 | 25.4 | 135 |
| table lamp | 3 | 1 | 33.3 | 18 |
| telephone | 7 | 2 | 28.6 | 22 |
| toilet | 24 | 4 | 16.7 | 93 |
| towel | 6 | 0 | 0.0 | 0 |
| trash bin | 18 | 2 | 11.1 | 79 |
| trash can | 11 | 8 | 72.7 | 202 |
| tv | 38 | 2 | 5.3 | 19 |
| washer | 8 | 3 | 37.5 | 91 |
| whiteboard | 4 | 1 | 25.0 | 34 |
| window | 10 | 2 | 20.0 | 7 |

Annotation category

| Group | Instances | Never proposed | Never % | Questions with a miss |
|---|---:|---:|---:|---:|
| backpack | 5 | 0 | 0.0 | 0 |
| basket | 1 | 0 | 0.0 | 0 |
| bathtub | 15 | 0 | 0.0 | 0 |
| bed | 25 | 4 | 16.0 | 182 |
| blanket | 7 | 2 | 28.6 | 20 |
| bookshelf | 5 | 0 | 0.0 | 0 |
| bowl | 8 | 1 | 12.5 | 10 |
| bucket | 1 | 1 | 100.0 | 24 |
| ceiling | 13 | 13 | 100.0 | 433 |
| chair | 334 | 48 | 14.4 | 277 |
| clock | 3 | 0 | 0.0 | 0 |
| closet | 1 | 0 | 0.0 | 0 |
| coat hanger | 1 | 1 | 100.0 | 81 |
| computer tower | 3 | 1 | 33.3 | 18 |
| couch | 7 | 0 | 0.0 | 0 |
| counter | 2 | 0 | 0.0 | 0 |
| cup | 2 | 1 | 50.0 | 96 |
| cutting board | 1 | 1 | 100.0 | 70 |
| desk | 23 | 4 | 17.4 | 5 |
| dishwasher | 2 | 0 | 0.0 | 0 |
| door | 70 | 16 | 22.9 | 155 |
| end table | 3 | 0 | 0.0 | 0 |
| exhaust fan | 2 | 2 | 100.0 | 74 |
| fireplace | 5 | 0 | 0.0 | 0 |
| guitar | 1 | 1 | 100.0 | 39 |
| headphones | 2 | 1 | 50.0 | 84 |
| heater | 18 | 18 | 100.0 | 459 |
| keyboard | 10 | 0 | 0.0 | 0 |
| kitchen counter | 1 | 1 | 100.0 | 60 |
| lamp | 16 | 5 | 31.2 | 22 |
| laptop | 6 | 1 | 16.7 | 25 |
| microwave | 4 | 0 | 0.0 | 0 |
| mirror | 4 | 2 | 50.0 | 40 |
| monitor | 15 | 0 | 0.0 | 0 |
| mouse | 8 | 0 | 0.0 | 0 |
| nightstand | 1 | 0 | 0.0 | 0 |
| office chair | 2 | 0 | 0.0 | 0 |
| paper bag | 2 | 2 | 100.0 | 121 |
| pillow | 16 | 6 | 37.5 | 103 |
| plant | 21 | 8 | 38.1 | 56 |
| power strip | 1 | 1 | 100.0 | 42 |
| printer | 2 | 0 | 0.0 | 0 |
| radiator | 1 | 1 | 100.0 | 22 |
| recycling bin | 1 | 0 | 0.0 | 0 |
| refrigerator | 23 | 0 | 0.0 | 0 |
| shoe rack | 2 | 1 | 50.0 | 31 |
| shoes | 29 | 12 | 41.4 | 181 |
| slippers | 6 | 1 | 16.7 | 73 |
| sofa | 47 | 3 | 6.4 | 29 |
| stool | 18 | 5 | 27.8 | 72 |
| stove | 21 | 5 | 23.8 | 35 |
| suitcase | 4 | 1 | 25.0 | 24 |
| table | 107 | 29 | 27.1 | 132 |
| table lamp | 3 | 1 | 33.3 | 18 |
| telephone | 7 | 2 | 28.6 | 22 |
| toilet | 24 | 4 | 16.7 | 93 |
| towel | 6 | 0 | 0.0 | 0 |
| trash can | 28 | 10 | 35.7 | 281 |
| tv | 38 | 2 | 5.3 | 19 |
| washer | 8 | 3 | 37.5 | 91 |
| whiteboard | 4 | 1 | 25.0 | 34 |
| window | 10 | 2 | 20.0 | 7 |

Largest visible size (GT pixels)

| Group | Instances | Never proposed | Never % | Questions with a miss |
|---|---:|---:|---:|---:|
| 0 | 22 | 22 | 100.0 | 281 |
| 154–615 | 79 | 44 | 55.7 | 735 |
| 1–153 | 28 | 23 | 82.1 | 330 |
| 2460+ | 733 | 84 | 11.5 | 1357 |
| 616–2459 | 194 | 51 | 26.3 | 816 |

Number of visible frames (any pixels)

| Group | Instances | Never proposed | Never % | Questions with a miss |
|---|---:|---:|---:|---:|
| 0 | 22 | 22 | 100.0 | 281 |
| 17–32 | 26 | 2 | 7.7 | 179 |
| 1–2 | 105 | 51 | 48.6 | 672 |
| 3–8 | 581 | 123 | 21.2 | 1584 |
| 9–16 | 322 | 26 | 8.1 | 522 |

Camera-to-annotation-centroid distance in the largest view (metres)

| Group | Instances | Never proposed | Never % | Questions with a miss |
|---|---:|---:|---:|---:|
| 2–4 | 301 | 77 | 25.6 | 873 |
| 4–8 | 26 | 15 | 57.7 | 174 |
| 8+ | 10 | 9 | 90.0 | 71 |
| <2 | 697 | 101 | 14.5 | 1683 |
| unknown | 22 | 22 | 100.0 | 281 |

Prompt relationship

| Group | Instances | Never proposed | Never % | Questions with a miss |
|---|---:|---:|---:|---:|
| annotation_binding_suspect | 13 | 13 | 100.0 | 433 |
| exact | 992 | 206 | 20.8 | 2022 |
| other_vocab_mapping | 1 | 0 | 0.0 | 0 |
| query_coarser | 18 | 3 | 16.7 | 63 |
| query_finer | 8 | 0 | 0.0 | 0 |
| synonym | 24 | 2 | 8.3 | 79 |

Prompt text → annotation label

| Group | Instances | Never proposed | Never % | Questions with a miss |
|---|---:|---:|---:|---:|
| backpack → backpack | 5 | 0 | 0.0 | 0 |
| basket → basket | 1 | 0 | 0.0 | 0 |
| bathtub → bathtub | 15 | 0 | 0.0 | 0 |
| bed → bed | 25 | 4 | 16.0 | 182 |
| blanket → blanket | 7 | 2 | 28.6 | 20 |
| bookshelf → bookshelf | 5 | 0 | 0.0 | 0 |
| bowl → bowl | 8 | 1 | 12.5 | 10 |
| bucket → bucket | 1 | 1 | 100.0 | 24 |
| ceiling light → ceiling | 13 | 13 | 100.0 | 433 |
| chair → chair | 334 | 48 | 14.4 | 277 |
| chair → office chair | 2 | 0 | 0.0 | 0 |
| clock → clock | 3 | 0 | 0.0 | 0 |
| closet → closet | 1 | 0 | 0.0 | 0 |
| coat hanger → coat hanger | 1 | 1 | 100.0 | 81 |
| computer mouse → mouse | 8 | 0 | 0.0 | 0 |
| computer tower → computer tower | 3 | 1 | 33.3 | 18 |
| counter → counter | 2 | 0 | 0.0 | 0 |
| counter → kitchen counter | 1 | 1 | 100.0 | 60 |
| cup → cup | 2 | 1 | 50.0 | 96 |
| cutting board → cutting board | 1 | 1 | 100.0 | 70 |
| desk → desk | 11 | 2 | 18.2 | 2 |
| dishwasher → dishwasher | 2 | 0 | 0.0 | 0 |
| door → door | 70 | 16 | 22.9 | 155 |
| exhaust fan → exhaust fan | 2 | 2 | 100.0 | 74 |
| fireplace → fireplace | 5 | 0 | 0.0 | 0 |
| guitar → guitar | 1 | 1 | 100.0 | 39 |
| headphones → headphones | 2 | 1 | 50.0 | 84 |
| heater → heater | 18 | 18 | 100.0 | 459 |
| keyboard → keyboard | 10 | 0 | 0.0 | 0 |
| lamp → lamp | 16 | 5 | 31.2 | 22 |
| laptop → laptop | 6 | 1 | 16.7 | 25 |
| microwave → microwave | 4 | 0 | 0.0 | 0 |
| mirror → mirror | 4 | 2 | 50.0 | 40 |
| monitor → monitor | 15 | 0 | 0.0 | 0 |
| nightstand → nightstand | 1 | 0 | 0.0 | 0 |
| paper bag → paper bag | 2 | 2 | 100.0 | 121 |
| pillow → pillow | 16 | 6 | 37.5 | 103 |
| plant → plant | 21 | 8 | 38.1 | 56 |
| power strip → power strip | 1 | 1 | 100.0 | 42 |
| printer → printer | 2 | 0 | 0.0 | 0 |
| radiator → radiator | 1 | 1 | 100.0 | 22 |
| refrigerator → refrigerator | 23 | 0 | 0.0 | 0 |
| shoe rack → shoe rack | 2 | 1 | 50.0 | 31 |
| shoes → shoes | 29 | 12 | 41.4 | 181 |
| slippers → slippers | 6 | 1 | 16.7 | 73 |
| sofa → couch | 7 | 0 | 0.0 | 0 |
| sofa → sofa | 47 | 3 | 6.4 | 29 |
| stool → stool | 18 | 5 | 27.8 | 72 |
| stove → stove | 21 | 5 | 23.8 | 35 |
| suitcase → suitcase | 4 | 1 | 25.0 | 24 |
| table lamp → table lamp | 3 | 1 | 33.3 | 18 |
| table → desk | 12 | 2 | 16.7 | 3 |
| table → end table | 3 | 0 | 0.0 | 0 |
| table → table | 107 | 29 | 27.1 | 132 |
| telephone → telephone | 7 | 2 | 28.6 | 22 |
| toilet → toilet | 24 | 4 | 16.7 | 93 |
| towel → towel | 6 | 0 | 0.0 | 0 |
| trash bin → recycling bin | 1 | 0 | 0.0 | 0 |
| trash bin → trash can | 17 | 2 | 11.8 | 79 |
| trash can → trash can | 11 | 8 | 72.7 | 202 |
| tv → tv | 38 | 2 | 5.3 | 19 |
| washer → washer | 8 | 3 | 37.5 | 91 |
| whiteboard → whiteboard | 4 | 1 | 25.0 | 34 |
| window → window | 10 | 2 | 20.0 | 7 |

True occlusion is unavailable in these raster/OBB files. A small mask could reflect distance, truncation, occlusion, or annotation failure. Bounding-box fill and image-border contact are reported as proxies and are never named as measured occlusion. ARKit GT assigns sensor-depth pixels to boxes; zero raster support is especially ambiguous there.

Occlusion measurement

| Group | Instances | Never proposed | Never % | Questions with a miss |
|---|---:|---:|---:|---:|
| unavailable | 1056 | 224 | 21.2 | 2249 |

Shape-fill proxy in the largest view

| Group | Instances | Never proposed | Never % | Questions with a miss |
|---|---:|---:|---:|---:|
| 0.25–0.5 | 279 | 60 | 21.5 | 837 |
| <0.25 | 68 | 45 | 66.2 | 763 |
| unknown | 22 | 22 | 100.0 | 281 |
| ≥0.5 | 687 | 97 | 14.1 | 1460 |

Border truncation proxy in the largest view

| Group | Instances | Never proposed | Never % | Questions with a miss |
|---|---:|---:|---:|---:|
| False | 361 | 84 | 23.3 | 1213 |
| None | 22 | 22 | 100.0 | 281 |
| True | 673 | 118 | 17.5 | 1561 |

Among 832 proposed instances, 337 appear in the unique selector output and 601 in counting output. 495 and 231 respectively lose all overlapping selected masks.

There are 0 capture/name operands with no matched annotation IDs, touching 0 questions. They cannot be audited as GT instances or assigned to a recall fix; see UNBOUND_OPERANDS.jsonl.

Thirty numerical case reads. The selection takes up to five cases per diagnostic group, ordered by the number of affected questions, then fills from the remaining most-used operands. This is a diagnostic sample, not an unbiased prevalence estimate. No pixels were viewed.

| # | Capture / ID / prompt → label | Max px | Visible / usable | Distance m | Best IoU / joint | Max SAM presence | Questions | What the numbers suggest |
|---:|---|---:|---:|---:|---|---:|---:|---|
| 1 | scannetppv2/e7ccd75e5d / 21 / pillow → pillow | 0 | 0 / 0 | unknown | 0.000 / unknown | 0.000 | 74 | The 32 GT rasters contain no support; neither threshold nor wording is established as the cause. |
| 2 | scannetppv2/ad562ce09b / 69 / slippers → slippers | 0 | 0 / 0 | unknown | 0.000 / unknown | 0.000 | 73 | The 32 GT rasters contain no support; neither threshold nor wording is established as the cause. |
| 3 | scannetppv2/17c5e6a336 / 50 / trash can → trash can | 0 | 0 / 0 | unknown | 0.000 / unknown | 0.000 | 23 | The 32 GT rasters contain no support; neither threshold nor wording is established as the cause. |
| 4 | scannetppv2/17c5e6a336 / 56 / trash can → trash can | 0 | 0 / 0 | unknown | 0.000 / unknown | 0.000 | 23 | The 32 GT rasters contain no support; neither threshold nor wording is established as the cause. |
| 5 | scannetppv2/b37c033757 / 195 / chair → chair | 0 | 0 / 0 | unknown | 0.000 / unknown | 0.000 | 23 | The 32 GT rasters contain no support; neither threshold nor wording is established as the cause. |
| 6 | scannetppv2/aaa9c251de / 28 / shoes → shoes | 74 | 1 / 0 | 1.44 | 0.000 / unknown | 0.204 | 69 | Even the largest GT view falls below the executor’s 154-pixel requirement; a perfect proposal may still be unusable. Floor 0.05 creates score-eligible extras in 1 visible frames; their masks are unknown. The largest view touches the border. |
| 7 | arkitscenes/47332599 / 18 / toilet → toilet | 4 | 1 / 0 | 3.68 | 0.013 / 0.80 | 0.957 | 50 | Even the largest GT view falls below the executor’s 154-pixel requirement; a perfect proposal may still be unusable. Floor 0.05 creates score-eligible extras in 1 visible frames; their masks are unknown. |
| 8 | scannetppv2/17c5e6a336 / 24 / bed → bed | 101 | 2 / 0 | 1.93 | 0.487 / 0.22 | 0.969 | 40 | Even the largest GT view falls below the executor’s 154-pixel requirement; a perfect proposal may still be unusable. Floor 0.05 creates score-eligible extras in 2 visible frames; their masks are unknown. A retained mask has partial overlap, suggesting a shape/part mismatch. |
| 9 | scannetppv2/7e7cd69a59 / 118 / exhaust fan → exhaust fan | 142 | 3 / 0 | 9.65 | 0.000 / unknown | 0.176 | 29 | Even the largest GT view falls below the executor’s 154-pixel requirement; a perfect proposal may still be unusable. Floor 0.05 creates score-eligible extras in 3 visible frames; their masks are unknown. |
| 10 | scannetppv2/7e7cd69a59 / 119 / heater → heater | 138 | 6 / 0 | 2.15 | 0.000 / unknown | 0.050 | 28 | Even the largest GT view falls below the executor’s 154-pixel requirement; a perfect proposal may still be unusable. Floor 0.05 still retains no candidate in any visible frame. The largest view touches the border. |
| 11 | scannetppv2/aaa9c251de / 71 / cup → cup | 178 | 2 / 1 | 1.08 | 0.336 / 0.32 | 0.672 | 96 | At most two views meet the program threshold; frame coverage and segmentation quality are plausible bottlenecks. Floor 0.05 creates score-eligible extras in 2 visible frames; their masks are unknown. A retained mask has partial overlap, suggesting a shape/part mismatch. |
| 12 | scannetppv2/e7ccd75e5d / 52 / ceiling light → ceiling | 541 | 3 / 1 | 2.46 | 0.000 / unknown | 0.008 | 86 | The GT fallback matches a lamp query to the ceiling surface. Treat this as a target-binding error, not evidence that SAM missed a lamp. Floor 0.05 still retains no candidate in any visible frame. |
| 13 | scannetppv2/307e3262f1 / 62 / ceiling light → ceiling | 11647 | 5 / 2 | 1.93 | 0.000 / unknown | 0.988 | 81 | The GT fallback matches a lamp query to the ceiling surface. Treat this as a target-binding error, not evidence that SAM missed a lamp. Floor 0.05 creates score-eligible extras in 4 visible frames; their masks are unknown. The largest view touches the border. |
| 14 | scannetppv2/80ffca8a48 / 63 / trash can → trash can | 809 | 7 / 2 | 1.47 | 0.311 / 0.65 | 0.984 | 73 | At most two views meet the program threshold; frame coverage and segmentation quality are plausible bottlenecks. Floor 0.05 creates score-eligible extras in 6 visible frames; their masks are unknown. A retained mask has partial overlap, suggesting a shape/part mismatch. |
| 15 | scannetppv2/17c5e6a336 / 12 / heater → heater | 4798 | 3 / 2 | 0.95 | 0.000 / unknown | 0.032 | 72 | At most two views meet the program threshold; frame coverage and segmentation quality are plausible bottlenecks. Floor 0.05 still retains no candidate in any visible frame. The largest view touches the border. |
| 16 | scannetppv2/17c5e6a336 / 46 / ceiling light → ceiling | 62995 | 27 / 26 | 1.41 | 0.039 / 0.93 | 0.969 | 98 | The GT fallback matches a lamp query to the ceiling surface. Treat this as a target-binding error, not evidence that SAM missed a lamp. Floor 0.05 creates score-eligible extras in 7 visible frames; their masks are unknown. The largest view touches the border. |
| 17 | scannetppv2/e7ccd75e5d / 37 / ceiling light → ceiling | 9491 | 3 / 3 | 3.14 | 0.007 / 0.42 | 0.629 | 86 | The GT fallback matches a lamp query to the ceiling surface. Treat this as a target-binding error, not evidence that SAM missed a lamp. Floor 0.05 creates score-eligible extras in 2 visible frames; their masks are unknown. The largest view touches the border. |
| 18 | scannetppv2/307e3262f1 / 17 / ceiling light → ceiling | 33095 | 18 / 18 | 2.22 | 0.073 / 0.45 | 0.988 | 81 | The GT fallback matches a lamp query to the ceiling surface. Treat this as a target-binding error, not evidence that SAM missed a lamp. Floor 0.05 creates score-eligible extras in 10 visible frames; their masks are unknown. The largest view touches the border. |
| 19 | scannet/scene0515_02 / 45 / counter → kitchen counter | 4438 | 8 / 8 | 2.23 | 0.416 / 0.42 | 0.898 | 60 | The query 'counter' is mapped to annotation 'kitchen counter'; prompt expansion is testable, but this mapping alone does not prove SAM misunderstood it. Floor 0.05 creates score-eligible extras in 8 visible frames; their masks are unknown. A retained mask has partial overlap, suggesting a shape/part mismatch. The largest view touches the border. |
| 20 | scannetppv2/aaa9c251de / 33 / ceiling light → ceiling | 39279 | 11 / 11 | 1.26 | 0.011 / 0.28 | 0.980 | 59 | The GT fallback matches a lamp query to the ceiling surface. Treat this as a target-binding error, not evidence that SAM missed a lamp. Floor 0.05 creates score-eligible extras in 7 visible frames; their masks are unknown. The largest view touches the border. |
| 21 | scannetppv2/17c5e6a336 / 38 / door → door | 2736 | 4 / 3 | 0.70 | 0.000 / unknown | 0.053 | 102 | Every visible frame has SAM presence below 0.2, so the joint-score gate cannot retain any mask, even with conditional score one. Floor 0.05 still retains no candidate in any visible frame. The largest view touches the border. |
| 22 | scannetppv2/307e3262f1 / 84 / coat hanger → coat hanger | 1977 | 10 / 7 | 1.82 | 0.000 / unknown | 0.069 | 81 | Every visible frame has SAM presence below 0.2, so the joint-score gate cannot retain any mask, even with conditional score one. Floor 0.05 still retains no candidate in any visible frame. The largest view touches the border. |
| 23 | scannetppv2/ad562ce09b / 11 / heater → heater | 3638 | 11 / 9 | 2.06 | 0.000 / unknown | 0.069 | 78 | Every visible frame has SAM presence below 0.2, so the joint-score gate cannot retain any mask, even with conditional score one. Floor 0.05 creates score-eligible extras in 3 visible frames; their masks are unknown. The largest view touches the border. |
| 24 | scannetppv2/0c7962bd64 / 35 / heater → heater | 7497 | 4 / 4 | 0.94 | 0.000 / unknown | 0.054 | 54 | Every visible frame has SAM presence below 0.2, so the joint-score gate cannot retain any mask, even with conditional score one. Floor 0.05 creates score-eligible extras in 1 visible frames; their masks are unknown. The largest view touches the border. |
| 25 | scannetppv2/7e7cd69a59 / 117 / whiteboard → whiteboard | 3372 | 5 / 5 | 1.56 | 0.000 / unknown | 0.089 | 34 | Every visible frame has SAM presence below 0.2, so the joint-score gate cannot retain any mask, even with conditional score one. Floor 0.05 creates score-eligible extras in 1 visible frames; their masks are unknown. The largest view touches the border. |
| 26 | scannetppv2/aaa9c251de / 123 / heater → heater | 6985 | 8 / 7 | 1.58 | 0.000 / unknown | 0.412 | 94 | Size, view count and exact naming do not explain the miss; discarded-mask quality or segmentation shape remains unknown. Floor 0.05 creates score-eligible extras in 4 visible frames; their masks are unknown. |
| 27 | scannetppv2/ad562ce09b / 25 / headphones → headphones | 376 | 10 / 4 | 1.19 | 0.335 / 0.85 | 0.992 | 84 | Size, view count and exact naming do not explain the miss; discarded-mask quality or segmentation shape remains unknown. Floor 0.05 creates score-eligible extras in 9 visible frames; their masks are unknown. A retained mask has partial overlap, suggesting a shape/part mismatch. The largest view touches the border. |
| 28 | scannetppv2/307e3262f1 / 1 / heater → heater | 8124 | 6 / 6 | 1.80 | 0.000 / unknown | 0.204 | 71 | Size, view count and exact naming do not explain the miss; discarded-mask quality or segmentation shape remains unknown. Floor 0.05 creates score-eligible extras in 3 visible frames; their masks are unknown. The largest view touches the border. |
| 29 | scannetppv2/307e3262f1 / 33 / trash can → trash can | 1537 | 6 / 3 | 1.19 | 0.456 / 0.93 | 0.992 | 67 | Size, view count and exact naming do not explain the miss; discarded-mask quality or segmentation shape remains unknown. Floor 0.05 creates score-eligible extras in 5 visible frames; their masks are unknown. A retained mask has partial overlap, suggesting a shape/part mismatch. The largest view touches the border. |
| 30 | scannetppv2/ad562ce09b / 54 / bed → bed | 5152 | 8 / 4 | 2.14 | 0.364 / 0.93 | 0.992 | 67 | Size, view count and exact naming do not explain the miss; discarded-mask quality or segmentation shape remains unknown. Floor 0.05 creates score-eligible extras in 8 visible frames; their masks are unknown. A retained mask has partial overlap, suggesting a shape/part mismatch. |

Three fixes to test, with the ideal-GT grant for their principal diagnostic group as a recovery ceiling:

- Dense retention: **+14.34 pp absolute distance; +12.31 pp counting**, for `unresolved` alone. Lower the joint floor to 0.05 and raise the cap to 30; compare the unchanged 0.3 linker floor against 0.05. Discarded masks are unknown, so this ceiling assumes perfect new proposals.

- Targeted tiles: **+8.82 pp absolute distance; +8.57 pp counting**, for `few_views` alone. Search four overlapping crops on up to four empty plan frames, optionally gated by student presence. Tiles preserve the existing geometry frame IDs; they do not create new views.

- Student-triggered search: **+1.84 pp absolute distance; +1.10 pp counting**, for `presence_gate` alone. Use the independent first-token presence signal to trigger tiles where baseline candidates are absent. This gate cannot itself create a mask, and the earlier presence advantage needs validation on dev-S1.

Prompt expansion remains a lower-priority control: the non-suspect lexical misses have zero paired absolute-distance/counting recovery here. Its dictionary excludes ceiling as an alias for ceiling light. The three ceilings above must not be added or treated as predictions of attainable gains. The actual SAM-ranked tile schedule intersects a usable GT view of only 50 misses (25 unresolved, 9 scarce-view, 6 presence-gated, and 10 suspect lexical targets). An ideal student gate could select a usable baseline-empty view for at most 81 misses. Thus the group grants are intentionally loose bounds, and the present tile trigger cannot realize the full scarce-view grant. The prompt dictionary applies to 123 usable misses across categories; none of these eligibility counts proves a matching mask will appear. A variant can improve proposal recall and still lose score through false accepts or counting merges.

Student evidence: the selector events of 2026-11-11 point to its PRES32/V3 run card and build.py feature joins. The underlying verify_kit/out/decision589_20261110T1915Z/PRESENCE_REPORT.md reports, on 33 held-out rooms, P(yes) AUROC 0.9741 versus SAM presence 0.9490; visible recall 89.5% versus 86.4%, and absent false-positive rate 6.5% versus 8.4%. On all 84 scans the AUROCs are 0.9612 versus 0.9242. This is raw-image first-token yes/no inference from the base student checkpoint, not a released lightweight feature probe or evidence for this dev-S1 checkpoint.

Existing code: grd_selector/work/vk/pres32_run.py builds frame requests; verifykit/model.py reads first-answer-token probabilities; work/selector/features.py::load_presence and work/setsel/build.py join them. The copied presence_run.py binds that backend to dev-S1 content-addressed frames. The student_tiles variant uses p_yes >0.5 only to trigger extra tiles on baseline-empty frames; it never deletes baseline candidates or uses GT. New dev-S1 presence outputs must be generated and bound before this variant can run.

More-frame inference is deferred: the delivered head exports, selector loops, GT rasters and frozen executor all bind exactly 32 anchors. A 64-frame SAM cache alone cannot be priced fairly with these heads. That experiment needs new matched geometry exports and GT frame authority. Upscaling the same PNG adds no information; the tile variant instead increases the model’s effective sampling of each crop.

Evidence files: analysis/PER_INSTANCE.jsonl, FRAME_METRICS.jsonl, CAUSE_PER_ITEM.jsonl, CAUSE_CONTRASTS.json, GRANT_*.json, REPRICE_PARITY.json, UNBOUND_OPERANDS.jsonl; the original cache, ITEMS manifest and direct receipts remain read-only.
