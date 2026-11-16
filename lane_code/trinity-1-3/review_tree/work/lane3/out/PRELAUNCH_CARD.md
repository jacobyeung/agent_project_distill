# Pre-launch card

This leg tests trace-ruled data repairs on the accepted warm-start export. A0 is the no-fusion control. A2 adds GF-1 on the same mixture; deployed-response replacement and additional direct data require separately bound inputs and an epoch-boundary change. The init is step 544, artifact `1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef` (`work/tree_r1/student_pilot/r2_contract.py:INIT`). Neither kit is authorized to launch.

Both arms use RGB end to end. Their heads and frozen towers run within the forward pass. Head outputs reach the language model as text tokens. Traces identify frames by number and admit quantities only from visible enumerations, printed responses, the question, or explicit arithmetic. Geometry is reconstructed on dense frames before selecting LM frames (`work/tree_r1/student_pilot/r2_contract.py`; `r2_dense.py`; `carrier_c1.py`).

## Bound step mixture

Both arms have 288 global rows, world 4 and 72 rows per rank. Stream quotas are VQA 128, routing 64, pose 64 and pointing 32. MDG is absent. The sealed leg also has 288 rows with those stream totals; its type draw was natural rather than the repaired type table (`out/MIX_A0.json`; `work/kit07ca49df_meta/m/k/b02e4385.json:recipe`; `work/cont_ops/D0_LAUNCH_PROCEDURE.md`, routing-share table).

Fractional entries below are long-run per-step targets. The deterministic sampler allocates integer draws and keeps facing twins together. The sealed leg's exact VQA type breakdown is not established here; it must not be inferred from benchmark answers. Real after-filter repeats remain unverified because `work/rows_slices/` is absent (`work/tree_r1/student_pilot/r2_mix.py`; `out/MIX_A0.json`).

| Type | Stream | A0 rows/step | A2 rows/step | Trace form | Numeric source |
|---|---|---:|---:|---|---|
| direction | vqa | 27.0787 | 27.0787 | direct qualitative | `out/MIX_A0.json` |
| facing_pairs | vqa | 27.1711 | 27.1711 | direct qualitative | `out/MIX_A0.json` |
| relative_distance | vqa | 22.7350 | 22.7350 | direct qualitative | `out/MIX_A0.json` |
| object_size | vqa | 10.8130 | 10.8130 | direct qualitative | `out/MIX_A0.json` |
| counting | vqa | 8.8722 | 8.8722 | direct: Locate, listed count, answer | `out/MIX_A0.json` |
| totals | vqa | 1.3863 | 1.3863 | direct: listed counts and explicit sum | `out/MIX_A0.json` |
| appearance_order | vqa | 14.4173 | 14.4173 | direct qualitative | `out/MIX_A0.json` |
| box_3d | vqa | 4.4361 | 4.4361 | direct qualitative | `out/MIX_A0.json` |
| room_size | vqa | 1.3863 | 1.3863 | direct qualitative; estimate only in final answer | `out/MIX_A0.json` |
| route_planning | vqa | 9.7040 | 9.7040 | direct qualitative | `out/MIX_A0.json` |
| camera_displacement | routing | 17.3458 | 17.3458 | program with GT response | `out/MIX_A0.json` |
| camera_movement_direction | routing | 15.1925 | 15.1925 | program with GT response | `out/MIX_A0.json` |
| camera_rotation | routing | 11.3645 | 11.3645 | program with GT response | `out/MIX_A0.json` |
| absolute_distance | routing | 14.8336 | 14.8336 | program with GT response | `out/MIX_A0.json` |
| recovery | routing | 2.3925 | 2.3925 | simulated-miss recovery | `out/MIX_A0.json` |
| units | routing | 2.8710 | 2.8710 | program with GT response | `out/MIX_A0.json` |
| pose | pose | 64.0000 | 64.0000 | perception | `out/MIX_A0.json` |
| pointing | pointing | 32.0000 | 32.0000 | perception | `out/MIX_A0.json` |

The sealed routing rows per step were camera displacement 15.7, movement 13.7, rotation 10.2, absolute distance 13.1, room size 0.65 and route planning 10.5. Those rounded values describe the sealed natural draw, not the repaired quotas (`work/cont_ops/D0_LAUNCH_PROCEDURE.md`, routing-share table).

## Stages and optimization

A0 runs full fine-tuning for 1,000 steps. A2 uses a default adapter stage of 400 steps and full fine-tuning for the remaining 600; the combined budget is 1,000. The A2 second stage needs the first stage's export and a new bound vocabulary witness; it is not an independent restart from the parent (`out/MIX_A0.json`; `work/tree_r1/student_pilot/r2_config.py:configure`).

A0 trains the LM, pose head, frame embeddings and admitted depth heads. Its base vision tower and the depth-init encoder remain frozen. A2's adapter stage trains only GF-1; the LM, vision, other heads and geometry tower remain frozen. A2's full stage trains the LM, heads and GF-1 while retaining the frozen towers. Neither arm attaches the camera connector (`work/tree_r1/student_pilot/carrier_c1.py:parameter_groups`; `gf1.py`; `r2_config.py`; `out/B2_MODEL_PROOF.json`).

