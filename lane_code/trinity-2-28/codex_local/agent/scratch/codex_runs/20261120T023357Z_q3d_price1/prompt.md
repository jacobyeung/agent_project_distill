# Build brief q3d_price1: pricing kit for Qwen-3D grounding under predicted geometry (CPU build only)

You are a Codex builder on trinity-2-28. Work only in W = /scratch/jjyeung/orch_n30/q3d_price1 (node-local). B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Read B/tools/LANE_RULES.md first; its rules bind you. Execute everything yourself; ask nobody to run things for you.

## Why (the decision this feeds)
Project goal: a ~9B spatial VLM, end to end from RGB, whose chain of thought calls heads inside its own checkpoint. Our largest measured loss on object questions is grounding: objects never proposed, or located in too few frames. Qwen-3D (arXiv 2608.02980; code and checkpoints linked from https://qwen-3d.github.io/) grounds objects in 3D with a mask decoder over Qwen2.5-VL's own tokens, but it takes SENSOR depth and dataset camera poses as input and never reports a run on geometry predicted from RGB. We run RGB only.

Question: how much grounding accuracy does Qwen-3D lose when sensor depth and dataset poses are replaced by geometry predicted from the same RGB frames by our frozen tower G3T (thatbrguy/g3t, a gravity-aligned VGGT-1B fine-tune; not metric, so it needs a scale)? One number decides whether its decoder recipe becomes our grounding-head candidate for the next leg.

## Arms (same scenes, same frames, same queries in every arm)
- A: sensor depth + dataset poses (the paper's setting).
- B: G3T depth x metric scale + G3T poses (RGB only). Primary scale = a deployable rule that uses no ground truth (find our rule in the records below; if you cannot reproduce it on this node, use the median ratio of a monocular metric depth model to G3T depth and say so). Secondary column: oracle per-scene scale.
- C1: G3T depth x scale + dataset poses. C2: sensor depth + G3T poses. These split depth from pose.
Benchmark: ScanRefer validation with the repository's own evaluation script, Qwen-3D 3B checkpoint, Acc@0.25 and Acc@0.5. Subset: at least 100 validation scenes with all their queries, fixed by a seeded list written into the kit. Paired bootstrap over scenes, 10,000 draws.

Details you must get right:
- Frame parity: every arm sees the identical frame list per scene. G3T handles a limited number of frames per call; pick the count G3T supports (64 unless the records say otherwise), and also report arm A at the repository's default frame setting.
- World frame: put the predicted cloud in a z-up, gravity-aligned frame like ScanNet's. Predicted boxes must be scored in the dataset frame: fit a rigid transform (rotation and translation only, no scale, for the primary column) from G3T camera centres to dataset camera centres per scene and apply it to the predictions. This uses dataset poses for scoring only, never as model input; say so in the record.
- Voxel size, pooling and token limits stay at the repository's defaults in every arm.

## Registered reading (write it into the record before any run exists)
- Gate 0: arm A must land within 3 points of the paper's 62.2 Acc@0.25 on the subset (subset noise allowed for by its interval). If not, stop and report an environment mismatch.
- B minus A at Acc@0.25, paired: -5 or better means "predicted geometry suffices; the decoder recipe is a grounding-head candidate". -15 or worse means "needs sensor geometry; closed". In between, C1 and C2 name which of depth or pose to improve.
- Confounds to state beside the result: ScanRefer validation scenes overlap our benchmark scenes, so this is a diagnostic only (no output becomes a training row or an init); the checkpoint saw only sensor geometry in training, so a drop bounds what a model trained on predicted geometry would lose from above; the scale rule is ours, not the paper's.

## What to build tonight (no GPU, no job submission)
1. Clone the public repository once (shallow) into W/src. Read its README and evaluation path. Record the commit.
2. Inventory the inputs the evaluation needs (checkpoint files and sizes, ScanRefer annotations, posed RGB-D frames per validation scene: colour, depth, intrinsics, poses) and what already exists on this cluster. Search only named places: /data2/jjyeung/agent_project_data/distill_design/INDEX.md (search it for ScanNet, G3T, tower exports, dev-S1, scale) and the records it names; a top-level `ls` of a dataset root that a record names. Never run find, du, ls -R or grep -r on /home or /data*.
3. Environment under W/env (never under /home). Point every cache at W (XDG_CACHE_HOME, HF_HOME, PIP_CACHE_DIR, TMPDIR).
4. Write W/kit: the geometry-source adapter (arms A, B, C1, C2), the scene and frame list builder, the scoring alignment, the bootstrap, one command run_read.sh that takes a GPU index, and unit tests for the adapter (round trip: sensor geometry through the adapter reproduces the repository's own point cloud for one scene to 1e-4; frame lists identical across arms; rigid alignment recovers a known transform).
5. Dry run on CPU: one scene through the full path of arm A and arm B, as far as the forward pass if memory and time allow (3B model, a few frames is enough), otherwise through tokenisation and voxel pooling with shapes checked. Say exactly how far it ran.
6. Record: write /data2/jjyeung/agent_project_data/distill_design/QWEN3D_PREDICTED_GEOMETRY_PRICING_20261120.md (question, arms, registered reading, confounds, options rejected with reasons, what might not work and how we would notice, status) and add one line to INDEX.md in that folder. Both are small files; write each once.

## Limits (cluster rules; a violation costs the user their cluster access)
- No GPU, no Slurm or Orchard job, no ssh, no git except the one shallow clone into W/src, no deletion commands of any kind (name files to remove in the report instead).
- Downloads: every download above 20 MB crosses the head node and must register with the IO governor before it moves a byte: read /data3/jjyeung/orch_n13_20261026/io_governor/README.md and follow it (one stream at a time, 8 MB/s; the node needs a live agent, tmux `iogov_agent`). If you cannot register, stop and post a BLOCKER. Never download unthrottled, never in parallel, never with `hf download`; use `curl -L --limit-rate 8M` inside the governed path. pip installs go through the same rule when a wheel is above 20 MB.
- Disk: stay under 20 GB in W tonight (code, environment, the 3B checkpoint). Do not fetch ScanNet frames or anything larger; report the size and source instead. Check `df -h /scratch` before and after; stop if free space is under 150 GB.
- Never read /data* or /home in bulk. A single file under 20 MB may be read once.

## Deliverables
Post one event file when done, named with the real UTC time from `date -u +%Y%m%dT%H%MZ`:
- B/events/q3d_price/<UTC>_RESULT_q3d_price1_kit_ready.md (at most 20 lines): kit path and sha256 of its tar, repository commit, what the dry run reached, inputs present and inputs missing with sizes and sources, the GPU-minutes estimate for the four arms on one 48 GB card, disk used, and the exact command to run.
- or B/events/q3d_price/<UTC>_BLOCKER_q3d_price1_<reason>.md with the evidence, if the checkpoint or code is not public, the governor refuses, or an input cannot be had under 20 GB.
Out of scope: the GPU read itself (the orchestrator assigns a card and gives the GO), any training, any change outside W and the two record files.
