# Train/eval scene audit: every training stream of the current and planned runs against every evaluation set (2026-11-10)

Analyst: lane scene_audit (Claude Opus), read-only CPU work on trinity-2-18. Scripts and raw outputs: `/scratch/jjyeung/orch_cd/scene_audit/` (`resolver.py`, `overlap.py`, `divisions.py`, `streams.py`, `out_*.json`). No benchmark answer field was read.

## Question
Is each training stream of the current line (CP1-Rv), its ancestors (C1-a m800, T0 m800, CP1 m200), MDG-A and the planned CP2 scene-disjoint from VSI-Bench 5,130, VSI-500, dev 858, VSTI-450 v3, ReVSI dev cap71, the clean camera pool and E0? Where a stream is not disjoint, how many rows and scenes overlap, and what would make a run's training receipt clean?

## Answer
- **No stream shares a scan with any evaluation set** (0 strict overlaps in every cell). Every training key resolved; none stayed unresolved.
- **At the room level, the line shares one ARKitScenes venue with VSI-Bench and ReVSI.** Venue 381879 holds the Training videos 41159521 and 41159526 and the Validation video 41159525. The Validation video carries 17 VSI-Bench items, 2 VSI-500 items and 2 ReVSI cap71 items.
  - CP1-Rv's own prepared rows are clean at the room level too. Its prep refuses or drops every row on the two Training videos.
  - The venue rows entered the line through its ancestors:
    - C1-a: 160 pose rows;
    - T0: 15 C1-r clips, 12 VQA rows, at most 5 V-SD rows and about 23 routing rows.
  - Every checkpoint downstream therefore inherits them: T0 m800, CP1 m200, CP1-Rv and MDG-A.
- **The planned CP2 would train on the clean camera pool's ScanNet slice.** CP2's pose draft includes A4 `r_s`, 392 rows. The clean pool's d1 slice is those exact 392 clips: 1,176 items on 98 scans_test scenes.
- **The `benchmark_trained_diagnostic` flag does not measure contamination.** Every provisional row builder sets it True unconditionally. No scene filter can make these full fine-tuning receipts clean under the current harness.

## Normalisation
- One physical identity per training key, built from these namespaces:
  - native ids;
  - rung-1 tokens `'v'+sha256('rung1 scene <ns>/<scene>')[:12]` for ns `scannet|scannetppv2|scannetpp|arkitscenes`;
  - posedata's ARKit token `'v'+sha256('arkitscenes/<video>')[:12]`;
  - posedata `v3.json`;
  - the p1cb alias authority (rung1, v590kgt and adt families);
  - K6-plan ARKit aliases;
  - r7 `scene_map.json`;
  - posedata2 `tmap.json`;
  - MP3D `'v'+sha256('rung1 scene mp3d/<opaque b>/<region>')[:12]`, with opaque b mapped to the building through `posedata2/work/a4/items_m.json` and `cnt/lm.json`.

