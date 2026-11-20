# ANCHOR kill test and Locate accuracy (2026-11-20)

## Question
Does A3x pass the K1 decision bars, and do existing student Locate citations identify raster-visible objects?

## Registered bars and definitions
Registered before any score at 2026-11-20T05:52:12.741630+00:00. Source SHA256: 74d0e34444ef060755623d9b9e4ab03ee2caee9e01c7ce9f1b6f8cea1cf51c47.

- R1 Exclusion is keyed by room and fails closed: ScanNet sceneXXXX across all _NN scans, ARKit visit_id across video_ids, ScanNet++ scene id. The union holds the six hashed lists (VSI-Bench, ReVSI, VSTI, dev-S1, R0-dev, K1 held-out), every R0 room, the 80 withheld rooms, the PE-K1 reserve and V1's 24 calibration captures. K1 captures are selected by the manifest's train flag.
- R2 A label fact is admitted only when both families give state L or M (1% or more) on that frame, their points lie within 5% of the frame diagonal (3% on M frames), and the file carries its form version, prompt sha256, model id and source-frame sha256. One family's word, S frames, counts, first-seen frames, labeller frame counts and look-alike phrases never make a target, a negative or a removal.
- R3 One frozen, hashed sibling table (desk/table, door/window, cooktop/oven, cabinet/storage cabinet, monitor/computer monitor, chair/seat/stool, bookshelf/shelf, sofa/couch/armchair) serves the sender and every null, removal and uniqueness rule.
- R4 A regenerated routed row uses the served configuration pinned by hash (selector rule, geometry, 32-anchor layout, SAM 3 setting) and audited GT distances in the 15% trust rule. Silently wrong rows are dropped; the grammar validator passes and fixed-seed rows are read before any seal.
- R5 Decision reads use dev-S1's 38 raster captures and are confirmed on R0-dev. K1 held-out decides nothing, because the init trained 4,959 VQA rows and 320 pointing rows there. dev-S1 gap-MRA bars wait for the EVAL_GT_HALF_EXTENT_AUDIT verdict.
- R6 No control arm trains. Consumers that share a stream bind at different boundaries, so a before/after read attributes each. Nothing label-derived binds at boundary 1, and every pointing consumer binds only with or after c' (loss from the JSON, thinking-off prefill).

### 2. ANCHOR: one Locate frame per operand before its call, read by a selector-free rule
- Limit: A, the selection share (the right instance for 83% of objects; a GT frame choice raised on-target picks from 82.9% to 88.3%). It also removes the fitted selector from the call, which decides whether routed reads on ReVSI and VSTI are eligible. At 64 frames with the 32 anchors nested, the cited anchor fixes identity and the candidate's members on the added frames supply coverage; that pairing is what can reach objects seen on one or two anchors.
- Trains: N's language model on routed distance rows re-rendered with one Locate line per operand. Responses are regenerated through rule A3x, so training equals serving.
- Row form. Example: "The heater is seen in frame 9." `<ground obj="radiator" mode="box">` `<tool_response>radiator: frames 3,4,9,17 (best 9) ...</tool_response>` "The bed is seen in frame 5." `<ground obj="bed" mode="box">` ... Reader record per call: `{"call":"radiator","locate_frame":9,"on_frame":[{"cand":2,"area_px":5410},{"cand":5,"area_px":610}],"chosen":2,"rule":"A3x"}`.
- Reader rule A3x (fixed math, nothing fitted): among linked candidates keep those with a member mask on the cited frame and take the largest mask on that frame. A call with no Locate line, or with no candidate on the frame, prints the existing "not seen" status. No selector and no added fallback rule.
- Labels: rasters give the frame on ScanNet and ScanNet++ (the anchor with the largest GT mask at 1% or more). On ARKit the frame must also be one where both families mark the operand L or M in V7's named form; with no such anchor the row carries no Locate line.
- Binds: N boundary 2 if the kill test passes before the package cut, else the next boundary. The reader rule enters a claimed read only after the dev-S1 and R0-dev bars.
- Owner and first step: a Codex implement dispatch under the reads lane runs the kill test on CPU today on the 1,012 K1 decision rows with the stored sb_kbox4 pools. The same dispatch scores, on existing dev-S1 direct reads, how often N's Locate frames show the cited object in the raster.
- Read and bar: (a) Kill test: the GT best-view anchor under A3x, with "not seen" on an empty frame counted, must beat the served call by 2.0 type points with paired lower bound above 0, fix half or more of its wrong picks (f >= 0.5) and break at most 5% of its right picks (h <= 0.05). A fail drops ANCHOR. (b) Held-out, CPU rescoring of the dev-S1 replay with serialized candidates on N's export: A3x replaces the selector when on-target rate has lower bound above -2 points and gap MRA lower bound above -1.0; a Locate line precedes at least 95% of calls; the cited frame is raster-visible for at least 90% of operands visible on any anchor.


