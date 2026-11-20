# NV key spend plan and calibration record (2026-11-20; lanes nvkey2 on Trinity, nv_orch1 on Orchard)

Status: running. This record states the plan in force, the calibration numbers each job's QUESTION rests on, and the spend. nvkey2 owns it and updates it as jobs finish.

## Question
The user holds about 15,000 dollars on the NV inference keys, shared with the main project, and the money expires on the night of 2026-11-20 PT (sends stop 2026-11-21T03:30Z, jobs end by 04:00Z). Which jobs buy labels that are measurably accurate against ground truth on a calibration set and feed a named build, row family or analysis, and how much can be sent?

## Answer
1. The plan is the panel ruling D/NV_KEY_PORTFOLIO_PANEL_20261120.md, amended by the consumer specification D/GROUNDING_LABEL_CONSUMER_SPEC_20261120.md (its collection orders O1-O13 win where the two differ). Two lanes send: nvkey2 from trinity-2-28 (8 requests a minute; up to 40 when the main project releases its share) for jobs whose inputs sit on Trinity (V1 calibration, V2 aliases, V6 K1 inventory, V5), and nv_orch1 from Orchard preempt CPU jobs (up to 40 a minute, user-approved) for jobs whose frames sit on Orchard (the 64-frame census, V7 ARKit clips, V4 pointing flags).
2. One spend stop covers both lanes: 8,000 dollars at list price; the main project and distillation together stay under 12,000. Every production job first posts a QUESTION with its calibration numbers.
3. Certified so far (raster truth on K1 training captures; dev-S1 rasters for C0): presence at 1% of the frame or more for Astra 6.2 and Argon; a single family's point at 5% or more only; two-family agreed presence. Not certified: points at 1-5% (unless both families agree and V1 shows 90% in the mask), labels under 1% (kept and flagged, never negatives), instance counts, first-seen frames, and pointing-row removals (V4 writes flags only).

## Evidence (95% capture-bootstrap intervals)
- C1, 24 K1 training captures, 6,279 presence facts, one call per capture: presence at 1% or more Astra 96.4 [94.3, 98.1], Argon 94.2 [91.4, 96.5]; absent classes 93.2 / 94.6; point in mask at 1% or more Astra 88.2 [85.2, 90.7] (94.2 at 5% or more, 76.4 at 1-5%), Argon 85.6. Presence is flat across frame quartiles and across the kinds list. 64 frames add nothing for Astra and lose 2 of 24 replies to unparsable JSON. Scores 2-28 K/scores/C1_C1_all24.json (K = /scratch/jjyeung/orch_n30/nvkey1/work).
- V1 (22 K1 training captures, 32 anchors; RESULT 0510Z): (a) guided names plus 3 decoys: presence at 1% or more Astra 95.9 [93.5, 97.9], Argon 92.4 [89.4, 95.1]; decoys rejected per frame 97.0 / 97.8; two families agree on 96.8% of facts and the agreed facts are 97.0% correct [96.3, 97.7]; points at 5% or more Astra 93.5, agreed 92.7 [90.5, 95.0] on ScanNet and ScanNet++ (95.9 ARKit); agreed points at 1-5% only 77.4 [68.3, 83.9]; counts exact at truth 1-4 69.8 / 71.1 and first-seen frames within one frame 76.5 / 65.4 (both fail). (b) blind inventory recall of GT instances at 1% or more (structural labels excluded): Argon 54.8 [44.4, 70.6], Astra 48.6 (ScanNet 88.9 / 84.0, ScanNet++ 41.3 / 34.3); precision on the annotated vocabulary 81.9 / 73.3 (fails the 85% recall bar). (c) judge with ring plus 256-px crop on 300 raster near-miss claims: rows both Argon and Astra flag are 90.0% truly wrong, and the pair flags 0.0% of true ScanNet rows, 4.3% of ScanNet++ and 8.9% of ARKit (box-derived masks), so the flag form passes for N's ScanNet and ScanNet++ pointing rows. Scores 2-28 K/scores/V1a.json, V1b.json, V1c.json.
- V2 alias calibration (300 random K1-train GT crops; 175 controls): GT class or a frozen synonym in the top 3 for Argon 81.1% [75.1, 86.8], Opus 5.5 71.4%; one_object true 92.0 / 89.7. Below the kill line (85%), so V2 production waits on the orchestrator (QUESTION 0517Z).
- C2 pointing pilot, 1,208 store rows (all on dev-S1 rooms, not admitted by N; analysis only): both families doubt 7.8% [5.8, 9.8]; they agree on 95.4% of rows; a blind third (Opus 5.5) keeps 24.5% of the 94 removal candidates and 89.4% of 94 controls, so the removal bar fails.
- C0 census (dev-S1, analysis only): presence 97.2-97.3 on 38 GT captures; the frame-count and proposal-or-selection limits are about equal on GT. The 64-frame census on Orchard (nv_orch1, RESULT 0438Z) lifts about two thirds of the GT-checked ScanNet++ frame-count objects to three frames.
- Prices per 32-frame call, proxy / list: Astra $0.203 / $0.276, Argon $0.094 / $0.124, Opus 5.5 $0.031 / $0.040 for a 10-row judge call. Proxy cost runs about 70-76% of list.

## Spend (updated with each RESULT)
- Trinity runner (nvkey1, then nvkey2): $122.0 list / $90.2 proxy at 05:17Z (about $45 an hour proxy at 8 requests a minute). Orchard (nv_orch1): $22.3 list / $16.4 proxy at 04:38Z. Ledger: D/NV_SPEND_LEDGER.jsonl (one line per job and model, list and proxy).
- Uncounted: 504 gateway timeouts (the proxy cuts a call at 336 s and returns no usage); 7 so far on Trinity, mostly V6 Argon primaries. Each may have cost up to about $0.3 upstream.

## Options rejected, and why
- Counts and first-seen frames as row fields: V1 form (a) misses both bars, and the consumer specification drops them (O10).
- Pointing-row removals for N: the blind third keeps a quarter of the two-family removals; V4 writes flags only, and moves to Orchard because every admitted row's frames sit there.
- 64-frame production calls: no gain for Astra and parse failures; production stays at the 32 anchors (O13).
- Points at 1-5% of the frame, even where both families agree: agreed points land in the mask 77.4% of the time on ScanNet and ScanNet++ (RULING 0436Z's 1-5% path fails).
- The blind inventory as a source of single-family labels: recall 49-55% and annotated-vocabulary precision 73-82%; inventory instances enter only where both families agree.
- A governed 6 GB pull of pointing frames to Trinity: unneeded once V4 sends from Orchard.

## What might not work, and how we would notice
- Correlated errors between families: the both-wrong rate in V6's O3 score and the gap between agreed accuracy and either family alone.
- Raster defects masquerade as labeller errors (ARKit box masks, ScanNet++ half-extent, ScanNet unannotated objects): per-dataset scores in every table.
- Rate limits: METER.json's 5-minute mean; WAF 429 or BLOCK lines in nv_slots/ALLOC.md stop every sender.

## Tests that would settle the open points
- V6's first 30 captures in form v2 (O3): L-or-M at 1% reaching 95, A at 0 px reaching 97, agreed points reaching 90 decide V7's form.
- V1 form (c) judge on 300 raster near-miss rows: flag precision 85% with at most 5% of true rows flagged decides whether V4 flags are worth sending.
- V2's 300-crop calibration: GT class or a frozen synonym in the top 3 on 90%, one-object flag agreeing with the raster on 95%.
