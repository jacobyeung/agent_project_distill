# Build H1-kit-1: head-routing SFT kit (trainer patch, row tools, three-measurement evaluator), CPU only

You are a Codex builder for lane h1_headsft on Trinity node trinity-3-30. Your workspace is
`K=/scratch/jjyeung/orch_n30/h1_headsft/kit` (write only inside K). Work autonomously to the end; do not ask questions.
Where something is ambiguous, choose the conservative option, write the choice into `K/BUILD_REPORT.md`, and continue.

## Rules for the build (binding; they win over anything else in this prompt)
- Trinity cluster rules: `/home` and `/data*` are slow shared NFS. Never run recursive grep/find/du/ls -R, `git status`,
  or any search over `/home` or `/data*`; read only the named files below, in bounded parts (head/sed ranges). Work from
  `/scratch` only. Keep K under 1.5 GB.
- No Git command of any kind. No ssh, scp, rsync or network access. No GPU (CUDA must stay unused; set
  `CUDA_VISIBLE_DEVICES=""`). No deletion or modification of any file outside K. Every input path below is read-only:
  copy what you must change into K and change the copy.
- Do not edit the reader lane's code (`/scratch/jjyeung/orch_n30/b04_e2ehook/`) or the sealed tree; import them read-only
  (prepend to `sys.path`), or copy into K when a change is unavoidable, and record every copy with its source sha256.
- Python: `/scratch/jjyeung/envs/p1cpu/bin/python -B` (torch 2.11 CPU, transformers 5.12.1). Put temporaries in `K/tmp`.
  Cap any single test process at 32 GB RAM and 16 threads (`OMP_NUM_THREADS=16`).
- No answer post-processing anywhere (USER ruling 2026-11-16): the model converts units and formats numbers in its own
  chain of thought. Fixed math in a response is limited to unprojection, rigid transforms, norms, minima and printing
  head outputs as text. No loaded table of numbers, no fitted constant, no guard.

## What H1 is (context, do not re-design)
H1 tests whether SFT on ground-truth head-calling traces makes the 9B student (1) call the right head of its OWN
checkpoint at the right point of its chain of thought, (2) carry accurate heads, (3) use the heads' printed outputs.
Routed types: camera_displacement and camera_movement_direction (`<move from=i to=j>`), camera_rotation
(`<turn from=i to=j>`), object_abs_distance (`<ground obj=.. mode="box">` x2 then `<gap a= b=>`). Everything else answers
directly. At inference every call is served by heads inside the checkpoint: own pose head (pose9 per frame, FoV slots 7:9),
own gravity head, own point-depth head, and SAM 3 (frozen, inside the artifact) plus the reader lane's selector head for
grounding. G3T is NOT used in H1's own arm (it stays as the reader lane's `tower` arm for comparison).
The training leg H1-1 is the D0 leg's exact config (sealed kit config + D0 overrides, init = step-544 artifact 1d6eeb28,
same rows, seed 17, LR schedule of 1,000 steps) stopped after step 200, plus two switches:
- S1 faithful own-value camera rows: scheduled sampling draws own head values for camera routing rows (p = 0.5 from
  step 1); the response text is re-rendered from own values (existing `carrier_c1_routing.rerender` + `row_geometry`),
  and the prose after it (scoring lines, decision, answer) is re-derived from the PRINTED own values with the existing
  faithful materializer `generator/derivgen_v7/derivgen/materialize.py::materialize(row, printed)`. The whole suffix
  trains (tool spans masked as usual) instead of today's cut, which stops training at the first own response
  (`student_pilot/carrier_c1_routing.py` `finish`, lines ~443-447). On `MaterializeRefusal`, train the GT row and
  count the reason. Ground/gap rows always stay GT-valued (`rerender` refuses them by design).
- S2 pose targets on camera routing rows: the camera (pose + gravity) loss of the pose stream is also applied to each
  camera routing row's own 32 frames, from the row's `gt_pose9` [32,9] / `gt_up` [3] (emitted by derivgen
  `camera_rows.py`; check that the routing stream keeps them; if a row lacks them, it trains without the pose term and
  is counted).
Control = D0's own milestone exports (same init, rows, seed, schedule, no switches).