## Method
Use only the 1,012 K1 decision rows and their sb_kbox4 candidate pools. Retain empty-frame calls as not seen. Report on-target rate, not-seen rate, paired change, corrected-wrong fraction f and damaged-right fraction h. Use 10,000 paired room-cluster bootstrap draws, seed 20261120, percentile 95% intervals. Report object-call and paired-row denominators explicitly. The specification says type points; on-target points and task-score points must not be silently equated.
For frame sensitivity, use the nearest different anchor with GT area >=1%, breaking equal-distance ties toward the earlier anchor; separately identify immediate-adjacent eligible anchors and cases with no eligible alternative. No fitted choice.
For Locate accuracy, report each existing development read separately by question type and dataset. Use exact frame mapping and exact noun-to-GT identities; report unresolved nouns and missing rasters separately, never silently count them visible. Report visibility conditional on the object being visible at >=1% on any anchor, plus all resolved citations. Ground truth is diagnostic only. No training rows are produced.



## Locate scoring contract (before raster scoring)
The step-400 and step-600 reads of run 6ed2c7aa are analyzed separately, using B2048; full and B4096 are not independent samples. Family main is dev-S1 (1,339 items); family a7 is R0-dev with anonymized captures and no local raster binding, so its visibility is not computed. The direct reads are forecasts for N, not an export of N.
A citation must be an integer anchor from 1 to 32. Out-of-range and fractional citations count as failures when the noun is otherwise evaluable, never as source-frame indices or timestamps. Verify all 32 source_frame_indices against the raster frame_indices before scoring.
Primary visibility uses an exact, case-normalized noun that names exactly one GT instance, with no synonym or sibling substitution. Report a separate permissive diagnostic for exact nouns naming multiple instances: success requires at least one single instance, not the union, to occupy >=1% on the cited anchor. Both denominators condition on >=1% visibility on at least one valid anchor. Missing GT, absent literal labels, ambiguous identity in the primary, and invalid rasters remain explicit coverage losses. The bound treating every absent literal label as a visible success is reported separately when useful.
Parser extracts explicit “find the X, first seen ... frame k” and “X is seen in frame k” statements; every numeric-frame line is audited for parsing coverage. Deduplicate repeated identical (item, noun, frame) claims. Citation incidence among all items is diagnostic and cannot certify the routed 95% call bar.

## Results

ANCHOR is not cleared to bind. The paired K1 kill test and neighbouring-anchor sensitivity are NOT COMPUTABLE on this node because the required sb_kbox4 pools are absent. This is an input blocker, not a measured kill-test failure. No K1 on-target rate, not-seen rate, paired interval, f or h is claimed.

The existing direct-read Locate diagnostic FAILS the 90% bar on its evaluable population: numeric citations score 24.0% [8.9, 37.0] at step 400 and 30.3% [7.4, 51.5] at step 600. The sparse, incomplete direct-read population does not decide N’s full routed admission gate.

