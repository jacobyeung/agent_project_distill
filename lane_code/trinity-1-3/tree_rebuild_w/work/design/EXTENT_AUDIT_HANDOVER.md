# Half-extent audit tool: handover to lane gt_audit (read-only use)

## Where
- Tool: `trinity-1-3:/scratch/jjyeung/orch_n30/rows_r1/work/codeD/audit.py` (403 lines; Codex build D, receipt `/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261117T152950Z_rows_r1_D`). Mirror: `trinity-1-18:/scratch/jjyeung/n30_mirror/rows_r1/work/codeD/`.
- Results it produced: `trinity-1-3:/scratch/jjyeung/orch_n30/rows_r1/out/extent_audit/` (REPORT.md, ROW_AUDIT.jsonl, BOX_AUDIT.json, RASTER_CHECKS.json, EXTENT_AUDIT.json, VALIDATION.json, HASHES.json). Env `/scratch/jjyeung/envs/p1cpu/bin/python`, CPU, about 260 MiB.
- It imports `backproject` and `verify_source` from `/scratch/jjyeung/orch_n30/rows_a2/vsti/code/geometry.py`, and `box`, `grid_points`, `box_grid_5cm` from `/scratch/jjyeung/orch_n30/tree_rebuild_w/work/tree_r1/trace_format/box_v313.py` (it extracts the function source, so the formatter's label rule is the one it replays; 8,572/8,572 stored labels replayed within 1e-8 m).

## How to run it on your own records
The script's inputs are the `FILES` dict at its top (family -> JSONL path) and the raster roots `ROOTS`. Each input line must carry, directly or under `ground_record`: `canonical` (e.g. `scannetpp/<id>`, `scannetppv2/<id>`, `scannet/sceneXXXX_YY`, `arkitscenes/<video>`), `program_audit.independent_ordered_boxes` = list of {`name`, `instance_id`, `centroid` [3], `axesLengths` [3], `normalizedAxes` [9]}, and optionally `source_gt_answer` (metres) and `native_independent_label`. For a list of (scene, object, box) records, write them one per line in that shape into a JSONL on your own /scratch, copy audit.py into your folder, set `FILES={'mine': <path>}`, `OUT`/`CODE` to your folder, and run `python audit.py`; per-box verdicts land in BOX_AUDIT.json, per-row in ROW_AUDIT.jsonl. It does not modify its inputs. Raster lookup key: canonical with `scannetpp/` -> `scannetppv2/` and `/` -> `__`; bare numeric npz names are ARKitScenes.

## Classification rule (per box, never per dataset)
1. Back-project each raster pin's depth pixels of the box's instance (K_frames or K, c2w, pixel centres +0.5, at most 2,000 samples per frame), after the raster passes `verify_source` (valid rotations, >= 2 instances, >= 100 samples, >= 88% containment).
2. Need >= 100 samples over >= 2 frames and one axis >= 0.12 m, else `unknown`.
3. `full`: >= 95% of points inside the box at x1 lengths (6 cm slack) and the 98th-percentile relative extent in [0.35, 0.60].
4. `half`: >= 90% inside at x2 lengths, >= 15 points better than x1, relative extent in [0.70, 1.15].
5. No raster: source-answer fallback; all four x1/x2 assignments of the pair's boxes are tried; a box is certified only if every assignment within 0.03 m of the source answer agrees on its scale and every opposite assignment misses by >= 0.08 m. Conflicting decisive evidence vetoes.

## Known unknowns
- Unknown means not decided, not half: thin boxes, small or partly seen instances, failed pose checks.
- The source fallback depends on the source label being right.
- Rows list two boxes; the tool cannot see whether unlisted instances of the same category would change a category-wide minimum.
- Raster occlusion semantics are not verified (one label per pixel suggests a visibility rendering).
- Finding so far: every `scannetpp/` (v1 asset) box is half; `scannetppv2/`, ScanNet and ARKitScenes boxes are full except a few ScanNet scenes (e.g. scene0348_01).