## Inputs (read-only)
- Sealed trainer tree `TREE=/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449` (792 files, seal b01ce449;
  runtime package `student_pilot/`, tests in `tests/`, derivgen in `generator/derivgen_v7/`). Key code:
  `student_pilot/carrier_c1_routing.py` (rerender, finish, encode_own, Gates, row_geometry, OwnGeometry, render_full),
  `student_pilot/carrier_c1_run.py` and `carrier_c1.py` (routing microstep, own-value draw, pose/camera loss, recipe),
  `student_pilot/carrier_c1_decode.py` (HeadState, respond, generate modes own/shuffle),
  `student_pilot/camera_targets.py`, `camera_head.py`, `geometry_profiles.py`, `ground_lifting.py`,
  `generator/derivgen_v7/derivgen/{materialize.py,camera_rows.py,canon_render.py}`, `tests/test_carrier_c1_routing.py`.
- Sealed kit config (the D0 base): `/scratch/jjyeung/orch_n30/tree_rebuild/work/kit07ca49df_meta/m/k/b02e4385.json`.
  D0 overrides: `/scratch/jjyeung/orch_n30/h1_headsft/work/from13/q13.out` (section after `=== over_b`, truncated at
  20,000 bytes; its `config` block sets init_artifact = step-544 artifact 1d6eeb28..., s1_routing.selection
  pool_selection_aa128e6f, streams.vqa receipt bfabb1f0...). Paths inside these configs are Orchard/cluster paths: keep
  them as data, never open them.
