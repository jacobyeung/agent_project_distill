# VQA and pointing streams for the mixed gate and the final run (mixdata, 2026-11-08)

Lane mixdata (trinity-2-18). Status 14:50Z: VQA and pointing receipts exist on AWS (job 105506) and are the final
run's streams. V-SD was tried and stopped (§4.3).
Both streams use C1's `build_stream` (schema c1-stream-v1) as patched on branch `mixdata-streams-20261108`
(commit f104924, parent cd671e6 = p3-mixed-20261108), which p3_build lands.

## 1. Question and answer
**Question.** Which rows go into the VQA and pointing streams, in what proportion? The same databases serve the mixed
gate (8 GPUs, ~200 updates) and the final run from BASE.

**Answer.**
- **VQA stream (V): 23,082 GT canonical-trace rows** on A1's training scenes, no answer-only rows (orchestrator ruling
  under USER 11-02: GT-solvable types get our canonical traces). Each type's answers match VSI-Bench 5,130's
  distribution. G1 and the final run use the same rows; base self-distilled rows were not viable today (§4.3).
- **Pointing stream (P): 17,408 GT rows** on 272 ScanNet/ScanNet++ scenes: 65% visible (small objects
  over-weighted), 35% absent. Target is base Qwen's JSON on the integer 0-1000 grid, `{"point_2d": [x, y]}`, or
  `{"point_2d": null}`.
- **Schedule (orchestrator ruling):** pose : routing : VQA : pointing = 1 : 2 : 1 : 1 microsteps, 8 rows each; each
  stream sized for <= 3,000 updates. The gate draws 1,600 rows per stream; p3_build may change the ratio in its config.
- **Frames:** every row names its 32 frames as `/data2/k6tk/<sha2>/<sha>.png` (the k6tk store on AWS, MAP sha
  17aa3e9e). The AWS job extracts exactly the referenced frames and bundles them for the gate job (§5).

## 2. Inputs and hard constraints (evidence)
- **Division.** `build_stream` raises on any row outside the pose receipt's division, so sources are pre-filtered.
  A1's division `/lustre/.../ap/e84d901c/z/4c230a7e.json` (sha 0d28fdd4…): 4,265 training scenes (d3 ARKit 2,868,
  d1 ScanNet 712, d2 ScanNet++ 685), one held-out d1 scene. Its `a1_authority` exclusions include benchmark lists
  b1/b2 and the gate scenes. Every row is checked against it before shipping.
- **Row format.** 32 frames (path + sha256, strictly increasing indices, `timestamps = index / fps`, fps d1 24,
  d2 60, d3 10), `total_num_frames` from the k6tk SCENES table. The trainer adds `ANSWER_FORMAT_INSTRUCTION`.
