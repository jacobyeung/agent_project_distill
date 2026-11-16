# Build H1-kit-2: standalone evaluator with pinned item sets (reused in RL), R0 exclusion, leftovers of build 1

You are a Codex builder for lane h1_headsft on Trinity node trinity-3-30. Workspace `K=/scratch/jjyeung/orch_n30/h1_headsft/kit`
(write only inside K). It already holds build 1 (read `K/BUILD_REPORT.md` first; keep everything that passes).
Work autonomously to the end; where something is ambiguous, choose the conservative option, record it in
`K/BUILD_REPORT.md` and continue.

## Rules for the build (binding)
- Trinity cluster rules: `/home` and `/data*` are slow shared NFS. Never run recursive grep/find/du/ls -R or any search
  over `/home` or `/data*`; read only named files there, in bounded parts. Bounded `find -maxdepth 5` is allowed inside the
  named `/scratch` directories below. Keep K under 1.5 GB.
- No Git. No ssh/scp/rsync/network. No GPU (`CUDA_VISIBLE_DEVICES=""`). No deletion or modification outside K; every
  input path is read-only (copy into K what you must change and record the source sha256).
- Python `/scratch/jjyeung/envs/p1cpu/bin/python -B`; temporaries in `K/tmp`; at most 32 GB RAM and 16 threads per process.
- No answer post-processing: the model converts units and formats numbers itself; the evaluator converts only the
  EXPECTED value into the question's unit when it compares, never the model's text.

## Why
The orchestrator ordered (2026-11-16 12:57Z): the call-placement / head-accuracy / usage evaluator must be a standalone
tool with fixed item sets, so the RL lane (b09_rlkit) runs it at RL checkpoints and the SFT and RL curves pair. It also
ordered (13:07Z): no row, frame, cache or training stream of this or any later leg may use a room of the reserve set R0
(`/scratch/jjyeung/orch_n30/h1_headsft/work/auth/R0_ROOMS.txt`, sha256 bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3,
372 rooms, keys `scannet/sceneNNNN` covering all rescans and `scannetpp/<id>`; R0-dev = `R0_DEV_ROOMS.txt` beside it,
100 rooms, development reads only).

## Deliverables (priority order; tests pass before moving on)
0. Fix build 1's evaluator failure by fixing the criterion, not the gap rule. `box_grid_5cm` is a fixed measurement rule and
   stays as it is. M3 compares against the PRINTED values: the expected answer of a perturbed run is the program's
   decision on the perturbed run's own printed responses (distance: the printed perturbed gap; displacement: the printed
   perturbed distance; direction: the option the four printed components select; rotation: the printed turn), never
   k times the unperturbed value. An item enters a mode's denominator only when the perturbation changes the printed
   decision (a different option, or a printed number moved by at least 20%). Follow = answer within 5% of the expected
   value converted into the question's unit (exact for options); stick = answer within 5% of the unperturbed run's
   answer. Replace the failing acceptance test with: scale_scene 2 moves the printed gap by at least 20% on the fixture,
   and the copier scores follow 1.0 against the printed value. Registered bars: follow >= 0.80, stick <= 0.10 per type.
1. `K/h1eval/cli.py`, one entry point with subcommands:
   - `items build`: writes pinned item-set manifests `K/items/<set>.json` (source path + source sha256 + canonical
     item list + its sha256 + per-type counts + room key per item). Sets, from these read-only copies on this node:
     `revsi999` from `/scratch/jjyeung/orch_n30/b07_offread/in/kit_revsi/inputs/i1.json` (999 items; 283
     object_abs_distance all "in meters", 37 room);
     `devs1_routed` (the 636 dev-S1 items of the native read: 150 per camera type, 150 distance, 36 room) from the C8r
     native kit copy under `/scratch/jjyeung/orch_n30/b07_offread/in/c8r/` or the reader lane's
     `/scratch/jjyeung/orch_n30/b04_e2ehook/work/n13/` (locate the task file with bounded find; record which one);
     `devs1_direct` from `/scratch/jjyeung/orch_n30/b07_offread/in/readk/kit/reader/e193_items.json` (the D0 stop-rule set);
     `r0dev` as an interface stub that refuses until an item file is supplied. Every set except `r0dev` refuses if any
     item's room is in R0_ROOMS.txt; the manifest records the count checked and found (0 expected).
   - `run --export <dir> --items <manifest> --arms own[,tower] --modes <list> --out <dir> [--frames 32] [--gt <npz dir>]`:
     the build-1 evaluator over the reader core; per-item JSONL plus one curve record
     `curve.json` = {lineage, step, export sha256, item-set sha256, evaluator code sha256 (over K/h1eval), frames,
     arms, modes, per-type M1/M2/M3/M4 with room-bootstrap 95% intervals (10,000 draws, seed 20261115)}.
     M1 reports the call rate for EVERY type: exact expected sequences for the four routed types (build 1's
     `expected_calls`), and for head-informable direct types (object_counting, object_rel_distance,
     object_rel_direction_medium/hard) the call rate and openers only, because a both-path model may legitimately call.
   - `pair --a <run dir> --b <run dir>`: paired per-type differences on the shared items (room bootstrap as above);
     refuses different item-set hashes.
   - `curve <run dirs...>`: one table ordered by lineage then step (SFT steps, then RL steps), each row's hashes shown.
   - Tests: items build reproduces the counts above and the R0 check; a run on the tiny fixture writes a valid curve
     record; pair refuses mismatched sets; curve orders mixed SFT/RL records; the evaluator's code hash changes when a
     scorer changes.
2. R0 exclusion in the trainer patch (`K/tree`, `K/patches/h1_trainer.patch`): config `h1.r0_rooms` (path + sha256 pin
   of R0_ROOMS.txt). At stream preparation and again at admission, every row of every stream (pose, vqa, routing,
   pointing) whose room maps into R0 is dropped and counted per stream (ScanNet `sceneNNNN_XX` -> `scannet/sceneNNNN`;
   ScanNet++ scene id -> `scannetpp/<id>`; ARKitScenes ids never match). Reuse the tree's exclusion machinery
   (`carrier_c1_routing.load_exclusions/excluded`, `s1_exclusions.py`) instead of new parsing where it fits. Switch absent
   = byte-identical behaviour (extend build 1's OFF identity test). Tests: synthetic rows in R0 are dropped and counted;
   rows outside pass; the pin mismatch refuses.
3. Build 1's open items listed in `K/BUILD_REPORT.md` that need no GPU and no unavailable input.
4. `K/patches/faithful_own_rows.patch`: S1 alone (faithful own-value camera rows; config switch
   `h1.faithful_own_camera_rows`), as a plain unified diff against the sealed tree, separate from S2, stop_after_step and
   R0, plus `K/patches/FAITHFUL_FIX_FOR_TREE.md` (at most 30 lines: the defect at `carrier_c1_routing.py:443-447`, what
   the patch changes, the switch, OFF identity, the tests and commands that prove it) so the tree lane can carry it in
   its next build. Show that h1_trainer.patch = faithful_own_rows.patch + the rest (apply both orders in K/tmp copies).
5. Update `K/BUILD_REPORT.md` (every test command with pass/fail counts; what is unverified) and `K/SHA256SUMS`, and add
   `K/README_EVAL.md` (how b09_rlkit runs `items build`, `run`, `pair`, `curve` on an RL checkpoint, in at most 40 lines).