### Locate accuracy on existing direct reads

Each rate uses citations of exact, unique raster instances visible on at least one anchor at >=1%. Intervals use 10,000 room-cluster resamples within each read (seed 20261120); the two exports are reported separately. Frames outside 1–32 and fractional frames fail. No synonym substitution is applied.

| Group | Step 400 | Step 600 |
|---|---|---|
| All numeric citations | 12/50: 24.0% [8.9, 37.0] | 10/33: 30.3% [7.4, 51.5] |
| arkitscenes | 4/15: 26.7% [7.1, 43.8] | 3/12: 25.0% [9.1, 45.5] |
| scannet | 0/3: 0.0% [0.0, 0.0] | 0/1: 0.0% [0.0, 0.0] |
| scannetppv2 | 8/32: 25.0% [0.0, 42.5] | 7/20: 35.0% [0.0, 64.0] |
| object_counting | not computable (0 citations) | not computable (0 citations) |
| object_rel_direction_easy | not computable (0 citations) | not computable (0 citations) |
| object_rel_direction_hard | not computable (0 citations) | not computable (0 citations) |
| object_rel_direction_medium | not computable (0 citations) | not computable (0 citations) |
| object_rel_distance | 7/29: 24.1% [0.0, 45.0] | 6/17: 35.3% [0.0, 70.6] |
| object_size_estimation | 5/21: 23.8% [6.2, 37.5] | 4/16: 25.0% [7.7, 43.8] |
| relative_count | not computable (0 citations) | not computable (0 citations) |
| relative_size_object | not computable (0 citations) | not computable (0 citations) |
| route_planning | not computable (0 citations) | not computable (0 citations) |

All nonempty primary groups fall below the 90% point bar. A zero-width bootstrap interval from a tiny stratum is not evidence of population certainty. Relative size has numeric claims but none with an exact unique local instance visible at 1%; other zero-citation types have no numeric Locate claim. Absolute distance is absent from these direct-read manifests.

| Sensitivity | Step 400 | Step 600 |
|---|---|---|
| Include unambiguous worded anchors | 13/51: 25.5% [10.8, 38.2] | 11/35: 31.4% [10.0, 52.0] |
| Numeric, valid 1–32 indices only | 12/36: 33.3% [13.0, 51.2] | 10/27: 37.0% [10.0, 60.6] |
| Any one instance of the exact label | 13/51: 25.5% [11.1, 38.5] | 10/33: 30.3% [7.4, 51.5] |

The worded-anchor sensitivity accepts first/initial, last, and explicit ordinals. It adds 24 claims across the reads; 13 spatial or time descriptions do not specify a unique anchor. It does not reinterpret “frame 70” or “frame 44.9” as timestamps. The numeric contract is the preregistered primary analysis; the worded sensitivity is exploratory.

| Coverage | Step 400 | Step 600 |
|---|---|---|
| Development items | 1339 | 1339 |
| Items with local GT and exact 32-anchor mapping | 485 | 485 |
| Items with numeric frame citations | 144 | 92 |
| Numeric operand citations | 150 | 93 |
| Citations missing a raster | 82 | 47 |
| Citations without a literal GT label | 5 | 4 |
| Citations with multiple same-label instances | 1 | 0 |
| Resolved citations never >=1% on any anchor | 12 | 9 |
| All invalid numeric citations (including missing GT) | 48 | 30 |
| Unparsed numeric-frame lines | 0 | 0 |

There are 38 staged GT captures (23 ARKitScenes, four ScanNet, 11 ScanNet++). Each direct read covers 139 captures; 485/1,339 items map to staged rasters. The funnel’s “38 of 60” denominator belongs to its separate distance slice and is not reused here. For the primary conditional citations there are 22 rooms at step 400 and 17 at step 600. Both reads contain an additional 1,781 anonymized R0-dev items; their GT binding is unavailable, so no R0 visibility rate is claimed. The B2048, B4096 and full traces are identical on all 1,339 dev-S1 items of each read; they are not pooled.

