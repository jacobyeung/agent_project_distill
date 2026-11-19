The tower-frames kit is built for CPU review. GPU execution remains BLOCKED by missing inputs; GPU use was 0 hours.

Built: lane-owned tree and reader code; N=32/64 lifting, visibility and geometry; all-slot G3T depth; raw-name SAM 3 replay; A/B/C pricing, bars, seeds, per-capture receipts, and three GPU launchers. The language model retains 32 anchors. `code/README.md` defines input contracts and the single kbox winner hook.

CPU evidence (commands run with CUDA_VISIBLE_DEVICES empty):
- `bash scripts/cpu.sh code/dryrun.py > out/dryrun.log 2>&1` produced `out/DRYRUN.json`.
- A: five stored K1 captures; pose, depth, A0 and A2 self-comparison differences are all exactly 0. Each distance arm covers 10 rows. Rebuilt own-scale geometry equals the cached geometry arrays exactly.
- B support: N=32 lifting equals the original tree on all five captures; N=64 visits 64 slots. Required kbox A0 row parity is MISSING: `/scratch/jjyeung/orch_n30/sb_kbox/out/box_ladder/PER_ITEM.jsonl` contains no A0 rows at this read.
- C: synthetic reader move/turn formatting PASS. Real 440/450 parity is MISSING: `/scratch/jjyeung/orch_n30/swarm_an/kit/san_kit.py` is absent on this node. No capture-to-export mapping was inferred.
- The dry run took 32.276 seconds; peak CPU RSS was 1139292 KiB. Its aggregate status is BLOCKER.
- `bash scripts/cpu.sh code/test_kit.py > out/tests.log 2>&1`: 10 tests PASS, including raw-name alias filtering, 64-frame geometry, anchor-only output, bootstrap bars, scale bridging, and corrupt-output rejection.
- `bash -n scripts/cpu.sh scripts/gpu_environment.sh scripts/run_A.sh scripts/run_B.sh scripts/run_C.sh` passed; all delivered Python files parse with `ast.parse`.

Future GPU commands, from `/scratch/jjyeung/orch_n30/sb_ktow` (not executed):
- `CUDA_VISIBLE_DEVICES="${CARD:?assigned GPU required}" bash scripts/run_A.sh` — expected 0.5 GPU-hours; 1-hour part cap.
- `CUDA_VISIBLE_DEVICES="${CARD:?assigned GPU required}" bash scripts/run_B.sh` — expected 2.5 GPU-hours; 4-hour part cap; requires an A bar PASS.
- `CUDA_VISIBLE_DEVICES="${CARD:?assigned GPU required}" bash scripts/run_C.sh` — expected 0.6 GPU-hours; 1-hour part cap; DA3 remains enabled after an A stop.
- Every launcher wraps `/data3/shared/scripts/vnice/vnice.sh`; the shared deadline is six hours from first GPU start. Asset reads resolve under `/scratch`; writes stay in this workspace. Valid DONE output hashes skip completed captures; partial attempts and HALTED runs block automatic retry.
- Memory: the specification budgets one 48-GB card; actual 64-frame G3T peak is MISSING. `code/dryrun.py` searched `RUN2.log`, `RUN2b.log`, and `run_tower_sam_2/worker.log` under `/scratch/jjyeung/k1`; none contains a peak-memory measurement. No card was chosen. Launch requires a verified log measurement and a separate GPU GO.

Every edited line in the lane copy (new line numbers; original lines and exact text are in `out/EDITED_LINES.json` and `.patch`):
- `code/vendor/e2e_reader/geometry.py`: 18,48.
- `code/vendor/e2e_reader/grounding.py`: 140,142,143.
- `code/vendor/e2e_reader/stage1.py`: 116,122,123,124,132,134.
- `code/vendor/student_pilot/geometry_profiles.py`: 83,123,143.
- `code/vendor/student_pilot/routed_candidates.py`: 69,76,87,93,95,191,196,215,220,231,235.
- `code/vendor/student_pilot/routed_features.py`: 86,88.
- `code/vendor/student_pilot/scene_state.py`: 27,33,37,44.
- `code/vendor/student_pilot/tower_read.py`: 69,85,86,87,88,89,95,109,110,204,272,273,274,294.

Statistics: pose uses 5,000 paired capture draws; distance/camera use 10,000 paired room draws with item weighting; seed 20261119 throughout. A implements pose/short-displacement and lifting bars; B requires positive train lower bound and held-out point; C requires +3 displacement points, positive lower bound, and no rotation/direction loss over 1 point. Missing results never pass. B held-out output permits one completed look after code review.

Outputs: `out/tower_frames/` contains every required output name, availability records, bar decisions and timing receipts. Unrun prices say MISSING. `out/INPUT_AUDIT.json` lists four missing GT paths: the supplied manifest has 300 captures and 296 GT rasters. The GPU roster is restricted to those 296 existing GT captures.

Deviations and unresolved inputs:
- The named tree path is absent; the kit uses the local `b04host3/tree_rebuild/work/base/tree_b01ce449` mirror and `b04host3/b04_e2ehook/e2e_reader`. Byte equality to the remote R1 copy is unverified. The named preflight has no runtime/weight binding; manifest and capture receipts supply the local bindings.
- Part B cannot claim section 6b PASS until kbox supplies its reference A0 rows. Its winning gather/fusion rule binds through `configs/KBOX_WINNING_BOX_RULE.json` only after a pinned PASS decision.
- Part C needs an authoritative local export of the routed items, poses, scale, gravity, truths and frame joins. The sampled `g3s32/export` NPZ is a mask export, not a pose export. The synthetic check does not satisfy real parity.
- Full 64-frame selector labels are MISSING because GT has 32 anchors. The diagnostic code reports top-1 on the same 32 labelled anchors at both N values and states that scope.
- Dense boxes use dense points; printed lists contain only real shared anchors. Printed best is the largest shared anchor; an object with none refuses. Depth AbsRel samples the GT raster at the 51x51 endpoint grid with nearest pixels.
- Room-bootstrap draw count comes from the box-ladder specification. GPU forward passes, timing estimates and memory have not been validated on hardware. Staged weight hashes are verified by the future runner before loading.
- The archive was not mirrored: the task forbids network and SSH. No GPU, network, Git, tmux or process-control action was run.

Archive: `out/sb_ktow.tar` contains code, configs, scripts, specs and review receipts; no data, weights or tensor caches. `scripts/package_delivery.py` created it and checked 314 members. Verify with `sha256sum -c out/sb_ktow.tar.sha256`.
SHA-256: `7438d6f5e96b7e5c026c1d713c92328e91d08a7407f97cfbe6f4b4e6b170d67c`.
Code identity: `9bc03a571d96d610e445e6dcf18d11c7d04f3cc5c955e653a7ba8f6a8b3cf349` (`out/CODE_SHA256.json`).
Writing skills: no-archaeology and summary; no borderline history sentences were retained.