The parent head rate is 1e-4; its LM rate is 1e-5 with scale 0.6, hence 6e-6. The pose scale is 0.6, hence 6e-5 for its scaled head group; inherited head parameters retain their native group rate. GF-1 uses 1e-4 in the adapter stage and the scaled LM rate, 6e-6, in full fine-tuning. Warmup is 0.05 of the stage and weight decay is 0.01 (`work/kit07ca49df_meta/m/k/b02e4385.json`; `work/tree_r1/student_pilot/carrier_c1.py:parameter_groups`; `gf1.py:parameter_groups`).

The opener choice is **keep** after full warm-start loading. A pinned witness must bind the donor artifact, accepted lineage, tokenizer vocabulary and opener IDs/constituents. A missing or mismatched witness refuses. The explicit reset setting and other initializations use the native mean-of-constituents reset (`work/tree_r1/student_pilot/r2_openers.py`; `tests/test_r2_build3.py:test_opener_export_keep_and_reset`).

## Registered reads and stop rule

Compare each repair export at steps 100 and 200 with the accepted step-544 export, on identical items and reader settings. Use paired differences with the registered 10,000-draw room bootstrap. Direct types use the frozen direct budget; routed types use deployed tools. The specified routed read has 150 distance, 36 room and 450 camera items (`work/records/design/TRACE_RULING_20261115.md:359`). Room-size training is direct in this leg; report the registered room diagnostic separately rather than silently changing that read.

| Read | Failure condition | Numeric source |
|---|---|---|
| F1 | Any listed direct type has a repair-minus-parent 95% interval wholly below zero: route planning, counting, easy/medium/hard direction, relative distance or object size. | `work/records/design/TRACE_RULING_20261115.md:365` |
| F2 | On the 150 facing twins, away accuracy's interval fails to clear the level constants 54, 40 or 36; more than 20% of twins have identical answers; or toward accuracy has a negative paired interval. | `work/records/design/TRACE_RULING_20261115.md:366` |
| F3 | Native distance score is over 5 points below the scripted score on script-answerable items; fewer than 95% of failed calls end in a parsed numeric answer; call rate is below 95%; repeated calls after failure exceed 2%; or any final answer is a refusal. | `work/records/design/TRACE_RULING_20261115.md:367` |
| F4 | On a direct type's full denominator, the scripted program with fallback beats the repair's direct answers with its interval above zero. | `work/records/design/TRACE_RULING_20261115.md:368` |

Totals must beat the train-fitted constant 7 (reported reference 46.30%), and single counts must not fall against constant 2 (reported reference 61.87%). These are evaluation guards, never sources for training quantities or quotas (`work/records/design/TRACE_RULING_20261115.md:370`).

Default stop rule: inspect the step-100 read; stop immediately for invalid traces, refusal answers, broken exclusions or resource/admission failures. Stop the affected experiment at step 200 if a registered falsifier or prior guard fails; record the type and repair its template or routing form before another seal. This operational default interprets the falsification rule; no automatic evaluation job or stop controller was run (`work/records/design/TRACE_RULING_20261115.md:361-380`).

## Resource expectations and claim scope

The parent measured 131 seconds per step. At that rate, 1,000 steps take approximately 36.39 hours and 145.56 GPU-hours at world 4. These are arithmetic estimates, not timings of the repaired leg. Trace lengths, type sampling, kept openers and A2's dense tower can change the rate (`work/cont_ops/D0_LAUNCH_PROCEDURE.md`, procedure steps 9–10; `out/MIX_A0.json`). A2's inherited plan estimates approximately 190 GPU-hours cached or 345 online for 1,000 steps, equivalent to approximately 171 or 310.5 seconds per step at world 4; the mixed-stage schedule here has not been timed (`work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md:106`).

No GPU memory peak was measured for either repaired arm. The current native estimator gives A2 adapter/full-stage envelopes of 22.07 / 64.95 GiB per rank at 32 LM frames, 64 dense frames and world 4, with a 20% reserve. These are GUESS shape budgets, including an assumed extra camera context; the actual camera connector is absent, so the estimator is conservative in that term. A0 has no calibrated peak; GUESS: the full-stage A2 envelope can serve only as a provisional upper planning envelope under identical sequence lengths, not as admission evidence (`out/B3_MEMORY_ESTIMATES.json`; `work/tree_r1/student_pilot/gf1_memory.py`). The first GPU admission must measure actual peaks and step time before training.

Claims are restricted to VSI-Bench, VSTI and ReVSI, each with both venue-inclusive scores and scores without ARKit venue 381879. dev-S1 supports paired comparisons only. Base pretraining, the frozen geometry tower and segmenter are disclosed; their external-pretraining exemption does not excuse project-trained component overlap. Every sealed scene exclusion remains, including benchmark and held-out dev-S1 scenes; unknown overlap refuses (`work/tree_r1/student_pilot/r2_policy.py`; `out/COMPONENT_POLICY.md`).

A0 gives up deployed-response trust/fallback training, real failure statuses, camera and room recovery, GF-1, larger traced direct data, VSTI camera-object direct rows and own-encoder grounding. It retains simulated-miss recovery and GT program responses; F3 therefore measures the remaining train-to-deployed-tool gap (`work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md`, section 4).

Not checked: real export/tokenizer witness, real filtered populations, real dense coverage, pretrained parity, GPU fit/time, distributed behavior and any registered evaluation. Unsupported legacy evaluation formats refuse; an authenticated item adapter is required before these reads (`out/B3_BANK_ENTRYPOINTS.json`).
