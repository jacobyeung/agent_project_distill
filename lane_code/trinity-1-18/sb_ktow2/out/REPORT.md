The tower_frames v2 kit is built; CPU dry run: BLOCKER. GPU use: 0 hours.
The remaining CPU blocker is section 8b: the box kit has no A0 rows for four selected train captures.

Changes vs v1: pinned 239/57 capture and 1,037/216 distance-row sets; independent context/view gates; train-only decisions; held-out report after DECISION.json; explicit C/V/box arms; reader median_ratio per output; anchor numbering; staged camera calls; shared-ledger budgets and first-capture peak measurement.
CPU source: the pinned R1 reader in the staged pack, with N edits; tree: `/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449`.
CPU interpreter: `/scratch/jjyeung/envs/p1cpu/bin/python`; GPU interpreter: `/scratch/jjyeung/envs/sam3_scipy_ovl/bin/python` (torch/numpy/PIL/scipy discoverable; GPU execution untested).

Commands producing the reported evidence, from `/scratch/jjyeung/orch_n30/sb_ktow2`:
- `bash scripts/cpu.sh code/dryrun.py > out/dryrun_v2.log 2>&1`
- `bash scripts/cpu.sh code/test_kit.py > out/tests_v2.log 2>&1`
- `bash -n scripts/cpu.sh scripts/gpu_environment.sh scripts/run_A.sh scripts/run_B.sh scripts/run_C.sh`
- `bash scripts/cpu.sh scripts/finalize_v2.py` writes the report, edited lines, hashes, GPU request and tar.
The dry run took 41.515 s; peak RSS was 809612 KiB. It used nice 10 and eight numerical threads.
Section 8a: five train captures; stored C64 self-comparisons have zero pose/depth/distance differences. All five recomputed scales agree with stored values within 1e-4 relative.
Section 8b: N=32 lifting matches the original tree on all five captures; N=64 visits all 64 slots. A0 reference matches the first capture; four references are MISSING.
Section 8c: synthetic formatting with a staged scale/gravity passes; all 450 records load and their calls parse. Real 440/450 parity awaits GPU G32 replay.
Section 8d: all 296 captures pass strictly increasing anchor slots and 9,472 anchor/model-row hash comparisons. Held-out values were not opened.
Regression checks: 16 tests PASS, including train-only bars, independent Part B, median-of-ratios scale, one-look refusal, shared budget admission and corrupt-resume rejection.

Exact CPU blocker: `/scratch/jjyeung/orch_n30/sb_kbox2/out/box_ladder/PER_ITEM.jsonl` lacks A0 rows for:
- `arkitscenes/41069076`, `arkitscenes/41098061`, `arkitscenes/41098085`, `arkitscenes/41098191`.
`out/BLOCKERS.json` names every missing row ID and the hashed reference file; no reference was synthesized.
The single box hook is `configs/KBOX_WINNING_BOX_RULE.json`. The box decision has no frozen object winner, so obj arms and the joint-gain table remain MISSING until that hook is bound.
Part C blocker: `/scratch/jjyeung/devs1_r2/REQUEST.json` has a bundle hash and root but lacks `items[].frames[].{index,path,sha256}`. All 450 real parity items are currently unbound; no scene/digest mapping was inferred.

GPU commands below are prepared, not run; each uses one 48-GB card and stops allocation above 40 GB:
- `CUDA_VISIBLE_DEVICES="${CARD:?assigned GPU required}" bash scripts/run_A.sh` — expected 0.5 GPU-h; hard stop 0.75 h.
- `CUDA_VISIBLE_DEVICES="${CARD:?assigned GPU required}" bash scripts/run_B.sh` — expected 2.5 GPU-h; hard stop 3.0 h; no Part A bar gate.
- `CUDA_VISIBLE_DEVICES="${CARD:?assigned GPU required}" bash scripts/run_C.sh` — expected 0.6 GPU-h; hard stop 0.75 h; diagnostic only.
Launchers use `/data3/shared/scripts/vnice/vnice.sh`, workspace-only writes, scratch-only assets, explicit GPU GO and a shared-ledger reservation. Valid DONE hashes skip finished units. Every pass records seconds and peak allocation.
The orchestrator owns the shared 16 GPU-hour ledger and two-card limit. `GPU_NEED.json` gives the full order and reverse cut order. This lane cannot create that shared reservation or write another lane's ledger.

Edited copied-tree/reader lines (inclusive ranges; exact before/after text and source hashes are in EDITED_LINES.json and EDITED_LINES.patch):
- `code/vendor/e2e_reader/geometry.py`: 18,48.
- `code/vendor/e2e_reader/grounding.py`: 140,142-143.
- `code/vendor/e2e_reader/stage1.py`: 116,120,127-128,136,138.
- `code/vendor/student_pilot/geometry_profiles.py`: 83,123,143.
- `code/vendor/student_pilot/routed_candidates.py`: 69,76,87,93,95,191,196,215,220,231,235,310-311,313-318,361.
- `code/vendor/student_pilot/routed_features.py`: 86,88.
- `code/vendor/student_pilot/scene_state.py`: 27,33,37,44.
- `code/vendor/student_pilot/tower_read.py`: 69,85-89,95,109-110,204,272-274,294.

Decision code uses 5,000 paired capture draws for pose and 10,000 paired room draws for distance, seed 20261119. Every full arm must cover its pinned population before a bar can pass. Box/frame/joint gains use identical rows; only joint gain prices both changes.
V64 member precision and selector labels use anchor members because GT has only 32 rasters. Printed lists/best/first use anchors; dense-only objects print not seen and are counted. First-seen truth uses GT share >=0.002.
Part C exposes G64_rot/G64_dir, G64_disp_proxy and native/proxy DA3 arms; proxy displacement is sensitivity only and cannot authorize adoption.
R0-dev and official items were not read. R0 access requires frozen PRIMARY_ARMS.json and consumes an exclusive per-category receipt before opening data; another read is refused.
Deviations: section 8b cannot PASS without the named A0 references; real camera replay cannot start without item/frame hashes. GPU timing and memory remain unmeasured. No archive mirror ran because network/SSH are forbidden.
The specification was copied once after its initial bounded read; all further specification reads used the workspace copy.
Archive: `out/sb_ktow2.tar`; verify with `sha256sum -c out/sb_ktow2.tar.sha256`. It contains this report, CPU receipts, code, configs and pinned inputs, without weights or frame tensors.
Writing skill: no-archaeology. The changes-vs-v1 sentence is retained because the task explicitly requires it.