These exports belong to ended run 6ed2c7aa (step 400 accepted direct decision read, step 600 diagnostic forecast), not vehicle N. This result does not certify or reject N’s complete routed gate. The kill test, on-target noninferiority, gap MRA, 95% preceding-Locate coverage and R0 confirmation remain uncomputed. No grounding label is authorized for training by this diagnostic.

Validation: seven focused tests pass. An independent implementation directly counted raw raster pixels for all 105 resolved numeric claims and reproduced every visibility decision. Every numeric-frame line in the two development reads was parsed. All 485 covered items per checkpoint have an exact source_frame_indices match. The raster label IDs are used directly; background is -1.

Artifacts: anchor_analysis.py, validate_locate.py, test_anchor_analysis.py, locate_summary.json (including dataset × type), locate_claims.jsonl, locate_item_audit.json, locate_validation.json, raster_visibility.json, tests.log, validation.log.

## Missing K1 inputs and transfer

### Transfer request (not executed)

Source: trinity-1-18. Destination: trinity-2-28, W/k1_inputs.
The supplied K1_TRANSFER_FILES.txt is a 684-line relative-path manifest generated
from the local SEEDS.json input_sha256 provenance. K1_MISSING_INPUTS.json carries
every absolute source path and recorded hash. It requests 209 candidate-pool
JSON files, 209 raster NPZ files, and 266 sb_kbox4 code/table/row-set files.
Only 204 captures and the specified 1,012 rows may contribute decision scores.

The source paths include:
- /scratch/jjyeung/k1/run_convert_2/01949c4249271126/candidates.json (plus 208 named pools).
- /scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/41048124.npz (plus the other 208 named raster files).
- /scratch/jjyeung/orch_n30/sb_kbox4/out/box_ladder/serving_tables/arkitscenes__41048124.json.gz (209 named serving tables).
- /scratch/jjyeung/orch_n30/sb_kbox4/out/box_ladder/PER_ITEM.jsonl.
- /scratch/jjyeung/orch_n30/sb_kbox4/{train_manifest.json,train_labels.json,train_pricing.py,predicted.py,serving_reference.py} and the other named code inputs.

Remote file sizes are UNKNOWN: the available provenance records hashes but no
byte sizes, the source trees are absent here, and SSH is forbidden. No aggregate
size is invented. The transfer owner must stat the exact named files, record each
byte size, check that the transfer plus current W stays below 20 GB, and confirm
100–200 GB free on destination scratch before transferring. No directory scan is
needed. No automatic transfer is authorized by a timeout.

Once the owner has placed K1_TRANSFER_FILES.txt at /tmp/anchor_kill1.files on
trinity-1-18 and completed those checks, run this one InfiniBand tar pipe there:

```bash
tar -cf - -C /scratch/jjyeung --verbatim-files-from -T /tmp/anchor_kill1.files | ssh -o ConnectTimeout=20 trinity-2-28.ib 'mkdir -p /scratch/jjyeung/orch_n30/anchor_kill1/k1_inputs && tar -xf - -C /scratch/jjyeung/orch_n30/anchor_kill1/k1_inputs'
```

Verify each received file against the supplied hashes. The source list supplies
the minimum pool/raster/table evidence; the served distance replay may need more
geometry dependencies after the sb_kbox4 code is inspected. The A3x raw-input
adapter is not implemented against files that are unavailable.

## Options rejected

- Substituting carry seed masks for stored linked pools: the seeds contain only one chosen mask and cannot rank the alternatives on a cited frame.
- Treating invalid frame numbers as timestamps, or matching siblings as synonyms: neither follows A3x or proves the cited instance.
- Pooling the three identical decoding arms: this would multiply the same evidence.
- Calling the diagnostic an N export or a routed gate: the read provenance and task manifests do not support that claim.

