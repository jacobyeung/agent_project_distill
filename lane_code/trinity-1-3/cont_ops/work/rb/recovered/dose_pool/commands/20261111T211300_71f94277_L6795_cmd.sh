<!-- recovered by seal_plan: transcript=71f94277 line=6795 utc=2026-11-11T21:13:00.629Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; mkdir -p devs1_tower/events devs1_tower/work devs1_tower/out; T=$(date -u +%Y%m%dT%H%MZ)
cat > devs1_tower/BRIEF.md <<'EOF'
# devs1_tower (Codex Astra): the adapter that runs the geometry tower on the held-out development scenes, on CPU with a fixture test
Your folder: /scratch/jjyeung/orch_cd/devs1_tower (write only here). Everything else is read-only: copy what you change into work/. The card operator (lane evalx) adopts your kit and runs it on a GPU later.

## Why
A held-out development set on training-side scenes ("dev-S1": /scratch/jjyeung/orch_cd/dose_pool/out/DEV_S1/MANIFEST.json, MANIFEST.md; its `geometry_tower_job` lists the captures) is where fusion and route rules will be frozen for benchmarks whose test scenes cover every other development scene. That needs the geometry tower's exports (G3T depth and pose, and the student's V-C depth head) for those captures in the format the pricing code reads.

## Spec (written by the card operator; follow it unless it is wrong, and say where you departed)
/scratch/jjyeung/orch_cd/evalx/events/20261111T2111Z_RESULT_devs1_tower_export_prep.md (read it whole). In short: reuse lane mdg_next's E0 tower path (/scratch/jjyeung/orch_cd/mdg_next/work/e0kit/run_e0.sh and its stages anchors, export, g3t, heads; /scratch/jjyeung/orch_cd/mdg_next/STATUS.md and its RESULT events describe it), which matches the reference export /scratch/jjyeung/orch_cd/ttower/work/geo/heads_g3s64_vcd to 0.1%.
Build:
1. `devs1_anchors.py`: for each capture, choose the dense frames floor-uniform from the frames the capture has in the k6 frame index (64 where at least 64 exist, otherwise all 32), pick 32 anchors floor-uniform among them, pin every frame file by sha256, and write the manifests the E0 stages read. Scenes are named {scannet,scannetppv2,arkitscenes}/<scene>; heads files <dataset>__<scene>.npz, as in heads_g3s64. Captures with only 32 frames are a separate, labelled set (g3s32): never mixed into the 64-frame set, and the frozen scale rule is recorded as applied outside its fitted format.
2. `devs1_tower.sh`: runs anchors, export, g3t and heads for one card, taking the frame root, the checkpoint paths, the output root and the card as arguments (nothing names a node), under the vnice wrapper, with a stall guard that stops the run when its progress file is quiet for 1,200 s, resumable per capture, with a preflight (free card, free disk, every pinned frame present and matching its sha, checkpoints present).
3. A CPU fixture test with synthetic frames that runs anchors and the heads stage end to end on stub tower outputs and checks the output format against a real file of heads_g3s64 (keys, shapes, dtypes, conventions), plus tests of the preflight refusals and of resume.
4. out/DEVS1_TOWER.md: what to stage on the run node (the list of 10,764 frame files by sha with total bytes, written as a file the Orchard operator can tar from; checkpoints; code), the launch line, GPU-hours, the outputs and how the pricing code (lane gt_ceiling, /scratch/jjyeung/orch_cd/gt_ceiling/work/tg) will read them, and what ground truth exists on this node for scoring (lane dose_pool's GT.npz files cover part of the captures: say which).

## Limits
CPU only; no GPU, no ssh, no git commands, no network, no deletion commands of any kind. Run under `ulimit -f 204800`; folder under 1 GB; temporary files under work/tmp. /home and /data* are overloaded network storage: do not read or write them. You cannot ask questions: decide, and write the choice down.

## Deliver
out/kit/ (sealed copy with SHA256SUMS), out/FRAMES_BY_SHA.txt, out/DEVS1_TOWER.md, tests and their counts, events/<UTC stamp from date -u +%Y%m%dT%H%MZ>_RESULT_devs1_tower.md and a final message, each at most 15 lines.
EOF
tmux new -d -s cx_devs1_tower "bash /scratch/jjyeung/orch_cd/orch_tools/codex_local.sh implement /scratch/jjyeung/orch_cd/devs1_tower /scratch/jjyeung/orch_cd/devs1_tower/BRIEF.md --model gpt-6-astra --effort high --skip-git-check --label devs1_tower > /scratch/jjyeung/orch_cd/devs1_tower/dispatch.out 2>&1"
cat > evalx/inbox/${T}_ORCH_ANSWER_devs1.md <<'EOF'
# ORCH ANSWER (dev-S1 tower export): defaults 1 and 2 accepted; Codex builds the adapter, not you
(1) Frames: I ask lane orchard_cp2 for one tar stream of the 10,764 sha-named PNGs (about 3.1 GB) from Orchard to trinity-2-18 at no more than 5 MB/s; you then make the one IB pipe to 1-18. (2) The 97 captures with 32 frames run G3T at 32, labelled g3s32 and reported separately; the 57 dense captures are the primary set. (3) Codex lane devs1_tower builds the adapter from your spec (/scratch/jjyeung/orch_cd/devs1_tower; RESULT in its events folder; adopt and dry-run it when it lands). Your attention stays on the run on GPU 6.
EOF
cat > orchard_cp2/inbox/${T}_ORCH_devs1_frames.md <<'EOF'
# ORCH: a small transfer when Codex lane devs1_tower has written its frame list (not before)
The held-out development set needs 10,764 frame files (about 3.1 GB) from the k6tk frame store on Orchard for a tower export on Trinity. When /scratch/jjyeung/orch_cd/devs1_tower/out/FRAMES_BY_SHA.txt exists, tar exactly those files from the store and stream them once to trinity-2-18 (/dev/shm/jjyeung_devs1_frames; it has 16 GB free: check first), at no more than 5 MB/s, with a manifest and sha256 check on arrival; then tell lane evalx through its inbox. One stream, no retry loop; if it drops, stop and tell me. This reads the frame store only; it changes nothing on Orchard.
EOF
S=/tmp/claude-25409/-scratch-jjyeung-orch-home-distill/71f94277-362e-467c-a4bc-ccc9ae6b87c8; printf 'devs1_tower|tmux:cx_devs1_tower||\n' >> $S/scratchpad/LANES; echo "$(date -u +%Y-%m-%dT%H:%MZ) evalx RESULT 2111Z dev-S1 tower export prep: reuse mdg_next's E0 tower path; frames (10,764 PNGs, ~3.1 GB) exist only in k6tk on Orchard/AWS; 57 captures have >=64 frames (primary), 97 have 32 (g3s32, separate); GT on node for 54 captures. Decided: Codex Astra devs1_tower builds the adapter (tmux cx_devs1_tower); orchard_cp2 streams the frames by sha list at 5 MB/s when the list exists; evalx stays on GPU 6." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md; tail -n 30 $S/tasks/b42sklafi.output | cut -c1-3000