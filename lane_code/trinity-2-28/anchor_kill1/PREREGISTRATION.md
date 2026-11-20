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
Use only the 1,012 K1 decision rows and their sb_kbox4 candidate pools. Retain empty-frame calls as not seen. Report on-target rate, not-seen rate, paired change, corrected-wrong fraction f and damaged-right fraction h. Use 10,000 paired room-cluster bootstrap draws, seed 20261120, percentile 95% intervals. Report object-call and paired-row denominators explicitly. The specification says type points; a task-score replay is required to certify a distance-type bar if it cannot be identified with on-target points.
For frame sensitivity, use the nearest different anchor with GT area >=1%, breaking equal-distance ties toward the earlier anchor; separately identify immediate-adjacent eligible anchors and cases with no eligible alternative. No fitted choice.
For Locate accuracy, report each existing development read separately by question type and dataset. Use exact frame mapping and exact noun-to-GT identities; report unresolved nouns and missing rasters separately, never silently count them visible. Report visibility conditional on the object being visible at >=1% on any anchor, plus all resolved citations. Ground truth is diagnostic only. No training rows are produced.

## Results
Pending input inventory. No scores computed.

## What might not work and how we would notice
Missing candidate pools prevent the kill test. Missing rasters or uncertain frame maps reduce Locate coverage; per-reason counts expose those losses. Multiple GT instances under a noun prevent an instance-specific claim. Direct traces alone cannot certify routed Locate coverage or gap MRA.

## Status
Bars registered; CPU input discovery in progress. No GPU, SSH, Git, API, or deletion.