## What might not work and how we would notice

The raster subset may differ from missing captures; every coverage loss is counted and each dataset is reported separately. Literal labels miss synonyms, so five and four numeric citations remain unresolved; the separate permissive same-label-instance result and worded-anchor sensitivity do not approach 90%. Raster errors could change individual matches; the claim ledger preserves every frame, GT ID and pixel fraction for inspection. Tiny strata produce degenerate bootstrap intervals and cannot establish population precision.

A successful K1 oracle test would not imply that the student can cite the right frame: these direct traces are evidence of that gap. A trained N export must satisfy all registered dev-S1 and R0-dev conditions before A3x enters a claimed read. The GT half-extent audit is not used here because no box, distance or gap MRA is scored.

## Tests that settle the remaining decision

Stage the named K1 inputs through the authorized owner, verify source hashes and exact population, implement the raw-pool adapter, reproduce deployed selections, and run A3x plus neighbouring-anchor sensitivity with 10,000 room draws. Report the spec’s +2-point, positive-lower-bound, f>=0.5 and h<=0.05 bars separately. On N’s export, run the registered serialized-candidate replay and R0-dev confirmation; also test preceding-Locate coverage and cited-frame visibility.

## Code, outputs and provenance

All paths below are relative to W = /scratch/jjyeung/orch_n30/anchor_kill1 on trinity-2-28. The code has no GPU or API dependency.

- Scoring: anchor_analysis.py; raw-raster validation and worded-anchor sensitivity: validate_locate.py; seven checks: test_anchor_analysis.py and tests.log.
- Per-citation evidence: locate_claims.jsonl, locate_item_audit.json, raster_visibility.json; grouped intervals: locate_summary.json and locate_validation.json.
- Registered text: PREREGISTRATION.md and LOCATE_CONTRACT.md; input inventory: corpus_inventory.json and gt_metadata.json.
- K1 transfer and implementation contract: K1_MISSING_INPUTS.json, K1_TRANSFER_FILES.txt, TRANSFER_REQUEST.md, K1_INPUT_SCHEMA.md. The raw-pool adapter is not complete; the normalized scoring kernel is tested but has not run on K1.
- Direct corpus sources: reads/6ed2c7aa_s400_devS1R0_direct_a59a7bff4c4.jsonl.gz (7,078,919 B, SHA256 0ac77475f2a054c5ec9239e09629c4ffbddfaf29dad48d4f83045975af51b9e9) and reads/6ed2c7aa_s600_devS1R0_direct_a136f924ab1.jsonl.gz (6,977,464 B, SHA256 e9849bc44f703c4aea322b24a22ad918988db6a9fff6e41a776ada6eeaa46312), under /data2/jjyeung/agent_project_data/distill_trace_corpus. The corpus INDEX.jsonl predates these entries; their exact names came from cont_ops events 20261119T1008Z and 20261119T2332Z.
- GT: /scratch/jjyeung/orch_n30/cont_ops24_c/gt/{t1_gt,arkit_gt}/gt; file hashes, sizes, labels and frame mappings are in raster_visibility.json.
- Population: /scratch/jjyeung/orch_n30/sb_cachk/out/v2/POPULATION.json (183,883 B): 204 decision captures, 1,012 rows; five captures and 25 rows excluded.

## Status

Locate diagnostic complete; K1 kill test and neighbour sensitivity BLOCKED on remote candidate inputs. ANCHOR has no admission clearance from this work. No labels, training rows, GPU jobs, SSH connections, Git commands, deletions, paid API calls or >20 MB NFS streams were used. The primary report persists in D; code and detailed outputs remain local because the brief forbids SSH mirroring. No independent launch review has been claimed.

Writing check: no borderline project-history sentence retained; experiment provenance and read identity are necessary for interpreting the result.
