Object-route pricing kit: built and packaged for review; the required CPU dry run is BLOCKER.
No GPU, network, SSH, Git, benchmark evaluation, R0 route look, or K1 held-out cache evaluation ran. No file outside this workspace was written.

The code implements size, absolute distance, relative-distance two-candidate/full programs, appearance fallback/strict programs, and counting diagnostics. It uses the reader box formatter and box_grid_5cm, with candidates_argmax selection.
Arms: g3t_s4, object fusion through KBOX_RULES_HOOK, track, T94, optional da3_f32, and dev-S1 per dataset. Missing dependencies stop affected pricing; no replacement mapping, score, or instance grouping is invented.
config/BARS.json records the specification thresholds, item-weighted room bootstrap (10,000 draws; seed 20261119), source comparisons, diagnostic-only counting, and cut order. Thresholds were written before data checks; no route scores exist.
The CPU evaluator reserves each category once, checks direct-score parity, and writes PER_ITEM, ROUTE_TABLE, FIRST_SEEN, and pass metadata. Outputs currently say MISSING; PER_ITEM.jsonl is empty with PER_ITEM_STATUS.json explaining why.

CPU dry run: 56.367 seconds; peak RSS 225716 KiB. Command: bash scripts/cpu.sh.
(a) R0 size 293, relative distance 279, appearance 246: join counts MISSING because the direct table/export receipt is absent. No join success is claimed.
(b) GT-mask checks passed for arkitscenes/41125837 and scannetpp/067e2e4e61: all five programs returned predictions; GT appearance order, per-object first-seen, option matching, full relative program, and refusal/fallback checks passed. StageOne replay is MISSING: no torch in the local CPU environment.
(c) The required 279 real relative-distance traces are MISSING, so the parser-count gate is BLOCKER. Synthetic grammar checks do not replace this gate.
(d) All 98 R0-dev scenes have f32=32, f64=64, intersection=2, union=94; f64 is not a superset. The f64 item twin agrees. All 94 PNGs of scene 04d0dc245b opened and matched chained manifest SHA256 pins.
All 1,493 object-question operands parse, including multi-name counts and farthest-from questions. These are syntax checks, not accuracy measurements.
CPU contract checks: 34 PASS. Command: CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=code /scratch/jjyeung/envs/planner_local_v1/bin/python code/checks.py. Counts/layouts/GT checks above come from scripts/cpu.sh.

Copied tree edits, including inherited N-frame changes (new-copy line numbers; complete before/after text in EDITED_LINES.patch):
- code/vendor/student_pilot/scene_state.py: 27, 33, 37, 44.
- code/vendor/student_pilot/geometry_profiles.py: 83, 123, 143.
- code/vendor/student_pilot/routed_candidates.py: 69, 76, 87, 93, 95, 191, 196, 215, 220, 231, 235.
- code/vendor/student_pilot/routed_features.py: 86, 88.
- code/vendor/student_pilot/tower_read.py: 67, 74, 85-89, 95, 109, 160, 204, 209, 272-274, 294.
- code/vendor/e2e_reader/geometry.py: 18, 48.
- code/vendor/e2e_reader/grounding.py: 140, 142-143.
- code/vendor/e2e_reader/stage1.py: 116, 122-124, 132, 134.
Edit receipt command: CUDA_VISIBLE_DEVICES= PYTHONPATH=code /scratch/jjyeung/envs/planner_local_v1/bin/python code/edit_receipt.py. GTSource is copied unchanged; the dry adapter binds per-frame intrinsics.

