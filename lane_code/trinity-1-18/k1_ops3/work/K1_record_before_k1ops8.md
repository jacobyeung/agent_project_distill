# K1 grounding kill test: own phase, convert and tables on the deployed pipeline (k1_ops7, 2026-11-16)

Status: IN PROGRESS. Own and convert are complete. Tables, refit, render and report wait for review_k1c pass 3 (PATCH3: portrait GT canvas map; PATCH4: JSON bound). No K1 score exists yet. The E3 deployed-geometry column (GD_reviewed and GD_sealed) is running.

## Question
Does the deployed mask and geometry backend keep the frozen SAM 3 tower, or should it use the student's own grounding? K1 decides this on 300 training captures (primary 296 under amendment 1, sensitivity 300), with manifest v2 under amendment 2.

## What ran
- Phase tower_sam: 300 of 300 captures on trinity-1-18 (root /scratch/jjyeung/k1/run_tower_sam_2, manifest v1 91a2dbf9).
- Phase own: Orchard job 170235 on one H100 ran 12:28:39-13:52Z. It used batch d1553118, the fix that stages CONFIG assets.depth.
  - Captures took 159 s for the first and about 15-18 s after that, prefill only, so 300 captures needed 1 h 23 min.
  - The return ad2472b1be07d4193 (result.tar.gz sha 09699e67, 97,853,329 B) was verified on pool and GCS, and its extracted root is /scratch/jjyeung/k1/own_170235/native/probe (300 PHASE_COMPLETE).
- Phase convert: 300 of 300 on CPU, written to /scratch/jjyeung/k1/run_convert_2 with manifest v2 e684e0c7.
  - The interpreter was envs/sam3_scipy_ovl: the tower_sam env plus scipy 1.14.1, the C8r production version.
  - The output cap was --max-bytes 4000000000, the value tower_sam run 2 used. run_convert_1 HALTED on the 1.5 GB default after 188 captures and was not used.

## Deployed gravity guard (ORCH ruling 20261116T1300Z)
- The deployed backend, which is the accepted native read C8r, installs the reviewed guard gravity_guard.py (sha b2df9c3a, validate_up_convention) over the sealed GeometryContract.validate. K1 convert and render install the same guard.
- A capture the reviewed guard refuses gets a bound refusal receipt and counts as a backend failure. It is never dropped.
- k1_phases.py and native_kit stay byte-equal, so the tower and own receipts still bind.
- Refusals on K1 own geometry (GUARD_REPORT.json in the convert root):

  | Guard | ARKitScenes (162) | ScanNet (51) | ScanNet++ (87) | Total |
  |---|---|---|---|---|
  | reviewed (deployed) | 0 | 0 | 2 | 2 |
  | sealed | 52 | 0 | 2 | 54 |

- The two reviewed refusals are scannetpp/0f69aefe3d (3 rows) and scannetpp/2c7c10379b (11 rows). Both are train captures in the primary set; no held-out row is refused.
- Under the sealed guard, 18% of captures would have scored as failures, almost all of them ARKitScenes captures whose reference camera is ill-conditioned (plane < 0.3).

## Portrait aspect stretch (ORCH ruling 20261116T1527Z)
- The deployed routed policy maps every frame onto a fixed 240x320 canvas: routed_features SHAPE (480,640), OUTPUT_SHAPE (240,320), nearest zoom.
- 80 of 300 captures are portrait (source 640x480 H x W). Their masks are the stretched image, while their pinned GT rasters are 320x240.
- K1 maps portrait GT onto the canvas with the same rule and records gt_canvas_map per capture. The primary set has 219 identity captures and 77 stretch captures.
- Evidence on arkitscenes/41048124: stretched GT gives a mean best IoU of 0.467 against candidates; any rotation gives at most 0.129. The landscape ScanNet control gives 0.434.
- The stretch is a defect of the deployed pipeline (aspect distortion on 80 of 300 captures). The report splits head accuracy into portrait and landscape.

## JSON bound (ORCH ruling 20261116T1548Z)
- 12 primary captures have tower candidates.json files over the 20 MB bindings.load bound (largest 31.6 MB). K1 reads them through a local 64 MiB loader after the sha pin check, and the receipts record the bound.

## Disclosures that go with every K1 number
- setlib d9271cc9 is a vendored copy. The original setlib and the sklearn bundle were lost with trinity-2-18.
- sklearn 1.5.2 (planner_local_v1) is proof_p2's named interpreter, and fixture proof P2 was not run.
- Amendment 1 disclosures also apply (pinned PNGs, no fallback traces, restored report import path).

## Evidence
- Lane folder: trinity-1-18 /scratch/jjyeung/orch_n30/k1_ops3/work: partb/{SUBMIT7.out, CANARY7.out, FINAL7.out}; own7/diag/{guard_census.py, full_guard.json, shape_diag.py}.
- Kit and reports: kc_guard, kc_guard_brief/REPORT.md and PATCH*.diff.
- Reviews: events/review_k1c/REVIEW_VERDICT_K1C{,2}.md.

## Options rejected
- The sealed guard as registered: it is not the deployed pipeline, and it would halt convert.
- Dropping refused or portrait captures: amendment 1 forbids dropping.
- Rotating portrait GT: the IoU test above rules it out.

## What might not work
- The reviewed guard passes geometry whose reference camera is nearly vertical. If such captures carry large pose errors, the deployed column looks worse on ARKitScenes; the portrait/landscape split and E3's GD_sealed versus GD_reviewed show it.

## Tests that settle it
- The registered C1-C5 tables on primary 296 and sensitivity 300, with an equal verdict on both (amendment 1). Results go here when downstream finishes.
