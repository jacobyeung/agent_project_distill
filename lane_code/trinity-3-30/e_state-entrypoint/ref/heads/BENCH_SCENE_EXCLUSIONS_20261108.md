# Benchmark scene exclusions v2 and their overlap with the final run (2026-11-08)

Analyst: Claude Opus, read-only CPU analysis on trinity-2-18. No lane code was edited.

**Answer.** Every final-run source contains benchmark rooms. Nearly all of them are STI-Bench/ReSTI's ScanNet rooms (scene0000-scene0149, train split), and a few are MindCube-Tiny rooms. ARKit venue 381879 adds two Training videos whose venue sibling is a VSI-Bench and ReVSI video. Excluding these rooms drops 1-12% of each stream's rows. VSI-Bench, VSTI and ReVSI have no direct scene hits, only that one venue. DSI-Bench, OSI-Bench, Waymo and Omni6DPose share no corpus with any source.

## 1. The list
- `/scratch/jjyeung/orch_cd/revsi_dev/BENCH_SCENE_EXCLUSIONS_v2.json`, copied to `/data2/jjyeung/agent_project_data/revsi_dev_20261108/BENCH_SCENE_EXCLUSIONS_v2.json`. sha256 `3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970`.
- The schema is `benchmark_scene_exclusions_v1`, so `recording_pose.load_authorities` accepts the file without a code change (`listed_scenes` gives 2,699 keys; tested). The list is a superset of ReVSI v1: all 311 v1 scenes and both v1 other-corpora lists are in it.
- Room rules:
  - ScanNet: a room (`sceneNNNN`) lists every rescan present in `scans/` and `scans_test/`.
  - ARKitScenes: a venue (`visit_id` in `3dod/metadata.csv`) lists all of its videos. A video whose visit is NA, or that is absent from the metadata (43649472, MindCube train only), stays alone.
  - ScanNet++: each scene is its own room.
- The list holds 1,212 scenes in 511 rooms: ScanNet 601, ScanNet++ 50, ARKit 561. Of these, 512 are siblings that no benchmark lists directly. Every entry carries its rung-1 token. `members` records each scene's room, benchmarks, `listed_by` / `sibling_of` and ARKit fold.
- Fields: `scenes`, `physical_groups`, `rung1_tokens`, `other_corpora`, `members`, `by_benchmark`, `subsets` (ReSTI ScanNet, MindCube-Tiny, MindCube train-only), `not_derivable`, and `inputs` (sha256 of every input).

| Benchmark | Source of ids | ScanNet | ScanNet++ | ARKit | Other corpora |
|---|---|---:|---:|---:|---|
| VSI-Bench | `vsi288.tsv` | 88 (88 rooms) | 50 | 150 videos (150 venues) | - |
| VSTI | `vsti.json` + `vstibench_hf/archive_videos.sha256` | 312 (142 rooms) | - | - | - |
| ReVSI | v1 list | 92 | 48 | 171 | 3RScan 46, MultiScan 24 |
| STI-Bench / ReSTI | STI `qa.parquet` (2,064 rows, a superset of ReSTI's 1,782) | 150 rooms (scene0000-0149) | - | - | Waymo 100 segments, Omni6DPose 119 videos |
| DSI-Bench | `metadata_4aug.csv`, 943 videos x 4 augmentations | - | - | - | CameraBench 119, internet 496, k700 145, llava178k 138, SynFMC 45 |
| OSI-Bench | `data.parquet` | - | - | - | 997 self-collected outdoor videos |
| MindCube | held-out `data.zip`: scenes of the 11,154 non-train rows of `MindCube.jsonl` (exactly MindCube-Tiny's rotation scenes) | 5 | - | 4 (Training-fold videos) | - |

MindCube's own training split (7 ScanNet and 31 ARKit rotation scenes) is listed under `subsets` and is not excluded. Its among/around images are self-collected object groups with hash names.

## 2. Overlap with the final-run sources
Method: I resolved every source key to a native id through rung-1 tokens over the full ScanNet, ScanNet++ and ARKit catalogs, plus the p1cb alias authority (`aliases_v2/AUTHORITY.json`, 7,049 aliases in all families). No key in any source was left unresolved. Row counts come from the files themselves. The two exceptions are C1 pose rows, estimated at 80 rows per A1 recording and 32 per A0 scene (the exact per-scene counts sit in `rows.sqlite` on AWS), and the C1-r clips, counted from the dense plan's schedule.