GPU commands below are prepared, unexecuted, and blocked until the dry run and required bindings pass. Set APPROVED_GPU (device index), STAGED_GPU_PYTHON (existing /scratch interpreter), and LOCAL_GO_JSON (local authorization/registration receipt); then:
`export GPU="$APPROVED_GPU" PYTHON="$STAGED_GPU_PYTHON" GO_FILE="$LOCAL_GO_JSON"`
| Command from the workspace | Cumulative hard arm limit | Card capacity |
| --- | --- | --- |
| `bash scripts/gpu_r0_g3t.sh` | 3 h shared with r0_sam | 48 GB |
| `bash scripts/gpu_r0_sam.sh` | remainder of the same 3 h | 48 GB |
| `bash scripts/gpu_T94_g3t.sh` | 2.8 h shared with T94_sam | 48 GB |
| `bash scripts/gpu_T94_sam.sh` | remainder of the same 2.8 h | 48 GB |
| `bash scripts/gpu_track.sh` | 4 h | 48 GB |
| `bash scripts/gpu_s1_g3t.sh` | 2 h shared with s1_sam | 48 GB |
| `bash scripts/gpu_s1_sam.sh` | remainder of the same 2 h | 48 GB |
Each script uses /data3/shared/scripts/vnice/vnice.sh, one local lock, a hard timeout, eight threads, 38 GiB host address-space cap, /scratch data/caches, and workspace outputs. Actual GPU peaks are MISSING, including T94; capacity entries are requirements from the spec.
DONE hashes and bindings gate resume. Interrupted reservations block automatic reruns. CUT_LEVEL=1 drops dev-S1; 2 also drops track size/relative; 3 also drops T94. Track priority is appearance, counting, absolute distance, size, relative distance.

Blockers and deviations:
- Direct source is absent locally: /scratch/jjyeung/orch_n30/swarm_an/kit/san_kit.py (specified source host: trinity-3-30). inputs/direct_R1_200_R0-dev.jsonl, direct_D0_200_R0-dev.jsonl, direct_R1_200_dev-S1.jsonl, DIRECT_EXPORT.json, and DIRECT_SCORER.json are MISSING. No remote transfer was attempted.
- R0 has 2,169 rows and 2,167 qids. r0_5f3b5ae38f23ff697994 and r0_c07cd9b246d953847b90 each have two appearance rows with different options. Pricing refuses these ambiguous identities; no deduplication or map was fabricated.
- Track: staged video predictor exists; sam3.pt SHA256 is 9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e. CPU load failed with `ModuleNotFoundError: No module named 'pkg_resources'`. The staged predictor also unconditionally calls .cuda(). See BLOCKER_track.md and TRACK_CPU_CHECK.json; command: bash scripts/track_cpu.sh.
- The single sibling binding config/KBOX_RULES_HOOK.json is MISSING: no winner/screens were assumed. The object-count hook needs the sibling's authoritative instance grouping. Today and GT-mask code are available independently.
- dev-S1 REQUEST.json supplies plan_sha256 but no plan filename. inputs/DEVS1_STAGING_PLAN.json is MISSING; no scene/frame mapping or skip count was guessed. The staged dev-S1 frames were not copied or decoded.
- inputs/REVSI_SUBTYPE_WEIGHTS.json is MISSING (trace-analysis section 11); ReVSI points are not approximated. The optional room prediction path <room kit lane>/out/room_pricing/pred/da3_f32/<scene>/pred.npz is unbound; da3_f32 is dropped until supplied.
- S4 fits were found at /scratch/jjyeung/orch_n30/e3_geom/work/harness/out/FITS.json and copied byte-for-byte. The reader serves own-depth scale, which beat S4 by 5.8 K1 distance points in the specification; g3t_s4 understates metric types.
- SAM output stores the required 80x112 RLE plus the original reader raster to preserve StageOne feature parity. GPU backends and track selection remain unvalidated because no GPU or working torch environment was used.
- LANE_RULES.md was not staged; NFS access was restricted to the two named specification/design files. Mirroring and the RESULT event remain with the orchestrator under the no-network/no-SSH task restriction.
No borderline revision-history prose is retained. This internal report includes execution details because the task explicitly requires them.

Package: out/sb_kobj.tar; SHA256 `ae40a5cfad289f8d61b2864ff2a62b45974f5d079176797c3f2b8952d5b1c4a2`. Command: sha256sum out/sb_kobj.tar. All archived members were checked against CODE_SHA256.json; the tar contains code, configs, scripts, and documentation, with no data or weights.
Primary deliverables: out/REPORT.md, out/DRYRUN.json, out/sb_kobj.tar, and out/sb_kobj.tar.sha256. README.md describes the exact missing-input contracts and CPU pricing command.