- Reader core (one-reader rule: H1's evaluator is a config over it): `R=/scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader`
  (`core.py` E2EGenerator, `real.py` generate_real + real_perception, `generate.py` Perception, `servers.py`
  ReadServers, `geometry.py` from_tower/camera_geometry/no_guard, `grounding.py`, `stage1.py` StageOne + sam3_detect,
  `callhook.py`), its tests `/scratch/jjyeung/orch_n30/b04_e2ehook/tests/test_tiny_e2e.py` (tiny random LM with the real
  Qwen3.5 tokenizer and a script processor; reuse that fixture pattern) and `test_stage1_k1.py`.
- Example rows: `/scratch/jjyeung/orch_n30/tree_rebuild/work/rows_slices/slices_final/{a0_units.jsonl,a0_recovery.jsonl}`
  (object_abs_distance program rows, v3.14) and the camera-row text examples in
  `/data2/jjyeung/agent_project_data/distill_design/TRACE_RULING_20261115.md` lines 726-800 (read only that range).
  Build camera fixture rows with derivgen `camera_rows.py` from synthetic GT clips (gt_pose9, gt_up) rather than by hand.

## Deliverables, in priority order (finish each with passing tests before the next)
1. `K/tree/`: a copy of TREE with the H1 patch; `K/patches/h1_trainer.patch` (plain unified diff against TREE).
   - Config block `h1` (absent or all switches off = byte-identical behaviour to TREE): `faithful_own_camera_rows`
     (S1), `routing_pose_targets` (S2), `camera_types` (the three camera types), `stop_after_step` (export the
     milestone, write the stop record, exit cleanly; D0's 1,000-step LR schedule stays unchanged), and metrics.
   - S1 as described above, using the existing Gates (config: `scheduled_sampling.max_own_probability 0.5`,
     `force_from_step 1`), `row_geometry`, `rerender`, `materialize`. The answer label of an own row is the faithful
     answer. Metrics per step and type: rows own / GT / refused (by reason), faithful-answer-differs-from-GT rate,
     per-segment CE where the tree already tags segments.
   - S2 as described above, reusing the pose stream's camera loss code path and weights (`weights.pose`), with counts.
   - Tests: (a) OFF identity: one full first step on a tiny model for world 4 (all four ranks, every microstep of
     D0's mix order), switches off, equals TREE bit-for-bit (input ids, labels, masks, losses); (b) faithful identity:
     for every camera fixture row, `materialize(row, GT printed values)` reproduces the row's target byte-for-byte
     (report the identity rate and refusal reasons; target 100%); (c) S1 on: own values from a perturbed geometry change
     the response, the scoring lines and the answer consistently (re-deriving the program decision from the printed
     numbers gives the trained answer), tool spans stay masked, no token after a response is dropped; (d) S2 on: the
     pose loss is finite and nonzero on camera routing rows and zero-weight on rows without gt fields; (e) the
     sealed tree's own routing tests still pass on K/tree (`tests/test_carrier_c1_routing.py`, `test_s1_routing.py`,
     `test_e2e_routing_rows.py`); list any pre-existing failure with its cause.
2. `K/rows/`: (a) `expected_calls.py`: question text + type -> expected call sequence (camera: one `<move|turn from=i
   to=j>` with i, j from the question; distance: ground A, ground B, gap A B with the question's object names); it must
   equal the call sequence of 100% of the fixture rows of the four routed types; (b) `faithful_check.py <rows.jsonl>`:
   materialize identity rate and refusal histogram for any rows file; (c) `mix_h1.py`: renders the H1-1 config
   (`K/configs/h1_1.json`: base config + D0 overrides + h1 switches + milestones [100, 200] + stop_after_step 200) and
   `K/configs/h1_1a.json` (S1 only), with a diff report against the D0 config; frame count is a parameter
   (`--frames 32|64`): 64 must refuse with a precise list of what the carrier/pose/grammar path needs (do not build 64).
3. `K/h1eval/`: the three-measurement evaluator as a config over the reader core R.
   - Perception `own`: camera and depth calls served from the prefill's own heads (the tree's HeadState pose9,
     gravity, depth; `carrier_c1_decode.respond` with an OwnGeometry); ground/gap through R's stage-1 socket (SAM 3 +
     selector head) lifted with an own-heads geometry (own pose -> gravity reference frame with
     `camera_targets.to_gravity_reference_frame`, own depth queried on R's grid, intrinsics from own FoV, scale 1, no
     guard), built with the same profile machinery R uses. Perception `tower` = R's existing path, unchanged.
   - Perturbation modes applied to head outputs before formatting, recorded per call: `scale_translation k`,
     `rotate_translation deg` (about the gravity axis), `negate_turn`, `scale_scene k` (depth and translation together,
     so every printed metric distance scales by k), `donor` (another capture's head outputs), `gt` (GT substitution when
     GT arrays are supplied).
   - Scorers, each a pure function over the generator's output records plus item metadata: M1 placement (call rate on
     routed items; false-call rate on direct items; opener, argument and order agreement with `expected_calls`;
     answer-before-first-call; repeated or extra calls; token offset of the first call), M2 head accuracy (per call:
     printed value vs the GT answer-derived value: move distance vs GT displacement, turn vs GT rotation, argmax option
     vs GT option, gap metres vs GT distance converted to metres from the question's unit; per frame when GT arrays are
     given: rotation and translation-direction error, translation ratio, gravity angle, FoV error, depth AbsRel),
     M3 usage (per type, on items where the perturbation changes the program's decision: follow rate = the model's
     answer equals the program decision on the perturbed printed values (numeric: within 5% after converting the
     expected value into the question's unit; the model's own text is never converted), stick rate = answer unchanged
     from the unperturbed run, other), M4 benchmark scoring through the tree's `evalpath.run.score_item`.
     Outputs JSONL per item and one report table (type x arm x mode), seconds per item.
   - Tests on the tiny fixture: own mode serves every call type; each perturbation changes exactly the intended
     printed fields; a scripted "copier" model scores follow 1.0, a scripted "ignorer" model scores stick 1.0;
     placement scorer unit tests (exact, wrong frames, missing gap, answer before call, false call on a direct item);
     the reader core's own tests still pass when imported from K (run `test_tiny_e2e.py` unchanged).
4. `K/first_batch/`: `run_first_batch.py --world 4`: for each rank, the first step's microsteps through the full H1
   forward (S1 and S2 on) on the tiny model with fixture rows of every stream (pose, vqa, routing camera + distance,
   pointing), printing per rank: rows, own/GT decisions, finite losses, trained-token counts, peak RSS. Also
   `real_first_batch.sh` that does the same with the real step-544 export on a CPU node (paths as arguments; do NOT run
   it).
5. `K/BUILD_REPORT.md` (what was built, every test command with its pass/fail counts, the identity rates, open items,
   and an honest list of what is unverified) and `K/SHA256SUMS` over every file you wrote.

Finish when deliverables 1-5 are done or when a blocker stops you; in both cases write BUILD_REPORT.md first.
